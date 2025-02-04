import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = \
    f"postgresql+asyncpg://{os.getenv("USER")}:{os.getenv("PASS")}@{os.getenv("PORT")}/{os.getenv("DB")}"

TEST_DATABASE_URL = \
    f"postgresql+asyncpg://{os.getenv("TUSER")}:{os.getenv("TPASS")}@{os.getenv("TPORT")}/{os.getenv("TDB")}"

SECRET_KEY: str = os.getenv("SECRET_KEY")
ALGORITHM: str = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRES_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES"))


CLOUD_NAME: str = os.getenv("CLOUD_NAME")
API_KEY: str = os.getenv("API_KEY")
API_SECRET: str = os.getenv("API_SECRET")
