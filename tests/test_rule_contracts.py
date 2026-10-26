"""Every shipped rule must have an effective negative and positive witness."""

import pytest
import pytest_fsd

from rule_contracts import ALL_NAMES, CORE_NAMES, EXTRA_NAMES, check_case, verify_registry


def test_every_registered_rule_has_an_explicit_contract():
    verify_registry()


@pytest.mark.parametrize('name', ALL_NAMES)
def test_rule_contract(name, tmp_path):
    check_case(name, tmp_path)


@pytest.mark.parametrize('name', sorted(CORE_NAMES | EXTRA_NAMES))
def test_contract_detects_noop_rule_mutation(name, tmp_path, monkeypatch):
    modules = {module.RULE_NAME: module for module in pytest_fsd.CORE_RULES}
    modules.update(pytest_fsd.EXTRA_RULES)
    monkeypatch.setattr(modules[name], 'check', lambda *args: [])
    with pytest.raises(AssertionError, match='Direct check did not execute ' + name):
        check_case(name, tmp_path)


@pytest.mark.parametrize('name', sorted(CORE_NAMES))
def test_contract_detects_missing_core_dispatch(name, tmp_path, monkeypatch):
    # Leave the direct checker available while disconnecting it from the facade.
    original = list(pytest_fsd.CORE_RULES)
    module = next(module for module in original if module.RULE_NAME == name)
    monkeypatch.setattr(pytest_fsd, 'CORE_RULES', [m for m in original if m is not module])
    import rule_contracts
    monkeypatch.setattr(rule_contracts, 'registry', lambda: {m.RULE_NAME: m for m in original})
    with pytest.raises(AssertionError, match='Facade did not execute ' + name):
        check_case(name, tmp_path)


@pytest.mark.parametrize('name', sorted(EXTRA_NAMES))
def test_contract_detects_missing_extra_dispatch(name, tmp_path, monkeypatch):
    import rule_contracts
    modules = rule_contracts.registry()
    monkeypatch.setattr(pytest_fsd, 'EXTRA_RULES', {key: value for key, value in pytest_fsd.EXTRA_RULES.items() if key != name})
    monkeypatch.setattr(rule_contracts, 'registry', lambda: modules)
    with pytest.raises(AssertionError, match='Facade did not execute ' + name):
        check_case(name, tmp_path)


@pytest.mark.parametrize('name', ['python-source', 'dynamic-imports'])
def test_contract_detects_missing_input_guard(name, tmp_path, monkeypatch):
    monkeypatch.setattr(pytest_fsd, 'check_sources', lambda *args: [])
    with pytest.raises(AssertionError, match='Facade did not execute ' + name):
        check_case(name, tmp_path)
