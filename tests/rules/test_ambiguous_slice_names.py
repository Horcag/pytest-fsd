# tests/rules/test_ambiguous_slice_names.py
"""Tests for the ambiguous-slice-names rule."""
import pytest
from pytest_fsd.rules import (
    ambiguous_slice_names, repetitive_naming, segments_by_purpose,
    typo_in_layer_name, no_reserved_folder_names, excessive_slicing,
    shared_lib_grouping,
)

from pytest_fsd.config import FsdConfig, load_config
from pytest_fsd.rules.ambiguous_slice_names import RULE_NAME, check


def test_ambiguous_slice_names_clean(create_project):
    """No errors when slice names don't collide with shared components."""
    project_root = create_project(
        """
        📂 shared
          📂 ui
            📄 __init__.py
            📂 button
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


def test_ambiguous_slice_names_violation(create_project):
    """Error when a feature slice has the same name as a shared component."""
    project_root = create_project(
        """
        📂 shared
          📂 ui
            📄 __init__.py
            📂 button
        📂 features
          📂 button
            📂 model
              📄 __init__.py
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "button" in violations[0].message


def test_ambiguous_slice_names_matches_shared_segments(create_project):
    project_root = create_project(
        "📂 shared\n  📂 i18n\n    📄 __init__.py\n"
        "📂 features\n  📂 i18n\n    📂 model\n    📄 __init__.py"
    )

    violations = check(load_config(str(project_root)), str(project_root))

    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert violations[0].file_path == str(project_root / "src/features/i18n")
    assert "shared/i18n" in violations[0].message


def test_hidden_shared_components_and_slices_are_ignored(create_project):
    project_root = create_project(
        '📂 shared\n  📂 .cache\n    📂 auth\n  📂 ui\n    📂 .button\n'
        '📂 features\n  📂 auth\n  📂 .button\n'
    )
    assert check(load_config(str(project_root)), str(project_root)) == []


def test_ambiguous_names_custom_layers_and_directory_only(tmp_path):
    for name in ('6_shared/i18n', '4_custom/i18n', '0_app/i18n'):
        (tmp_path / 'src' / name).mkdir(parents=True)
    (tmp_path / 'src/6_shared/file.py').touch()
    (tmp_path / 'src/4_custom/file.py').mkdir()
    config = FsdConfig(layers=['0_app', '4_custom', '6_shared'])
    violations = check(config, str(tmp_path))
    assert [v.file_path for v in violations] == [str(tmp_path / 'src/4_custom/i18n')]


def test_private_shared_names_are_checked(create_project):
    project_root = create_project('📂 shared\n  📂 lib\n    📂 _auth\n📂 features\n  📂 _auth')
    violations = check(load_config(str(project_root)), str(project_root))
    assert [v.file_path for v in violations] == [str(project_root / 'src/features/_auth')]


def test_ambiguous_names_without_shared_layer_are_valid(tmp_path):
    (tmp_path / 'src/custom/auth').mkdir(parents=True)
    assert check(FsdConfig(layers=['custom']), str(tmp_path)) == []


@pytest.mark.parametrize('rule', [
    ambiguous_slice_names, repetitive_naming, segments_by_purpose,
    typo_in_layer_name, no_reserved_folder_names, excessive_slicing,
    shared_lib_grouping,
])
def test_naming_rules_missing_or_non_directory_root_is_safe(tmp_path, rule):
    config = FsdConfig()
    assert rule.check(config, str(tmp_path)) == []
    (tmp_path / 'src').touch()
    assert rule.check(config, str(tmp_path)) == []
