"""Invalid input must not turn architecture checks into a silent success."""

import pytest

from pytest_fsd import validate_fsd_architecture
from pytest_fsd.config import load_config
from pytest_fsd.rules import forbidden_imports


@pytest.mark.parametrize("setting", [
    'extra_rules = ["no-wildcard-export"]',
    'layers = "features"',
    'layers = []',
    'layers = ["features", "features"]',
    'layers = ["../features"]',
    'extra_rules = "no-file-segments"',
    'ignore_paths = [42]',
    'base_path = ""',
    'base_path = 12',
    'extra_rule = ["no-file-segments"]',
])
def test_invalid_configuration_fails(tmp_path, setting):
    (tmp_path / "pyproject.toml").write_text('[tool.pytest_fsd]\n' + setting, encoding="utf-8")
    with pytest.raises(ValueError, match="pytest_fsd"):
        validate_fsd_architecture(str(tmp_path))


def test_missing_source_directory_fails(tmp_path):
    with pytest.raises(AssertionError, match="Configured source directory does not exist"):
        validate_fsd_architecture(str(tmp_path))


@pytest.mark.parametrize("content", [b"from src.features import (\n", b"\xff\n", b"# coding: unknown-encoding\n"])
def test_invalid_source_fails(tmp_path, content):
    file = tmp_path / "src/shared/lib/source.py"
    file.parent.mkdir(parents=True)
    file.write_bytes(content)
    with pytest.raises(AssertionError, match="python-source"):
        validate_fsd_architecture(str(tmp_path))


@pytest.mark.parametrize("encoding", ["latin-1", "utf-8-sig"])
def test_python_encoding_declaration_preserves_import_checks(tmp_path, encoding):
    file = tmp_path / "src/shared/lib/source.py"
    file.parent.mkdir(parents=True)
    source = "# coding: " + ("latin-1" if encoding == "latin-1" else "utf-8") + "\n# café\nfrom src.features import tables\n"
    file.write_bytes(source.encode(encoding))
    (tmp_path / "src/features/tables/model").mkdir(parents=True)
    (tmp_path / "src/features/tables/__init__.py").write_text("__all__ = []\n", encoding="utf-8")
    violations = forbidden_imports.check(load_config(str(tmp_path)), str(tmp_path))
    assert violations and all(v.rule == "forbidden-imports" for v in violations)
    with pytest.raises(AssertionError, match="forbidden-imports"):
        validate_fsd_architecture(str(tmp_path))


@pytest.mark.parametrize("kind", ["layer", "directory", "file"])
def test_symlinks_cannot_hide_import_violations(tmp_path, kind):
    real = tmp_path / "real"
    real.mkdir()
    source = real / "source.py"
    source.write_text("from src.features import tables\n", encoding="utf-8")
    base = tmp_path / "src/shared"
    if kind == "layer":
        base.parent.mkdir()
        base.symlink_to(real, target_is_directory=True)
    elif kind == "directory":
        base.mkdir(parents=True)
        (base / "lib").symlink_to(real, target_is_directory=True)
    else:
        (base / "lib").mkdir(parents=True)
        (base / "lib/source.py").symlink_to(source)
    with pytest.raises(AssertionError, match="python-source"):
        validate_fsd_architecture(str(tmp_path))
