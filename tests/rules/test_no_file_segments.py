"""Tests for the no-file-segments rule (extra)."""

from pathlib import Path

import pytest

from pytest_fsd.config import FsdConfig


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


def test_no_file_segments_ignores_directories_with_python_suffix(create_project):
    project_root = create_project(
        "📂 features\n  📂 auth\n    📂 model.py\n"
        "📂 shared\n  📂 api.py\n"
        "📂 app\n  📂 config.py"
    )
    assert check(load_config(str(project_root)), str(project_root)) == []


@pytest.mark.parametrize("base_path", ["src", "package/source", "."])
@pytest.mark.parametrize("layer_name", ["features", "3_features", "custom"])
def test_no_file_segments_configured_roots_layers_and_depth(tmp_path, base_path, layer_name):
    config = FsdConfig(base_path=base_path, layers=["0_app", layer_name, "6_shared"])
    source = tmp_path / base_path
    layer = source / layer_name
    layer.mkdir(parents=True)

    (layer / "auth/model").mkdir(parents=True)
    (layer / "auth/model/handler.py").touch()
    (layer / "auth/__init__.py").touch()
    (layer / "auth/ui.py").touch()
    for exempt in ("0_app", "6_shared"):
        (source / exempt / "model").mkdir(parents=True)
        (source / exempt / "model/handler.py").touch()
        (source / exempt / "__init__.py").touch()
        (source / exempt / "config.py").touch()
    assert {Path(v.file_path).relative_to(source).as_posix() for v in check(config, str(tmp_path))} == {
        layer_name + "/auth/ui.py", "0_app/config.py", "6_shared/config.py"
    }


@pytest.mark.parametrize("name", ["_private", "__private", ".metadata", "__pycache__"])
def test_no_file_segments_private_packages_and_metadata(tmp_path, name):
    config = FsdConfig()
    slice_path = tmp_path / "src/features" / name
    slice_path.mkdir(parents=True)
    (slice_path / "model.py").touch()
    violations = check(config, str(tmp_path))
    if name in ("_private", "__private"):
        assert [Path(v.file_path) for v in violations] == [slice_path / "model.py"]
    else:
        assert violations == []


@pytest.mark.parametrize("entry", ["missing_root", "file_root", "file_layer"])
def test_no_file_segments_absent_directories(tmp_path, entry):
    config = FsdConfig()
    if entry == "file_root":
        (tmp_path / "src").touch()
    elif entry == "file_layer":
        (tmp_path / "src").mkdir()
        (tmp_path / "src/features").touch()
    assert check(config, str(tmp_path)) == []
