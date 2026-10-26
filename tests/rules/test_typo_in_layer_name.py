# tests/rules/test_typo_in_layer_name.py
"""Tests for the typo-in-layer-name rule."""
from pytest_fsd.config import FsdConfig, load_config
from pytest_fsd.rules.typo_in_layer_name import RULE_NAME, check


def test_typo_in_layer_name_clean(create_project):
    """No errors when all root folders are known layers."""
    project_root = create_project(
        """
        📂 app
        📂 features
          📂 auth
            📄 __init__.py
        📂 shared
          📂 ui
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_typo_in_layer_name_typo(create_project):
    """Error when a root folder is not a known layer (typo detection)."""
    project_root = create_project(
        """
        📂 app
        📂 fietures
          📂 auth
            📄 __init__.py
        📂 shared
          📂 ui
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "fietures" in violations[0].message


def test_typo_names_configured_ignored_hidden_and_files(tmp_path):
    root = tmp_path / 'source'
    root.mkdir()
    for name in ('0_app', 'custom', '6_shared', 'scripts', '.hidden', '__pycache__', 'fietures'):
        (root / name).mkdir()
    (root / 'unknown.py').touch()
    config = FsdConfig(base_path='source', layers=['0_app', 'custom', '6_shared'], ignore_paths=['scripts'])
    assert [v.file_path for v in check(config, str(tmp_path))] == [str(root / 'fietures')]


def test_ignoring_top_level_name_does_not_ignore_other_names(tmp_path):
    (tmp_path / 'src/migrations').mkdir(parents=True)
    violations = check(FsdConfig(ignore_paths=['scripts']), str(tmp_path))
    assert [v.file_path for v in violations] == [str(tmp_path / 'src/migrations')]


def test_private_top_level_directory_needs_configuration(tmp_path):
    path = tmp_path / 'src/_custom'
    path.mkdir(parents=True)
    assert [v.file_path for v in check(FsdConfig(), str(tmp_path))] == [str(path)]
    assert check(FsdConfig(ignore_paths=['_custom']), str(tmp_path)) == []
