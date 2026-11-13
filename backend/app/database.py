
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Load environment variables from backend/.env
load_dotenv(
    Path(__file__).resolve().parents[1] / ".env"
)


# Use PostgreSQL when DATABASE_URL is configured.
# Otherwise, continue using SQLite locally.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./helpdesk.db"
)


# Normalize PostgreSQL connection URL.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )


# SQLite requires a special connection argument.
connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)


# Create database engine.
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)


# Create database sessions.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# SQLAlchemy declarative base.
Base = declarative_base()


# Database dependency for FastAPI.
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

