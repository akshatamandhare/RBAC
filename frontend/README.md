# Streamlit Frontend

## Run Backend
From project root:

```powershell
python main.py
```

This starts FastAPI at `http://127.0.0.1:8000`.

## Run Frontend
In a new terminal from project root:

```powershell
streamlit run frontend/streamlit_app.py
```

Optional backend URL override:

```powershell
$env:RBAC_API_BASE_URL="http://127.0.0.1:8000"
streamlit run frontend/streamlit_app.py
```

## Default Sample Accounts
- `admin_user / AdminPass123!`
- `finance_user / FinancePass123!`
- `hr_user / HRPass123!`
- `engineering_user / EngPass123!`
- `employee_user / EmployeePass123!`

## Notes
- UI displays role + accessible departments.
- Responses include source citations and confidence scores.
- Access control is enforced server-side by JWT + RBAC middleware.
