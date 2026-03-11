# src/pytest_fsd/rules/forbidden_imports/__init__.py
"""
[Rule: forbidden-imports / no-higher-level-imports]
Layers can only import from layers below them in the FSD hierarchy.
Uses pytest-archon for dynamic runtime checking.
"""

import os
from typing import List

from pytest_archon import archrule

from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "forbidden-imports"


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that each layer only imports from layers below it."""
    violations = []
    base_path = config.base_path
    layers = config.layers

    for i, current_layer in enumerate(layers):
        layer_path = os.path.join(project_root, base_path, current_layer)
        if not os.path.isdir(layer_path):
            continue

        # Проверяем наличие .py файлов в слое
        has_python_files = False
        for _, _, files in os.walk(layer_path):
            if any(f.endswith(".py") and f != "__init__.py" for f in files):
                has_python_files = True
                break

        if not has_python_files:
            continue

        forbidden_layers = layers[:i]
        if forbidden_layers:
            forbidden_modules = [f"{base_path}.{layer}.*" for layer in forbidden_layers]
            try:
                (
                    archrule(
                        f"[{current_layer.upper()}] must not import layers above it"
                    )
                    .match(f"{base_path}.{current_layer}.*")
                    .should_not_import(*forbidden_modules)
                    .check(base_path)
                )
            except BaseException as e:
                violations.append(
                    Violation(
                        rule=RULE_NAME,
                        file_path=current_layer,
                        message=str(e).strip(),
                    )
                )

    return violations
