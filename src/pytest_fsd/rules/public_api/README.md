# `public-api`

Require every slice (and every segment in `shared`) to have an `__init__.py` file that serves as its public API definition.

In Python, `__init__.py` acts as the public API entry point for a package. Other modules should import from the slice via this file, not from internal modules.

## Examples

✅ Pass:

```
📂 features/
  📂 auth/
    📄 __init__.py   # ← Public API present
    📂 model/
📂 shared/
  📂 lib/
    📄 __init__.py   # ← Public API present
```

❌ Fail:

```
📂 features/
  📂 auth/           # ❌ missing __init__.py
    📂 model/
📂 shared/
  📂 lib/            # ❌ missing __init__.py
    📄 hash.py
```

## Rationale

The public API for slices is the only entrypoint into a slice, ensuring that the internal structure can change freely as long as the public API stays the same. A slice without one becomes a weak point for refactoring.
