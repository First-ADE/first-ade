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
from ..exceptions import DatabaseException

# Shared declarative base for all database models
Base = declarative_base()


class DatabaseManager:
    """Thread-safe singleton database connection and session provider.

    Encapsulates the cached SQLAlchemy engines, connection pools, and declarative Base.
    Ensures safe database connection lifetimes while maintaining complete test isolation
    by caching engines using their absolute database file paths.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.lock = threading.Lock()
        self.engines_cache: Dict[str, Tuple[Engine, sessionmaker]] = {}
        self._initialized = True

    def get_engine_and_factory(self, config: Config) -> Tuple[Engine, sessionmaker]:
        """Get or create cached SQLAlchemy engine and session factory for the configured path.

        Automatically handles Windows path normalization, folder creation, and guarantees
        table structure initialization exactly once per database file.
        """
        db_path = config.global_settings.audit_path or ":memory:"
        db_path_str = str(db_path)

        with self.lock:
            if db_path_str in self.engines_cache:
                engine, factory = self.engines_cache[db_path_str]
                return engine, factory

            try:
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

                # Programmatically run Alembic migrations on engine creation
                run_migrations(engine)

                session_factory = sessionmaker(bind=engine, expire_on_commit=False)
                self.engines_cache[db_path_str] = (engine, session_factory)
                return engine, session_factory
            except Exception as e:
                raise DatabaseException(f"Failed to initialize database engine for path '{db_path}': {e}") from e

    def get_engine(self, config: Config) -> Engine:
        """Retrieve the cached SQLAlchemy engine for the provided config."""
        engine, _ = self.get_engine_and_factory(config)
        return engine

    @contextmanager
    def session(self, config: Config) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of database operations.

        Ensures safe transaction commit on success, automatic rollback on exception,
        and guarantees session closure.
        """
        _, session_factory = self.get_engine_and_factory(config)
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise DatabaseException(f"Database session transaction failed: {e}") from e
        finally:
            session.close()


def get_engine_and_factory(config: Config) -> Tuple[Engine, sessionmaker]:
    """Deprecated: Use DatabaseManager().get_engine_and_factory(config) instead.

    Provided for backward compatibility.
    """
    return DatabaseManager().get_engine_and_factory(config)


def get_engine(config: Config) -> Engine:
    """Deprecated: Use DatabaseManager().get_engine(config) instead.

    Provided for backward compatibility.
    """
    return DatabaseManager().get_engine(config)


@contextmanager
def db_session(config: Config) -> Generator[Session, None, None]:
    """Deprecated: Use DatabaseManager().session(config) instead.

    Provided for backward compatibility.
    """
    with DatabaseManager().session(config) as session:
        yield session


def run_migrations(engine: Engine) -> None:
    """Programmatically run Alembic migrations on the given engine.

    Includes self-healing auto-stamping logic for legacy databases.
    """
    from pathlib import Path

    from alembic import command
    from alembic.config import Config as AlembicConfig
    from sqlalchemy import inspect

    # Determine migration directory path relative to this file
    current_dir = Path(__file__).parent.parent
    script_location = current_dir / "migrations"

    # Create Alembic Config
    alembic_cfg = AlembicConfig()
    alembic_cfg.set_main_option("script_location", str(script_location))

    # Inspect connection to see if it is a legacy database
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    with engine.begin() as connection:
        alembic_cfg.attributes["connection"] = connection

        if "audit_log" in existing_tables and "alembic_version" not in existing_tables:
            # Legacy database without migration tracking.
            # Inspect override_log schema to determine revision level
            columns = [col["name"] for col in inspector.get_columns("override_log")]

            if "expiry_notified" in columns:
                # Legacy DB already has Migration 2 applied, stamp it directly to head
                command.stamp(alembic_cfg, "2a3b4c5d6e7f")  # pragma: allowlist secret
            else:
                # Legacy DB is at Migration 1, stamp it to initial, and let upgrade head do the rest
                command.stamp(alembic_cfg, "1a2b3c4d5e6f")  # pragma: allowlist secret

        # Upgrade to head
        command.upgrade(alembic_cfg, "head")
