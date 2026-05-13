# tests/rules/test_typo_in_layer_name.py
"""Tests for the typo-in-layer-name rule."""
from pytest_fsd.config import load_config
from pytest_fsd.rules.typo_in_layer_name import RULE_NAME, check


def test_typo_in_layer_name_clean(create_project):
    """No errors when all root folders are known layers."""
    project_root = create_project(
        """
        📂 app
        📂 features
          📂 auth
            📄 __init__.py
        📂 shared
          📂 ui
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_typo_in_layer_name_typo(create_project):
    """Error when a root folder is not a known layer (typo detection)."""
    project_root = create_project(
        """
        📂 app
        📂 fietures
          📂 auth
            📄 __init__.py
        📂 shared
          📂 ui
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "fietures" in violations[0].message
