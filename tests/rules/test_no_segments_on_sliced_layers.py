"""Tests for the no-segments-on-sliced-layers rule."""

from pathlib import Path

import pytest

from pytest_fsd.config import FsdConfig


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


@pytest.mark.parametrize("base_path", ["src", "package/source", "."])
@pytest.mark.parametrize("layer_name", ["features", "3_features", "custom"])
def test_no_segments_on_sliced_layers_configured_roots_layers_and_depth(tmp_path, base_path, layer_name):
    config = FsdConfig(base_path=base_path, layers=["0_app", layer_name, "6_shared"])
    source = tmp_path / base_path
    layer = source / layer_name
    layer.mkdir(parents=True)

    for name in ("ui", "model", "api", "lib", "config"):
        (layer / name).mkdir()
    (layer / "auth/ui").mkdir(parents=True)
    (layer / "api.py").touch()
    for exempt in ("0_app", "6_shared"):
        (source / exempt / "ui").mkdir(parents=True)
    assert {Path(v.file_path).name for v in check(config, str(tmp_path))} == {"ui", "model", "api", "lib", "config"}


@pytest.mark.parametrize("entry", ["missing_root", "file_root", "file_layer"])
def test_no_segments_on_sliced_layers_absent_directories(tmp_path, entry):
    config = FsdConfig()
    if entry == "file_root":
        (tmp_path / "src").touch()
    elif entry == "file_layer":
        (tmp_path / "src").mkdir()
        (tmp_path / "src/features").touch()
    assert check(config, str(tmp_path)) == []
