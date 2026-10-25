# tests/rules/test_ambiguous_slice_names.py
"""Tests for the ambiguous-slice-names rule."""
from pytest_fsd.config import load_config
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
