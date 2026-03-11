# tests/rules/test_shared_lib_grouping.py
"""Tests for the shared-lib-grouping rule (extra)."""
from pytest_fsd.config import load_config
from pytest_fsd.rules.shared_lib_grouping import RULE_NAME, check


def test_shared_lib_grouping_clean(create_project):
    """No errors when shared/lib has few files."""
    project_root = create_project(
        """
        📂 shared
          📂 lib
            📄 __init__.py
            📄 dates.py
            📄 strings.py
        """,
        extra_rules=["shared-lib-grouping"],
    )
    (project_root / "src" / "shared" / "lib" / "dates.py").write_text("# dates\n")
    (project_root / "src" / "shared" / "lib" / "strings.py").write_text("# strings\n")

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_shared_lib_grouping_violation(create_project):
    """Error when shared/lib has more than 15 ungrouped files."""
    project_root = create_project(
        """
        📂 shared
          📂 lib
            📄 __init__.py
        """,
        extra_rules=["shared-lib-grouping"],
    )

    lib_path = project_root / "src" / "shared" / "lib"
    for i in range(16):
        (lib_path / f"module_{i:02d}.py").write_text(f"# module {i}\n")

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "16 ungrouped files" in violations[0].message
