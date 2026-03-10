# `forbidden-imports`

Forbids imports from higher layers. This is in accordance with the FSD import rule on layers:

> A module in a slice can only import other slices when they are located on layers strictly below.

This rule maps to Steiger's `no-higher-level-imports`.

## How it works

Uses `pytest-archon` to dynamically verify that modules in each layer do not import from any layer above them in the configured hierarchy.

For example, with default layers `["app", "windows", "widgets", "features", "entities", "shared"]`:

- `features` can import from `entities` and `shared`
- `features` **cannot** import from `widgets`, `windows`, or `app`

## Examples

✅ Pass:

```python
# src/features/auth/model/handler.py
from src.entities.user import User        # OK: entities is below features
from src.shared.lib.hash import hash_pw   # OK: shared is below features
```

❌ Fail:

```python
# src/features/auth/model/handler.py
from src.pages.home import HomePage       # VIOLATION: pages is above features
```

## Rationale

This is one of the main rules of Feature-Sliced Design. It ensures low coupling and predictability during refactoring.
