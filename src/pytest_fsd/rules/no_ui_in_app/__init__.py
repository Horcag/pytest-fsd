# src/pytest_fsd/rules/no_ui_in_app/__init__.py
"""
[Rule: no-ui-in-app]
The app layer should not directly import UI frameworks.
UI components belong in pages/windows/widgets layers.
"""

import ast
import os
from typing import List

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

    if "app" not in config.layers:
        return violations

    app_path = os.path.join(base_dir, "app")
    if not os.path.isdir(app_path):
        return violations

    for root, _, files in os.walk(app_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=file_path)
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
