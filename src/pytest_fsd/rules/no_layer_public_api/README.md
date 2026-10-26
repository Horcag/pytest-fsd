# `no-layer-public-api`

Forbid `__init__.py` files in sliced layer directories (e.g., `features/`, `entities/`, `pages/`, `widgets/`).

These directories serve as grouping containers for slices — they are not packages with their own API.

## Examples

✅ Pass:

```
📂 features/          # No __init__.py here
  📂 auth/
    📄 __init__.py    # Slice has a Public API — OK
    📂 model/
```

❌ Fail:

```
📂 features/
  📄 __init__.py      # ❌ Layer directory should not be a package
  📂 auth/
    📄 __init__.py
    📂 model/
```

## Rationale

Having `__init__.py` in a layer directory misleads developers into thinking it is a module with its own API. Layers in FSD are purely structural containers.

## Scope

The check applies to direct children of configured sliced layers, including custom layer names and numeric ordering prefixes. The `app` and `shared` layers are exempt. Nested slice implementation directories are outside this rule.
