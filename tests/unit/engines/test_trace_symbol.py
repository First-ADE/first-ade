# implements: FR-003
# traces_to: Π.2.1

from unittest.mock import Mock, patch

import pytest

from ade_compliance.config import EngineConfig
from ade_compliance.engines.trace_engine import TraceEngine


@pytest.fixture
def trace_engine():
    config = EngineConfig(enabled=True, strictness="enforce")
    return TraceEngine(config)


def test_fallback_regex_class_symbol_mapping(trace_engine):
    """Verify regex fallback extracts class name from the lines following a comment."""
    code_content = """
    # implements: FR-001
    class SpecEngine:
        def check(self):
            pass
    """
    with patch.object(trace_engine, "_get_parser_and_lang", return_value=(None, None)):
        links = trace_engine.extract_links("src/spec.py", code_content)
        assert len(links) == 1
        assert links[0].symbol == "SpecEngine"
        assert links[0].target == "FR-001"


def test_fallback_regex_func_symbol_mapping(trace_engine):
    """Verify regex fallback extracts function name from the lines following a comment."""
    code_content = """
    // implements: FR-002
    function calculateTotal(items) {
        return 0;
    }
    """
    with patch.object(trace_engine, "_get_parser_and_lang", return_value=(None, None)):
        links = trace_engine.extract_links("src/calc.js", code_content)
        assert len(links) == 1
        assert links[0].symbol == "calculateTotal"
        assert links[0].target == "FR-002"


def test_fallback_regex_assign_symbol_mapping(trace_engine):
    """Verify regex fallback extracts variable name from an assignment line following a comment."""
    code_content = """
    # traces_to: Π.3.1
    database_url = "postgresql://localhost"
    """
    with patch.object(trace_engine, "_get_parser_and_lang", return_value=(None, None)):
        links = trace_engine.extract_links("src/db.py", code_content)
        assert len(links) == 1
        assert links[0].symbol == "database_url"
        assert links[0].target == "Π.3.1"


def test_fallback_regex_skip_decorators_mapping(trace_engine):
    """Verify regex fallback skips decorators to match the underlying declaration."""
    code_content = """
    # implements: FR-003
    @router.post("/overrides")
    @metrics.timer
    def create_override(request):
        pass
    """
    with patch.object(trace_engine, "_get_parser_and_lang", return_value=(None, None)):
        links = trace_engine.extract_links("src/server.py", code_content)
        assert len(links) == 1
        assert links[0].symbol == "create_override"


def test_fallback_regex_no_symbol_if_not_declaration(trace_engine):
    """Verify regex fallback yields None if comment is not followed by a declaration."""
    code_content = """
    # implements: FR-004
    print("Just print something unrelated")
    """
    with patch.object(trace_engine, "_get_parser_and_lang", return_value=(None, None)):
        links = trace_engine.extract_links("src/run.py", code_content)
        assert len(links) == 1
        assert links[0].symbol is None


def test_matrix_formatting_with_symbols(trace_engine):
    """Verify that generate_matrix formats target with symbol name in parentheses when symbol is present."""
    from ade_compliance.models import TraceLink

    links = [
        TraceLink(source="src/a.py", target="FR-001", type="implements", symbol="MyClass"),
        TraceLink(source="src/a.py", target="Π.3.1", type="traces_to", symbol=None),
    ]

    matrix = trace_engine.generate_matrix(links)

    assert "src/a.py" in matrix
    assert matrix["src/a.py"]["implements"] == ["FR-001 (MyClass)"]
    assert matrix["src/a.py"]["traces_to"] == ["Π.3.1"]


def test_tree_sitter_ast_symbol_mapping_mocked(trace_engine):
    """Verify tree-sitter AST comments and symbol extraction flow via mocks."""
    mock_parser = Mock()
    mock_tree = Mock()
    mock_root = Mock()
    mock_comment_node = Mock()
    mock_sibling_node = Mock()
    mock_name_node = Mock()

    # Configure tree relationships
    mock_parser.parse.return_value = mock_tree
    mock_tree.root_node = mock_root
    mock_root.type = "module"
    mock_root.children = [mock_comment_node]

    mock_comment_node.type = "comment"
    mock_comment_node.start_byte = 0
    mock_comment_node.end_byte = 22  # '# implements: FR-005'
    mock_comment_node.next_sibling = mock_sibling_node

    mock_sibling_node.type = "function_definition"
    mock_sibling_node.child_by_field_name.return_value = mock_name_node

    mock_name_node.start_byte = 23
    mock_name_node.end_byte = 31  # 'my_func'

    source_bytes = b"# implements: FR-005\ndef my_func(): pass"

    with patch.object(trace_engine, "_get_parser_and_lang", return_value=(mock_parser, Mock())):
        links = trace_engine.extract_links("src/math.py", source_bytes.decode("utf-8"))

        assert len(links) == 1
        assert links[0].target == "FR-005"
        assert links[0].symbol == "my_func"
