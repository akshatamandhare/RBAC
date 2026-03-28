# Deployment and Setup Guide

## Prerequisites
- Python 3.11+
- pip
- Optional: Docker Desktop

## Local Setup
1. Create and activate virtual environment
2. Install dependencies:
   pip install -r requirements.txt
3. Start backend:
   python main.py
4. Start frontend in separate terminal:
   streamlit run frontend/streamlit_app.py

## Environment Variables
- RBAC_SECRET_KEY: JWT signing secret
- RBAC_DATABASE_URL: default sqlite:///./rbac.db
- LLM_PROVIDER: mock or openai or gemini
- OPENAI_API_KEY: required if LLM_PROVIDER=openai
- OPENAI_MODEL: optional model override
- GEMINI_API_KEY: required if LLM_PROVIDER=gemini
- GEMINI_MODEL: optional model override (default gemini-1.5-flash)
- RBAC_API_BASE_URL: frontend backend base URL

## Docker Deployment
Use Dockerfile and docker-compose.yml in repository root.

- Build and run:
  docker compose up --build

Backend runs on 8000, frontend on 8501.
