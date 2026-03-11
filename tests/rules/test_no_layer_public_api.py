# tests/rules/test_no_layer_public_api.py
"""Tests for the no-layer-public-api rule."""
from pytest_fsd.config import load_config
from pytest_fsd.rules.no_layer_public_api import RULE_NAME, check


def test_no_layer_public_api_clean(create_project):
    """No errors when sliced layers don't have __init__.py."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
            📄 __init__.py
        📂 entities
          📂 users
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_no_layer_public_api_violation(create_project):
    """Error when a sliced layer has __init__.py."""
    project_root = create_project(
        """
        📂 features
          📄 __init__.py
          📂 auth
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "features" in violations[0].message
