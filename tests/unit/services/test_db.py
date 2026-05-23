# implements: FR-002
# traces_to: Π.2.1

from ade_compliance.config import Config
from ade_compliance.services.db import get_engine, db_session


def test_get_engine_memory():
    config = Config()
    config.global_settings.audit_path = ":memory:"
    engine = get_engine(config)
    assert str(engine.url) == "sqlite://"


def test_db_session_memory():
    config = Config()
    config.global_settings.audit_path = ":memory:"
    with db_session(config) as session:
        assert session is not None
