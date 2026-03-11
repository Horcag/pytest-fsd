# tests/rules/test_forbidden_imports.py
"""
Tests for the forbidden-imports rule.

Правило использует pytest-archon, который вызывает pytest.fail() напрямую.
Поэтому тестируем через subprocess, чтобы изолировать pytest-раннер.
"""
import os
import subprocess
import sys


def _run_fsd_validation(project_root: str) -> subprocess.CompletedProcess:
    """Run validate_fsd_architecture in a subprocess with correct PYTHONPATH."""
    pytest_fsd_src = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "src",
    )
    env = os.environ.copy()
    # Объединяем путь к src pytest-fsd и путь к тестовому проекту
    env["PYTHONPATH"] = os.pathsep.join([pytest_fsd_src, str(project_root)])

    test_file = os.path.join(project_root, "test_arch.py")

    return subprocess.run(
        [sys.executable, "-m", "pytest", test_file, "-x", "--tb=short", "--no-header"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        env=env,
    )


def test_forbidden_imports_no_errors(create_project):
    """No errors when layers only import from below."""
    project_root = create_project(
        """
        📂 shared
          📂 ui
            📄 __init__.py
        📂 entities
          📂 users
            📂 ui
            📄 __init__.py
            📄 model.py
        📂 windows
          📂 editor
            📂 ui
            📄 __init__.py
        """
    )

    (project_root / "src" / "entities" / "users" / "model.py").write_text(
        "# valid import from lower layer\n", encoding="utf-8"
    )
    (project_root / "test_arch.py").write_text(
        "from pytest_fsd import validate_fsd_architecture\n"
        "def test_arch():\n"
        "    validate_fsd_architecture('.')\n"
    )

    result = _run_fsd_validation(str(project_root))
    assert result.returncode == 0, f"Unexpected failure:\n{result.stdout}\n{result.stderr}"


def test_forbidden_imports_errors(create_project):
    """Error when shared imports from entities (higher layer)."""
    project_root = create_project(
        """
        📂 shared
          📂 ui
            📄 __init__.py
            📄 model.py
        📂 entities
          📂 users
            📂 ui
            📄 __init__.py
        """
    )

    (project_root / "src" / "shared" / "ui" / "model.py").write_text(
        "from src.entities.users import User\n"
    )
    (project_root / "test_arch.py").write_text(
        "from pytest_fsd import validate_fsd_architecture\n"
        "def test_arch():\n"
        "    validate_fsd_architecture('.')\n"
    )

    result = _run_fsd_validation(str(project_root))
    assert result.returncode != 0, "Expected failure due to forbidden import"
