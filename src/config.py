from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    github_token: str = ""
    github_webhook_secret: str = ""
    anthropic_api_key: str = ""
    database_url: str = "postgresql+asyncpg://auditor:changeme@postgres:5432/iac_auditor"
    redis_url: str = "redis://redis:6379/0"
    audit_branch_prefix: str = "security/auto-fix/"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
