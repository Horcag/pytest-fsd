# tests/rules/test_no_public_api_sidestep.py
"""Tests for the no-public-api-sidestep rule."""
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
