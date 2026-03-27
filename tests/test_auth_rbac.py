import os
from pathlib import Path
from fastapi.testclient import TestClient


TEST_DB = Path("./test_rbac.db")
os.environ["RBAC_DATABASE_URL"] = "sqlite:///./test_rbac.db"
os.environ["RBAC_SECRET_KEY"] = "test-secret-key"

if TEST_DB.exists():
    TEST_DB.unlink()

from app.main import app  # noqa: E402

client = TestClient(app)


def login(username: str, password: str) -> dict:
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()


def auth_header(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def test_login_success_and_me():
    tokens = login("finance_user", "FinancePass123!")
    me = client.get("/auth/me", headers=auth_header(tokens["access_token"]))
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == "finance_user"
    assert body["role"] == "finance"


def test_login_failure():
    resp = client.post("/auth/login", json={"username": "finance_user", "password": "wrong"})
    assert resp.status_code == 401


def test_finance_cannot_access_hr():
    tokens = login("finance_user", "FinancePass123!")
    resp = client.get("/hr/policies", headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 403


def test_finance_can_access_finance():
    tokens = login("finance_user", "FinancePass123!")
    resp = client.get("/finance/reports", headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 200


def test_admin_can_access_admin_endpoints():
    tokens = login("admin_user", "AdminPass123!")
    users = client.get("/admin/users", headers=auth_header(tokens["access_token"]))
    assert users.status_code == 200
    audit = client.get("/admin/audit", headers=auth_header(tokens["access_token"]))
    assert audit.status_code == 200


def test_refresh_and_logout_flow():
    tokens = login("engineering_user", "EngPass123!")
    refresh_resp = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_resp.status_code == 200
    refreshed = refresh_resp.json()
    assert refreshed["access_token"]

    logout_resp = client.post("/auth/logout", json={"refresh_token": refreshed["refresh_token"]})
    assert logout_resp.status_code == 200

    # Token should now be revoked
    second_refresh = client.post("/auth/refresh", json={"refresh_token": refreshed["refresh_token"]})
    assert second_refresh.status_code == 401


def test_audit_log_is_written_for_rbac_denial():
    tokens = login("employee_user", "EmployeePass123!")
    denied = client.get("/finance/reports", headers=auth_header(tokens["access_token"]))
    assert denied.status_code == 403

    admin_tokens = login("admin_user", "AdminPass123!")
    logs_resp = client.get("/admin/audit", headers=auth_header(admin_tokens["access_token"]))
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert any(item["action"] == "rbac_denied" for item in logs)
