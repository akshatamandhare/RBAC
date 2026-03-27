from __future__ import annotations

import os
import time
import sys
from pathlib import Path

from fastapi.testclient import TestClient


REPORT_PATH = Path("artifacts/module2/reports/performance_security_report.md")
TEST_DB = Path("./test_rbac_benchmark.db")

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ["RBAC_DATABASE_URL"] = "sqlite:///./test_rbac_benchmark.db"
os.environ["RBAC_SECRET_KEY"] = "benchmark-secret-key"
os.environ["LLM_PROVIDER"] = "mock"

if TEST_DB.exists():
    TEST_DB.unlink()

from app.main import app  # noqa: E402

client = TestClient(app)


def login(username: str, password: str) -> dict:
    resp = client.post("/auth/login", json={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def timed_request(method: str, path: str, **kwargs):
    start = time.perf_counter()
    response = client.request(method, path, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return response, elapsed_ms


def run_benchmark() -> str:
    fin = login("finance_user", "FinancePass123!")
    hr = login("hr_user", "HRPass123!")
    admin = login("admin_user", "AdminPass123!")

    rows = []

    # Baseline endpoints
    for _ in range(20):
        resp, ms = timed_request("GET", "/health")
        rows.append(("GET /health", resp.status_code, ms))

    for _ in range(20):
        resp, ms = timed_request(
            "POST",
            "/chat/query",
            headers=auth_header(fin["access_token"]),
            json={"query": "quarterly financial results", "top_k": 5},
        )
        rows.append(("POST /chat/query (finance)", resp.status_code, ms))

    for _ in range(10):
        resp, ms = timed_request(
            "POST",
            "/chat/query",
            headers=auth_header(hr["access_token"]),
            json={"query": "employee policy", "top_k": 5},
        )
        rows.append(("POST /chat/query (hr)", resp.status_code, ms))

    # Security checks
    deny_resp, deny_ms = timed_request("GET", "/admin/users", headers=auth_header(fin["access_token"]))
    rows.append(("GET /admin/users (finance denied)", deny_resp.status_code, deny_ms))

    unauth_resp, unauth_ms = timed_request("POST", "/chat/query", json={"query": "x", "top_k": 3})
    rows.append(("POST /chat/query (unauthorized)", unauth_resp.status_code, unauth_ms))

    allow_resp, allow_ms = timed_request("GET", "/admin/users", headers=auth_header(admin["access_token"]))
    rows.append(("GET /admin/users (admin)", allow_resp.status_code, allow_ms))

    # Summaries
    by_endpoint: dict[str, list[float]] = {}
    for name, status, ms in rows:
        if 200 <= status < 500:
            by_endpoint.setdefault(name, []).append(ms)

    lines = []
    lines.append("# Performance and Security Testing Report\n")
    lines.append("## Endpoint Latency Summary (ms)\n")
    lines.append("| Endpoint | Requests | Avg | P95 | Max |")
    lines.append("|---|---:|---:|---:|---:|")

    for name, samples in sorted(by_endpoint.items()):
        s = sorted(samples)
        n = len(s)
        avg = sum(s) / max(1, n)
        p95 = s[min(n - 1, int(0.95 * (n - 1)))]
        max_v = s[-1]
        lines.append(f"| {name} | {n} | {avg:.2f} | {p95:.2f} | {max_v:.2f} |")

    lines.append("\n## Security Assertions\n")
    lines.append(f"- Finance denied admin endpoint: {'PASS' if deny_resp.status_code == 403 else 'FAIL'} ({deny_resp.status_code})")
    lines.append(f"- Unauthorized chat rejected: {'PASS' if unauth_resp.status_code == 401 else 'FAIL'} ({unauth_resp.status_code})")
    lines.append(f"- Admin allowed admin endpoint: {'PASS' if allow_resp.status_code == 200 else 'FAIL'} ({allow_resp.status_code})")

    lines.append("\n## Optimization Notes\n")
    lines.append("- Retrieval uses role-scoped TF-IDF cache to avoid repeated vectorizer fitting in steady state.")
    lines.append("- For larger corpora, move to persistent vector DB retrieval only and reduce in-process ranking load.")
    lines.append("- Add response compression and stricter timeout/retry policy at API gateway.")

    return "\n".join(lines)


def main() -> None:
    report = run_benchmark()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Saved report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
