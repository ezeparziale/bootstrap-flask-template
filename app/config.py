from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_TRACK_MODIFICATIONS: str
    MAIL_SERVER: str
    MAIL_PORT: str
    MAIL_USE_TLS: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str

    class Config:
        env_file = ".env"


settings = Settings()