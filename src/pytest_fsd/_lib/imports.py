"""Resolve local import statements without loading project modules."""

import ast
import os
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from .ast_utils import get_node_location, parse_python_file
from ..config import FsdConfig


def resolve_module(
    module: Optional[str], level: int, file_path: str, base_dir: str, layers: List[str]
) -> Optional[Tuple[str, ...]]:
    """Resolve a module to components relative to the configured source root."""
    base = Path(base_dir).resolve()
    parts = tuple(module.split(".")) if module else ()
    if level:
        parent = Path(file_path).resolve().parent
        for _ in range(level - 1):
            parent = parent.parent
        try:
            relative = parent.joinpath(*parts).relative_to(base)
        except ValueError:
            return None
        return relative.parts

    # Both `src.features.auth` and source-root imports `features.auth` are valid.
    # Nested roots also accept their qualified path, e.g. `backend.src.features`.
    for count in range(min(len(base.parts), len(parts)), 0, -1):
        if parts[:count] == base.parts[-count:]:
            candidate = parts[count:]
            if candidate and candidate[0] in layers:
                return candidate
    if parts and parts[0] in layers and (base / parts[0]).is_dir():
        return parts
    return None


def imported_modules(
    node: ast.AST, file_path: str, base_dir: str, layers: List[str]
) -> List[Tuple[str, ...]]:
    """Include package imports and existing child modules in from-imports."""
    result = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            parts = resolve_module(alias.name, 0, file_path, base_dir, layers)
            if parts is not None:
                result.append(parts)
    elif isinstance(node, ast.ImportFrom):
        parts = resolve_module(node.module, node.level, file_path, base_dir, layers)
        if parts is not None:
            result.append(parts)
            for alias in node.names:
                child = Path(base_dir).joinpath(*parts, alias.name)
                if alias.name != "*" and (child.is_dir() or child.with_suffix(".py").is_file()):
                    result.append(parts + (alias.name,))
        elif node.module and not node.level:
            # `from src import features` (or a nested source root).
            base = Path(base_dir).resolve()
            module_parts = tuple(node.module.split("."))
            if module_parts == base.parts[-len(module_parts):]:
                for alias in node.names:
                    if alias.name in layers and (base / alias.name).is_dir():
                        result.append((alias.name,))
    return list(dict.fromkeys(result))


def iter_imports(
    config: FsdConfig, project_root: str
) -> Iterator[Tuple[str, Tuple[str, ...], Tuple[str, ...], dict]]:
    """Yield local source/target components and diagnostic locations."""
    base_dir = os.path.join(project_root, config.base_path)
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for filename in sorted(files):
            if not filename.endswith(".py"):
                continue
            file_path = os.path.join(root, filename)
            source_parts = Path(file_path).relative_to(base_dir).parts
            if source_parts[0] not in config.layers:
                continue
            parsed = parse_python_file(file_path)
            if parsed is None:
                continue  # The facade reports unreadable/invalid Python sources.
            source, tree = parsed
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for target in imported_modules(node, file_path, base_dir, config.layers):
                        yield file_path, source_parts, target, get_node_location(node, source)
