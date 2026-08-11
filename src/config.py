from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env before instantiating Settings so local overrides take effect.
load_dotenv()


class Settings(BaseSettings):
    """Application configuration, sourced from environment variables and .env."""

    github_token: str = ""
    github_webhook_secret: str = ""
    anthropic_api_key: str = ""
    database_url: str = "postgresql+asyncpg://auditor:changeme@postgres:5432/iac_auditor"
    redis_url: str = "redis://redis:6379/0"
    audit_branch_prefix: str = "security/auto-fix/"
    log_level: str = "INFO"
    llm_model: str = "claude-3-sonnet-20241022"

    class Config:
        env_file = ".env"


settings = Settings()
