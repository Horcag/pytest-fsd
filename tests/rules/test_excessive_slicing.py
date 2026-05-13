# tests/rules/test_excessive_slicing.py
"""Tests for the excessive-slicing rule (extra)."""
from pytest_fsd.config import load_config
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
