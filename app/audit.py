from sqlalchemy.orm import Session
from app.models import AuditLog


def write_audit_log(
    db: Session,
    *,
    username: str,
    action: str,
    method: str,
    path: str,
    status_code: int,
    details: str = "",
) -> None:
    entry = AuditLog(
        username=username or "anonymous",
        action=action,
        method=method,
        path=path,
        status_code=status_code,
        details=details,
    )
    db.add(entry)
    db.commit()
