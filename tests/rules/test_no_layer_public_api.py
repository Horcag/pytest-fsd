"""Tests for the no-layer-public-api rule."""

from pathlib import Path

import pytest

from pytest_fsd.config import FsdConfig


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


def test_no_layer_public_api_ignores_directory_named_init(create_project):
    project_root = create_project("📂 features\n  📂 __init__.py")
    assert check(load_config(str(project_root)), str(project_root)) == []


@pytest.mark.parametrize("base_path", ["src", "package/source", "."])
@pytest.mark.parametrize("layer_name", ["features", "3_features", "custom"])
def test_no_layer_public_api_configured_roots_layers_and_depth(tmp_path, base_path, layer_name):
    config = FsdConfig(base_path=base_path, layers=["0_app", layer_name, "6_shared"])
    source = tmp_path / base_path
    layer = source / layer_name
    layer.mkdir(parents=True)

    (layer / "__init__.py").touch()
    (layer / "auth").mkdir()
    (layer / "auth/__init__.py").touch()
    for exempt in ("0_app", "6_shared"):
        (source / exempt).mkdir()
        (source / exempt / "__init__.py").touch()
    assert [Path(v.file_path) for v in check(config, str(tmp_path))] == [layer / "__init__.py"]


@pytest.mark.parametrize("entry", ["missing_root", "file_root", "file_layer"])
def test_no_layer_public_api_absent_directories(tmp_path, entry):
    config = FsdConfig()
    if entry == "file_root":
        (tmp_path / "src").touch()
    elif entry == "file_layer":
        (tmp_path / "src").mkdir()
        (tmp_path / "src/features").touch()
    assert check(config, str(tmp_path)) == []
