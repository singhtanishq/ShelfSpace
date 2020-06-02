"""SQLAlchemy engine/session setup."""

import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _create_engine(database_url: str) -> Engine:
    kwargs: dict = {"pool_pre_ping": True, "pool_recycle": 3600}
    if database_url.startswith("sqlite"):
        kwargs = {"connect_args": {"check_same_thread": False}}
    return create_engine(database_url, **kwargs)


engine = _create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def _enable_sqlite_fk(dbapi_connection, connection_record):  # pragma: no cover
    """SQLite ignores foreign keys unless explicitly enabled per connection."""
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_test_engine():
    """Engine used by the test-suite (in-memory SQLite unless overridden)."""
    url = settings.TEST_DATABASE_URL or "sqlite://"
    return _create_engine(url)


def media_path(*parts: str) -> str:
    path = os.path.join(settings.MEDIA_DIR, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path
