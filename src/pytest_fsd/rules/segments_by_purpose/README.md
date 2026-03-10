# `segments-by-purpose`

Discourage the use of segment names that group code by its essence, and instead encourage grouping by purpose.

## Banned segment names

`utils`, `util`, `helpers`, `helper`, `hooks`, `hook`, `modals`, `modal`, `components`, `component`, `types`, `type`, `interfaces`, `interface`, `containers`, `container`, `services`, `service`, `constants`, `consts`, `const`

## Examples

✅ Pass:

```
📂 shared/
  📂 ui/
  📂 lib/
📂 entities/
  📂 user/
    📂 ui/
    📂 model/
```

❌ Fail:

```
📂 shared/
  📂 utils/       # ❌
  📂 helpers/     # ❌
  📂 hooks/       # ❌
📂 entities/
  📂 user/
    📂 components/ # ❌
    📂 model/
```

## Rationale

Segments group code by **technical purpose**. Folder names like `components` sound like they only contain UI components, but there are other things that affect UI (formatters, browser API hooks, etc.) that share the same purpose. `hooks` is an abstract concept — it doesn't tell anything about what the function does. `utils` and `helpers` risk becoming a dumping ground for unrelated code.
