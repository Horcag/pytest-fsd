# tests/rules/test_no_segmentless_slices.py
"""Tests for the no-segmentless-slices rule."""
from pytest_fsd.config import load_config
from pytest_fsd.rules.no_segmentless_slices import RULE_NAME, check


def test_no_segmentless_slices_clean(create_project):
    """No errors when all slices have at least one standard segment."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
            📄 __init__.py
        📂 entities
          📂 users
            📂 ui
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_no_segmentless_slices_violation(create_project):
    """Error when a slice has no standard segments."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📄 __init__.py
            📄 something.py
        """
    )
    (project_root / "src" / "features" / "auth" / "something.py").write_text("# no segments\n")

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "auth" in violations[0].message
