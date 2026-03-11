# tests/rules/test_no_segments_on_sliced_layers.py
"""Tests for the no-segments-on-sliced-layers rule."""
from pytest_fsd.config import load_config
from pytest_fsd.rules.no_segments_on_sliced_layers import RULE_NAME, check


def test_no_segments_on_sliced_layers_clean(create_project):
    """No errors when sliced layers contain only slices, not segments."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_no_segments_on_sliced_layers_violation(create_project):
    """Error when a sliced layer contains a segment folder directly."""
    project_root = create_project(
        """
        📂 features
          📂 ui
          📂 auth
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "ui" in violations[0].message
