# RBAC Secure RAG System

Enterprise-ready role-based document retrieval and chat platform with:
- FastAPI backend
- JWT authentication
- RBAC middleware enforcement
- RAG pipeline with source citations and confidence scoring
- Streamlit chat frontend

## Repository Structure
- app/: backend API, auth, RBAC, RAG service
- frontend/: Streamlit UI and API client
- tests/: integration/auth/chat test suites
- scripts/: benchmarking and operational scripts
- docs/: architecture, API spec, deployment, reports, role guides
- artifacts/: generated pipeline artifacts and test reports

## Quick Start

### 1) Install
pip install -r requirements.txt

### 2) Start Backend
python main.py

### 3) Start Frontend
streamlit run frontend/streamlit_app.py

### 4) Run Tests
python -m pytest -q

### 5) Run Benchmark
python scripts/benchmark_system.py

## Sample Accounts
- admin_user / AdminPass123!
- ceo_user / CeoPass123!
- finance_user / FinancePass123!
- finance_lead / FinanceLead123!
- hr_user / HRPass123!
- engineering_user / EngPass123!
- employee_user / EmployeePass123!

## Core Features
- Secure auth flow: login, refresh, logout, profile
- Access control: role-path authorization and data-level filtering
- RAG answers: source attribution and confidence score
- Auditability: allow/deny logs persisted in database
- UX transparency: citations and snippets shown in UI

## Documentation
- docs/ARCHITECTURE.md
- docs/API_SPEC.md
- docs/DEPLOYMENT_GUIDE.md

## Deployment
- Local: python main.py and streamlit run frontend/streamlit_app.py
- Containerized: docker compose up --build
<<<<<<< HEAD
- Environment template: .env.example
=======
- Environment template: .env

>>>>>>> 669959f4d67cdefd4f7fb6803f421c014178ef29
