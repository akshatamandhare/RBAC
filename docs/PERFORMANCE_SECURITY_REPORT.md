# Performance and Security Testing Report

This report is generated and updated from:
- scripts/benchmark_system.py
- pytest integration suites in tests/

## Scope
- Authentication workflow
- RBAC enforcement and denial paths
- RAG query response latency
- Session refresh/logout token revocation
- Data isolation checks between finance and HR

## Metrics Collected
- Endpoint average latency
- P95 latency
- Maximum observed latency
- HTTP status correctness for protected endpoints

## Security Assertions
- Unauthorized requests to protected endpoints return 401
- Authenticated but unauthorized role requests return 403
- Refresh token revocation prevents replay
- Audit logs contain allow/deny traces

## Optimization Actions
- Added role-scoped retrieval cache in app/rag_service.py
- Added lazy DB initialization middleware in app/main.py for resilient startup in all execution contexts
- Maintained mock fallback for deterministic LLM behavior during tests

## Reproduction
Run:
1. python -m pytest -q
2. python scripts/benchmark_system.py

Then review generated report:
- artifacts/module2/reports/performance_security_report.md
