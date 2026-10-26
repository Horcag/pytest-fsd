# tests/rules/test_shared_lib_grouping.py
"""Tests for the shared-lib-grouping rule (extra)."""
import pytest

from pytest_fsd.config import FsdConfig, load_config
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


@pytest.mark.parametrize('count', [14, 15, 16])
def test_shared_lib_grouping_boundaries_and_file_types(tmp_path, count):
    path = tmp_path / 'src/6_shared/lib'
    path.mkdir(parents=True)
    for i in range(count):
        (path / ('module_%s.py' % i)).touch()
    (path / '__init__.py').touch()
    (path / 'module.py').mkdir()
    (path / 'notes.txt').touch()
    nested = path / 'nested'
    nested.mkdir()
    for i in range(20):
        (nested / ('nested_%s.py' % i)).touch()
    violations = check(FsdConfig(layers=['6_shared']), str(tmp_path))
    assert [v.file_path for v in violations] == ([str(path)] if count == 16 else [])


def test_shared_lib_private_modules_count_but_other_layers_do_not(tmp_path):
    for layer in ('0_app', '4_custom', '6_shared'):
        lib = tmp_path / 'src' / layer / 'lib'
        lib.mkdir(parents=True)
        for i in range(16):
            (lib / ('_module_%s.py' % i)).touch()
    violations = check(FsdConfig(layers=['0_app', '4_custom', '6_shared']), str(tmp_path))
    assert [v.file_path for v in violations] == [str(tmp_path / 'src/6_shared/lib')]
    assert check(FsdConfig(layers=['0_app', '4_custom']), str(tmp_path)) == []
