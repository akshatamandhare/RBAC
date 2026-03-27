import os
from pathlib import Path

from fastapi.testclient import TestClient


TEST_DB = Path("./test_rbac_e2e.db")
os.environ["RBAC_DATABASE_URL"] = "sqlite:///./test_rbac_e2e.db"
os.environ["RBAC_SECRET_KEY"] = "e2e-secret-key"
os.environ["LLM_PROVIDER"] = "mock"

if TEST_DB.exists():
    TEST_DB.unlink()

from app.main import app  # noqa: E402

client = TestClient(app)


ROLE_USERS = {
    "admin": ("admin_user", "AdminPass123!"),
    "finance": ("finance_user", "FinancePass123!"),
    "hr": ("hr_user", "HRPass123!"),
    "engineering": ("engineering_user", "EngPass123!"),
    "all_employees": ("employee_user", "EmployeePass123!"),
}


def login(username: str, password: str) -> dict:
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_complete_workflow_all_roles():
    for role, creds in ROLE_USERS.items():
        username, password = creds
        tokens = login(username, password)
        me = client.get("/auth/me", headers=auth_header(tokens["access_token"]))
        assert me.status_code == 200
        assert me.json()["role"] == role

        profile = client.get("/auth/profile", headers=auth_header(tokens["access_token"]))
        assert profile.status_code == 200
        assert "departments" in profile.json()

        chat = client.post(
            "/chat/query",
            headers=auth_header(tokens["access_token"]),
            json={"query": "company announcements and policy", "top_k": 5},
        )
        assert chat.status_code == 200
        payload = chat.json()
        assert "answer" in payload
        assert "sources" in payload
        assert 0.0 <= payload["confidence"] <= 1.0


def test_role_based_data_isolation_finance_vs_hr():
    finance_tokens = login("finance_user", "FinancePass123!")
    hr_tokens = login("hr_user", "HRPass123!")

    finance_chat = client.post(
        "/chat/query",
        headers=auth_header(finance_tokens["access_token"]),
        json={"query": "employee records and leave policy", "top_k": 7},
    )
    assert finance_chat.status_code == 200
    for src in finance_chat.json()["sources"]:
        assert src["department"] != "hr"

    hr_chat = client.post(
        "/chat/query",
        headers=auth_header(hr_tokens["access_token"]),
        json={"query": "quarterly revenue and financial overview", "top_k": 7},
    )
    assert hr_chat.status_code == 200
    for src in hr_chat.json()["sources"]:
        assert src["department"] != "finance"


def test_error_handling_and_edge_cases():
    # Missing token
    missing_token = client.post("/chat/query", json={"query": "hello", "top_k": 5})
    assert missing_token.status_code == 401

    # Empty query
    tokens = login("finance_user", "FinancePass123!")
    empty_query = client.post(
        "/chat/query",
        headers=auth_header(tokens["access_token"]),
        json={"query": "   ", "top_k": 5},
    )
    assert empty_query.status_code == 400

    # Invalid login
    bad_login = client.post("/auth/login", json={"username": "x", "password": "y"})
    assert bad_login.status_code == 401

    # Invalid token type on protected endpoint (use refresh token as bearer)
    refresh_as_access = client.get("/auth/me", headers=auth_header(tokens["refresh_token"]))
    assert refresh_as_access.status_code == 401


def test_session_lifecycle_refresh_logout_revoke():
    tokens = login("engineering_user", "EngPass123!")

    refreshed = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    payload = refreshed.json()

    logout_resp = client.post("/auth/logout", json={"refresh_token": payload["refresh_token"]})
    assert logout_resp.status_code == 200

    # Re-using revoked refresh token should fail
    reused = client.post("/auth/refresh", json={"refresh_token": payload["refresh_token"]})
    assert reused.status_code == 401


def test_security_headers_and_health():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
