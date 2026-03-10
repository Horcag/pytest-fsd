# `ambiguous-slice-names`

Forbid slice names that match segment names in the `shared` layer. For example, if `shared/i18n` exists, having `features/i18n` is confusing.

## Examples

✅ Pass:

```
📂 shared/
  📂 ui/
  📂 i18n/
📂 features/
  📂 auth/          # OK: "auth" is not a shared segment
```

❌ Fail:

```
📂 shared/
  📂 ui/
  📂 i18n/
📂 features/
  📂 i18n/          # ❌ same name as shared/i18n
```

## Rationale

When there is a segment in `shared` with the same name as a slice in another layer, it becomes ambiguous where new code should be written and obscures the search for existing code.
