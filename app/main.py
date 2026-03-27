from datetime import datetime
from threading import Lock
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db, SessionLocal
from app.models import User, RefreshToken, AuditLog
from app.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserOut,
    AuditLogOut,
    ChatRequest,
    ChatResponse,
    ProfileResponse,
)
from app.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.seed_data import SAMPLE_USERS
from app.audit import write_audit_log
from app.rbac import RBACMiddleware
from app.rag_service import run_rag_query, accessible_departments_for_role


app = FastAPI(title="RBAC FastAPI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RBACMiddleware)

_db_init_lock = Lock()
_db_initialized = False


def seed_users() -> None:
    db = SessionLocal()
    try:
        for item in SAMPLE_USERS:
            existing = db.query(User).filter(User.username == item["username"]).first()
            if existing:
                continue
            db_user = User(
                username=item["username"],
                password_hash=hash_password(item["password"]),
                role=item["role"],
                is_active=True,
            )
            db.add(db_user)
        db.commit()
    finally:
        db.close()


def ensure_initialized() -> None:
    global _db_initialized
    if _db_initialized:
        return
    with _db_init_lock:
        if _db_initialized:
            return
        Base.metadata.create_all(bind=engine)
        seed_users()
        _db_initialized = True


@app.on_event("startup")
def on_startup() -> None:
    ensure_initialized()


@app.middleware("http")
async def ensure_db_ready(request: Request, call_next):
    ensure_initialized()
    return await call_next(request)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "rbac-backend"}


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        write_audit_log(
            db,
            username=payload.username,
            action="login_failed",
            method="POST",
            path="/auth/login",
            status_code=401,
            details="Invalid username or password",
        )
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not user.is_active:
        write_audit_log(
            db,
            username=user.username,
            action="login_failed",
            method="POST",
            path="/auth/login",
            status_code=403,
            details="User is inactive",
        )
        raise HTTPException(status_code=403, detail="Inactive user")

    access_token = create_access_token(subject=user.username, role=user.role)
    refresh_token, refresh_jti, refresh_expiry = create_refresh_token(subject=user.username, role=user.role)

    db_token = RefreshToken(user_id=user.id, token_jti=refresh_jti, expires_at=refresh_expiry, revoked=False)
    db.add(db_token)
    db.commit()

    write_audit_log(
        db,
        username=user.username,
        action="login_success",
        method="POST",
        path="/auth/login",
        status_code=200,
        details=f"role={user.role}",
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@app.post("/auth/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        claims = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    if claims.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    username = claims.get("sub", "")
    role = claims.get("role", "")
    jti = claims.get("jti", "")

    db_token = db.query(RefreshToken).filter(RefreshToken.token_jti == jti).first()
    if db_token is None or db_token.revoked:
        raise HTTPException(status_code=401, detail="Refresh token revoked or unknown")

    if db_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    access_token = create_access_token(subject=username, role=role)
    new_refresh, new_jti, new_expiry = create_refresh_token(subject=username, role=role)

    db_token.revoked = True
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    db.add(RefreshToken(user_id=user.id, token_jti=new_jti, expires_at=new_expiry, revoked=False))
    db.commit()

    write_audit_log(
        db,
        username=username,
        action="token_refresh",
        method="POST",
        path="/auth/refresh",
        status_code=200,
    )

    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@app.post("/auth/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> dict:
    try:
        claims = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    jti = claims.get("jti", "")
    username = claims.get("sub", "anonymous")
    db_token = db.query(RefreshToken).filter(RefreshToken.token_jti == jti).first()

    if db_token:
        db_token.revoked = True
        db.commit()

    write_audit_log(
        db,
        username=username,
        action="logout",
        method="POST",
        path="/auth/logout",
        status_code=200,
    )
    return {"message": "Session terminated"}


@app.get("/auth/me", response_model=UserOut)
def auth_me(request: Request, db: Session = Depends(get_db)) -> UserOut:
    username = getattr(request.state, "username", None)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(id=user.id, username=user.username, role=user.role, is_active=user.is_active)


@app.get("/auth/profile", response_model=ProfileResponse)
def auth_profile(request: Request, db: Session = Depends(get_db)) -> ProfileResponse:
    username = getattr(request.state, "username", None)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return ProfileResponse(
        username=user.username,
        role=user.role,
        departments=accessible_departments_for_role(user.role),
    )


@app.post("/chat/query", response_model=ChatResponse)
def chat_query(payload: ChatRequest, request: Request) -> ChatResponse:
    username = getattr(request.state, "username", None)
    role = getattr(request.state, "role", None)
    if not username or not role:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    result = run_rag_query(username=username, role=role, question=payload.query, top_k=payload.top_k)
    return ChatResponse(**result)


@app.get("/finance/reports")
def finance_reports() -> dict:
    return {"data": "Finance quarterly reports"}


@app.get("/hr/policies")
def hr_policies() -> dict:
    return {"data": "HR policy documents"}


@app.get("/engineering/roadmap")
def engineering_roadmap() -> dict:
    return {"data": "Engineering roadmap"}


@app.get("/general/announcements")
def general_announcements() -> dict:
    return {"data": "Company-wide announcements"}


@app.get("/admin/users")
def admin_users(db: Session = Depends(get_db)) -> list[UserOut]:
    users = db.query(User).all()
    return [UserOut(id=u.id, username=u.username, role=u.role, is_active=u.is_active) for u in users]


@app.get("/admin/audit", response_model=list[AuditLogOut])
def admin_audit_logs(db: Session = Depends(get_db)) -> list[AuditLogOut]:
    rows = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200).all()
    return [
        AuditLogOut(
            timestamp=row.timestamp,
            username=row.username,
            action=row.action,
            method=row.method,
            path=row.path,
            status_code=row.status_code,
            details=row.details,
        )
        for row in rows
    ]
