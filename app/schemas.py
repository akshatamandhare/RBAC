from datetime import datetime
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool


class AuditLogOut(BaseModel):
    timestamp: datetime
    username: str
    action: str
    method: str
    path: str
    status_code: int
    details: str


class ChatRequest(BaseModel):
    query: str
    top_k: int = 5


class SourceCitation(BaseModel):
    chunk_id: str
    source_document: str
    department: str
    retrieval_score: float
    snippet: str


class ChatResponse(BaseModel):
    user: str
    role: str
    query: str
    answer: str
    confidence: float
    retrieved_count: int
    sources: list[SourceCitation]


class ProfileResponse(BaseModel):
    username: str
    role: str
    departments: list[str]
