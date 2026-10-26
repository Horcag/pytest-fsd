"""Dynamic import inspection must enforce boundaries without executing sources."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

from pytest_fsd import validate_fsd_architecture
from pytest_fsd.config import FsdConfig
from pytest_fsd.rules import forbidden_imports, no_cross_imports, no_public_api_sidestep


def write_project(root, source, source_path="features/auth/api/router.py"):
    files = {
        "features/auth/__init__.py": "__all__ = []\n",
        "features/auth/api/__init__.py": "",
        "features/tables/__init__.py": "__all__ = ['value']\nvalue = 1\n",
        "features/tables/model/value.py": "value = 1\n",
        "shared/lib/__init__.py": "value = 1\n",
        source_path: source,
    }
    for name, body in files.items():
        path = root / "src" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[tool.pytest_fsd]\nbase_path = "src"\n'
        'layers = ["app", "features", "entities", "shared"]\n',
        encoding="utf-8",
    )
    return FsdConfig(base_path="src", layers=["app", "features", "entities", "shared"])


@pytest.mark.parametrize("source", [
    "import importlib\nimportlib.import_module('src.features.tables')\n",
    "import importlib as loader\nloader.import_module('src.features.tables')\n",
    "from importlib import import_module\nimport_module('features.tables')\n",
    "from importlib import import_module as load\nload('src.features.tables')\n",
    "import importlib\nload = importlib.import_module\nload('src.features.tables')\n",
    "from importlib import import_module\nload = import_module\nload('src.features.tables')\n",
    "__import__('src.features.tables')\n",
    "load = __import__\nload('src.features.tables')\n",
    "import importlib\nimportlib.import_module(name='src.features.tables')\n",
    "__import__(name='src.features.tables')\n",
    "import importlib\nimportlib.import_module('src.' + 'features.tables')\n",
    "import importlib\nlayer = 'features'\nname = 'src.' + layer + '.tables'\nimportlib.import_module(name)\n",
    "import importlib\nlayer = 'features'\nimportlib.import_module(f'src.{layer}.tables')\n",
    "import importlib\nimportlib.import_module('...tables', package='src.features.auth.api')\n",
    "import importlib\nimportlib.import_module('...tables', package=__package__)\n",
    "__import__('tables', {'__package__': 'src.features.auth.api'}, None, (), 3)\n",
    "__import__('tables', globals={'__package__': __package__}, level=3)\n",
    "__import__('src.features', fromlist=['tables'])\n",
    "__import__('src.features', fromlist=('tables',))\n",
    "import importlib\nexec(\"importlib.import_module('src.features.tables')\")\n",
    "exec(\"import src.features.tables\")\n",
    "exec(\"from src.features import tables\")\n",
    "eval(\"__import__('src.features.tables')\")\n",
    "code = \"import src.features.tables\"\nexec(code)\n",
])
def test_dynamic_cross_slice_import_forms(tmp_path, source):
    config = write_project(tmp_path, source)
    violations = no_cross_imports.check(config, str(tmp_path))
    assert violations, source
    assert all(v.rule == "no-cross-imports" for v in violations)
    assert all(v.line_number and v.column_number for v in violations)


@pytest.mark.parametrize("source", [
    "import importlib\nimportlib.import_module('src.features.tables')\n",
    "__import__('src.features.tables')\n",
    "exec(\"from src.features.tables import value\")\n",
    "eval(\"__import__('src.features.tables')\")\n",
])
def test_dynamic_upward_imports(tmp_path, source):
    config = write_project(tmp_path, source, "shared/lib/source.py")
    violations = forbidden_imports.check(config, str(tmp_path))
    assert violations, source
    assert all(v.rule == "forbidden-imports" for v in violations)


@pytest.mark.parametrize("source", [
    "import importlib\nimportlib.import_module('src.features.tables.model.value')\n",
    "__import__('src.features.tables.model.value')\n",
    "__import__('src.features.tables', fromlist=['model'])\n",
    "__import__('src.features.tables', fromlist=['hidden'])\n",
    "exec(\"from src.features.tables.model import value\")\n",
    "eval(\"__import__('src.features.tables.model.value')\")\n",
])
def test_dynamic_public_api_bypasses(tmp_path, source):
    config = write_project(tmp_path, source, "app/api/router.py")
    violations = no_public_api_sidestep.check(config, str(tmp_path))
    assert violations, source
    assert all(v.rule == "no-public-api-sidestep" for v in violations)


@pytest.mark.parametrize("source", [
    "import importlib\nimportlib.import_module(get_target())\n",
    "from importlib import import_module as load\nload(target)\n",
    "__import__(target)\n",
    "import importlib\nimportlib.import_module(f'src.{get_layer()}.tables')\n",
    "import importlib\nimportlib.import_module('.tables', package=get_package())\n",
    "__import__('tables', globals=get_globals(), level=3)\n",
    "__import__('src.features', fromlist=get_names())\n",
    "__import__('tables', level=get_level())\n",
    "exec(code)\n",
    "eval(get_code())\n",
    "exec(\"import importlib; importlib.import_module(target)\")\n",
])
def test_unresolved_dynamic_imports_fail_facade(tmp_path, source):
    write_project(tmp_path, source)
    with pytest.raises(AssertionError, match=r"\[dynamic-imports\]"):
        validate_fsd_architecture(str(tmp_path))


@pytest.mark.parametrize("source", [
    "import importlib\nimportlib.import_module('src.shared.lib')\n",
    "from importlib import import_module as load\nload('json')\n",
    "__import__('json')\n",
    "__import__('src.shared.lib', fromlist=['value'])\n",
    "exec(\"from src.shared.lib import value\")\n",
    "eval(\"__import__('json')\")\n",
    "def import_module(name):\n    return name\nimport_module(target)\n",
    "def __import__(name):\n    return name\n__import__(target)\n",
    "def exec(code):\n    return code\nexec(code)\n",
    "def eval(code):\n    return code\neval(code)\n",
    "from importlib import import_module as load\ndef operation(load):\n    return load(target)\n",
    "import importlib\ndef operation(importlib):\n    return importlib.import_module(target)\n",
])
def test_allowed_dynamic_imports_and_shadowed_callable_controls(tmp_path, source):
    config = write_project(tmp_path, source)
    assert no_cross_imports.check(config, str(tmp_path)) == []
    assert forbidden_imports.check(config, str(tmp_path)) == []
    assert no_public_api_sidestep.check(config, str(tmp_path)) == []
    validate_fsd_architecture(str(tmp_path))


def test_dunder_import_public_export_is_allowed(tmp_path):
    config = write_project(
        tmp_path, "__import__('src.features.tables', fromlist=['value'])\n", "app/api/router.py"
    )
    assert no_public_api_sidestep.check(config, str(tmp_path)) == []
    validate_fsd_architecture(str(tmp_path))


def test_dynamic_analysis_is_repeatable_and_does_not_execute_sources(tmp_path):
    marker = tmp_path / "executed.txt"
    source = (
        "from pathlib import Path\n"
        "Path(" + repr(str(marker)) + ").write_text('executed')\n"
        "import importlib\n"
        "importlib.import_module('src.features.tables')\n"
    )
    config = write_project(tmp_path, source)
    errors = []
    for _ in range(2):
        with pytest.raises(AssertionError, match="no-cross-imports") as error:
            validate_fsd_architecture(str(tmp_path))
        errors.append(str(error.value))
    assert errors[0] == errors[1]
    assert not marker.exists()
    (tmp_path / "src/features/auth/api/router.py").write_text(
        "import importlib\nimportlib.import_module('json')\n", encoding="utf-8"
    )
    assert no_cross_imports.check(config, str(tmp_path)) == []
    validate_fsd_architecture(str(tmp_path))


@pytest.mark.parametrize("source,rule", [
    ("import importlib\nimportlib.import_module('src.features.tables')\n", "no-cross-imports"),
    ("__import__(unknown_target)\n", "dynamic-imports"),
    ("exec(unknown_code)\n", "dynamic-imports"),
    ("__import__('json')\n", None),
])
def test_dynamic_facade_exit_status(tmp_path, source, rule):
    write_project(tmp_path, source)
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
    code = (
        "from pytest_fsd import validate_fsd_architecture; "
        "validate_fsd_architecture(" + repr(str(tmp_path)) + ")"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path.parent, env=env,
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == (1 if rule else 0), result.stdout + result.stderr
    if rule:
        assert "[" + rule + "]" in result.stdout + result.stderr


@pytest.mark.parametrize("source", [
    "operation = lambda value=__import__('src.features.tables'): value\n",
    "mapping = {**unknown, 'module': __import__('src.features.tables')}\n",
    "message = f\"{unknown}{__import__('src.features.tables')}\"\n",
    "exec(\"load('src.features.tables')\", {'load': __import__})\n",
    "__import__('src.features', fromlist=['tables.model'])\n",
])
def test_nested_dynamic_import_calls_are_not_skipped(tmp_path, source):
    config = write_project(tmp_path, source)
    assert no_cross_imports.check(config, str(tmp_path)), source
    with pytest.raises(AssertionError, match=r"\[no-cross-imports\]"):
        validate_fsd_architecture(str(tmp_path))


def test_conditional_loader_alias_cannot_hide_import(tmp_path):
    source = (
        "from importlib import import_module\n"
        "load = import_module if condition else other\n"
        "load('src.features.tables')\n"
    )
    write_project(tmp_path, source)
    with pytest.raises(AssertionError, match=r"\[(no-cross-imports|dynamic-imports)\]"):
        validate_fsd_architecture(str(tmp_path))


@pytest.mark.parametrize("source", [
    "operation = lambda value=__import__('json'): value\n",
    "mapping = {**unknown, 'module': __import__('json')}\n",
    "message = f\"{unknown}{__import__('json')}\"\n",
    "exec(\"load('json')\", {'load': __import__})\n",
])
def test_nested_external_import_controls(tmp_path, source):
    write_project(tmp_path, source)
    validate_fsd_architecture(str(tmp_path))


def test_recursive_literal_exec_has_bounded_analysis_budget(tmp_path):
    # A depth limit alone still expands this tiny input exponentially.
    source = "code = " + repr("exec(code);" * 5) + "\nexec(code)\n"
    write_project(tmp_path, source)
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
    code = (
        "from pytest_fsd import validate_fsd_architecture; "
        "validate_fsd_architecture(" + repr(str(tmp_path)) + ")"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path.parent, env=env,
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "[dynamic-imports]" in result.stdout + result.stderr


@pytest.mark.parametrize('source', [
    "target = 'src.features.tables'\ncondition and (target := 'json')\n__import__(target)\n",
    "target = 'src.features.tables'\nvalue = (target := 'json') if condition else None\n__import__(target)\n",
    "import importlib\ndef f():\n    [x for importlib in items]\n    importlib.import_module('src.features.tables')\n",
    "from importlib import *\nimport_module('src.features.tables')\n",
])
def test_branch_and_scope_changes_do_not_hide_dynamic_imports(tmp_path, source):
    write_project(tmp_path, source)
    with pytest.raises(AssertionError, match='no-cross-imports|dynamic-imports'):
        validate_fsd_architecture(str(tmp_path))


def test_comprehension_binding_shadows_builtin_only_inside_comprehension(tmp_path):
    write_project(tmp_path, '[eval(value) for eval in handlers]\n')
    validate_fsd_architecture(str(tmp_path))


@pytest.mark.parametrize('source', [
    "def f(load=__import__):\n    load('src.features.tables')\n",
    "f = lambda load=__import__: load('src.features.tables')\n",
    "import importlib\nloaders = [importlib.import_module]\nload = loaders[index]\nload('src.features.tables')\n",
    "import importlib\nload = {'loader': importlib.import_module}.get(key)\nload('src.features.tables')\n",
    "import importlib\nregister([importlib.import_module])\n",
])
def test_loader_provenance_survives_indirection(tmp_path, source):
    write_project(tmp_path, source)
    with pytest.raises(AssertionError, match='no-cross-imports|dynamic-imports'):
        validate_fsd_architecture(str(tmp_path))


@pytest.mark.parametrize('source', [
    "load = eval('__import__')\nload('src.features.tables')\n",
    "getattr(__import__('importlib'), 'import_module')('src.features.tables')\n",
    "code = compile(\"import src.features.tables\", '<dynamic>', 'exec')\nexec(code)\n",
    "import importlib\nimportlib.import_module('.'.join(('src', 'features', 'tables')))\n",
    "def f(x: __import__('src.features.tables')):\n    pass\n",
    "class X(__import__('src.features.tables').Base):\n    pass\n",
])
def test_computed_loader_and_definition_expressions(tmp_path, source):
    config = write_project(tmp_path, source)
    assert no_cross_imports.check(config, str(tmp_path))


@pytest.mark.parametrize('source', [
    "load = enabled and __import__\nload('src.features.tables')\n",
    "load = __import__ or other\nload('src.features.tables')\n",
])
def test_boolean_loader_aliases_cannot_hide_imports(tmp_path, source):
    write_project(tmp_path, source)
    with pytest.raises(AssertionError, match='no-cross-imports|dynamic-imports'):
        validate_fsd_architecture(str(tmp_path))


@pytest.mark.parametrize('source', [
    "import importlib\nclass C:\n    importlib = object()\n    def f(self):\n        return importlib.import_module('src.features.tables')\n",
    "def f(*args: __import__('src.features.tables').T):\n    pass\n",
    "def f(**kwargs: __import__('src.features.tables').T):\n    pass\n",
])
def test_method_globals_and_variadic_annotations_are_inspected(tmp_path, source):
    config = write_project(tmp_path, source)
    assert no_cross_imports.check(config, str(tmp_path))


def test_global_declaration_does_not_shadow_module_loader(tmp_path):
    config = write_project(tmp_path,
        "import importlib\ndef f():\n    global importlib\n"
        "    importlib.import_module('src.features.tables')\n    importlib = object()\n")
    assert no_cross_imports.check(config, str(tmp_path))


@pytest.mark.parametrize('source', [
    "__import__('src.features.tables', fromlist=None)\n",
    "__import__('', globals={'__package__': 'src.features'}, fromlist=['tables'], level=1)\n",
])
def test_builtin_import_optional_fromlist_and_relative_empty_name(tmp_path, source):
    config = write_project(tmp_path, source)
    assert no_cross_imports.check(config, str(tmp_path))


@pytest.mark.parametrize('source', [
    "import importlib\nimportlib.import_module('tkinter')\n",
    "__import__('PyQt6.QtWidgets')\n",
    "exec(\"import tkinter\")\n",
])
def test_dynamic_gui_imports_follow_app_rule(tmp_path, source):
    from pytest_fsd.rules import no_ui_in_app
    config = write_project(tmp_path, source, 'app/api/router.py')
    assert no_ui_in_app.check(config, str(tmp_path))


@pytest.mark.parametrize('source', [
    "exec('from .model import *')\n",
    "__import__('src.features.tables.model', fromlist=['*'])\n",
])
def test_dynamic_wildcard_exports_follow_optional_rule(tmp_path, source):
    from pytest_fsd.rules import no_wildcard_exports
    config = write_project(tmp_path, source, 'features/auth/__init__.py')
    assert no_wildcard_exports.check(config, str(tmp_path))


@pytest.mark.skipif(sys.version_info < (3, 10), reason='match requires Python 3.10')
def test_match_branches_do_not_hide_dynamic_imports(tmp_path):
    write_project(tmp_path,
        "target = 'src.features.tables'\nmatch flag:\n    case True:\n        target = 'json'\n__import__(target)\n")
    with pytest.raises(AssertionError, match='no-cross-imports|dynamic-imports'):
        validate_fsd_architecture(str(tmp_path))


@pytest.mark.skipif(sys.version_info < (3, 10), reason='match requires Python 3.10')
def test_match_pattern_binding_shadows_loader(tmp_path):
    write_project(tmp_path,
        "from importlib import import_module as load\ndef f(flag):\n"
        "    match flag:\n        case {'load': load}:\n            load(target)\n")
    validate_fsd_architecture(str(tmp_path))


@pytest.mark.skipif(sys.version_info < (3, 11), reason='except* requires Python 3.11')
def test_exception_group_branches_do_not_hide_dynamic_imports(tmp_path):
    write_project(tmp_path,
        "target = 'src.features.tables'\ntry:\n    operation()\nexcept* Exception:\n"
        "    target = 'json'\n__import__(target)\n")
    with pytest.raises(AssertionError, match='no-cross-imports|dynamic-imports'):
        validate_fsd_architecture(str(tmp_path))
