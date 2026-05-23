# implements: FR-002
# traces_to: Π.2.1

from ade_compliance.utils.path import sanitize_relative_path


def test_sanitize_relative_path_valid(tmp_path):
    base = tmp_path.resolve()
    res = sanitize_relative_path(base, "models/axiom.py")
    assert res == base / "models" / "axiom.py"


def test_sanitize_relative_path_traversal(tmp_path):
    base = tmp_path.resolve()
    # Path traversal should be stripped
    res = sanitize_relative_path(base, "../../../etc/passwd")
    assert res == base / "etc" / "passwd" or res is None


def test_sanitize_relative_path_invalid_characters(tmp_path):
    base = tmp_path.resolve()
    res = sanitize_relative_path(base, "models/axiom$;.py")
    # axiom$;.py has invalid characters, so it should be skipped or stripped
    assert res == base / "models" or res is None
