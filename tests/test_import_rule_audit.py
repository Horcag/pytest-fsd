"""Boundary regressions for the complete import-rule audit."""

import pytest

from pytest_fsd.config import FsdConfig
from pytest_fsd.rules import (
    forbidden_imports,
    no_cross_imports,
    no_public_api_sidestep,
    no_ui_in_app,
    no_wildcard_exports,
)


def project(tmp_path, files, base="backend/src", layers=None):
    for name, source in files.items():
        path = tmp_path / base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    return FsdConfig(base_path=base, layers=layers or ["app", "features", "entities", "shared"])


@pytest.mark.parametrize("target,api", [
    ("shared/config/settings", "shared/config"),
    ("shared/lib/dates/internal", "shared/lib/dates"),
    ("shared/ui/button/internal", "shared/ui/button"),
])
@pytest.mark.parametrize("form", ["absolute", "relative", "dynamic", "exec"])
def test_shared_implementation_imports_require_public_boundary(tmp_path, target, api, form):
    module = target.replace("/", ".")
    statements = {
        "absolute": "from backend.src." + module + " import hidden",
        "relative": "from .." + module + " import hidden",
        "dynamic": "import importlib\nimportlib.import_module('backend.src." + module + "')",
        "exec": "exec(\"from backend.src." + module + " import hidden\")",
    }
    statement = statements[form]
    config = project(tmp_path, {
        "app/start.py": statement + "\n",
        api + "/__init__.py": "__all__ = ['visible']\n",
        target + ".py": "hidden = 1\n",
    })
    violations = no_public_api_sidestep.check(config, str(tmp_path))
    assert len(violations) == 1
    assert violations[0].rule == "no-public-api-sidestep"
    assert "Importing internal module" in violations[0].message
    assert violations[0].line_number == (2 if form == "dynamic" else 1)
    assert violations[0].column_number == 1


@pytest.mark.parametrize("api", ["shared/config", "shared/lib/dates", "shared/ui/button", "entities/user"])
@pytest.mark.parametrize("exports", ["__all__ = ['visible']", "__all__ = []", ""])
def test_public_boundary_export_names(tmp_path, api, exports):
    module = "backend.src." + api.replace("/", ".")
    config = project(tmp_path, {
        "app/start.py": "from " + module + " import visible\n",
        api + "/__init__.py": exports + "\n",
    })
    violations = no_public_api_sidestep.check(config, str(tmp_path))
    assert len(violations) == (0 if "['visible']" in exports else 1)


@pytest.mark.parametrize("api", ["shared/config", "shared/lib/dates", "shared/ui/button", "entities/user"])
@pytest.mark.parametrize("form", ["import", "from-parent", "from-own"])
def test_public_packages_and_own_boundary_remain_allowed(tmp_path, api, form):
    module = "backend.src." + api.replace("/", ".")
    parent, name = module.rsplit(".", 1)
    statements = {
        "import": "import " + module,
        "from-parent": "from " + parent + " import " + name,
        "from-own": "from .internal import hidden",
    }
    source_path = api + "/source.py" if form == "from-own" else "app/start.py"
    config = project(tmp_path, {
        source_path: statements[form] + "\n",
        api + "/__init__.py": "__all__ = []\n",
        api + "/internal.py": "hidden = 1\n",
    })
    assert no_public_api_sidestep.check(config, str(tmp_path)) == []


@pytest.mark.parametrize("module", ["shared.lib.dates", "shared.ui.button"])
def test_shared_standalone_modules_are_public_apis(tmp_path, module):
    config = project(tmp_path, {
        "app/start.py": "from backend.src." + module + " import visible\n",
        module.replace(".", "/") + ".py": "visible = 1\n",
    })
    assert no_public_api_sidestep.check(config, str(tmp_path)) == []


def test_prefixed_shared_boundaries_and_sibling_libraries(tmp_path):
    config = project(tmp_path, {
        "6_shared/lib/one/source.py": "__import__('backend.src.6_shared.lib.two.internal')\n",
        "6_shared/lib/one/__init__.py": "__all__ = []\n",
        "6_shared/lib/two/__init__.py": "__all__ = []\n",
        "6_shared/lib/two/internal.py": "hidden = 1\n",
    }, layers=["1_app", "4_features", "5_entities", "6_shared"])
    # Numeric-prefixed layers are importable through programmatic loaders.
    assert len(no_public_api_sidestep.check(config, str(tmp_path))) == 1


@pytest.mark.parametrize("path", ["other/source.py", "__init__.py", ".cache/source.py"])
def test_unconfigured_sources_do_not_trigger_public_api_rule(tmp_path, path):
    config = project(tmp_path, {
        path: "from backend.src.entities.user.internal import hidden\n",
        "entities/user/internal.py": "hidden = 1\n",
    })
    assert no_public_api_sidestep.check(config, str(tmp_path)) == []


@pytest.mark.parametrize("rule", [forbidden_imports, no_cross_imports])
@pytest.mark.parametrize("prefix", ["backend.src.", "src.", ""])
@pytest.mark.parametrize("dynamic", [False, True])
def test_layer_and_slice_boundaries_with_nested_roots(tmp_path, rule, prefix, dynamic):
    module = prefix + "features.other"
    statement = "__import__('" + module + "')" if dynamic else "from " + module + " import visible"
    path = "shared/lib/start.py" if rule is forbidden_imports else "features/own/__init__.py"
    config = project(tmp_path, {path: statement + "\n", "features/other/__init__.py": "__all__ = ['visible']\n"})
    violations = rule.check(config, str(tmp_path))
    assert violations
    assert all(v.line_number == 1 and v.column_number == 1 for v in violations)


@pytest.mark.parametrize("framework", sorted(no_ui_in_app.FORBIDDEN_UI_MODULES))
@pytest.mark.parametrize("dynamic", [False, True])
def test_gui_frameworks_in_prefixed_app(tmp_path, framework, dynamic):
    statement = "__import__('" + framework + ".widgets')" if dynamic else "from " + framework + " import Widget"
    config = project(tmp_path, {"1_app/start.py": statement + "\n"}, layers=["1_app", "6_shared"])
    violations = no_ui_in_app.check(config, str(tmp_path))
    assert len(violations) == 1
    assert framework in violations[0].message
    assert violations[0].line_number == 1


@pytest.mark.parametrize("rule,path,source", [
    (no_public_api_sidestep, "features/own/.cache/source.py", "from backend.src.entities.user.internal import hidden\n"),
    (no_ui_in_app, "app/.cache/source.py", "import tkinter\n"),
    (no_wildcard_exports, "entities/user/.cache/__init__.py", "from external import *\n"),
])
def test_ignored_directories_are_not_scanned(tmp_path, rule, path, source):
    config = project(tmp_path, {path: source, "entities/user/internal.py": "hidden = 1\n"})
    assert rule.check(config, str(tmp_path)) == []


@pytest.mark.parametrize("source", ["from .internal import *\n", "exec('from .internal import *')\n", "__import__('external', fromlist=['*'])\n"])
def test_wildcard_apis_static_and_dynamic_boundaries(tmp_path, source):
    config = project(tmp_path, {"shared/lib/dates/__init__.py": source})
    violations = no_wildcard_exports.check(config, str(tmp_path))
    assert len(violations) == 1
    assert violations[0].line_number == 1
    assert violations[0].column_number == 1


@pytest.mark.parametrize("exports", [
    "__all__ = ['visible']\nexports = __all__\nexports.append('hidden')\n",
    "__all__ = ['visible']\nexports = __all__\nexports.clear()\n",
    "__all__ = ['visible']\ndef mutate():\n    __all__.clear()\nmutate()\n",
    "__all__ = ['visible']\nconfigure(__all__)\n",
])
def test_escaped_export_lists_do_not_prove_public_names(tmp_path, exports):
    config = project(tmp_path, {
        "app/start.py": "from backend.src.entities.user import visible\n",
        "entities/user/__init__.py": exports,
    })
    violations = no_public_api_sidestep.check(config, str(tmp_path))
    assert len(violations) == 1
    assert "does not define `__all__`" in violations[0].message


@pytest.mark.parametrize("rule,path,source", [
    (forbidden_imports, "shared/_private/source.py", "from backend.src.features.other import visible\n"),
    (no_cross_imports, "features/_private/source.py", "from backend.src.features.other import visible\n"),
    (no_public_api_sidestep, "app/_private/source.py", "from backend.src.entities.user.internal import hidden\n"),
    (no_ui_in_app, "app/_private/source.py", "import tkinter\n"),
    (no_wildcard_exports, "entities/_private/__init__.py", "from external import *\n"),
])
def test_private_python_packages_remain_in_scope(tmp_path, rule, path, source):
    config = project(tmp_path, {
        path: source,
        "entities/user/internal.py": "hidden = 1\n",
        "features/other/__init__.py": "__all__ = ['visible']\n",
    })
    assert rule.check(config, str(tmp_path))


def test_public_api_recommendation_with_source_root_itself(tmp_path):
    config = project(tmp_path, {
        "app/start.py": "from entities.user.internal import hidden\n",
        "entities/user/internal.py": "hidden = 1\n",
    }, base=".")
    violations = no_public_api_sidestep.check(config, str(tmp_path))
    assert len(violations) == 1
    assert "Import from 'entities.user' instead." in violations[0].message


def test_cross_import_reports_each_sibling_boundary_once(tmp_path):
    config = project(tmp_path, {
        "features/own/source.py": "from backend.src.features.other import model, api\n",
        "features/other/__init__.py": "__all__ = ['model', 'api']\n",
        "features/other/model.py": "",
        "features/other/api.py": "",
    })
    violations = no_cross_imports.check(config, str(tmp_path))
    assert len(violations) == 1
    assert "features/other" in violations[0].message


def test_cross_import_preserves_distinct_sibling_boundaries(tmp_path):
    config = project(tmp_path, {
        "features/own/source.py": "from backend.src.features import other, another\n",
        "features/other/__init__.py": "",
        "features/another/__init__.py": "",
    })
    violations = no_cross_imports.check(config, str(tmp_path))
    assert len(violations) == 2
    assert any("features/other" in v.message for v in violations)
    assert any("features/another" in v.message for v in violations)


@pytest.mark.parametrize("rule,path", [
    (forbidden_imports, "6_shared/lib/source.py"),
    (no_cross_imports, "4_features/own/source.py"),
])
def test_numeric_layer_names_in_dynamic_import_boundaries(tmp_path, rule, path):
    config = project(tmp_path, {
        path: "__import__('backend.src.4_features.other')\n",
        "4_features/other/__init__.py": "",
    }, layers=["1_app", "4_features", "5_entities", "6_shared"])
    violations = rule.check(config, str(tmp_path))
    assert len(violations) == 1
    assert violations[0].line_number == 1


def test_layer_rank_uses_configured_order(tmp_path):
    config = project(tmp_path, {
        "shared/lib/source.py": "from backend.src.features.other import visible\n",
        "features/other/__init__.py": "__all__ = ['visible']\n",
    }, layers=["shared", "features"])
    assert forbidden_imports.check(config, str(tmp_path)) == []
