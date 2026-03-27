# FinSolve Chat User Guide by Role

## Overview
The Streamlit app provides role-restricted RAG chat.

Workflow:
1. Login with your account.
2. Submit a question in chat.
3. Review response and source citations.
4. Check confidence score and source snippets.

## Role Access

### admin / ceo / leadership
- Can query all departments.
- Best for enterprise-wide questions.

### finance / finance_lead
- Can query finance content.
- Cannot access HR-only sources.

### hr / hr_lead
- Can query HR content.
- Cannot access finance-only sources.

### engineering / engineering_lead / tech_lead
- Can query engineering content.

### marketing / sales / all_employees
- Can query marketing and general content (as configured by backend policy).

## Source Transparency
Each assistant answer includes:
- source document name
- chunk ID
- department
- retrieval score
- snippet preview

## Confidence Guidance
- 0.70-1.00: high confidence
- 0.40-0.69: moderate confidence
- 0.00-0.39: low confidence (verify with sources)

## Troubleshooting
- 401/Session expired: log in again.
- 403/Insufficient permission: your role cannot access requested department content.
- No sources returned: broaden question or use less specific terms.
