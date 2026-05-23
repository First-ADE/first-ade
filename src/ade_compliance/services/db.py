# implements: FR-007
# traces_to: Π.3.1

"""Centralized Database Connection and Session Provider for ADE Compliance.

Provides a unified SQLAlchemy engine, a shared declarative Base,
and a transaction-safe context-managed session helper.
"""

import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, Tuple

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from ..config import Config

# Shared declarative base for all database models
Base = declarative_base()


# Thread lock for thread-safe caching of engines and session factories
_db_lock = threading.Lock()
_engines_cache: Dict[str, Tuple[Engine, sessionmaker]] = {}


def get_engine_and_factory(config: Config) -> Tuple[Engine, sessionmaker]:
    """Get or create cached SQLAlchemy engine and session factory for the configured path.

    Automatically handles Windows path normalization, folder creation, and guarantees
    table structure initialization (create_all) exactly once per database.
    """
    db_path = config.global_settings.audit_path or ":memory:"
    db_path_str = str(db_path)

    with _db_lock:
        if db_path_str in _engines_cache:
            return _engines_cache[db_path_str]

        if db_path == ":memory:":
            url = "sqlite://"
        else:
            # Normalize Windows backslashes to forward slashes for SQLite compatibility
            path_str = db_path_str.replace("\\", "/")
            url = f"sqlite:///{path_str}"

            # Automatically create target parent folders if they do not exist
            p = Path(db_path)
            if p.parent and not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)

        engine = create_engine(url)
        # Ensure all tables registered under shared Base are created once upon initialization
        Base.metadata.create_all(engine)

        session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        _engines_cache[db_path_str] = (engine, session_factory)
        return engine, session_factory


def get_engine(config: Config) -> Engine:
    """Create or retrieve the cached unified SQLAlchemy engine for the configured path."""
    engine, _ = get_engine_and_factory(config)
    return engine


@contextmanager
def db_session(config: Config) -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of database operations.

    Ensures safe transaction commit on success, automatic rollback on exception,
    and guarantees session closure.
    """
    _, session_factory = get_engine_and_factory(config)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
