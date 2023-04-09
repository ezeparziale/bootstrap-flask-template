from datetime import timedelta
from typing import Any, Dict, Optional

from pydantic import BaseSettings, PostgresDsn, validator


class Settings(BaseSettings):
    # Flask
    SECRET_KEY: str

    # Site
    SITE_NAME: str
    POSTS_PER_PAGE: int = 10
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCK_TIME: timedelta = timedelta(minutes=5)
    BLOCK_TIME: timedelta = timedelta(minutes=1)

    # Mail
    MAIL_SERVER: str
    MAIL_PORT: str = 587
    MAIL_USE_TLS: bool = True
    MAIL_USERNAME: str
    MAIL_PASSWORD: str

    # Database
    POSTGRES_HOSTNAME: str
    POSTGRES_PORT: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOSTNAME"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    class Config:
        env_file = ".env"


settings = Settings()
