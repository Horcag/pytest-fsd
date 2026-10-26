# tests/rules/test_repetitive_naming.py
"""Tests for the repetitive-naming rule."""
from pytest_fsd.config import FsdConfig, load_config
from pytest_fsd.rules.repetitive_naming import RULE_NAME, check


def test_repetitive_naming_clean(create_project):
    """No errors when files don't repeat slice name."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
              📄 handler.py
              📄 command.py
            📄 __init__.py
        """
    )
    (project_root / "src" / "features" / "auth" / "model" / "handler.py").write_text(
        "# valid file name\n", encoding="utf-8"
    )

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert violations == []


def test_repetitive_naming_violation(create_project):
    """Error when a file repeats the slice name (e.g., auth_model.py in auth/)."""
    project_root = create_project(
        """
        📂 features
          📂 auth
            📂 model
              📄 __init__.py
              📄 auth_handler.py
            📄 __init__.py
        """
    )
    (project_root / "src" / "features" / "auth" / "model" / "auth_handler.py").write_text(
        "# file with duplicated slice name\n", encoding="utf-8"
    )

    config = load_config(str(project_root))
    violations = check(config, str(project_root))
    assert len(violations) == 1
    assert violations[0].rule == RULE_NAME
    assert "auth_handler.py" in violations[0].message


def test_repetitive_naming_prunes_hidden_and_cache_directories(create_project):
    project_root = create_project(
        '📂 features\n  📂 auth\n    📂 .cache\n      📄 auth_cached.py\n'
        '    📂 __pycache__\n      📄 auth_cached.py\n'
        '  📂 .auth\n    📄 .auth_model.py\n'
    )
    assert check(load_config(str(project_root)), str(project_root)) == []


def test_repetitive_naming_exact_prefix_and_layer_scope(tmp_path):
    for layer in ('0_app', '4_custom', '6_shared'):
        path = tmp_path / 'src' / layer / 'auth' / 'model'
        path.mkdir(parents=True)
        for name in ('auth.py', 'auth_handler.py', 'author.py', 'oauth.py', 'auth.txt', '__init__.py'):
            (path / name).touch()
    config = FsdConfig(layers=['0_app', '4_custom', '6_shared'])
    violations = check(config, str(tmp_path))
    assert {v.file_path for v in violations} == {
        str(tmp_path / 'src/4_custom/auth/model/auth.py'),
        str(tmp_path / 'src/4_custom/auth/model/auth_handler.py'),
    }


def test_private_slices_and_modules_are_still_checked(create_project):
    project_root = create_project(
        '📂 features\n  📂 _auth\n    📄 _auth_model.py\n'
        '  📂 auth\n    📂 _private\n      📄 auth_model.py\n'
    )
    violations = check(load_config(str(project_root)), str(project_root))
    assert {v.file_path for v in violations} == {
        str(project_root / 'src/features/_auth/_auth_model.py'),
        str(project_root / 'src/features/auth/_private/auth_model.py'),
    }
