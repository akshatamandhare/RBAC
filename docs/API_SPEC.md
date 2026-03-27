# API Specification and Endpoint Reference

Base URL: http://127.0.0.1:8000

## Public Endpoints

### GET /health
- Description: service liveness
- Response 200:
  - status
  - service

### POST /auth/login
- Request:
  - username
  - password
- Response 200:
  - access_token
  - refresh_token
  - token_type

### POST /auth/refresh
- Request:
  - refresh_token
- Response 200:
  - access_token
  - refresh_token
  - token_type

### POST /auth/logout
- Request:
  - refresh_token
- Response 200:
  - message

## Authenticated Endpoints (Bearer access token)

### GET /auth/me
- Returns current user identity

### GET /auth/profile
- Returns:
  - username
  - role
  - departments (allowed)

### POST /chat/query
- Request:
  - query (string)
  - top_k (int, optional)
- Response:
  - user
  - role
  - query
  - answer
  - confidence
  - retrieved_count
  - sources[]
    - chunk_id
    - source_document
    - department
    - retrieval_score
    - snippet

## Department/Role Protected Examples
- GET /finance/reports
- GET /hr/policies
- GET /engineering/roadmap
- GET /general/announcements

## Admin Endpoints
- GET /admin/users
- GET /admin/audit

## Error Codes
- 400: invalid input
- 401: missing or invalid token
- 403: insufficient role permissions
- 404: resource/user not found
- 500: internal error
