# tests/rules/test_repetitive_naming.py
"""Tests for the repetitive-naming rule."""
from pytest_fsd.config import load_config
from pytest_fsd.rules.repetitive_naming import RULE_NAME, check


def test_repetitive_naming_clean(create_project):
    """No errors when files don't repeat slice name."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
              📄 handler.py
              📄 command.py
            📄 __init__.py
        """
    )
    (project_root / "src" / "features" / "auth" / "model" / "handler.py").write_text(
        "# valid file name\n", encoding="utf-8"
    )

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_repetitive_naming_violation(create_project):
    """Error when a file repeats the slice name (e.g., auth_model.py in auth/)."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
              📄 auth_handler.py
            📄 __init__.py
        """
    )
    (project_root / "src" / "features" / "auth" / "model" / "auth_handler.py").write_text(
        "# file with duplicated slice name\n", encoding="utf-8"
    )

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "auth_handler.py" in violations[0].message
