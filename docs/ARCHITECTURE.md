# System Architecture and Technical Documentation

## Overview
The system provides secure document Q&A with:
- FastAPI backend
- JWT authentication
- Role-based authorization middleware
- RAG service with role-filtered retrieval
- Streamlit frontend for interactive chat and source transparency

## Components
1. Authentication Service
- Endpoints: login, refresh, logout, profile, me
- Token model: short-lived access token + revocable refresh token

2. Authorization Layer
- RBAC middleware validates bearer token and role-to-path permissions
- Audit logs persist allow/deny events for traceability

3. Data Layer
- SQLite via SQLAlchemy models:
  - users
  - refresh_tokens
  - audit_logs

4. RAG Service
- Loads chunk artifacts
- Filters chunks by role and department policy
- Ranks chunks by TF-IDF cosine similarity
- Generates answer with source attribution and confidence score

5. Frontend
- Streamlit chat UI
- Login/session handling
- Displays user role + allowed departments
- Shows source citations and snippets

## Data Flow
1. User logs in through frontend
2. Frontend receives access + refresh tokens
3. Frontend calls /auth/profile to display role context
4. User submits query
5. Backend middleware enforces JWT + RBAC
6. Chat endpoint triggers RAG retrieval and response generation
7. Frontend renders answer, confidence, and source citations

## Security Controls
- Password hashing with bcrypt
- JWT signing with HMAC SHA256
- Refresh token persistence and revocation support
- RBAC path protection
- Audit logging for security-sensitive events

## Reliability and Operations
- Health endpoint for probes
- Deterministic mock LLM fallback when provider unavailable
- Benchmark script for baseline latency and security assertions
