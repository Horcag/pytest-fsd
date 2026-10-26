# src/pytest_fsd/_lib/ast_utils.py
"""Shared AST parsing utilities used by multiple rules."""

import ast
import tokenize
from typing import Dict, List, Tuple, Optional


def parse_python_file(filepath: str) -> Optional[Tuple[str, ast.Module]]:
    """Read and parse Python source without importing or executing it."""
    try:
        with tokenize.open(filepath) as f:
            source = f.read()
        return source, ast.parse(source, filename=filepath)
    except (OSError, UnicodeError, SyntaxError, ValueError, LookupError, RecursionError):
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
    """Return statically declared string exports, or None when unknown."""
    parsed = parse_python_file(filepath)
    if parsed is None:
        return None
    _, tree = parsed

    def names(value: ast.AST) -> Optional[List[str]]:
        if isinstance(value, (ast.List, ast.Tuple)):
            result = []
            for element in value.elts:
                if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
                    return None
                result.append(element.value)
            return result
        if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
            left, right = names(value.left), names(value.right)
            if left is not None and right is not None:
                return left + right
        return None

    exported = None
    # A called local function can expose or change the export list indirectly.
    mutators = {
        definition.name for definition in tree.body
        if isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(isinstance(child, ast.Name) and child.id == "__all__"
                for child in ast.walk(definition))
    }
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for descendant in ast.walk(node):
            if isinstance(descendant, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                value = descendant.value
                if value is not None and any(isinstance(n, ast.Name) and n.id == "__all__" for n in ast.walk(value)):
                    exported = None  # A mutable export list escaped through an alias.
            if isinstance(descendant, ast.Call):
                if isinstance(descendant.func, ast.Name) and descendant.func.id in mutators | {"exec", "eval"}:
                    exported = None
                if any(isinstance(n, ast.Name) and n.id == "__all__"
                       for argument in list(descendant.args) + [kw.value for kw in descendant.keywords]
                       for n in ast.walk(argument)):
                    exported = None  # An opaque call can change the list in place.
            if isinstance(descendant, ast.Subscript) and isinstance(descendant.ctx, (ast.Store, ast.Del)):
                if isinstance(descendant.value, ast.Name) and descendant.value.id == "__all__":
                    exported = None
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
                exported = names(node.value) if len(node.targets) == 1 else None
            elif any(isinstance(child, ast.Name) and child.id == "__all__"
                     for target in node.targets for child in ast.walk(target)):
                exported = None
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "__all__" and node.value is not None:
                exported = names(node.value)
        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "__all__":
                added = names(node.value)
                if isinstance(node.op, ast.Add) and exported is not None and added is not None:
                    exported += added
                else:
                    exported = None
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id == "__all__":
                if exported is not None and len(call.args) == 1 and not call.keywords:
                    if call.func.attr == "append" and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
                        exported.append(call.args[0].value)
                        continue
                    if call.func.attr == "extend":
                        added = names(call.args[0])
                        if added is not None:
                            exported += added
                            continue
                exported = None
        else:
            # Conditional declarations and mutations cannot define a known API.
            for descendant in ast.walk(node):
                if isinstance(descendant, ast.Name) and descendant.id == "__all__" and isinstance(descendant.ctx, (ast.Store, ast.Del)):
                    exported = None
                    break
                if isinstance(descendant, ast.Call) and isinstance(descendant.func, ast.Attribute):
                    receiver = descendant.func.value
                    if isinstance(receiver, ast.Name) and receiver.id == "__all__":
                        exported = None
                        break
    return exported
