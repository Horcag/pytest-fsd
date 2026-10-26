"""Portable positive/negative witnesses for every shipped architecture check.

Used by pytest and by `python -I tests/rule_contracts.py VERSION` against wheels.
"""

from pathlib import Path
import tempfile
from importlib.metadata import version
import sys

import pytest_fsd
from pytest_fsd.config import load_config
from pytest_fsd._lib.source_validation import check_sources

CORE_NAMES = {
    'forbidden-imports', 'no-cross-imports', 'no-public-api-sidestep',
    'no-layer-public-api', 'no-ui-in-app', 'repetitive-naming',
    'no-segmentless-slices', 'segments-by-purpose', 'ambiguous-slice-names',
    'no-segments-on-sliced-layers', 'public-api', 'typo-in-layer-name',
}
EXTRA_NAMES = {
    'excessive-slicing', 'shared-lib-grouping', 'no-file-segments',
    'no-reserved-folder-names', 'no-wildcard-exports',
}
GUARD_NAMES = {'python-source', 'dynamic-imports'}
ALL_NAMES = sorted(CORE_NAMES | EXTRA_NAMES | GUARD_NAMES)


def registry():
    rules = {module.RULE_NAME: module for module in pytest_fsd.CORE_RULES}
    rules.update(pytest_fsd.EXTRA_RULES)
    return rules


def verify_registry():
    assert {module.RULE_NAME for module in pytest_fsd.CORE_RULES} == CORE_NAMES
    assert set(pytest_fsd.EXTRA_RULES) == EXTRA_NAMES
    assert len(pytest_fsd.CORE_RULES) == len(CORE_NAMES)


def baseline():
    files = {
        'features/accounts/__init__.py': "__all__ = ['value']\nvalue = 1\n",
        'features/accounts/model/record.py': 'value = 1\n',
        'features/billing/__init__.py': "__all__ = ['value']\nvalue = 1\n",
        'features/billing/api/routes.py': '',
        'entities/customer/__init__.py': "__all__ = ['value']\nvalue = 1\n",
        'entities/customer/model/record.py': 'value = 1\n',
        'shared/config/__init__.py': "__all__ = ['value']\nvalue = 1\n",
        'shared/lib/formatting/__init__.py': "__all__ = ['value']\nvalue = 1\n",
        'shared/lib/formatting/core.py': 'value = 1\n',
        'app/config/start.py': '',
    }
    return files


def bad_files(name):
    files = baseline()
    changes = {
        'forbidden-imports': {'shared/config/runtime.py': 'from src.features.accounts import value\n'},
        'no-cross-imports': {'features/accounts/model/record.py': 'from src.features.billing import value\n'},
        'no-public-api-sidestep': {'app/config/start.py': 'from src.entities.customer.model.record import value\n'},
        'no-layer-public-api': {'features/__init__.py': ''},
        'no-ui-in-app': {'app/ui/panel.py': ''},
        'repetitive-naming': {'features/accounts/model/accounts_record.py': ''},
        'no-segmentless-slices': {'features/accounts/model/record.py': None},
        'segments-by-purpose': {'features/accounts/services/client.py': ''},
        'ambiguous-slice-names': {
            'features/formatting/__init__.py': '__all__ = []\n',
            'features/formatting/model/record.py': '',
        },
        'no-segments-on-sliced-layers': {'features/model/__init__.py': '', 'features/model/lib/record.py': ''},
        'public-api': {'features/accounts/__init__.py': None},
        'typo-in-layer-name': {'fietures/record.py': ''},
        'no-file-segments': {'features/accounts/api.py': ''},
        'no-reserved-folder-names': {'features/accounts/model/api/record.py': ''},
        'no-wildcard-exports': {'features/accounts/__init__.py': "from .model.record import *\n__all__ = ['value']\n"},
        'python-source': {'features/accounts/model/record.py': 'from broken import (\n'},
        'dynamic-imports': {'features/accounts/model/record.py': '__import__(runtime_target)\n'},
    }
    if name == 'excessive-slicing':
        for index in range(19):  # two baseline slices + 19 = 21 > 20
            files['features/item' + str(index) + '/__init__.py'] = '__all__ = []\n'
            files['features/item' + str(index) + '/model/record.py'] = ''
    elif name == 'shared-lib-grouping':
        for index in range(16):
            files['shared/lib/tool' + str(index) + '.py'] = ''
    else:
        for path, source in changes[name].items():
            if source is None:
                files.pop(path)
            else:
                files[path] = source
    return files


def materialize(root, files, extra_rules):
    for relative, source in files.items():
        path = root / 'src' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding='utf-8')
    extras = ', '.join('"' + name + '"' for name in extra_rules)
    (root / 'pyproject.toml').write_text(
        '[tool.pytest_fsd]\nbase_path = "src"\n'
        'layers = ["app", "features", "entities", "shared"]\n'
        'extra_rules = [' + extras + ']\n', encoding='utf-8',
    )


def facade_message(root):
    try:
        pytest_fsd.validate_fsd_architecture(str(root))
    except AssertionError as error:
        return str(error)
    return ''


def check_case(name, root):
    """Assert direct checking, facade dispatch, clean control and opt-in behavior."""
    extras = [name] if name in EXTRA_NAMES else []
    good, bad = root / 'good', root / 'bad'
    materialize(good, baseline(), extras)
    materialize(bad, bad_files(name), extras)
    checker = check_sources if name in GUARD_NAMES else registry()[name].check
    for project, expected in ((good, False), (bad, True)):
        found = any(v.rule == name for v in checker(load_config(str(project)), str(project)))
        assert found == expected, 'Direct check did not execute ' + name
        message = facade_message(project)
        assert ('[' + name + ']' in message) == expected, 'Facade did not execute ' + name
        assert not any('[' + other + ']' in message for other in ALL_NAMES if other != name), message
        if not expected:
            assert not message, message
    if name in EXTRA_NAMES:
        text = (bad / 'pyproject.toml').read_text(encoding='utf-8')
        (bad / 'pyproject.toml').write_text(text.replace('extra_rules = ["' + name + '"]', 'extra_rules = []'), encoding='utf-8')
        assert not facade_message(bad), 'Disabled extra rule still affects validation: ' + name


def main():
    assert version('pytest-fsd') == sys.argv[1]
    verify_registry()
    for name in ALL_NAMES:
        with tempfile.TemporaryDirectory(prefix='pytest-fsd-contract-') as directory:
            check_case(name, Path(directory))
        print('PASS rule contract:', name)
    print('Verified all 17 rules and both input guards; positive, negative and extra-rule controls.')


if __name__ == '__main__':
    main()
