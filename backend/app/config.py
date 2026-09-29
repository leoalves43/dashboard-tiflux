"""Runtime settings read from environment (.env via docker compose env_file)."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    url_tiflux: str = "https://api.tiflux.com/api/v2"
    token_tiflux: str
    db_host: str = "db"
    db_port: int = 5432
    db_user: str
    db_password: str
    db_name: str
    schema_name: str = "dashboard"
    sync_interval_minutes: int = 5
    tz: str = "America/Sao_Paulo"  # calendar grouping and export timestamps

    @property
    def database_url(self) -> URL:
        """psycopg 3 URL; URL.create escapes special characters in the password."""
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )
