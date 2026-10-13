# src/pytest_fsd/_lib/ast_utils.py
"""Shared AST parsing utilities used by multiple rules."""

import ast
from typing import Dict, List, Tuple, Optional


def parse_python_file(filepath: str) -> Optional[Tuple[str, ast.Module]]:
    """Read and parse Python source without importing or executing it."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        return source, ast.parse(source, filename=filepath)
    except (OSError, UnicodeError, SyntaxError, ValueError):
        return None


def get_node_location(node: ast.AST, source: str) -> Dict[str, Optional[int]]:
    """Return one-based character positions with an exclusive end position."""
    lines = source.split("\n")

    def column(line: Optional[int], offset: Optional[int]) -> Optional[int]:
        if line is None or offset is None:
            return None
        # AST columns count UTF-8 bytes; diagnostics count characters.
        return len(lines[line - 1].encode("utf-8")[:offset].decode("utf-8")) + 1

    line = getattr(node, "lineno", None)
    end_line = getattr(node, "end_lineno", None)
    return {
        "line_number": line,
        "column_number": column(line, getattr(node, "col_offset", None)),
        "end_line_number": end_line,
        "end_column_number": column(end_line, getattr(node, "end_col_offset", None)),
    }


def get_imports_from_file(
    filepath: str,
) -> List[Tuple[int, Optional[str], int, List[str]]]:
    """Return list of (line_number, full_module_path, level, imported_names).

    Level represents relative imports:
    0 = absolute import (e.g. `import foo` or `from foo import bar`)
    1 = current directory (`from . import bar` -> module=None, level=1)
    2 = parent directory (`from ..foo import bar` -> module='foo', level=2)
    """
    imports = []
    parsed = parse_python_file(filepath)
    if parsed is None:
        return []
    _, tree = parsed

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, alias.name, 0, [alias.name]))
        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            imports.append((node.lineno, node.module, node.level, names))

    return imports


def get_exported_names(filepath: str) -> Optional[List[str]]:
    """Return the list of names exported in __all__ if defined, or None if not defined."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
    except Exception:
        return None

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        return [
                            elt.value
                            for elt in node.value.elts
                            if getattr(elt, "value", None) is not None
                        ]
    return None
