from datetime import timedelta
from typing import Any, Dict, Optional

from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_core.core_schema import FieldValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Flask
    SECRET_KEY: str

    # Site
    SITE_NAME: str
    POSTS_PER_PAGE: int = 10
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCK_TIME: timedelta = timedelta(minutes=5)
    BLOCK_TIME: timedelta = timedelta(minutes=1)
    CHECK_LAST_PASSWORD: int = 5
    PASSWORD_EXPIRATION_DAYS: int = 90
    ADMIN_EMAILS: list[str] = []

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

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: str | None, info: FieldValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_HOSTNAME"),
            port=int(info.data.get("POSTGRES_PORT")),  # type: ignore  # noqa
            path=info.data.get("POSTGRES_DB", ""),
        )

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
