# implements: FR-007
# traces_to: Π.3.1

"""Centralized Database Connection and Session Provider for ADE Compliance.

Provides a unified SQLAlchemy engine, a shared declarative Base,
and a transaction-safe context-managed session helper.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from ..config import Config

# Shared declarative base for all database models
Base = declarative_base()


def get_engine(config: Config) -> Engine:
    """Create a unified SQLAlchemy engine for the database path configured.

    Handles Windows path normalization and automatically creates any missing parent directories.
    """
    db_path = config.global_settings.audit_path

    if db_path == ":memory:" or not db_path:
        url = "sqlite://"
    else:
        # Normalize Windows backslashes to forward slashes for SQLite compatibility
        path_str = str(db_path).replace("\\", "/")
        url = f"sqlite:///{path_str}"

        # Automatically create target parent folders if they do not exist
        p = Path(db_path)
        if p.parent and not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)

    return create_engine(url)


@contextmanager
def db_session(config: Config) -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of database operations.

    Ensures safe transaction commit on success, automatic rollback on exception,
    and guarantees session closure.
    """
    engine = get_engine(config)
    # Ensure all tables registered under shared Base are created
    Base.metadata.create_all(engine)

    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
