# tests/rules/test_no_public_api_sidestep.py
"""Tests for the no-public-api-sidestep rule."""
import pytest

from pytest_fsd.config import load_config
from pytest_fsd.rules.no_public_api_sidestep import RULE_NAME, check


def test_no_public_api_sidestep_clean(create_project):
    """No errors when importing through public API (__init__.py)."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📄 __init__.py
            📄 model.py
          📂 profile
            📄 __init__.py
            📄 ui.py
        """
    )
    (project_root / "src" / "features" / "auth" / "__init__.py").write_text(
        "from .model import do_auth\n__all__ = ['do_auth']\n", encoding="utf-8"
    )
    (project_root / "src" / "features" / "profile" / "ui.py").write_text(
        "from src.features.auth import do_auth\n", encoding="utf-8"
    )

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_no_public_api_sidestep_error(create_project):
    """Error when importing directly from internal module."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📄 __init__.py
            📄 model.py
          📂 profile
            📄 __init__.py
            📄 ui.py
        """
    )
    (project_root / "src" / "features" / "auth" / "__init__.py").write_text(
        "from .model import do_auth\n__all__ = ['do_auth']\n", encoding="utf-8"
    )
    (project_root / "src" / "features" / "profile" / "ui.py").write_text(
        "from src.features.auth.model import do_auth\n", encoding="utf-8"
    )

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "Importing internal module" in violations[0].message
    assert "auth.model" in violations[0].message
    assert (violations[0].line_number, violations[0].column_number) == (1, 1)
    assert (violations[0].end_line_number, violations[0].end_column_number) == (1, 44)


def test_no_public_api_sidestep_missing_all(create_project):
    """Error when slice does not define __all__ in its __init__.py."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📄 __init__.py
            📄 model.py
          📂 profile
            📄 __init__.py
            📄 ui.py
        """
    )
    (project_root / "src" / "features" / "auth" / "__init__.py").write_text(
        "from .model import do_auth\n", encoding="utf-8"  # No __all__
    )
    (project_root / "src" / "features" / "profile" / "ui.py").write_text(
        "from src.features.auth import do_auth\n", encoding="utf-8"
    )

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "does not define `__all__`" in violations[0].message


def test_no_public_api_sidestep_not_in_all(create_project):
    """Error when importing a name not in __all__."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📄 __init__.py
            📄 model.py
          📂 profile
            📄 __init__.py
            📄 ui.py
        """
    )
    (project_root / "src" / "features" / "auth" / "__init__.py").write_text(
        "from .model import do_auth\n__all__ = []\n", encoding="utf-8"
    )
    (project_root / "src" / "features" / "profile" / "ui.py").write_text(
        "from src.features.auth import do_auth\n", encoding="utf-8"
    )

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "is not explicitly exported" in violations[0].message


def test_no_public_api_sidestep_multiline_location(create_project):
    project_root = create_project(
        "📂 features\n  📂 auth\n    📄 __init__.py\n    📄 model.py\n"
        "  📂 profile\n    📄 __init__.py\n    📄 ui.py"
    )
    (project_root / "src/features/profile/ui.py").write_text(
        "from src.features.auth.model import (\n    do_auth,\n)\n", encoding="utf-8"
    )

    violations = check(load_config(str(project_root)), str(project_root))

    assert len(violations) == 1
    assert (violations[0].line_number, violations[0].column_number) == (1, 1)
    assert (violations[0].end_line_number, violations[0].end_column_number) == (3, 2)


@pytest.mark.parametrize("statement", [
    "import src.features.auth",
    "import src.features.auth as auth",
    "from src.features import auth",
    "from .. import auth",
    "from features import auth",
])
def test_slice_module_import_does_not_check_module_name_in_all(create_project, statement):
    project_root = create_project(
        "📂 features\n  📂 auth\n    📄 __init__.py\n    📄 model.py\n"
        "  📂 profile\n    📄 __init__.py\n    📄 ui.py"
    )
    (project_root / "src/features/auth/__init__.py").write_text("__all__ = ['do_auth']\n", encoding="utf-8")
    (project_root / "src/features/profile/ui.py").write_text(statement + "\n", encoding="utf-8")

    assert check(load_config(str(project_root)), str(project_root)) == []


@pytest.mark.parametrize("statement", [
    "import src.features.auth.model as model",
    "from ..auth.model import do_auth",
    "from features.auth.model import do_auth",
])
def test_internal_import_spellings_are_rejected(create_project, statement):
    project_root = create_project(
        "📂 features\n  📂 auth\n    📄 __init__.py\n    📄 model.py\n"
        "  📂 profile\n    📄 __init__.py\n    📄 ui.py"
    )
    (project_root / "src/features/profile/ui.py").write_text(statement + "\n", encoding="utf-8")

    violations = check(load_config(str(project_root)), str(project_root))

    assert len(violations) == 1
    assert "Importing internal module" in violations[0].message


@pytest.mark.parametrize("exports", [
    "__all__: list = ['do_auth']",
    "__all__ = ('do_auth',)",
    "__all__ = []\n__all__ += ['do_auth']",
    "__all__ = [] + ['do_auth']",
    "__all__ = []\n__all__.append('do_auth')",
    "__all__ = []\n__all__.extend(['do_auth'])",
    "__all__ = []\n__all__ = ['do_auth']",
])
def test_static_export_declarations_are_recognized(create_project, exports):
    project_root = create_project(
        "📂 features\n  📂 auth\n    📄 __init__.py\n"
        "  📂 profile\n    📄 ui.py"
    )
    (project_root / "src/features/auth/__init__.py").write_text(exports + "\n", encoding="utf-8")
    (project_root / "src/features/profile/ui.py").write_text("from src.features.auth import do_auth\n", encoding="utf-8")

    assert check(load_config(str(project_root)), str(project_root)) == []


@pytest.mark.parametrize("exports", [
    "__all__ = ['do_auth']\n__all__ = []",
    "__all__ = ['do_auth', 1]",
    "__all__ = ['do_auth']\n__all__ = dynamic_names",
    "__all__ = ['do_auth']\n__all__.clear()",
    "__all__ = ['do_auth']\nif condition:\n    __all__ = []",
    "__all__ = ['do_auth']\n__all__[0] = 'other'",
    "__all__ = ['do_auth']\nif condition:\n    __all__.clear()",
])
def test_invalid_or_replaced_exports_do_not_authorize_names(create_project, exports):
    project_root = create_project(
        "📂 features\n  📂 auth\n    📄 __init__.py\n"
        "  📂 profile\n    📄 ui.py"
    )
    (project_root / "src/features/auth/__init__.py").write_text(exports + "\n", encoding="utf-8")
    (project_root / "src/features/profile/ui.py").write_text("from src.features.auth import do_auth\n", encoding="utf-8")

    assert len(check(load_config(str(project_root)), str(project_root))) == 1


@pytest.mark.parametrize("exports, expected", [("__all__ = ['do_auth']", 0), ("", 1)])
def test_wildcard_import_requires_explicit_exports(create_project, exports, expected):
    project_root = create_project(
        "📂 features\n  📂 auth\n    📄 __init__.py\n"
        "  📂 profile\n    📄 ui.py"
    )
    (project_root / "src/features/auth/__init__.py").write_text(exports + "\n", encoding="utf-8")
    (project_root / "src/features/profile/ui.py").write_text("from src.features.auth import *\n", encoding="utf-8")

    assert len(check(load_config(str(project_root)), str(project_root))) == expected


def test_nested_base_path_and_relative_cross_slice_import(tmp_path):
    from pytest_fsd.config import FsdConfig

    base = tmp_path / "package/src"
    (base / "features/auth").mkdir(parents=True)
    (base / "features/profile").mkdir(parents=True)
    (base / "features/auth/__init__.py").write_text("__all__ = ['do_auth']\n", encoding="utf-8")
    (base / "features/auth/model.py").touch()
    (base / "features/profile/ui.py").write_text(
        "from package.src.features.auth.model import do_auth\n"
        "from ....src.features.auth.model import do_auth\n", encoding="utf-8"
    )

    violations = check(FsdConfig(base_path="package/src"), str(tmp_path))

    assert len(violations) == 2
    assert [violation.line_number for violation in violations] == [1, 2]


def test_exported_module_is_a_valid_public_api_name(create_project):
    project_root = create_project(
        "📂 features\n  📂 auth\n    📄 __init__.py\n    📄 model.py\n"
        "  📂 profile\n    📄 ui.py"
    )
    (project_root / "src/features/auth/__init__.py").write_text("__all__ = ['model']\n", encoding="utf-8")
    (project_root / "src/features/profile/ui.py").write_text("from src.features.auth import model\n", encoding="utf-8")

    assert check(load_config(str(project_root)), str(project_root)) == []
