# tests/rules/test_no_ui_in_app.py
"""Tests for the no-ui-in-app rule."""
from pytest_fsd.config import load_config
from pytest_fsd.rules.no_ui_in_app import RULE_NAME, check


def test_no_ui_in_app_clean(create_project):
    """No errors when app layer doesn't import UI frameworks."""
    project_root = create_project(
        """
        📂 app
          📄 __init__.py
          📄 main.py
        📂 shared
          📂 config
            📄 __init__.py
        """
    )
    (project_root / "src" / "app" / "main.py").write_text(
        "import os\nimport sys\n"
    )

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_no_ui_in_app_tkinter_import(create_project):
    """Error when app layer imports tkinter."""
    project_root = create_project(
        """
        📂 app
          📄 __init__.py
          📄 main.py
        """
    )
    (project_root / "src" / "app" / "main.py").write_text(
        "import tkinter as tk\n"
    )

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "tkinter" in violations[0].message


def test_no_ui_in_app_from_import(create_project):
    """Error when app layer uses 'from PyQt6 import ...'."""
    project_root = create_project(
        """
        📂 app
          📄 __init__.py
          📄 main.py
        """
    )
    (project_root / "src" / "app" / "main.py").write_text(
        "from PyQt6.QtWidgets import QApplication\n"
    )

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert "PyQt6" in violations[0].message
