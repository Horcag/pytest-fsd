from pathlib import Path

import pytest

from pytest_fsd.config import FsdConfig

from pytest_fsd.config import load_config
from pytest_fsd.rules.public_api import RULE_NAME, check


def test_public_api_no_errors_on_valid_project(create_project):
    """Test that no errors are reported when all slices have public APIs."""
    project_root = create_project(
        """
        📂 shared
          📂 ui
            📄 __init__.py
        📂 entities
          📂 users
            📂 ui
            📄 __init__.py
          📂 posts
            📂 ui
            📄 __init__.py
        📂 features
          📂 comments
            📂 ui
            📄 __init__.py
        📂 windows
          📂 editor
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_public_api_errors_on_missing_api(create_project):
    """Test that errors are reported when slices or shared segments lack a public API."""
    project_root = create_project(
        """
        📂 shared
          📂 config
        📂 entities
          📂 users
            📂 ui
            📄 __init__.py
          📂 posts
            📂 ui
        📂 features
          📂 comments
            📂 ui
        📂 windows
          📂 editor
            📂 ui
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))

    # Expecting 4 violations: shared/config, entities/posts, features/comments, windows/editor
    assert len(violations) == 4

    messages = sorted([v.message for v in violations])
    assert any("Segment 'config' in 'shared' is missing __init__.py" in msg for msg in messages)
    assert any("Slice 'posts' in layer 'entities' is missing __init__.py" in msg for msg in messages)
    assert any("Slice 'comments' in layer 'features' is missing __init__.py" in msg for msg in messages)
    assert any("Slice 'editor' in layer 'windows' is missing __init__.py" in msg for msg in messages)
    assert all(v.rule == RULE_NAME for v in violations)


def test_public_api_shared_ui_lib_exceptions(create_project):
    """Test that shared/ui and shared/lib don't need __init__.py at root, but their subfolders do."""
    project_root = create_project(
        """
        📂 shared
          📂 ui
            📄 styles.py
            📄 button.py
            📂 complex_widget
          📂 lib
            📄 utils.py
            📂 async_helpers
              📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))

    # Expecting 1 violation: shared/ui/complex_widget is missing __init__.py
    assert len(violations) == 1
    assert "Subfolder 'complex_widget' in 'shared/ui' is missing __init__.py" in violations[0].message


def test_public_api_requires_a_file_not_a_directory(create_project):
    project_root = create_project(
        "📂 features\n  📂 auth\n    📂 __init__.py\n"
        "📂 shared\n  📂 api\n    📂 __init__.py\n"
        "  📂 ui\n    📂 button\n      📂 __init__.py\n"
        "  📂 lib\n    📂 dates\n      📂 __init__.py"
    )

    violations = check(load_config(str(project_root)), str(project_root))

    assert {v.file_path for v in violations} == {
        str(project_root / "src" / path)
        for path in ["features/auth", "shared/api", "shared/ui/button", "shared/lib/dates"]
    }
    assert all(v.rule == RULE_NAME for v in violations)


@pytest.mark.parametrize("base_path", ["src", "package/source", "."])
@pytest.mark.parametrize("layer_name", ["features", "3_features", "custom"])
def test_public_api_configured_roots_layers_and_depth(tmp_path, base_path, layer_name):
    config = FsdConfig(base_path=base_path, layers=["0_app", layer_name, "6_shared"])
    source = tmp_path / base_path
    layer = source / layer_name
    layer.mkdir(parents=True)

    (layer / "missing").mkdir()
    (layer / "valid/deep").mkdir(parents=True)
    (layer / "valid/__init__.py").touch()
    (source / "0_app/no_api").mkdir(parents=True)
    (source / "6_shared/config").mkdir(parents=True)
    (source / "6_shared/ui/button").mkdir(parents=True)
    (source / "6_shared/lib/dates/deep").mkdir(parents=True)
    (source / "6_shared/lib/dates/__init__.py").touch()
    assert {Path(v.file_path).relative_to(source).as_posix() for v in check(config, str(tmp_path))} == {
        layer_name + "/missing", "6_shared/config", "6_shared/ui/button"
    }


@pytest.mark.parametrize("name", ["_private", "__private", ".metadata", "__pycache__"])
def test_public_api_private_packages_and_metadata(tmp_path, name):
    config = FsdConfig()
    slice_path = tmp_path / "src/features" / name
    slice_path.mkdir(parents=True)
    violations = check(config, str(tmp_path))
    if name in ("_private", "__private"):
        assert [Path(v.file_path) for v in violations] == [slice_path]
    else:
        assert violations == []


@pytest.mark.parametrize("segment", ["api", "ui", "lib"])
@pytest.mark.parametrize("name", ["_private", "__private", ".metadata", "__pycache__"])
def test_public_api_shared_private_packages_and_metadata(tmp_path, segment, name):
    config = FsdConfig()
    package = tmp_path / "src/shared" / segment / name
    package.mkdir(parents=True)
    if segment == "api":
        (package.parent / "__init__.py").touch()
    violations = check(config, str(tmp_path))
    if segment in ("ui", "lib") and name in ("_private", "__private"):
        assert [Path(v.file_path) for v in violations] == [package]
    else:
        assert violations == []


@pytest.mark.parametrize("name", ["_private", "__private", ".metadata", "__pycache__"])
def test_public_api_shared_segment_names(tmp_path, name):
    config = FsdConfig()
    segment = tmp_path / "src/shared" / name
    segment.mkdir(parents=True)
    violations = check(config, str(tmp_path))
    if name in ("_private", "__private"):
        assert [Path(v.file_path) for v in violations] == [segment]
    else:
        assert violations == []


@pytest.mark.parametrize("entry", ["missing_root", "file_root", "file_layer"])
def test_public_api_absent_directories(tmp_path, entry):
    config = FsdConfig()
    if entry == "file_root":
        (tmp_path / "src").touch()
    elif entry == "file_layer":
        (tmp_path / "src").mkdir()
        (tmp_path / "src/features").touch()
    assert check(config, str(tmp_path)) == []
