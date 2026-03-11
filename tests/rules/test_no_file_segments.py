# tests/rules/test_no_file_segments.py
"""Tests for the no-file-segments rule (extra)."""
from pytest_fsd.config import load_config
from pytest_fsd.rules.no_file_segments import RULE_NAME, check


def test_no_file_segments_clean(create_project):
    """No errors when all segments are folders."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
            📂 ui
            📄 __init__.py
        """,
        extra_rules=["no-file-segments"],
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_no_file_segments_violation(create_project):
    """Error when a segment is a file (model.py) instead of a folder (model/)."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📄 __init__.py
            📄 model.py
        """,
        extra_rules=["no-file-segments"],
    )
    (project_root / "src" / "features" / "auth" / "model.py").write_text("# file segment\n")

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "model" in violations[0].message
