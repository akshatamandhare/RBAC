# Performance and Security Testing Report

## Endpoint Latency Summary (ms)

| Endpoint | Requests | Avg | P95 | Max |
|---|---:|---:|---:|---:|
| GET /admin/users (admin) | 1 | 9.67 | 9.67 | 9.67 |
| GET /admin/users (finance denied) | 1 | 5.95 | 5.95 | 5.95 |
| GET /health | 20 | 2.98 | 3.64 | 3.70 |
| POST /chat/query (finance) | 20 | 11.36 | 30.07 | 40.78 |
| POST /chat/query (hr) | 10 | 9.06 | 8.85 | 14.76 |
| POST /chat/query (unauthorized) | 1 | 7.34 | 7.34 | 7.34 |

## Security Assertions

- Finance denied admin endpoint: PASS (403)
- Unauthorized chat rejected: PASS (401)
- Admin allowed admin endpoint: PASS (200)

## Optimization Notes

- Retrieval uses role-scoped TF-IDF cache to avoid repeated vectorizer fitting in steady state.
- For larger corpora, move to persistent vector DB retrieval only and reduce in-process ranking load.
- Add response compression and stricter timeout/retry policy at API gateway.