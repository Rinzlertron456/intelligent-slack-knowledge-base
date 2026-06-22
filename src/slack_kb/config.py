from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_model: str = "gemini-2.0-flash"
    gemini_embed_model: str = "text-embedding-004"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

    database_url: SecretStr
    gemini_api_key: SecretStr = Field(default=SecretStr(""))

    slack_bot_token: SecretStr = Field(default=SecretStr(""))
    slack_app_token: SecretStr = Field(default=SecretStr(""))
    org_admin_user_ids: str = ""

    retrieval_limit: int = 8
    min_similarity: float = 0.35
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    @field_validator("database_url")
    @classmethod
    def database_url_must_be_postgres(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if not raw.startswith(("postgres://", "postgresql://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return value

    def validate_slack(self) -> None:
        if not self.slack_bot_token.get_secret_value().startswith("xoxb-"):
            raise ValueError("SLACK_BOT_TOKEN must be a Slack bot token")
        if not self.slack_app_token.get_secret_value().startswith("xapp-"):
            raise ValueError("SLACK_APP_TOKEN must be a Socket Mode app token")

    @property
    def org_admins(self) -> set[str]:
        return {
            user_id.strip()
            for user_id in self.org_admin_user_ids.split(",")
            if user_id.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
