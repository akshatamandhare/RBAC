from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.database import SessionLocal
from app.audit import write_audit_log
from app.security import decode_token


PROTECTED_PATH_ROLES = {
    "/admin": {"admin", "ceo"},
    "/finance": {"admin", "ceo", "leadership", "finance_lead", "finance"},
    "/hr": {"admin", "ceo", "leadership", "hr_lead", "hr"},
    "/engineering": {"admin", "ceo", "leadership", "engineering_lead", "tech_lead", "engineering"},
    "/general": {"admin", "ceo", "leadership", "all_employees"},
    "/auth/me": {"admin", "ceo", "leadership", "finance", "finance_lead", "hr", "hr_lead", "engineering", "engineering_lead", "tech_lead", "marketing", "sales", "all_employees"},
    "/auth/profile": {"admin", "ceo", "leadership", "finance", "finance_lead", "hr", "hr_lead", "engineering", "engineering_lead", "tech_lead", "marketing", "sales", "all_employees"},
    "/chat": {"admin", "ceo", "leadership", "finance", "finance_lead", "hr", "hr_lead", "engineering", "engineering_lead", "tech_lead", "marketing", "sales", "all_employees"},
}


class RBACMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        required_roles = None

        for prefix, roles in PROTECTED_PATH_ROLES.items():
            if path.startswith(prefix):
                required_roles = roles
                break

        if required_roles is None:
            return await call_next(request)

        db = SessionLocal()
        username = "anonymous"
        try:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                write_audit_log(
                    db,
                    username=username,
                    action="rbac_denied",
                    method=method,
                    path=path,
                    status_code=401,
                    details="Missing bearer token",
                )
                return JSONResponse(status_code=401, content={"detail": "Missing bearer token"})

            token = auth_header.split(" ", 1)[1]
            payload = decode_token(token)
            if payload.get("type") != "access":
                write_audit_log(
                    db,
                    username=username,
                    action="rbac_denied",
                    method=method,
                    path=path,
                    status_code=401,
                    details="Invalid access token type",
                )
                return JSONResponse(status_code=401, content={"detail": "Invalid token type"})

            username = payload.get("sub", "anonymous")
            role = payload.get("role", "")
            request.state.username = username
            request.state.role = role

            if role not in required_roles:
                write_audit_log(
                    db,
                    username=username,
                    action="rbac_denied",
                    method=method,
                    path=path,
                    status_code=403,
                    details=f"Role '{role}' not allowed",
                )
                return JSONResponse(status_code=403, content={"detail": "Insufficient role permissions"})

            response = await call_next(request)
            write_audit_log(
                db,
                username=username,
                action="rbac_allowed",
                method=method,
                path=path,
                status_code=response.status_code,
            )
            return response
        except ValueError:
            write_audit_log(
                db,
                username=username,
                action="rbac_denied",
                method=method,
                path=path,
                status_code=401,
                details="Token decode failure",
            )
            return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})
        finally:
            db.close()
