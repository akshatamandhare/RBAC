from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "RBAC Backend"
    secret_key: str = os.getenv("RBAC_SECRET_KEY", "change-this-in-production")
    algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    database_url: str = os.getenv("RBAC_DATABASE_URL", "sqlite:///./rbac.db")


settings = Settings()
