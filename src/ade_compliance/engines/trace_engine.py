# implements: FR-003
# traces_to: Π.3.1

import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..models.axiom import TraceLink, Violation, ViolationState
from .base import BaseEngine


class TraceEngine(BaseEngine):
    def __init__(self, config):
        super().__init__(config)
        self._cache: Dict[str, Tuple[str, List[TraceLink]]] = {}
        self._parsers: Dict[str, Tuple[Optional[object], Optional[object]]] = {}

    def _get_parser_and_lang(self, file_path: str) -> Tuple[Optional[object], Optional[object]]:
        suffix = Path(file_path).suffix.lower()
        if suffix in self._parsers:
            return self._parsers[suffix]

        parser = None
        lang = None

        try:
            from tree_sitter import Language, Parser

            if suffix == ".py":
                import tree_sitter_python as tspython

                lang = Language(tspython.language())
                parser = Parser(lang)
            elif suffix == ".js":
                import tree_sitter_javascript as tsjavascript

                lang = Language(tsjavascript.language())
                parser = Parser(lang)
            elif suffix in (".ts", ".tsx"):
                import tree_sitter_typescript as tstypescript

                lang = Language(tstypescript.language_typescript())
                parser = Parser(lang)
            elif suffix == ".java":
                import tree_sitter_java as tsjava

                lang = Language(tsjava.language())
                parser = Parser(lang)
        except Exception:
            # Fallback gracefully if tree-sitter or packages are not installed (e.g. in minimal environments)
            pass

        self._parsers[suffix] = (parser, lang)
        return parser, lang

    def _find_associated_symbol(self, comment_node, source_bytes: bytes) -> Optional[str]:
        """Navigate AST sibling nodes to find class/function/variable associated with this comment."""
        curr = comment_node.next_sibling
        while curr:
            if curr.type in ("comment", "line_comment", "block_comment"):
                curr = curr.next_sibling
                continue
            if curr.type == "decorated_definition":
                for i in range(curr.child_count):
                    child = curr.child(i)
                    if child.type in ("function_definition", "class_definition"):
                        curr = child
                        break
            if curr.type in (
                "class_definition",
                "function_definition",
                "class_declaration",
                "method_declaration",
                "function_declaration",
                "assignment",
                "variable_declarator",
            ):
                if hasattr(curr, "child_by_field_name") and curr.child_by_field_name("name"):
                    n = curr.child_by_field_name("name")
                    return source_bytes[n.start_byte : n.end_byte].decode("utf-8")
                for i in range(curr.child_count):
                    ch = curr.child(i)
                    if ch.type == "identifier":
                        return source_bytes[ch.start_byte : ch.end_byte].decode("utf-8")
                if curr.type == "assignment":
                    left = curr.child_by_field_name("left") or curr.child(0)
                    if left:
                        return source_bytes[left.start_byte : left.end_byte].decode("utf-8")
            break
        return None

    def _walk_comments_with_symbols(self, node, source_bytes: bytes) -> List[Tuple[str, Optional[str]]]:
        comments = []
        if node.type in ("comment", "line_comment", "block_comment"):
            try:
                comment_text = source_bytes[node.start_byte : node.end_byte].decode("utf-8")
                symbol = self._find_associated_symbol(node, source_bytes)
                comments.append((comment_text, symbol))
            except Exception:
                pass

        for child in node.children:
            comments.extend(self._walk_comments_with_symbols(child, source_bytes))
        return comments

    def extract_links(self, file_path: str, content: str) -> List[TraceLink]:
        # Compute hash
        content_hash = hashlib.md5(content.encode("utf-8"), usedforsecurity=False).hexdigest()

        # Check cache
        if file_path in self._cache:
            cached_hash, cached_links = self._cache[file_path]
            if cached_hash == content_hash:
                return cached_links

        links: List[TraceLink] = []
        parser, _ = self._get_parser_and_lang(file_path)

        comments_with_symbols: List[Tuple[str, Optional[str]]] = []
        if parser:
            try:
                source_bytes = content.encode("utf-8")
                tree = parser.parse(source_bytes)
                comments_with_symbols = self._walk_comments_with_symbols(tree.root_node, source_bytes)
            except Exception:
                parser = None

        if not parser:
            # Fallback to regex comment search if tree-sitter parsing is unavailable or failed
            lines = content.splitlines()
            for idx, line in enumerate(lines):
                # 1. Single-line comments (# and //)
                single_match = re.search(r"(?:#|//)\s*(.*)", line)
                if single_match:
                    comment_text = single_match.group(0)  # Preserve the full comment prefix to maintain regex format
                    # Search up to 5 lines ahead for associated symbol
                    symbol = None
                    for j in range(idx + 1, min(idx + 6, len(lines))):
                        next_line = lines[j].strip()
                        if (
                            not next_line
                            or next_line.startswith("#")
                            or next_line.startswith("//")
                            or next_line.startswith("@")
                        ):
                            continue
                        class_match = re.search(r"\bclass\s+(\w+)", next_line)
                        if class_match:
                            symbol = class_match.group(1)
                            break
                        func_match = re.search(r"\b(?:def|function)\s+(\w+)", next_line)
                        if func_match:
                            symbol = func_match.group(1)
                            break
                        assign_match = re.search(r"\b(?:const|let|var)?\s*(\w+)\s*=", next_line)
                        if assign_match:
                            symbol = assign_match.group(1)
                            break
                        break
                    comments_with_symbols.append((comment_text, symbol))

            # 2. Multi-line block comments (/* ... */)
            # For simplicity, block comments in fallback are processed without direct symbol mapping
            for block in re.findall(r"/\*([\s\S]*?)\*/", content):
                for line in block.splitlines():
                    cleaned_line = re.sub(r"^\s*\*\s*", "", line).strip()
                    comments_with_symbols.append((cleaned_line, None))

        # Regex to match implements:, validates:, traces_to:
        pattern = re.compile(r"(?i)\b(implements|validates|traces_to)\s*:\s*([^\n\r*]+)")

        for comment, symbol in comments_with_symbols:
            matches = pattern.findall(comment)
            for link_type, targets in matches:
                # Clean targets
                targets_str = targets.split("*/")[0].strip()  # Strip block comment close if present
                for target in [t.strip() for t in targets_str.split(",") if t.strip()]:
                    links.append(
                        TraceLink(
                            source=file_path,
                            target=target,
                            type=link_type.lower(),
                            symbol=symbol,
                        )
                    )

        # Update cache
        self._cache[file_path] = (content_hash, links)
        return links

    async def check(self, files: List[str]) -> List[Violation]:
        if not self.should_run():
            return []

        from ..utils.path import normalize_project_path

        violations: List[Violation] = []
        for file_path in files:
            norm_path = normalize_project_path(file_path)
            path = Path(file_path)
            # Only trace code in src/ or tests/
            if not (norm_path.startswith("src/") or norm_path.startswith("tests/")):
                continue

            # Skip migrations
            if "src/ade_compliance/migrations/" in norm_path:
                continue

            # Support checking supported language suffixes
            if path.suffix.lower() not in (".py", ".js", ".ts", ".tsx", ".java"):
                continue

            if not path.exists():
                continue

            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            links = self.extract_links(file_path, content)

            # Heuristic: Every implementation file in src/ must have at least one trace link
            if norm_path.startswith("src/") and not links:
                violations.append(
                    Violation(
                        axiom_id="Π.3.1",
                        file_path=norm_path,
                        message=f"Missing traceability links in {norm_path}. Must declare implements/traces_to markers in comments.",
                        state=ViolationState.NEW,
                    )
                )

        return violations

    def generate_matrix(self, links: List[TraceLink]) -> Dict[str, Dict[str, List[str]]]:
        matrix: Dict[str, Dict[str, List[str]]] = {}
        for link in links:
            if link.source not in matrix:
                matrix[link.source] = {
                    "implements": [],
                    "validates": [],
                    "traces_to": [],
                }

            ltype = link.type.lower()
            if ltype in matrix[link.source]:
                # If symbol metadata is present, include it in target formatting
                target_str = f"{link.target} ({link.symbol})" if link.symbol else link.target
                # Avoid duplicates
                if target_str not in matrix[link.source][ltype]:
                    matrix[link.source][ltype].append(target_str)
        return matrix
