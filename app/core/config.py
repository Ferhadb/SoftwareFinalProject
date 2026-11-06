from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    database_url: str = "sqlite:///./spendsmart.db"
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 60
    categorizer: str = "rules"  # rules | ml | llm | chain
    llm_api_key: str | None = None
    log_level: str = "INFO"


@lru_cache  # one instance per process = Singleton (LC07)
def get_settings() -> Settings:
    return Settings()
