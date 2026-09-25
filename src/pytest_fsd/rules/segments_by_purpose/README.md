# `segments-by-purpose`

FSD segment names should describe their purpose (`ui`, `model`, `api`, `lib`, `config`) rather than the kind of item inside them. The check covers direct children of slices and direct children of `shared`; it also checks `.py` files acting as segments.

```text
src/features/auth/validators/  # violation
src/features/auth/fixtures.py  # violation
src/features/auth/model/       # allowed
```

The forbidden names include generic names from [Steiger FSD plugin 0.7.0](https://github.com/feature-sliced/steiger/blob/master/packages/steiger-plugin-fsd/src/segments-by-purpose/index.ts), such as `components`, `helpers`, `utils`, `types`, `services`, `stores`, `schemas`, `handlers`, `fixtures`, `middlewares`, `validators`, `resolvers`, `mutations`, and `assets`, including their singular forms. The existing Python port also checks `hook(s)` and `container(s)`. Framework-specific JavaScript terms are not all copied into this Python rule.

A `fixtures` directory outside the configured FSD layers is not checked.
