# tests/rules/test_excessive_slicing.py
"""Tests for the excessive-slicing rule (extra)."""
import pytest

from pytest_fsd.config import FsdConfig, load_config
from pytest_fsd.rules.excessive_slicing import RULE_NAME, check


def test_excessive_slicing_clean(create_project):
    """No errors when layer has few slices."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
            📄 __init__.py
          📂 payment
            📂 model
              📄 __init__.py
            📄 __init__.py
        """,
        extra_rules=["excessive-slicing"],
    )
    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_excessive_slicing_violation(create_project, tmp_path):
    """Error when a layer has more than 20 slices."""
    # Создаём 21 слайс в features
    tree_lines = []
    for i in range(21):
        tree_lines.append(f"  📂 slice_{i:02d}")
        tree_lines.append("    📂 model")
        tree_lines.append("      📄 __init__.py")
        tree_lines.append("    📄 __init__.py")

    tree = "📂 features\n" + "\n".join(tree_lines)
    project_root = create_project(tree, extra_rules=["excessive-slicing"])

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "21 slices" in violations[0].message


@pytest.mark.parametrize('count', [19, 20, 21])
def test_excessive_slicing_boundaries_and_non_slices(tmp_path, count):
    for layer in ('0_app', '4_custom', '6_shared'):
        path = tmp_path / 'src' / layer
        path.mkdir(parents=True)
        for i in range(count):
            (path / ('_slice_%s' % i)).mkdir()
        for name in ('.cache', '.git', '__pycache__'):
            (path / name).mkdir()
        (path / 'file.py').touch()
    violations = check(FsdConfig(layers=['0_app', '4_custom', '6_shared']), str(tmp_path))
    assert [v.file_path for v in violations] == ([str(tmp_path / 'src/4_custom')] if count == 21 else [])
    if violations:
        assert '21 slices' in violations[0].message
