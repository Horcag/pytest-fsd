# tests/rules/test_no_cross_imports.py
"""
Tests for the no-cross-imports rule.

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
    env["PYTHONPATH"] = os.pathsep.join([pytest_fsd_src, str(project_root)])

    test_file = os.path.join(project_root, "test_arch.py")

    return subprocess.run(
        [sys.executable, "-m", "pytest", test_file, "-x", "--tb=short", "--no-header"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        env=env,
    )


def test_no_cross_imports_clean(create_project):
    """No errors when slices within the same layer are independent."""
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

    (project_root / "src" / "features" / "auth" / "model.py").write_text(
        "# internal slice code\n", encoding="utf-8"
    )
    (project_root / "src" / "features" / "profile" / "ui.py").write_text(
        "# internal slice code\n", encoding="utf-8"
    )
    (project_root / "test_arch.py").write_text(
        "from pytest_fsd import validate_fsd_architecture\n"
        "def test_arch():\n"
        "    validate_fsd_architecture('.')\n",
        encoding="utf-8",
    )

    result = _run_fsd_validation(str(project_root))
    assert result.returncode == 0, f"Unexpected failure:\n{result.stdout}\n{result.stderr}"


def test_no_cross_imports_errors(create_project):
    """Error when one slice imports from another slice in the same layer."""
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

    (project_root / "src" / "features" / "auth" / "model.py").write_text(
        "from src.features.profile import some_func\n", encoding="utf-8"
    )
    (project_root / "test_arch.py").write_text(
        "from pytest_fsd import validate_fsd_architecture\n"
        "def test_arch():\n"
        "    validate_fsd_architecture('.')\n",
        encoding="utf-8",
    )

    result = _run_fsd_validation(str(project_root))
    assert result.returncode != 0, "Expected failure due to cross import"


def test_no_cross_imports_shared_allowed(create_project):
    """Shared layer slices can depend on each other."""
    project_root = create_project(
        """
        📂 shared
          📂 ui
            📄 __init__.py
            📄 component.py
          📂 config
            📄 __init__.py
            📄 env.py
        """
    )

    (project_root / "src" / "shared" / "ui" / "component.py").write_text(
        "from src.shared.config import env\n", encoding="utf-8"
    )
    (project_root / "test_arch.py").write_text(
        "from pytest_fsd import validate_fsd_architecture\n"
        "def test_arch():\n"
        "    validate_fsd_architecture('.')\n",
        encoding="utf-8",
    )

    result = _run_fsd_validation(str(project_root))
    assert result.returncode == 0, f"Unexpected failure in shared:\n{result.stdout}\n{result.stderr}"
