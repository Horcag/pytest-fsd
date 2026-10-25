"""Architecture boundaries must work without pytest-archon's runtime state."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

from pytest_fsd import validate_fsd_architecture
from pytest_fsd.config import FsdConfig
from pytest_fsd.rules import forbidden_imports, no_cross_imports


def write_project(root, source, source_path="features/auth/api/router.py", base="src"):
    files = {
        "features/auth/__init__.py": "__all__ = []\n",
        "features/tables/__init__.py": "from .model.value import value\n__all__ = ['value']\n",
        "features/tables/model/value.py": "value = 1\n",
        "shared/lib/__init__.py": "value = 1\n",
        source_path: source,
    }
    for name, body in files.items():
        path = root / base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[tool.pytest_fsd]\nbase_path = "' + base + '"\n'
        'layers = ["app", "features", "entities", "shared"]\n', encoding="utf-8"
    )
    return FsdConfig(base_path=base, layers=["app", "features", "entities", "shared"])


@pytest.mark.parametrize("source", [
    "from src.features.tables import value\n",
    "import src.features.tables as tables\n",
    "from src.features import tables\n",
    "from features.tables import value\n",
    "from features import tables\n",
    "from ...tables import value\n",
    "from ... import tables\n",
    "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from src.features.tables import value\n",
    "def operation():\n    from src.features.tables import value\n",
    "try:\n    from src.features.tables import value\nexcept ImportError:\n    pass\n",
])
@pytest.mark.parametrize("path", ["features/auth/api/router.py", "features/auth/api/__init__.py"])
def test_cross_slice_import_forms(tmp_path, source, path):
    config = write_project(tmp_path, source, path)
    violations = no_cross_imports.check(config, str(tmp_path))
    assert violations and all(v.rule == "no-cross-imports" for v in violations)
    assert all(v.line_number and v.column_number for v in violations)


@pytest.mark.parametrize("source,path", [
    ("from src.features.tables import value\n", "shared/lib/source.py"),
    ("from src.features.tables import value\n", "shared/__init__.py"),
    ("import src.features\n", "shared/__init__.py"),
    ("from src import features\n", "shared/__init__.py"),
    ("from features import tables\n", "shared/__init__.py"),
    ("from ...features.tables import value\n", "shared/lib/source.py"),
    ("from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from src.features.tables import value\n", "shared/lib/source.py"),
])
def test_upward_import_forms(tmp_path, source, path):
    config = write_project(tmp_path, source, path)
    violations = forbidden_imports.check(config, str(tmp_path))
    assert violations and all(v.rule == "forbidden-imports" for v in violations)


@pytest.mark.parametrize("base,prefix", [("backend/src", "backend.src"), ("backend/src", "src"), ("backend/src", "")])
def test_nested_source_root_and_foreign_cwd(tmp_path, monkeypatch, base, prefix):
    target = (prefix + "." if prefix else "") + "features.tables"
    config = write_project(tmp_path, "from " + target + " import value\n", base=base)
    monkeypatch.chdir(tmp_path.parent)
    assert no_cross_imports.check(config, str(tmp_path))


@pytest.mark.parametrize("source,path", [
    ("from src.shared.lib import value\n", "features/auth/api/router.py"),
    ("from ..model import value\n", "features/auth/api/router.py"),
    ("from src.app.config import value\n", "app/api/router.py"),
    ("from src.shared.config import value\n", "shared/lib/source.py"),
    ("import requests\n", "features/auth/api/router.py"),
    ("import other.features.tables\n", "features/auth/api/router.py"),
])
def test_permitted_import_controls(tmp_path, source, path):
    config = write_project(tmp_path, source, path)
    assert no_cross_imports.check(config, str(tmp_path)) == []
    assert forbidden_imports.check(config, str(tmp_path)) == []


def test_validator_does_not_execute_sources_or_cache_projects(tmp_path):
    config = write_project(tmp_path, "raise RuntimeError('must not run')\nfrom src.features.tables import value\n")
    for _ in range(2):
        with pytest.raises(AssertionError, match="no-cross-imports"):
            validate_fsd_architecture(str(tmp_path))
    (tmp_path / "src/features/auth/api/router.py").write_text("", encoding="utf-8")
    assert no_cross_imports.check(config, str(tmp_path)) == []


@pytest.mark.parametrize("source,path,rule", [
    ("from src.features.tables import value\n", "features/auth/api/router.py", "no-cross-imports"),
    ("from src.features.tables import value\n", "shared/lib/source.py", "forbidden-imports"),
    ("from src.shared.lib import value\n", "features/auth/api/router.py", None),
])
@pytest.mark.parametrize("runner", ["python", "pytest"])
def test_public_facade_exit_status(tmp_path, source, path, rule, runner):
    write_project(tmp_path, source, path)
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"),
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTEST_ADDOPTS="")
    code = "from pytest_fsd import validate_fsd_architecture; validate_fsd_architecture(" + repr(str(tmp_path)) + ")"
    if runner == "python":
        command = [sys.executable, "-c", code]
    else:
        test_file = tmp_path / "test_architecture.py"
        test_file.write_text("def test_architecture():\n    " + code + "\n", encoding="utf-8")
        command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(test_file)]
    result = subprocess.run(command, cwd=tmp_path.parent, env=env, capture_output=True, text=True, timeout=30)
    if rule:
        assert result.returncode == 1, result.stdout + result.stderr
        assert "[" + rule + "]" in result.stdout + result.stderr
        if runner == "pytest":
            assert "1 failed" in result.stdout
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        if runner == "pytest":
            assert "1 passed" in result.stdout


def test_relative_import_can_leave_and_reenter_source_root(tmp_path):
    config = write_project(tmp_path, "from .....src.features.tables import value\n", base="backend/src")
    assert no_cross_imports.check(config, str(tmp_path))
