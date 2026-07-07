"""Tree-sitter based source code parser for extracting symbols and references."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tree_sitter
import tree_sitter_language_pack as tslp


@dataclass
class Symbol:
    """A code symbol extracted from a source file."""

    name: str
    kind: str  # "function", "class", "method", "variable", "type", "interface"
    file_path: str
    line_start: int
    line_end: int
    signature: str = ""
    docstring: str = ""
    parent: str | None = None
    references: list[str] = field(default_factory=list)

    @property
    def qualified_name(self) -> str:
        """Return the fully-qualified symbol name."""
        if self.parent:
            return f"{self.parent}.{self.name}"
        return self.name


@dataclass
class Edge:
    """A directed reference edge between two symbols."""

    source: str  # file path of the referencing file
    target: str  # name of the referenced symbol
    kind: str  # "calls", "imports", "inherits", "uses"
    file_path: str
    line: int


# Node types that represent definitions, per language family
_DEFINITION_QUERIES: dict[str, str] = {
    "python": """
        (function_definition name: (identifier) @name) @definition.function
        (class_definition name: (identifier) @name) @definition.class
        (assignment left: (identifier) @name) @definition.variable
    """,
    "typescript": """
        (function_declaration name: (identifier) @name) @definition.function
        (class_declaration name: (identifier) @name) @definition.class
        (method_definition name: (property_identifier) @name) @definition.method
        (interface_declaration name: (type_identifier) @name) @definition.interface
        (type_alias_declaration name: (type_identifier) @name) @definition.type
        (variable_declarator name: (identifier) @name) @definition.variable
        (lexical_declaration (variable_declarator name: (identifier) @name)) @definition.variable
    """,
    "javascript": """
        (function_declaration name: (identifier) @name) @definition.function
        (class_declaration name: (identifier) @name) @definition.class
        (method_definition name: (property_identifier) @name) @definition.method
        (variable_declarator name: (identifier) @name) @definition.variable
        (lexical_declaration (variable_declarator name: (identifier) @name)) @definition.variable
    """,
    "go": """
        (function_declaration name: (identifier) @name) @definition.function
        (method_declaration name: (field_identifier) @name) @definition.method
        (type_declaration (type_spec name: (type_identifier) @name)) @definition.type
    """,
    "rust": """
        (function_item name: (identifier) @name) @definition.function
        (impl_item type: (type_identifier) @name) @definition.class
        (struct_item name: (type_identifier) @name) @definition.type
        (enum_item name: (type_identifier) @name) @definition.type
        (trait_item name: (type_identifier) @name) @definition.interface
    """,
    "java": """
        (method_declaration name: (identifier) @name) @definition.method
        (class_declaration name: (identifier) @name) @definition.class
        (interface_declaration name: (identifier) @name) @definition.interface
    """,
    "c": """
        (function_definition declarator: (function_declarator declarator: (identifier) @name)) @definition.function
        (struct_specifier name: (type_identifier) @name) @definition.type
        (enum_specifier name: (type_identifier) @name) @definition.type
    """,
    "cpp": """
        (function_definition declarator: (function_declarator declarator: (identifier) @name)) @definition.function
        (function_definition declarator: (function_declarator declarator: (qualified_identifier name: (identifier) @name))) @definition.function
        (class_specifier name: (type_identifier) @name) @definition.class
        (struct_specifier name: (type_identifier) @name) @definition.type
    """,
}

# Alias for shared queries
_DEFINITION_QUERIES["tsx"] = _DEFINITION_QUERIES["typescript"]
_DEFINITION_QUERIES["jsx"] = _DEFINITION_QUERIES["javascript"]
_DEFINITION_QUERIES["php"] = """
    (function_definition name: (name) @name) @definition.function
    (class_declaration name: (name) @name) @definition.class
    (method_declaration name: (name) @name) @definition.method
"""
_DEFINITION_QUERIES["csharp"] = """
    (method_declaration name: (identifier) @name) @definition.method
    (class_declaration name: (identifier) @name) @definition.class
    (interface_declaration name: (identifier) @name) @definition.interface
    (struct_declaration name: (identifier) @name) @definition.type
    (enum_declaration name: (identifier) @name) @definition.type
"""
_DEFINITION_QUERIES["ruby"] = """
    (method name: (identifier) @name) @definition.method
    (class name: (constant) @name) @definition.class
    (module name: (constant) @name) @definition.class
"""
_DEFINITION_QUERIES["kotlin"] = """
    (function_declaration (simple_identifier) @name) @definition.function
    (class_declaration (type_identifier) @name) @definition.class
"""
_DEFINITION_QUERIES["swift"] = """
    (function_declaration name: (simple_identifier) @name) @definition.function
    (class_declaration name: (type_identifier) @name) @definition.class
    (protocol_declaration name: (type_identifier) @name) @definition.interface
"""
_DEFINITION_QUERIES["scala"] = """
    (function_definition name: (identifier) @name) @definition.function
    (class_definition name: (identifier) @name) @definition.class
    (trait_definition name: (identifier) @name) @definition.interface
    (object_definition name: (identifier) @name) @definition.class
"""

# Node types that represent references (calls, usages)
_CALL_NODE_TYPES = {
    "call_expression",
    "call",
    "invocation_expression",
    "method_invocation",
}

_IMPORT_NODE_TYPES = {
    "import_statement",
    "import_declaration",
    "import_from_statement",
    "use_declaration",
}


class TreeSitterParser:
    """Parses source files using tree-sitter to extract symbols and references.

    Uses tree-sitter grammars from tree-sitter-language-pack for multi-language
    support. Extracts function/class/method definitions and their signatures,
    plus reference edges (calls, imports) for building the symbol graph.
    """

    def __init__(self) -> None:
        self._grammars: dict[str, tree_sitter.Language] = {}
        self._parser = tree_sitter.Parser()

    # Maximum file size to parse (1 MB) — skip larger files to avoid OOM
    MAX_FILE_SIZE = 1_048_576

    def parse_file(self, path: Path) -> list[Symbol]:
        """Parse a source file and return extracted symbols.

        Args:
            path: Path to the source file.

        Returns:
            List of Symbol instances found in the file.
        """
        from arbiterx.mapper.languages import detect_language

        # Skip files larger than threshold to prevent OOM
        if path.stat().st_size > self.MAX_FILE_SIZE:
            return []

        source = path.read_bytes()
        language = detect_language(path)
        if language is None:
            return []

        grammar = self._load_grammar(language)
        if grammar is None:
            return []

        self._parser.language = grammar
        tree = self._parser.parse(source)

        return self._extract_definitions(tree, source, str(path), language)

    def parse_references(self, path: Path) -> list[Edge]:
        """Parse a source file and return reference edges.

        Args:
            path: Path to the source file.

        Returns:
            List of Edge instances found in the file.
        """
        from arbiterx.mapper.languages import detect_language

        # Skip files larger than threshold to prevent OOM
        if path.stat().st_size > self.MAX_FILE_SIZE:
            return []

        source = path.read_bytes()
        language = detect_language(path)
        if language is None:
            return []

        grammar = self._load_grammar(language)
        if grammar is None:
            return []

        self._parser.language = grammar
        tree = self._parser.parse(source)

        return self._extract_references(tree, source, str(path), language)

    def _load_grammar(self, language: str) -> tree_sitter.Language | None:
        """Load and cache the tree-sitter grammar for a language."""
        if language not in self._grammars:
            from arbiterx.mapper.languages import _GRAMMAR_NAME_MAP

            grammar_name = _GRAMMAR_NAME_MAP.get(language, language)
            try:
                self._grammars[language] = tslp.get_language(grammar_name)
            except Exception:
                # Grammar unavailable — skip silently (LookupError, DownloadError, etc.)
                return None
        return self._grammars[language]

    def _extract_definitions(
        self, tree: Any, source: bytes, file_path: str, language: str
    ) -> list[Symbol]:
        """Extract symbol definitions using AST traversal.

        Uses a generic traversal approach that works across languages
        by matching known definition node types.
        """
        symbols: list[Symbol] = []
        root = tree.root_node

        # Try query-based extraction first (more precise)
        query_str = _DEFINITION_QUERIES.get(language)
        if query_str:
            symbols = self._query_definitions(root, source, file_path, language, query_str)
            if symbols:
                return symbols

        # Fallback: generic AST traversal
        self._walk_for_definitions(root, source, file_path, language, symbols, parent=None)
        return symbols

    def _query_definitions(
        self,
        root: Any,
        source: bytes,
        file_path: str,
        language: str,
        query_str: str,
    ) -> list[Symbol]:
        """Extract definitions using tree-sitter queries."""
        symbols: list[Symbol] = []
        try:
            lang = self._grammars[language]
            query = lang.query(query_str)
            captures = query.captures(root)
        except Exception:
            return []

        # Process captures - group by definition node
        # captures is dict[str, list[Node]] in newer tree-sitter
        if isinstance(captures, dict):
            name_nodes = captures.get("name", [])
            for node in name_nodes:
                name = self._node_text(node, source)
                if not name or name.startswith("_") and name.startswith("__"):
                    continue

                # Determine kind from the parent node type
                parent_node = node.parent
                kind = self._node_type_to_kind(parent_node.type if parent_node else "")

                # Get signature (the line containing the definition)
                def_node = parent_node if parent_node else node
                signature = self._extract_signature(def_node, source)

                # Get docstring (next sibling or first child that's a string)
                docstring = self._extract_docstring(def_node, source, language)

                # Determine parent class/scope
                parent_name = self._find_parent_scope(node, source)

                symbols.append(
                    Symbol(
                        name=name,
                        kind=kind,
                        file_path=file_path,
                        line_start=node.start_point[0] + 1,
                        line_end=(def_node.end_point[0] + 1) if def_node else node.end_point[0] + 1,
                        signature=signature,
                        docstring=docstring,
                        parent=parent_name,
                    )
                )
        else:
            # Older tree-sitter returns list of (node, capture_name) tuples
            for node, capture_name in captures:
                if capture_name != "name":
                    continue
                name = self._node_text(node, source)
                if not name:
                    continue

                parent_node = node.parent
                kind = self._node_type_to_kind(parent_node.type if parent_node else "")
                def_node = parent_node if parent_node else node
                signature = self._extract_signature(def_node, source)
                docstring = self._extract_docstring(def_node, source, language)
                parent_name = self._find_parent_scope(node, source)

                symbols.append(
                    Symbol(
                        name=name,
                        kind=kind,
                        file_path=file_path,
                        line_start=node.start_point[0] + 1,
                        line_end=def_node.end_point[0] + 1,
                        signature=signature,
                        docstring=docstring,
                        parent=parent_name,
                    )
                )

        return symbols

    def _walk_for_definitions(
        self,
        node: Any,
        source: bytes,
        file_path: str,
        language: str,
        symbols: list[Symbol],
        parent: str | None,
    ) -> None:
        """Generic recursive walk to find definitions."""
        node_type = node.type

        # Detect definition-like nodes generically
        if "definition" in node_type or "declaration" in node_type:
            name = self._find_name_child(node, source)
            if name and len(name) > 0 and not name.startswith("("):
                kind = self._node_type_to_kind(node_type)
                signature = self._extract_signature(node, source)
                docstring = self._extract_docstring(node, source, language)

                symbols.append(
                    Symbol(
                        name=name,
                        kind=kind,
                        file_path=file_path,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        signature=signature,
                        docstring=docstring,
                        parent=parent,
                    )
                )

                # If it's a class, recurse with this as parent
                if "class" in node_type:
                    for child in node.children:
                        self._walk_for_definitions(
                            child, source, file_path, language, symbols, parent=name
                        )
                    return

        # Recurse into children
        for child in node.children:
            self._walk_for_definitions(child, source, file_path, language, symbols, parent)

    def _extract_references(
        self, tree: Any, source: bytes, file_path: str, language: str
    ) -> list[Edge]:
        """Extract reference edges by walking the AST for calls and identifiers."""
        edges: list[Edge] = []
        self._walk_for_references(tree.root_node, source, file_path, edges)
        return edges

    def _walk_for_references(
        self, node: Any, source: bytes, file_path: str, edges: list[Edge]
    ) -> None:
        """Walk AST to find call expressions and import references."""
        node_type = node.type

        if node_type in _CALL_NODE_TYPES:
            # Extract the function/method being called
            callee = self._extract_callee_name(node, source)
            if callee and len(callee) > 1:
                edges.append(
                    Edge(
                        source=file_path,
                        target=callee,
                        kind="calls",
                        file_path=file_path,
                        line=node.start_point[0] + 1,
                    )
                )

        elif node_type in _IMPORT_NODE_TYPES:
            # Extract imported names
            imported = self._extract_import_names(node, source)
            for name in imported:
                if name and len(name) > 1:
                    edges.append(
                        Edge(
                            source=file_path,
                            target=name,
                            kind="imports",
                            file_path=file_path,
                            line=node.start_point[0] + 1,
                        )
                    )

        for child in node.children:
            self._walk_for_references(child, source, file_path, edges)

    # --- Helper methods ---

    def _node_text(self, node: Any, source: bytes) -> str:
        """Extract the text content of a node."""
        try:
            return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
        except (AttributeError, TypeError):
            return ""

    def _find_name_child(self, node: Any, source: bytes) -> str:
        """Find the 'name' child of a definition node."""
        for child in node.children:
            if child.type in (
                "identifier",
                "type_identifier",
                "property_identifier",
                "field_identifier",
                "name",
            ):
                return self._node_text(child, source)
            # For declarators (C/C++)
            if "declarator" in child.type:
                return self._find_name_child(child, source)
        return ""

    def _node_type_to_kind(self, node_type: str) -> str:
        """Map a tree-sitter node type to our symbol kind."""
        if "function" in node_type or "method" in node_type:
            if "method" in node_type:
                return "method"
            return "function"
        if "class" in node_type:
            return "class"
        if "interface" in node_type or "trait" in node_type:
            return "interface"
        if "struct" in node_type or "type" in node_type or "enum" in node_type:
            return "type"
        if "variable" in node_type or "assignment" in node_type or "lexical" in node_type:
            return "variable"
        if "module" in node_type or "namespace" in node_type:
            return "module"
        return "function"  # safe default

    def _extract_signature(self, node: Any, source: bytes) -> str:
        """Extract the signature (first line) of a definition."""
        text = self._node_text(node, source)
        # Take up to the first newline or body start
        lines = text.split("\n")
        sig = lines[0] if lines else text
        # Truncate at body markers
        for marker in ("{", ":", "=>"):
            idx = sig.find(marker)
            if idx > 0 and marker == ":":
                # For Python, include the colon but not the body
                sig = sig[: idx + 1]
                break
            elif idx > 0:
                sig = sig[:idx].rstrip()
                break
        return sig.strip()[:200]  # Cap at 200 chars

    def _extract_docstring(self, node: Any, source: bytes, language: str) -> str:
        """Extract docstring/comment from definition node."""
        if language == "python":
            # Look for expression_statement > string as first child of body
            for child in node.children:
                if child.type == "block":
                    for block_child in child.children:
                        if block_child.type == "expression_statement":
                            for expr in block_child.children:
                                if expr.type == "string":
                                    doc = self._node_text(expr, source)
                                    # Strip triple quotes
                                    doc = doc.strip("\"'").strip()
                                    return doc[:500]
                        break  # Only check first statement
        else:
            # Look for preceding comment
            prev = node.prev_sibling
            if prev and prev.type in ("comment", "block_comment"):
                return self._node_text(prev, source).strip("/* \n")[:500]

        return ""

    def _find_parent_scope(self, node: Any, source: bytes) -> str | None:
        """Find the enclosing class/module name for a symbol."""
        current = node.parent
        while current:
            if "class" in current.type and "definition" in current.type:
                name = self._find_name_child(current, source)
                if name:
                    return name
            if "class" in current.type and "declaration" in current.type:
                name = self._find_name_child(current, source)
                if name:
                    return name
            current = current.parent
        return None

    def _extract_callee_name(self, node: Any, source: bytes) -> str:
        """Extract the name of the function/method being called."""
        for child in node.children:
            if child.type == "identifier":
                return self._node_text(child, source)
            if child.type in ("member_expression", "attribute"):
                # Get the attribute/method name (rightmost identifier)
                return self._node_text(child, source)
            if child.type == "field_expression":
                return self._node_text(child, source)
        return ""

    def _extract_import_names(self, node: Any, source: bytes) -> list[str]:
        """Extract all imported symbol names from an import node."""
        names: list[str] = []

        # Generic extraction: find identifier-like children
        for child in node.children:
            if child.type in ("dotted_name", "identifier", "type_identifier"):
                names.append(self._node_text(child, source))
            elif child.type in ("import_clause", "import_specifier"):
                for sub in child.children:
                    if sub.type in ("identifier", "type_identifier"):
                        names.append(self._node_text(sub, source))

        return names
