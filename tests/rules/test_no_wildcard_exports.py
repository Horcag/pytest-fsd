"""Python equivalents of Steiger's public API wildcard export cases."""

import pytest

from pytest_fsd import validate_fsd_architecture
from pytest_fsd.config import FsdConfig, load_config
from pytest_fsd.rules.no_wildcard_exports import RULE_NAME, check


@pytest.mark.parametrize(
    "api_path",
    [
        "entities/user/__init__.py",
        "entities/user/model/__init__.py",
        "features/auth/__init__.py",
        "widgets/header/__init__.py",
        "pages/home/__init__.py",
        "shared/lib/__init__.py",
        "shared/api/rest/__init__.py",
        "app/__init__.py",
        "6_shared/lib/__init__.py",
    ],
)
def test_wildcard_exports_on_all_layers(tmp_path, api_path):
    api = tmp_path / "src" / api_path
    api.parent.mkdir(parents=True)
    api.write_text("from .model import *\n", encoding="utf-8")
    config = FsdConfig(layers=[api_path.split("/")[0]])

    violations = check(config, str(tmp_path))

    assert len(violations) == 1
    violation = violations[0]
    assert violation.rule == RULE_NAME
    assert violation.file_path == str(api)
    assert "'.model'" in violation.message
    assert (violation.line_number, violation.column_number) == (1, 1)
    assert (violation.end_line_number, violation.end_column_number) == (1, 21)


@pytest.mark.parametrize(
    "source",
    [
        "from .model import User, Session\n",
        "from .model import (\n    User,\n    Session,\n)\n",
        "from . import model as model\n",
        "import example.model as model\n",
        '# from .model import *\ntext = "from .model import *"\n',
    ],
)
def test_explicit_imports_and_text_are_allowed(create_project, source):
    project_root = create_project("📂 entities\n  📂 user\n    📄 __init__.py")
    (project_root / "src/entities/user/__init__.py").write_text(source, encoding="utf-8")

    assert check(load_config(str(project_root)), str(project_root)) == []


def test_each_wildcard_is_reported_even_with_explicit_all(create_project):
    project_root = create_project("📂 shared\n  📂 lib\n    📄 __init__.py")
    (project_root / "src/shared/lib/__init__.py").write_text(
        "from .dates import today\n"
        "from ..formatters import *\n"
        "from external import *\n"
        "__all__ = ['today']\n",
        encoding="utf-8",
    )

    violations = check(load_config(str(project_root)), str(project_root))

    assert [v.line_number for v in violations] == [2, 3]
    assert "'..formatters'" in violations[0].message
    assert "'external'" in violations[1].message


def test_conditional_wildcard_location_counts_characters(create_project):
    project_root = create_project("📂 shared\n  📂 lib\n    📄 __init__.py")
    (project_root / "src/shared/lib/__init__.py").write_text(
        "if TYPE_CHECKING:\n    привет = 1; from .model import *\n", encoding="utf-8"
    )

    violations = check(load_config(str(project_root)), str(project_root))

    assert len(violations) == 1
    violation = violations[0]
    assert (violation.line_number, violation.column_number) == (2, 17)
    assert (violation.end_line_number, violation.end_column_number) == (2, 37)
    assert ":2:17 ->" in violation.format()


@pytest.mark.parametrize("separator", ["\u2028", "\u0085", "\f"])
def test_columns_use_python_physical_lines(create_project, separator):
    project_root = create_project("📂 shared\n  📂 lib\n    📄 __init__.py")
    prefix = "text = 'a" + separator + "b'; "
    statement = "from .model import *"
    (project_root / "src/shared/lib/__init__.py").write_text(
        prefix + statement + "\n", encoding="utf-8"
    )

    violations = check(load_config(str(project_root)), str(project_root))

    assert len(violations) == 1
    violation = violations[0]
    assert (violation.line_number, violation.column_number) == (1, len(prefix) + 1)
    assert (violation.end_line_number, violation.end_column_number) == (
        1, len(prefix + statement) + 1
    )


def test_internal_modules_and_unconfigured_layers_are_skipped(create_project):
    project_root = create_project(
        "📂 entities\n  📂 user\n    📄 model.py\n"
        "📂 other\n  📄 __init__.py\n📄 __init__.py"
    )
    for path in ["entities/user/model.py", "other/__init__.py", "__init__.py"]:
        (project_root / "src" / path).write_text("from .model import *\n", encoding="utf-8")

    assert check(load_config(str(project_root)), str(project_root)) == []


def test_custom_source_root(tmp_path):
    api = tmp_path / "package" / "shared" / "lib" / "__init__.py"
    api.parent.mkdir(parents=True)
    api.write_text("from .model import *\n", encoding="utf-8")

    violations = check(FsdConfig(base_path="package"), str(tmp_path))

    assert [v.file_path for v in violations] == [str(api)]


@pytest.mark.parametrize("source", ["from .model import (", "\xff", "\x00"])
def test_unparseable_public_api_is_reported(create_project, source):
    project_root = create_project("📂 shared\n  📂 lib\n    📄 __init__.py")
    (project_root / "src/shared/lib/__init__.py").write_bytes(source.encode("latin-1"))

    violations = check(load_config(str(project_root)), str(project_root))

    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert violations[0].file_path.endswith("shared/lib/__init__.py")
    assert violations[0].message.startswith("Cannot inspect public API: ")


def test_unreadable_public_api_is_reported(create_project, monkeypatch):
    project_root = create_project("📂 shared\n  📂 lib\n    📄 __init__.py")

    def refuse_read(*args, **kwargs):
        raise PermissionError("read denied")

    monkeypatch.setattr("tokenize.open", refuse_read)
    violations = check(FsdConfig(), str(project_root))

    assert len(violations) == 1
    assert violations[0].message == "Cannot inspect public API: read denied"


def test_missing_source_root(tmp_path):
    assert check(FsdConfig(), str(tmp_path)) == []


def test_wildcard_rule_is_opt_in_through_facade(create_project):
    project_root = create_project("📂 shared\n  📂 lib\n    📄 __init__.py")
    (project_root / "src/shared/lib/__init__.py").write_text(
        "from .unavailable_module import *\n", encoding="utf-8"
    )

    validate_fsd_architecture(str(project_root))

    with (project_root / "pyproject.toml").open("a", encoding="utf-8") as config:
        config.write('\nextra_rules = ["no-wildcard-exports"]\n')

    with pytest.raises(AssertionError, match="\\[no-wildcard-exports\\]") as error:
        validate_fsd_architecture(str(project_root))
    assert "__init__.py:1:1 ->" in str(error.value)
