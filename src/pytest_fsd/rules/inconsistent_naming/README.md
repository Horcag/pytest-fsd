# `inconsistent-naming`

> 🔶 **Covered by Ruff.** This rule is NOT part of `pytest-fsd` core checks, but is fully enforceable via Ruff's `N` (pep8-naming) plugin.

Ensure that all modules and directories follow consistent naming conventions (`snake_case` for Python).

In Steiger, this rule specifically checks consistency of **pluralization** in the `entities` layer (e.g., all entities should be either singular or plural, not mixed). In Python, `Ruff` handles the broader naming consistency problem via PEP 8 conventions.

## Ruff Configuration

```toml
[tool.ruff.lint]
select = ["N"]  # pep8-naming — enforces snake_case for modules, variables, functions
```

### What `N` covers

| Rule   | Description                                     |
| ------ | ----------------------------------------------- |
| `N801` | Class names should use CapitalCase              |
| `N802` | Function names should be lowercase              |
| `N806` | Variable names should be lowercase              |
| `N815` | Variable in class scope should not be camelCase |
| `N999` | Invalid module name                             |

## Steiger Equivalent

```text
📂 entities/
  📂 users/      # Plural
  📂 post/       # ❌ Singular — inconsistent with "users"
```

In Python FSD, use `snake_case` everywhere and pick one pluralization style for your entities layer. Ruff enforces the `snake_case` part; pluralization consistency is a team convention enforced via code review.
