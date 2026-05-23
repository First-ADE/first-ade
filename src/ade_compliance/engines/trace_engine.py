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

    def _walk_comments(self, node, source_bytes: bytes) -> List[str]:
        comments = []
        if node.type in ("comment", "line_comment", "block_comment"):
            try:
                comment_text = source_bytes[node.start_byte:node.end_byte].decode("utf-8")
                comments.append(comment_text)
            except Exception:
                pass

        for child in node.children:
            comments.extend(self._walk_comments(child, source_bytes))
        return comments

    def extract_links(self, file_path: str, content: str) -> List[TraceLink]:
        # Compute hash
        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
        
        # Check cache
        if file_path in self._cache:
            cached_hash, cached_links = self._cache[file_path]
            if cached_hash == content_hash:
                return cached_links

        links: List[TraceLink] = []
        parser, _ = self._get_parser_and_lang(file_path)

        comments: List[str] = []
        if parser:
            try:
                source_bytes = content.encode("utf-8")
                tree = parser.parse(source_bytes)
                comments = self._walk_comments(tree.root_node, source_bytes)
            except Exception:
                # Fallback to regex comment search if tree-sitter parsing fails
                comments = re.findall(r"(?:#|//|/\*)\s*(.*)(?:\*/)?", content)
        else:
            # Complete regex fallback for comment blocks if parsers are unavailable
            comments = re.findall(r"(?:#|//|/\*)\s*(.*)(?:\*/)?", content)

        # Regex to match implements:, validates:, traces_to:
        pattern = re.compile(r"(?i)\b(implements|validates|traces_to)\s*:\s*([^\n\r*]+)")

        for comment in comments:
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
                        )
                    )

        # Update cache
        self._cache[file_path] = (content_hash, links)
        return links

    async def check(self, files: List[str]) -> List[Violation]:
        if not self.should_run():
            return []

        violations: List[Violation] = []
        for file_path in files:
            path = Path(file_path)
            # Only trace code in src/ or tests/
            if not (file_path.startswith("src/") or file_path.startswith("tests/")):
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
            if file_path.startswith("src/") and not links:
                violations.append(
                    Violation(
                        axiom_id="Π.3.1",
                        file_path=file_path,
                        message=f"Missing traceability links in {file_path}. Must declare implements/traces_to markers in comments.",
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
                # Avoid duplicates
                if link.target not in matrix[link.source][ltype]:
                    matrix[link.source][ltype].append(link.target)
        return matrix
