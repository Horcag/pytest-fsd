# tests/rules/test_no_reserved_folder_names.py
"""Tests for the no-reserved-folder-names rule (extra)."""
import pytest
from pytest_fsd._lib.fs_utils import STANDARD_SEGMENTS

from pytest_fsd.config import FsdConfig, load_config
from pytest_fsd.rules.no_reserved_folder_names import RULE_NAME, check


def test_no_reserved_folder_names_clean(create_project):
    """No errors when segment subfolders don't use reserved names."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
              📂 validators
            📄 __init__.py
        """,
        extra_rules=["no-reserved-folder-names"],
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_no_reserved_folder_names_violation(create_project):
    """Error when a subfolder inside a segment uses a reserved segment name."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
              📂 api
            📄 __init__.py
        """,
        extra_rules=["no-reserved-folder-names"],
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "api" in violations[0].message


def test_reserved_names_are_checked_inside_custom_segments(create_project):
    project_root = create_project(
        "📂 shared\n  📂 i18n\n    📂 translations\n      📂 model\n"
        "📂 features\n  📂 auth\n    📂 routing\n      📂 api"
    )

    violations = check(load_config(str(project_root)), str(project_root))

    assert {v.file_path for v in violations} == {
        str(project_root / "src/shared/i18n/translations/model"),
        str(project_root / "src/features/auth/routing/api"),
    }
    assert all(v.rule == RULE_NAME for v in violations)


def test_reserved_names_ignore_hidden_and_cache_trees(create_project):
    project_root = create_project(
        '📂 features\n  📂 auth\n    📂 model\n      📂 .cache\n        📂 api\n'
        '      📂 __pycache__\n        📂 lib\n    📂 .cache\n      📂 ui\n'
        '  📂 .cache\n    📂 model\n      📂 api\n'
        '📂 shared\n  📂 .cache\n    📂 ui\n'
    )
    assert check(load_config(str(project_root)), str(project_root)) == []


def test_reserved_names_custom_layers_and_file_traps(tmp_path):
    expected = []
    for name in ('4_custom/auth/routing/api', '6_shared/i18n/deep/model', '0_app/model/api'):
        path = tmp_path / 'src' / name
        path.mkdir(parents=True)
        if not name.startswith('0_app'):
            expected.append(str(path))
    (tmp_path / 'src/4_custom/auth/routing/ui.py').touch()
    assert {v.file_path for v in check(FsdConfig(layers=['0_app', '4_custom', '6_shared']), str(tmp_path))} == set(expected)


def test_private_packages_are_checked_for_reserved_subfolders(create_project):
    project_root = create_project('📂 features\n  📂 _auth\n    📂 _routing\n      📂 _private\n        📂 api')
    assert [v.file_path for v in check(load_config(str(project_root)), str(project_root))] == [
        str(project_root / 'src/features/_auth/_routing/_private/api')
    ]


@pytest.mark.parametrize('name', STANDARD_SEGMENTS)
def test_every_reserved_name_is_directory_only(tmp_path, name):
    parent = tmp_path / 'src/shared/lib'
    parent.mkdir(parents=True)
    path = parent / name
    path.touch()
    assert check(FsdConfig(), str(tmp_path)) == []
    path.unlink()
    path.mkdir()
    assert [v.file_path for v in check(FsdConfig(), str(tmp_path))] == [str(path)]
