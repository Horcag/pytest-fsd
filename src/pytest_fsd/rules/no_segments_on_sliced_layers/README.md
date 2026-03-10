# `no-segments-on-sliced-layers`

Forbid segment folders (`ui`, `model`, `api`, `lib`, `config`) as direct children of sliced layers like `features`, `entities`, `pages`, `widgets`.

These layers must contain only **slices** (domain-meaningful subfolders).

## Examples

✅ Pass:

```
📂 entities/
  📂 user/          # ← this is a slice
    📂 ui/
    📂 model/
```

❌ Fail:

```
📂 entities/
  📂 user/
    📂 ui/
  📂 api/           # ❌ segment sitting directly in a sliced layer
```

## Rationale

The name `api` is conventionally a segment in FSD. When you see it as a direct child of a sliced layer, it's either a poorly named slice (confusing) or code that ended up unsliced (a violation of FSD structure).
