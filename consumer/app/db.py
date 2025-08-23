import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging

DATABASE_URL = os.getenv("DATABASE_URL") or \
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST','postgres')}:{os.getenv('POSTGRES_PORT','5432')}/{os.getenv('POSTGRES_DB')}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# Utility context manager for safe DB session handling
from contextlib import contextmanager

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logging.exception("Database session error")
        raise
    finally:
        db.close()
