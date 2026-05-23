from unittest.mock import Mock, patch, mock_open
import pytest
from ade_compliance.config import EngineConfig
from ade_compliance.engines.trace_engine import TraceEngine


@pytest.fixture
def trace_engine():
    config = EngineConfig(enabled=True, strictness="enforce")
    return TraceEngine(config)


@pytest.mark.asyncio
async def test_check_no_traceability_links(trace_engine):
    # Mock open to return code without any comments/markers
    code_content = "def add(a, b):\n    return a + b\n"
    with patch("builtins.open", mock_open(read_data=code_content)):
        with patch("pathlib.Path.exists", return_value=True):
            violations = await trace_engine.check(["src/math.py"])
            assert len(violations) == 1
            assert violations[0].axiom_id == "Π.3.1"
            assert "Missing traceability links" in violations[0].message


@pytest.mark.asyncio
async def test_check_valid_traceability_links(trace_engine):
    # Mock open to return code with a valid implements marker
    code_content = "# implements: FR-001\ndef add(a, b):\n    return a + b\n"
    with patch("builtins.open", mock_open(read_data=code_content)):
        with patch("pathlib.Path.exists", return_value=True):
            violations = await trace_engine.check(["src/math.py"])
            assert len(violations) == 0


def test_extract_python_comments(trace_engine):
    code_content = (
        "# implements: FR-001, Requirement 1.2\n"
        "# traces_to: Π.3.1\n"
        "def run():\n"
        "    pass\n"
    )
    links = trace_engine.extract_links("src/run.py", code_content)
    assert len(links) == 3
    
    # Verify implements links
    impls = [k for k in links if k.type == "implements"]
    assert len(impls) == 2
    assert {i.target for i in impls} == {"FR-001", "Requirement 1.2"}

    # Verify traces_to links
    traces = [k for k in links if k.type == "traces_to"]
    assert len(traces) == 1
    assert traces[0].target == "Π.3.1"


def test_extract_javascript_comments(trace_engine):
    code_content = (
        "// implements: FR-002\n"
        "/* validates: src/run.py */\n"
        "const x = 1;\n"
    )
    links = trace_engine.extract_links("src/run.js", code_content)
    assert len(links) == 2
    
    impls = [k for k in links if k.type == "implements"]
    assert len(impls) == 1
    assert impls[0].target == "FR-002"

    vals = [k for k in links if k.type == "validates"]
    assert len(vals) == 1
    assert vals[0].target == "src/run.py"


def test_extract_java_comments(trace_engine):
    code_content = (
        "// implements: FR-003\n"
        "/**\n"
        " * validates: FR-004, FR-005\n"
        " */\n"
        "class Main {}\n"
    )
    links = trace_engine.extract_links("src/Main.java", code_content)
    assert len(links) == 3
    
    impls = [k for k in links if k.type == "implements"]
    assert len(impls) == 1
    assert impls[0].target == "FR-003"

    vals = [k for k in links if k.type == "validates"]
    assert len(vals) == 2
    assert {v.target for v in vals} == {"FR-004", "FR-005"}


def test_matrix_generation(trace_engine):
    code_content_1 = "# implements: FR-001\n# traces_to: Π.3.1\ndef a(): pass\n"
    code_content_2 = "# validates: src/a.py\n# implements: FR-001\ndef test_a(): pass\n"
    
    # Extract links manually to feed to matrix
    links_1 = trace_engine.extract_links("src/a.py", code_content_1)
    links_2 = trace_engine.extract_links("tests/test_a.py", code_content_2)
    
    all_links = links_1 + links_2
    matrix = trace_engine.generate_matrix(all_links)
    
    assert "src/a.py" in matrix
    assert matrix["src/a.py"]["implements"] == ["FR-001"]
    assert matrix["src/a.py"]["traces_to"] == ["Π.3.1"]

    assert "tests/test_a.py" in matrix
    assert matrix["tests/test_a.py"]["validates"] == ["src/a.py"]
    assert matrix["tests/test_a.py"]["implements"] == ["FR-001"]


@pytest.mark.asyncio
async def test_caching_behavior(trace_engine):
    code_content = "# implements: FR-001\n"
    
    with patch("builtins.open", mock_open(read_data=code_content)):
        with patch("pathlib.Path.exists", return_value=True):
            mock_parser = Mock()
            with patch.object(trace_engine, "_get_parser_and_lang", return_value=(mock_parser, Mock())):
                # First check - should call parse
                violations_1 = await trace_engine.check(["src/math.py"])
                assert len(violations_1) == 0
                assert mock_parser.parse.call_count == 1
                
                # Second check with same file - should hit cache and NOT parse again
                violations_2 = await trace_engine.check(["src/math.py"])
                assert len(violations_2) == 0
                assert mock_parser.parse.call_count == 1  # Parse count stays 1
