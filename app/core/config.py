from functools import lru_cache

from pydantic import model_validator
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

    @model_validator(mode="after")
    def _production_safety(self):
        # Render gives "postgres://..." / "postgresql://..."; we use the psycopg 3 driver.
        for old in ("postgres://", "postgresql://"):
            if self.database_url.startswith(old):
                self.database_url = (
                    "postgresql+psycopg://" + self.database_url[len(old) :]
                )
        if self.app_env == "prod" and self.jwt_secret == "change-me":
            raise ValueError("JWT_SECRET must be set when APP_ENV=prod")
        return self


@lru_cache  # one instance per process = Singleton (LC07)
def get_settings() -> Settings:
    return Settings()
