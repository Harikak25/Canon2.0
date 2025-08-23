
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Prefer a full DATABASE_URL if provided; otherwise build it from individual env vars.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")

    if not all([user, password, database]):
        raise RuntimeError(
            "Database configuration is incomplete. Set DATABASE_URL or POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB."
        )

    # Explicitly specify psycopg2 driver
    DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

# Create the engine with pre-ping to avoid stale connections
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# Classic (sync) Session factory for SQLAlchemy 2.0 style
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator:
    """FastAPI dependency that yields a database session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
