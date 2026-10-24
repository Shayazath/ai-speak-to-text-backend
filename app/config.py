import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "local-development-secret"
    )

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")


settings = Settings()
