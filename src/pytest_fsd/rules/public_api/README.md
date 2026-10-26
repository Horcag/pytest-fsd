# `public-api`

Require every slice and every shared segment other than `ui` and `lib` to have an `__init__.py` file that serves as its public API definition.

`shared/ui` and `shared/lib` may contain individual modules without a root public API. Each immediate subfolder in those two segments must have its own `__init__.py`. This check stops at that boundary; it does not require every nested implementation package to declare a public API. The `app` layer is exempt.

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
  📂 config/         # ❌ missing __init__.py
    📄 settings.py
```

## Rationale

The public API for slices is the only entrypoint into a slice, ensuring that the internal structure can change freely as long as the public API stays the same. A slice without one becomes a weak point for refactoring.

## Scope

Configured layer names and source roots are supported, including numeric ordering prefixes. Ordinary underscore-prefixed package directories are checked. Dot-hidden directories and `__pycache__` are metadata and are skipped. Checks apply at the documented slice or segment boundary, not recursively to implementation packages.
