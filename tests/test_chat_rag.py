import os
from pathlib import Path
from fastapi.testclient import TestClient


TEST_DB = Path("./test_rbac_chat.db")
os.environ["RBAC_DATABASE_URL"] = "sqlite:///./test_rbac_chat.db"
os.environ["RBAC_SECRET_KEY"] = "chat-test-secret"
os.environ["LLM_PROVIDER"] = "mock"

if TEST_DB.exists():
    TEST_DB.unlink()

from app.main import app  # noqa: E402

client = TestClient(app)


def login(username: str, password: str) -> dict:
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_profile_endpoint_returns_departments():
    tokens = login("finance_user", "FinancePass123!")
    resp = client.get("/auth/profile", headers=auth_header(tokens["access_token"]))
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["role"] == "finance"
    assert "finance" in payload["departments"]


def test_chat_query_returns_sources_and_confidence():
    tokens = login("finance_user", "FinancePass123!")
    resp = client.post(
        "/chat/query",
        headers=auth_header(tokens["access_token"]),
        json={"query": "quarterly financial results", "top_k": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert isinstance(data["sources"], list)
    assert data["retrieved_count"] >= 0
    assert 0.0 <= data["confidence"] <= 1.0


def test_rbac_is_enforced_on_chat_with_missing_token():
    resp = client.post("/chat/query", json={"query": "test", "top_k": 3})
    assert resp.status_code == 401
