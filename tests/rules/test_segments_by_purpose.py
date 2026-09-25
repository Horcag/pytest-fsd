# tests/rules/test_segments_by_purpose.py
"""Tests for the segments-by-purpose rule."""
from pathlib import Path

from pytest_fsd.config import load_config
from pytest_fsd.rules.segments_by_purpose import RULE_NAME, check


def test_segments_by_purpose_clean(create_project):
    """No errors when segments use purpose-based names."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
            📂 ui
            📂 lib
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_segments_by_purpose_banned_folder(create_project):
    """Error when a segment uses a banned name ('utils')."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 utils
            📂 model
              📄 __init__.py
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "utils" in violations[0].message


def test_segments_by_purpose_banned_in_shared(create_project):
    """Error when shared contains a banned segment name ('helpers')."""
    project_root = create_project(
        """
        📂 shared
          📂 helpers
          📂 lib
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert "helpers" in violations[0].message


def test_segments_by_purpose_rejects_new_upstream_names(create_project):
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 validators
            📄 fixtures.py
        """
    )
    violations = check(load_config(str(project_root)), str(project_root))
    assert {Path(v.file_path).name for v in violations} == {"validators", "fixtures.py"}
