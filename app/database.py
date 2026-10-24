
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

BACKEND_DIR = Path(__file__).resolve().parent.parent


def create_database_engine(**kwargs):
    connect_args = {}
    ssl_ca = os.getenv("DB_SSL_CA")

    if ssl_ca:
        ca_path = Path(ssl_ca)
        if not ca_path.is_absolute():
            ca_path = BACKEND_DIR / ca_path

        if not ca_path.is_file():
            raise FileNotFoundError(
                f"Database CA certificate not found: {ca_path}"
            )

        connect_args = {
            "ssl_ca": str(ca_path),
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
        }

    return create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args=connect_args,
        **kwargs,
    )


engine = create_database_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
