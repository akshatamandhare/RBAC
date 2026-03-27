# Demo Video Script and Recording Checklist

Note: Automated agents cannot record or upload a video file directly. This script is provided to produce the required demo quickly.

## Length
8 to 12 minutes

## Flow
1. Intro (30s)
- State problem: secure enterprise RAG with RBAC
- Show repository structure

2. Backend Security (2m)
- Open app/main.py
- Show auth endpoints and JWT flow
- Show RBAC middleware protection in app/rbac.py

3. Data and RAG (2m)
- Show app/rag_service.py
- Explain role filtering + retrieval + citations + confidence

4. Frontend UX (2m)
- Launch Streamlit frontend
- Login as finance_user
- Ask finance question and inspect sources
- Try HR question and show isolation behavior

5. Role Switching (1.5m)
- Logout and login as hr_user
- Ask HR question, show role and departments in sidebar

6. Admin and Audit (1m)
- Login as admin_user
- Open /admin/audit in API docs or test output

7. Tests and Benchmark (1m)
- Run pytest
- Run scripts/benchmark_system.py
- Show generated reports

## Recording Checklist
- Screen resolution 1080p
- Font scaling readable
- Show commands and outputs
- Keep credentials to sample accounts only
- Export as MP4
