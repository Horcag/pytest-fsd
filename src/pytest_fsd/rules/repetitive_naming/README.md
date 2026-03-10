# `repetitive-naming`

Prevent file names within a slice from duplicating the slice name.

## Examples

✅ Pass:

```
📂 features/
  📂 auth/
    📂 model/
      📄 handler.py     # OK: descriptive without repeating "auth"
      📄 command.py
    📄 __init__.py
```

❌ Fail:

```
📂 features/
  📂 auth/
    📂 model/
      📄 auth_handler.py   # ❌ repeats "auth"
      📄 auth_command.py   # ❌ repeats "auth"
    📄 __init__.py
```

## Rationale

When you're already inside the `auth` slice, every file is implicitly in the "auth" context. Repeating the slice name in file names is redundant and adds noise. Use descriptive names that describe the file's _role_ within the slice.
