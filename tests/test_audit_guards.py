"""Guard regressions found during the complete rule audit."""

import ast
from pathlib import Path

import pytest

from pytest_fsd import validate_fsd_architecture
from pytest_fsd._lib.ast_utils import get_exported_names
from pytest_fsd.config import load_config


@pytest.mark.parametrize('code', [
    "alias = __all__\nalias.append('hidden')\n",
    "configure(__all__)\n",
    "def mutate():\n    __all__[0] = 'hidden'\nmutate()\n",
    "def mutate():\n    alias = __all__\n    alias.clear()\nmutate()\n",
    "exec(\"__all__.clear()\")\n",
])
def test_mutable_exports_cannot_prove_api_names(tmp_path, code):
    file = tmp_path / '__init__.py'
    file.write_text("__all__ = ['safe']\n" + code, encoding='utf-8')
    assert get_exported_names(str(file)) is None


def test_later_fresh_exports_restore_static_knowledge(tmp_path):
    file = tmp_path / '__init__.py'
    file.write_text("__all__ = ['safe']\nconfigure(__all__)\n__all__ = ['fresh']\n", encoding='utf-8')
    assert get_exported_names(str(file)) == ['fresh']


def test_root_tool_value_must_be_a_table(tmp_path):
    (tmp_path / 'pyproject.toml').write_text('tool = 42\n', encoding='utf-8')
    with pytest.raises(ValueError, match='pytest_fsd'):
        load_config(str(tmp_path))


def test_unreadable_source_root_reports_incomplete_scan(tmp_path, monkeypatch):
    source = tmp_path / 'src'
    source.mkdir()
    import os
    original = os.scandir

    def blocked(path):
        if Path(path) == source:
            raise PermissionError(13, 'denied', str(source))
        return original(path)

    monkeypatch.setattr(os, 'scandir', blocked)
    with pytest.raises(AssertionError, match='python-source'):
        validate_fsd_architecture(str(tmp_path))


def test_parser_recursion_failure_cannot_turn_into_success(tmp_path, monkeypatch):
    file = tmp_path / 'src/features/account/model/source.py'
    file.parent.mkdir(parents=True)
    file.write_text('value = 1\n', encoding='utf-8')

    def too_deep(*args, **kwargs):
        raise RecursionError('source too deep')

    monkeypatch.setattr(ast, 'parse', too_deep)
    with pytest.raises(AssertionError, match='python-source'):
        validate_fsd_architecture(str(tmp_path))


@pytest.mark.parametrize('path', ['.cache', '__pycache__'])
def test_metadata_does_not_count_as_uninspectable_python(tmp_path, path):
    file = tmp_path / 'src/shared' / path / 'broken.py'
    file.parent.mkdir(parents=True)
    file.write_text('from broken import (\n', encoding='utf-8')
    validate_fsd_architecture(str(tmp_path))


@pytest.mark.parametrize('name', ['inconsistent-naming', 'import-locality', 'insignificant-slice', 'no-processes'])
def test_documentary_rule_pages_are_not_silent_extra_rules(tmp_path, name):
    (tmp_path / 'pyproject.toml').write_text('[tool.pytest_fsd]\nextra_rules = ["' + name + '"]\n', encoding='utf-8')
    with pytest.raises(ValueError, match='Unknown pytest_fsd extra_rules'):
        load_config(str(tmp_path))


def test_configured_layer_cannot_be_reserved_metadata(tmp_path):
    (tmp_path / 'pyproject.toml').write_text('[tool.pytest_fsd]\nlayers = ["__pycache__"]\n', encoding='utf-8')
    with pytest.raises(ValueError, match='reserved metadata'):
        load_config(str(tmp_path))


def test_configured_layer_file_is_an_incomplete_scan(tmp_path):
    source = tmp_path / 'src'
    source.mkdir()
    (source / 'features').write_text('value = 1\n', encoding='utf-8')
    with pytest.raises(AssertionError, match='python-source'):
        validate_fsd_architecture(str(tmp_path))


@pytest.mark.parametrize('code', [
    "def expose():\n    return __all__\nexpose().append('hidden')\n",
    "__all__ = alias = ['safe']\nalias.append('hidden')\n",
    "__all__, other = (['different'], None)\n",
])
def test_indirect_export_rebindings_do_not_reuse_stale_names(tmp_path, code):
    file = tmp_path / '__init__.py'
    file.write_text("__all__ = ['safe']\n" + code, encoding='utf-8')
    assert get_exported_names(str(file)) is None
