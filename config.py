import os
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Settings(BaseSettings):
    DEBUG: bool

    # db_urls
    LOCAL_DATABASE_URL: str
    HOST_DATABASE_URL: str
    TEST_DATABASE_URL: str

    # prod_db
    USER: str
    PASS: str
    HOST: str
    PORT: int
    DB: str

    # test_db
    TUSER: str
    TPASS: str
    THOST: str
    TPORT: int
    TDB: str

    # jwt
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRES_MINUTES: int
    REFRESH_TOKEN_EXPIRES_DAYS: int

    #cloudinary
    CLOUD_NAME: str
    API_KEY: str
    API_SECRET: str

    #sentry
    SENTRY_URL: str

    # mail
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_FROM: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    FORGET_PASSWORD_LINK_EXPIRE_MINUTES: int

    BACKEND_URL: str

    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(__file__), ".env"), extra="ignore")


Config = Settings()

ROLE_SCOPES = {
    "user": ["user"],
    "moderator": ["user",  "moderator"],
    "admin":  ["user", "moderator", "admin"],
}
