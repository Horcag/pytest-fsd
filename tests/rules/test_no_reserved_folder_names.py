# tests/rules/test_no_reserved_folder_names.py
"""Tests for the no-reserved-folder-names rule (extra)."""
from pytest_fsd.config import load_config
from pytest_fsd.rules.no_reserved_folder_names import RULE_NAME, check


def test_no_reserved_folder_names_clean(create_project):
    """No errors when segment subfolders don't use reserved names."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
              📂 validators
            📄 __init__.py
        """,
        extra_rules=["no-reserved-folder-names"],
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_no_reserved_folder_names_violation(create_project):
    """Error when a subfolder inside a segment uses a reserved segment name."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
              📂 api
            📄 __init__.py
        """,
        extra_rules=["no-reserved-folder-names"],
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "api" in violations[0].message
