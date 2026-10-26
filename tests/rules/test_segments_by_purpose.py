# tests/rules/test_segments_by_purpose.py
"""Tests for the segments-by-purpose rule."""
from pathlib import Path

import pytest
from pytest_fsd.rules.segments_by_purpose import BANNED_SEGMENT_NAMES

from pytest_fsd.config import FsdConfig, load_config
from pytest_fsd.rules.segments_by_purpose import RULE_NAME, check


def test_segments_by_purpose_clean(create_project):
    """No errors when segments use purpose-based names."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
            📂 ui
            📂 lib
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_segments_by_purpose_banned_folder(create_project):
    """Error when a segment uses a banned name ('utils')."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 utils
            📂 model
              📄 __init__.py
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "utils" in violations[0].message


def test_segments_by_purpose_banned_in_shared(create_project):
    """Error when shared contains a banned segment name ('helpers')."""
    project_root = create_project(
        """
        📂 shared
          📂 helpers
          📂 lib
            📄 __init__.py
        """
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert "helpers" in violations[0].message


def test_segments_by_purpose_rejects_new_upstream_names(create_project):
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 validators
            📄 fixtures.py
        """
    )
    violations = check(load_config(str(project_root)), str(project_root))
    assert {Path(v.file_path).name for v in violations} == {"validators", "fixtures.py"}


@pytest.mark.parametrize('name', sorted(BANNED_SEGMENT_NAMES))
@pytest.mark.parametrize('as_file', [False, True])
def test_all_banned_segment_names(tmp_path, name, as_file):
    parent = tmp_path / 'src/custom/auth'
    parent.mkdir(parents=True)
    path = parent / (name + '.py' if as_file else name)
    path.touch() if as_file else path.mkdir()
    violations = check(FsdConfig(layers=['custom']), str(tmp_path))
    assert [v.file_path for v in violations] == [str(path)]


def test_segments_by_purpose_depth_and_layer_scope(tmp_path):
    for name in ('0_app/helpers', '4_custom/auth/model/helpers',
                 '4_custom/.cache/helpers', '4_custom/__pycache__/helpers',
                 '6_shared/lib/helpers'):
        (tmp_path / 'src' / name).mkdir(parents=True)
    assert check(FsdConfig(layers=['0_app', '4_custom', '6_shared']), str(tmp_path)) == []


def test_private_slice_segments_are_checked(create_project):
    project_root = create_project('📂 features\n  📂 _auth\n    📂 utils')
    assert [v.file_path for v in check(load_config(str(project_root)), str(project_root))] == [
        str(project_root / 'src/features/_auth/utils')
    ]
