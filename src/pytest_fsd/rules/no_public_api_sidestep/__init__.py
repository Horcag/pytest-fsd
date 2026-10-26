"""Require imports between slices and Shared APIs to use public boundaries."""

import ast
import os
from typing import List, Optional, Tuple

from ..._lib.ast_utils import get_exported_names, get_node_location, parse_python_file
from ..._lib.dynamic_imports import analyze_imports
from ..._lib.fs_utils import (
    get_layer_by_canonical_name,
    get_sliced_layers,
    is_ignored_directory,
)
from ..._lib.imports import imported_modules, resolve_module
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "no-public-api-sidestep"


def _public_boundary(
    target: Tuple[str, ...], base_dir: str, sliced_layers: List[str], shared_layer: Optional[str]
) -> Optional[Tuple[str, ...]]:
    if len(target) < 2:
        return None
    if target[0] in sliced_layers:
        return target[:2]
    if target[0] != shared_layer:
        return None
    if target[1] not in ("ui", "lib"):
        return target[:2]
    # Shared UI components and libraries expose individual package APIs;
    # standalone modules in these segments are already public entrypoints.
    if len(target) >= 3 and os.path.isdir(os.path.join(base_dir, *target[:3])):
        return target[:3]
    return None


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify imports use the slice or Shared package public API."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)
    base_module = config.base_path.replace(os.sep, ".").strip(".")
    if not os.path.isdir(base_dir):
        return violations

    sliced_layers = get_sliced_layers(config)
    shared_layer = get_layer_by_canonical_name(config, "shared")
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = sorted(name for name in dirs if not is_ignored_directory(name)
                         and (root != base_dir or name in config.layers))
        for file in sorted(files):
            if not file.endswith(".py"):
                continue
            file_path = os.path.join(root, file)
            parts = os.path.relpath(file_path, base_dir).split(os.sep)
            if parts[0] not in config.layers:
                continue
            current_boundary = _public_boundary(tuple(parts[:-1]), base_dir, sliced_layers, shared_layer)
            parsed = parse_python_file(file_path)
            if parsed is None:
                continue
            source, tree = parsed
            for node in analyze_imports(source, tree, file_path, base_dir).imports:
                targets = []
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        target = resolve_module(alias.name, 0, file_path, base_dir, config.layers)
                        if target is not None:
                            targets.append((target, alias.name, []))
                elif isinstance(node, ast.ImportFrom):
                    target = resolve_module(node.module, node.level, file_path, base_dir, config.layers)
                    if target is not None and _public_boundary(target, base_dir, sliced_layers, shared_layer):
                        targets.append((target, node.module or "." * node.level, [alias.name for alias in node.names]))
                    else:
                        for imported in imported_modules(node, file_path, base_dir, config.layers):
                            if len(imported) >= 2:
                                targets.append((imported, ".".join(imported), []))

                for target, module_path, imported_names in targets:
                    boundary = _public_boundary(target, base_dir, sliced_layers, shared_layer)
                    if boundary is None or current_boundary == boundary:
                        continue
                    api_name = "/".join(boundary)
                    api_module = ".".join(part for part in (base_module, ".".join(boundary)) if part)
                    api_kind = "Slice" if boundary[0] in sliced_layers else "Shared API"
                    location = get_node_location(node, source)
                    if len(target) > len(boundary):
                        violations.append(Violation(
                            rule=RULE_NAME, file_path=file_path, **location,
                            message=f"Importing internal module '{module_path}' "
                            f"from public API '{api_name}'. "
                            f"Import from '{api_module}' instead.",
                        ))
                    elif imported_names:
                        target_init = os.path.join(base_dir, *boundary, "__init__.py")
                        if not os.path.isfile(target_init):
                            continue
                        exported_names = get_exported_names(target_init)
                        if exported_names is None:
                            violations.append(Violation(
                                rule=RULE_NAME, file_path=file_path, **location,
                                message=f"{api_kind} '{api_name}' does not define `__all__` "
                                "as a statically resolvable sequence of strings in its __init__.py. "
                                "Public API exports must be explicit to prevent encapsulation bypass.",
                            ))
                        else:
                            for name in imported_names:
                                if name != "*" and name not in exported_names:
                                    violations.append(Violation(
                                        rule=RULE_NAME, file_path=file_path, **location,
                                        message=f"Name '{name}' is not explicitly exported in "
                                        f"'{api_name}/__init__.py'. "
                                        "Add it to `__all__` to make it part of the Public API.",
                                    ))
    return violations
