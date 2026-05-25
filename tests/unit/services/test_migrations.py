import uuid

from sqlalchemy import create_engine, inspect, text

from ade_compliance.config import Config, GlobalSettings
from ade_compliance.services.db import DatabaseManager, run_migrations


def test_migration_from_scratch(tmp_path):
    """Test that a new database is correctly created with all latest migrations."""
    db_file = tmp_path / f"scratch_{uuid.uuid4().hex[:8]}.sqlite"
    config = Config(global_settings=GlobalSettings(audit_path=str(db_file).replace("\\", "/")))

    db_manager = DatabaseManager()
    engine, _ = db_manager.get_engine_and_factory(config)

    # Inspect the created database
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "alembic_version" in tables
    assert "audit_log" in tables
    assert "override_log" in tables
    assert "escalation_queue" in tables

    # Verify that the columns in override_log include expiry_notified
    columns = [col["name"] for col in inspector.get_columns("override_log")]
    assert "expiry_notified" in columns


def test_legacy_stamping_pre_expiry_notified(tmp_path):
    """Test self-healing migration for legacy database lacking expiry_notified and alembic_version."""
    db_file = tmp_path / f"legacy_pre_{uuid.uuid4().hex[:8]}.sqlite"

    # 1. Create a raw legacy database directly using sqlite connection (pre-expiry_notified)
    db_path_str = str(db_file).replace("\\", "/")
    engine = create_engine(f"sqlite:///{db_path_str}")
    with engine.begin() as conn:
        conn.execute(
            text("""
            CREATE TABLE audit_log (
                id INTEGER NOT NULL PRIMARY KEY,
                timestamp DATETIME,
                action VARCHAR,
                details VARCHAR,
                previous_hash VARCHAR,
                hash VARCHAR
            )
        """)
        )
        conn.execute(
            text("""
            CREATE TABLE override_log (
                id VARCHAR NOT NULL PRIMARY KEY,
                axiom_id VARCHAR NOT NULL,
                scope_type VARCHAR NOT NULL,
                scope_value VARCHAR NOT NULL,
                rationale VARCHAR NOT NULL,
                created_by VARCHAR NOT NULL,
                created_at DATETIME,
                expires_at DATETIME NOT NULL,
                is_permanent BOOLEAN,
                permanent_justification VARCHAR,
                revoked_at DATETIME
            )
        """)
        )
        conn.execute(
            text("""
            CREATE TABLE escalation_queue (
                id INTEGER NOT NULL PRIMARY KEY,
                title VARCHAR NOT NULL,
                body VARCHAR NOT NULL,
                created_at DATETIME,
                retry_count INTEGER,
                next_retry DATETIME,
                is_blocked BOOLEAN,
                error_message VARCHAR
            )
        """)
        )

    # Verify database has no alembic_version and override_log has no expiry_notified
    inspector = inspect(engine)
    assert "alembic_version" not in inspector.get_table_names()
    assert "expiry_notified" not in [col["name"] for col in inspector.get_columns("override_log")]

    # 2. Run programmatic migrations on this legacy database
    run_migrations(engine)

    # 3. Verify it was correctly stamped to Migration 1, then upgraded to Migration 2 (head)
    inspector = inspect(engine)
    assert "alembic_version" in inspector.get_table_names()
    assert "expiry_notified" in [col["name"] for col in inspector.get_columns("override_log")]


def test_legacy_stamping_post_expiry_notified(tmp_path):
    """Test self-healing migration for legacy database having expiry_notified but lacking alembic_version."""
    db_file = tmp_path / f"legacy_post_{uuid.uuid4().hex[:8]}.sqlite"

    # 1. Create a raw legacy database directly using sqlite connection (post-expiry_notified)
    db_path_str = str(db_file).replace("\\", "/")
    engine = create_engine(f"sqlite:///{db_path_str}")
    with engine.begin() as conn:
        conn.execute(
            text("""
            CREATE TABLE audit_log (
                id INTEGER NOT NULL PRIMARY KEY,
                timestamp DATETIME,
                action VARCHAR,
                details VARCHAR,
                previous_hash VARCHAR,
                hash VARCHAR
            )
        """)
        )
        conn.execute(
            text("""
            CREATE TABLE override_log (
                id VARCHAR NOT NULL PRIMARY KEY,
                axiom_id VARCHAR NOT NULL,
                scope_type VARCHAR NOT NULL,
                scope_value VARCHAR NOT NULL,
                rationale VARCHAR NOT NULL,
                created_by VARCHAR NOT NULL,
                created_at DATETIME,
                expires_at DATETIME NOT NULL,
                is_permanent BOOLEAN,
                permanent_justification VARCHAR,
                revoked_at DATETIME,
                expiry_notified BOOLEAN DEFAULT 0
            )
        """)
        )
        conn.execute(
            text("""
            CREATE TABLE escalation_queue (
                id INTEGER NOT NULL PRIMARY KEY,
                title VARCHAR NOT NULL,
                body VARCHAR NOT NULL,
                created_at DATETIME,
                retry_count INTEGER,
                next_retry DATETIME,
                is_blocked BOOLEAN,
                error_message VARCHAR
            )
        """)
        )

    # Verify database has no alembic_version and override_log already has expiry_notified
    inspector = inspect(engine)
    assert "alembic_version" not in inspector.get_table_names()
    assert "expiry_notified" in [col["name"] for col in inspector.get_columns("override_log")]

    # 2. Run programmatic migrations on this legacy database
    run_migrations(engine)

    # 3. Verify it was stamped directly to Migration 2 (head) and no errors occurred
    inspector = inspect(engine)
    assert "alembic_version" in inspector.get_table_names()
