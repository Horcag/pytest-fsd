"""Tests for the no-segmentless-slices rule."""

from pathlib import Path

import pytest

from pytest_fsd.config import FsdConfig


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


def test_no_segmentless_slices_checks_entry_types(create_project):
    project_root = create_project(
        "📂 features\n  📂 bare_file\n    📄 model\n"
        "  📂 suffixed_directory\n    📂 model.py\n"
        "  📂 file_segment\n    📄 model.py\n"
        "  📂 directory_segment\n    📂 model"
    )

    violations = check(load_config(str(project_root)), str(project_root))

    assert {v.file_path for v in violations} == {
        str(project_root / "src/features/bare_file"),
        str(project_root / "src/features/suffixed_directory"),
    }


@pytest.mark.parametrize("base_path", ["src", "package/source", "."])
@pytest.mark.parametrize("layer_name", ["features", "3_features", "custom"])
def test_no_segmentless_slices_configured_roots_layers_and_depth(tmp_path, base_path, layer_name):
    config = FsdConfig(base_path=base_path, layers=["0_app", layer_name, "6_shared"])
    source = tmp_path / base_path
    layer = source / layer_name
    layer.mkdir(parents=True)

    for name in ("empty", "nested_only", "valid_directory", "valid_file"):
        (layer / name).mkdir()
    (layer / "nested_only/deep/model").mkdir(parents=True)
    (layer / "valid_directory/model").mkdir()
    (layer / "valid_file/api.py").touch()
    for exempt in ("0_app", "6_shared"):
        (source / exempt / "empty").mkdir(parents=True)
    assert {Path(v.file_path).name for v in check(config, str(tmp_path))} == {"empty", "nested_only"}


@pytest.mark.parametrize("name", ["_private", "__private", ".metadata", "__pycache__"])
def test_no_segmentless_slices_private_packages_and_metadata(tmp_path, name):
    config = FsdConfig()
    slice_path = tmp_path / "src/features" / name
    slice_path.mkdir(parents=True)
    violations = check(config, str(tmp_path))
    if name in ("_private", "__private"):
        assert [Path(v.file_path) for v in violations] == [slice_path]
    else:
        assert violations == []


@pytest.mark.parametrize("segment", ["ui", "model", "api", "lib", "config"])
@pytest.mark.parametrize("kind", ["file", "directory"])
def test_no_segmentless_slices_all_standard_segment_forms(tmp_path, segment, kind):
    config = FsdConfig()
    slice_path = tmp_path / "src/features/auth"
    slice_path.mkdir(parents=True)
    if kind == "file":
        (slice_path / (segment + ".py")).touch()
    else:
        (slice_path / segment).mkdir()
    assert check(config, str(tmp_path)) == []


@pytest.mark.parametrize("entry", ["missing_root", "file_root", "file_layer"])
def test_no_segmentless_slices_absent_directories(tmp_path, entry):
    config = FsdConfig()
    if entry == "file_root":
        (tmp_path / "src").touch()
    elif entry == "file_layer":
        (tmp_path / "src").mkdir()
        (tmp_path / "src/features").touch()
    assert check(config, str(tmp_path)) == []
