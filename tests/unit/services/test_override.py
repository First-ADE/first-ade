"""T052: Unit tests for OverrideService.

Tests override persistence, minimum rationale length checks, permanent justification rules,
path scope matching (FILE, DIRECTORY, COMPONENT), and revocation behaviors.
"""

import uuid

import pytest

from ade_compliance.config import Config, GlobalSettings
from ade_compliance.services.override import OverrideEntry, OverrideService


@pytest.fixture
def config(tmp_path):
    db_file = tmp_path / f"audit_{uuid.uuid4().hex[:8]}.sqlite"
    # Ensure Windows paths are formatted correctly
    db_path = str(db_file).replace("\\", "/")
    return Config(global_settings=GlobalSettings(audit_path=db_path))


@pytest.fixture
def override_service(config):
    service = OverrideService(config)
    yield service
    service.audit.engine.dispose()
    service.engine.dispose()


class TestOverrideService:
    """Test Override service lifecycle, boundaries, and scopes."""

    def test_create_override_success(self, override_service):
        """Create a valid override and verify persistence and audit logs."""
        o = override_service.create_override(
            axiom_id="Π.1.1",
            scope_type="FILE",
            scope_value="src/main.py",
            rationale="This is a very long rationale of more than twenty characters.",
            created_by="architect-1",
        )

        assert o.axiom_id == "Π.1.1"
        assert o.scope_type == "FILE"
        assert o.scope_value == "src/main.py"
        assert len(o.rationale) >= 20
        assert o.created_by == "architect-1"
        assert o.is_permanent is False
        assert o.permanent_justification is None

        # Verify SQL persistence
        session = override_service.Session()
        entry = session.query(OverrideEntry).first()
        assert entry.id == o.id
        assert entry.rationale == o.rationale
        session.close()

        # Verify audit logs
        entries = override_service.audit.get_entries()
        assert any(e["action"] == "OVERRIDE_RECORDED" for e in entries)

    def test_create_override_short_rationale_raises_error(self, override_service):
        """Creating an override with rationale < 20 characters must raise ValueError."""
        with pytest.raises(ValueError, match="at least 20 characters long"):
            override_service.create_override(
                axiom_id="Π.1.1",
                scope_type="FILE",
                scope_value="src/main.py",
                rationale="Too short",
                created_by="architect-1",
            )

    def test_create_override_permanent_requires_justification(self, override_service):
        """Permanent override without permanent justification must raise ValueError."""
        with pytest.raises(ValueError, match="permanent_justification is required"):
            override_service.create_override(
                axiom_id="Π.1.1",
                scope_type="FILE",
                scope_value="src/main.py",
                rationale="This is a very long rationale of more than twenty characters.",
                created_by="architect-1",
                is_permanent=True,
                permanent_justification="",
            )

    def test_create_override_permanent_unprefixed_rejected(self, override_service):
        """Permanent override with unprefixed justification must raise ValueError."""
        with pytest.raises(ValueError, match="must start with either 'SSO-PR-' or 'SSO-SIG-'"):
            override_service.create_override(
                axiom_id="Π.1.1",
                scope_type="FILE",
                scope_value="src/main.py",
                rationale="This is a very long rationale of more than twenty characters.",
                created_by="architect-1",
                is_permanent=True,
                permanent_justification="This is an invalid unprefixed justification.",
            )

    def test_create_override_permanent_prefixed_success(self, override_service):
        """Permanent override with SSO-PR- or SSO-SIG- prefixed justification must succeed."""
        o = override_service.create_override(
            axiom_id="Π.1.1",
            scope_type="FILE",
            scope_value="src/main.py",
            rationale="This is a very long rationale of more than twenty characters.",
            created_by="architect-1",
            is_permanent=True,
            permanent_justification="SSO-PR-123-This is a valid permanent justification.",
        )
        assert o.is_permanent is True
        assert o.permanent_justification == "SSO-PR-123-This is a valid permanent justification."

    def test_create_override_cryptographic_signature(self, override_service):
        """Verify that a cryptographically signed permanent justification passes validation, while a tampered signature fails."""
        import base64

        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding, rsa

        from ade_compliance.services.crypto import register_architect_key

        # 1. Generate an RSA key pair for testing
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # 2. Register the mock architect's public key
        register_architect_key("HA-CRYPTO-TEST", public_key_pem)

        # 3. Create a valid rationale
        rationale = "This is a very long rationale of more than twenty characters."

        # 4. Sign the rationale using the private key
        signature = private_key.sign(
            rationale.encode("utf-8"),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        sig_b64 = base64.b64encode(signature).decode("utf-8")

        # 5. Verify that valid signature succeeds
        o = override_service.create_override(
            axiom_id="Π.1.1",
            scope_type="FILE",
            scope_value="src/main.py",
            rationale=rationale,
            created_by="HA-CRYPTO-TEST",
            is_permanent=True,
            permanent_justification=f"SSO-SIG-{sig_b64}",
        )
        assert o.is_permanent is True
        assert o.permanent_justification.startswith("SSO-SIG-")

        # 6. Verify that creating a permanent override with a tampered signature fails
        tampered_sig = base64.b64encode(b"tampered_signature_payload_data").decode("utf-8")
        with pytest.raises(ValueError, match="Cryptographic attestation failed"):
            override_service.create_override(
                axiom_id="Π.1.1",
                scope_type="FILE",
                scope_value="src/main.py",
                rationale=rationale,
                created_by="HA-CRYPTO-TEST",
                is_permanent=True,
                permanent_justification=f"SSO-SIG-{tampered_sig}",
            )

    def test_get_active_overrides_filters_expired_and_revoked(self, override_service):
        """get_active_overrides must exclude expired or revoked overrides."""
        # 1. Create a normal active override
        override_service.create_override(
            axiom_id="Π.1.1",
            scope_type="FILE",
            scope_value="src/active.py",
            rationale="This is a very long rationale of more than twenty characters.",
            created_by="architect-1",
            expires_in_days=10,
        )

        # 2. Create an expired override
        expired_o = override_service.create_override(
            axiom_id="Π.1.2",
            scope_type="FILE",
            scope_value="src/expired.py",
            rationale="This is a very long rationale of more than twenty characters.",
            created_by="architect-1",
            expires_in_days=-1,  # Expired yesterday
        )

        # 3. Create a revoked override
        revoked_o = override_service.create_override(
            axiom_id="Π.1.3",
            scope_type="FILE",
            scope_value="src/revoked.py",
            rationale="This is a very long rationale of more than twenty characters.",
            created_by="architect-1",
            expires_in_days=10,
        )
        override_service.revoke_override(revoked_o.id)

        active = override_service.get_active_overrides()
        active_axioms = [o.axiom_id for o in active]

        assert "Π.1.1" in active_axioms
        assert "Π.1.2" not in active_axioms
        assert "Π.1.3" not in active_axioms

    def test_is_override_active_matching_scopes(self, override_service):
        """Test is_override_active scope matching logic across FILE, DIRECTORY, COMPONENT."""
        # FILE scope
        override_service.create_override(
            axiom_id="Π.1.1",
            scope_type="FILE",
            scope_value="src/core/main.py",
            rationale="This is a very long rationale of more than twenty characters.",
            created_by="architect-1",
        )
        assert override_service.is_override_active("Π.1.1", "src/core/main.py") is True
        assert override_service.is_override_active("Π.1.1", "src/core/other.py") is False

        # DIRECTORY scope
        override_service.create_override(
            axiom_id="Π.2.1",
            scope_type="DIRECTORY",
            scope_value="src/core",
            rationale="This is a very long rationale of more than twenty characters.",
            created_by="architect-1",
        )
        assert override_service.is_override_active("Π.2.1", "src/core/main.py") is True
        assert override_service.is_override_active("Π.2.1", "src/core/sub/helper.py") is True
        assert override_service.is_override_active("Π.2.1", "src/other/main.py") is False

        # COMPONENT scope
        override_service.create_override(
            axiom_id="Π.3.1",
            scope_type="COMPONENT",
            scope_value="scheduler",
            rationale="This is a very long rationale of more than twenty characters.",
            created_by="architect-1",
        )
        assert override_service.is_override_active("Π.3.1", "src/components/scheduler/main.py") is True
        assert override_service.is_override_active("Π.3.1", "src/scheduler_helper.py") is True
        assert override_service.is_override_active("Π.3.1", "src/core/main.py") is False

    def test_revoke_override(self, override_service):
        """Revoking an override must change its status to inactive and log OVERRIDE_REVOKED."""
        o = override_service.create_override(
            axiom_id="Π.1.1",
            scope_type="FILE",
            scope_value="src/main.py",
            rationale="This is a very long rationale of more than twenty characters.",
            created_by="architect-1",
        )

        assert override_service.is_override_active("Π.1.1", "src/main.py") is True

        res = override_service.revoke_override(o.id)
        assert res is True
        assert override_service.is_override_active("Π.1.1", "src/main.py") is False

        # Verify audit logs
        entries = override_service.audit.get_entries()
        assert any(e["action"] == "OVERRIDE_REVOKED" for e in entries)

    def test_create_override_invalid_scope_type(self, override_service):
        """Creating an override with an invalid scope type must raise ValueError."""
        with pytest.raises(ValueError, match="Override scope_type must be one of"):
            override_service.create_override(
                axiom_id="Π.1.1",
                scope_type="INVALID_TYPE",
                scope_value="src/main.py",
                rationale="This is a very long rationale of more than twenty characters.",
                created_by="architect-1",
            )

    def test_create_override_empty_scope_value(self, override_service):
        """Creating an override with an empty or whitespace scope value must raise ValueError."""
        with pytest.raises(ValueError, match="Override scope_value cannot be empty"):
            override_service.create_override(
                axiom_id="Π.1.1",
                scope_type="FILE",
                scope_value="   ",
                rationale="This is a very long rationale of more than twenty characters.",
                created_by="architect-1",
            )

    def test_is_override_active_absolute_paths(self, override_service):
        """Verify that overrides match correctly even when absolute or differently prefixed paths are used."""
        override_service.create_override(
            axiom_id="Π.1.1",
            scope_type="FILE",
            scope_value="src/core/main.py",
            rationale="This is a very long rationale of more than twenty characters.",
            created_by="architect-1",
        )

        # Match using absolute path
        import os

        workspace_abs = os.path.abspath(".")
        abs_path = os.path.join(workspace_abs, "src", "core", "main.py")

        assert override_service.is_override_active("Π.1.1", abs_path) is True
        assert override_service.is_override_active("Π.1.1", "./src/core/main.py") is True

    def test_override_audit_trail_logged(self, override_service):
        """T052: Create an override, then verify audit_log table has an OVERRIDE_RECORDED entry matching the override ID."""
        o = override_service.create_override(
            axiom_id="Π.1.1",
            scope_type="FILE",
            scope_value="src/main.py",
            rationale="This is a very long rationale of more than twenty characters.",
            created_by="architect-1",
        )

        entries = override_service.audit.get_entries()
        override_entries = [e for e in entries if e["action"] == "OVERRIDE_RECORDED"]

        assert len(override_entries) >= 1
        # Verify the audit entry details contain the override ID
        matched = [e for e in override_entries if e["details"].get("id") == o.id]
        assert len(matched) == 1, f"Expected audit entry with id={o.id}, got: {override_entries}"

    def test_revoke_override_audit_trail(self, override_service):
        """T052: Create and revoke an override, verify OVERRIDE_REVOKED audit entry exists."""
        o = override_service.create_override(
            axiom_id="Π.1.1",
            scope_type="FILE",
            scope_value="src/main.py",
            rationale="This is a very long rationale of more than twenty characters.",
            created_by="architect-1",
        )

        # Revoke the override
        result = override_service.revoke_override(o.id)
        assert result is True

        # Verify OVERRIDE_REVOKED audit entry exists
        entries = override_service.audit.get_entries()
        revoke_entries = [e for e in entries if e["action"] == "OVERRIDE_REVOKED"]

        assert len(revoke_entries) >= 1
        # Verify the revoke audit entry references the override ID
        matched = [e for e in revoke_entries if e["details"].get("id") == o.id]
        assert len(matched) == 1, f"Expected OVERRIDE_REVOKED entry with id={o.id}, got: {revoke_entries}"
