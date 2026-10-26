"""Require cross-slice imports to use the target slice's public API."""

import ast
import os
from typing import List

from ..._lib.ast_utils import get_exported_names, get_node_location, parse_python_file
from ..._lib.fs_utils import get_sliced_layers
from ..._lib.dynamic_imports import analyze_imports
from ..._lib.imports import imported_modules, resolve_module
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "no-public-api-sidestep"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that all cross-slice imports go through the slice's Public API."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)
    base_module = config.base_path.replace(os.sep, ".").strip(".")
    if not os.path.isdir(base_dir):
        return violations

    sliced_layers = get_sliced_layers(config)
    for root, _, files in os.walk(base_dir):
        for file in files:
            if not file.endswith(".py"):
                continue
            file_path = os.path.join(root, file)
            parts = os.path.relpath(file_path, base_dir).split(os.sep)
            current_layer = parts[0]
            current_slice = parts[1] if len(parts) > 2 and current_layer in sliced_layers else None
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
                    if target is not None and len(target) >= 2:
                        targets.append((target, node.module or "." * node.level, [alias.name for alias in node.names]))
                    else:
                        for imported in imported_modules(node, file_path, base_dir, config.layers):
                            if len(imported) >= 2:
                                targets.append((imported, ".".join(imported), []))

                for target, module_path, imported_names in targets:
                    if len(target) < 2:
                        continue
                    target_layer, target_slice = target[:2]
                    if target_layer not in sliced_layers:
                        continue
                    if current_layer == target_layer and current_slice == target_slice:
                        continue
                    location = get_node_location(node, source)
                    if len(target) > 2:
                        violations.append(Violation(
                            rule=RULE_NAME, file_path=file_path, **location,
                            message=f"Importing internal module '{module_path}' "
                            f"from slice '{target_layer}/{target_slice}'. "
                            f"Import from '{base_module}.{target_layer}.{target_slice}' instead.",
                        ))
                    elif imported_names:
                        target_init = os.path.join(base_dir, target_layer, target_slice, "__init__.py")
                        if not os.path.isfile(target_init):
                            continue
                        exported_names = get_exported_names(target_init)
                        if exported_names is None:
                            violations.append(Violation(
                                rule=RULE_NAME, file_path=file_path, **location,
                                message=f"Slice '{target_layer}/{target_slice}' does not define `__all__` "
                                "as a static list of strings in its __init__.py. "
                                "Public API exports must be explicit to prevent encapsulation bypass.",
                            ))
                        else:
                            for name in imported_names:
                                if name != "*" and name not in exported_names:
                                    violations.append(Violation(
                                        rule=RULE_NAME, file_path=file_path, **location,
                                        message=f"Name '{name}' is not explicitly exported in "
                                        f"'{target_layer}/{target_slice}/__init__.py'. "
                                        "Add it to `__all__` to make it part of the Public API.",
                                    ))
    return violations
