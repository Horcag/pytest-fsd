# src/pytest_fsd/rules/no_ui_in_app/__init__.py
"""Reject app/ui and direct GUI framework imports in the app layer."""

import ast
import os
from typing import List

from ..._lib.fs_utils import get_layer_by_canonical_name
from ..._lib.violations import Violation
from ...config import FsdConfig

RULE_NAME = "no-ui-in-app"

FORBIDDEN_UI_MODULES = {
    "tkinter",
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "ttkbootstrap",
    "customtkinter",
}


def check(config: FsdConfig, project_root: str) -> List[Violation]:
    """Verify that the app layer does not import UI frameworks directly."""
    violations = []
    base_dir = os.path.join(project_root, config.base_path)

    app_layer = get_layer_by_canonical_name(config, "app")
    if not app_layer:
        return violations

    app_path = os.path.join(base_dir, app_layer)
    if not os.path.isdir(app_path):
        return violations

    ui_path = os.path.join(app_path, "ui")
    if os.path.isdir(ui_path):
        violations.append(
            Violation(
                rule=RULE_NAME,
                file_path=ui_path,
                message="Segment 'app/ui' is not allowed. Put UI components in pages or widgets.",
            )
        )

    for root, _, files in os.walk(app_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Blind Spot 7 Optimization: Skip AST parsing if no UI keywords are present
                if not any(ui_lib in content for ui_lib in FORBIDDEN_UI_MODULES):
                    continue

                tree = ast.parse(content, filename=file_path)
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        base_import = alias.name.split(".")[0]
                        if base_import in FORBIDDEN_UI_MODULES:
                            violations.append(
                                Violation(
                                    rule=RULE_NAME,
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    message=f"Layer 'app' should not import UI framework "
                                    f"'{base_import}'. Extract UI to 'windows', 'pages' or 'widgets'.",
                                )
                            )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        base_import = node.module.split(".")[0]
                        if base_import in FORBIDDEN_UI_MODULES:
                            violations.append(
                                Violation(
                                    rule=RULE_NAME,
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    message=f"Layer 'app' should not import UI framework "
                                    f"'{base_import}'. Extract UI to 'windows', 'pages' or 'widgets'.",
                                )
                            )

    return violations
