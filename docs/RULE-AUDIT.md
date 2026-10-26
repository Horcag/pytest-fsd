# Complete rule audit — 0.7.0

Audit date: 2026-10-26. Scope: every implemented rule, configuration dispatch,
source inspection and dynamic-import guards. This is the Python package's
contract, including its documented differences from Steiger.

## Evidence that checks actually run

`tests/rule_contracts.py` contains an explicit inventory of all 12 core rules,
five opt-in rules and two input guards. Each has a clean project and a project
that violates only that named check. Both the direct checker and the public
`validate_fsd_architecture` facade must produce the expected result. Every
opt-in rule is also tested disabled. Inventory drift fails a test.

`tests/test_rule_contracts.py` also substitutes a no-op for each of the 17 rule
implementations, disconnects each of the 12 core and five extra dispatches,
and disables each of the two input guards. All 36 mutations must be detected
by the witnesses. An unrelated failure cannot satisfy a witness: diagnostics
must identify the intended rule and no other audited check.

CI builds a wheel and source distribution on Python 3.8–3.14. It runs
`python -I tests/rule_contracts.py VERSION` against the installed wheel outside
the source import path. All 19 named contracts must execute; the same portable
matrix is used for post-publication acceptance.

## Validation snapshot

The release audit contains 669 pytest cases on Python 3.11 and newer, including
36 mutation controls. Three language-version-specific cases are skipped on
Python 3.8/3.9 and one on Python 3.10. The installed-package matrix executes all
19 named contracts on every supported interpreter; none of those contracts is
skipped. Static validation includes Python 3.8 grammar, Ruff's error/undefined-
name checks and whitespace validation.

## Rule inventory and adversarial cases

| Check | Scope and audit cases | Focused regressions |
|---|---|---|
| `forbidden-imports` | Layer ordering, package and module targets, absolute/relative/dynamic imports, prefixed layers, nested roots, permitted downward imports | `test_import_validation.py`, `test_dynamic_imports.py`, `test_import_rule_audit.py` |
| `no-cross-imports` | Public-package and internal sibling imports, every sliced layer, own-slice and App/Shared controls; one diagnostic per sibling/location | `rules/test_no_cross_imports.py`, import suites |
| `no-public-api-sidestep` | Slice and Shared segment/library/component boundaries, explicit exports, same-boundary controls, standalone library/UI modules, relative and dynamic paths, source-root recommendations | `rules/test_no_public_api_sidestep.py`, `test_import_rule_audit.py` |
| `no-layer-public-api` | Sliced-layer API files, App/Shared exemption, directory named `__init__.py`, custom/prefixed layers and source roots | `rules/test_no_layer_public_api.py` |
| `no-ui-in-app` | App/UI folder and GUI framework imports, relative lookalikes, aliases/dynamic imports, non-App controls | `rules/test_no_ui_in_app.py`, dynamic/import audit suites |
| `repetitive-naming` | Exact slice name and underscore-prefix filename matches, nonmatching names, recursive metadata pruning and private packages | `rules/test_repetitive_naming.py` |
| `no-segmentless-slices` | All five standard segments as folders or files; nested-only, missing and fake segment types; custom roots/layers and private packages | `rules/test_no_segmentless_slices.py` |
| `segments-by-purpose` | All 50 banned names as directories and Python files, permitted purpose names, depth and App/Shared scope | `rules/test_segments_by_purpose.py` |
| `ambiguous-slice-names` | Collisions with Shared segment and immediate child names, deeper/nonmatching controls, metadata and private packages | `rules/test_ambiguous_slice_names.py` |
| `no-segments-on-sliced-layers` | Every direct standard segment folder, valid nested segments, App/Shared exemption, custom/prefixed layers and roots | `rules/test_no_segments_on_sliced_layers.py` |
| `public-api` | Missing and fake API files; private slices and Shared packages; intentional Shared/UI/lib root exception and immediate child APIs | `rules/test_public_api.py` |
| `typo-in-layer-name` | Unknown and configured layers, explicit top-level ignores, metadata exclusion and legitimate underscore directories | `rules/test_typo_in_layer_name.py` |
| `excessive-slicing` (opt-in) | 19/20/21 real slices, files and metadata do not count, private slices count, App/Shared exemption | `rules/test_excessive_slicing.py` |
| `shared-lib-grouping` (opt-in) | 14/15/16 loose Python files; APIs, subdirectories and non-Python files do not count; private Python modules count | `rules/test_shared_lib_grouping.py` |
| `no-file-segments` (opt-in) | Direct Python files in slices and App/Shared; real directories ending `.py` are not file segments; private packages | `rules/test_no_file_segments.py` |
| `no-reserved-folder-names` (opt-in) | All reserved names nested inside standard/custom segments, recursion and metadata/private-package behavior, App exemption | `rules/test_no_reserved_folder_names.py` |
| `no-wildcard-exports` (opt-in) | Public API wildcard syntax, nested APIs, dynamic fromlists/exec, named-import and internal-file controls; encoding/error locations | `rules/test_no_wildcard_exports.py`, dynamic/import audit suites |
| `python-source` guard | Missing/unreadable roots, invalid syntax/encoding, parser recursion, symlinks, layer file traps and metadata exclusions | `test_validation_inputs.py`, `test_audit_guards.py` |
| `dynamic-imports` guard | Unknown targets/fromlists/packages/code, escaped loaders, scope/branch handling, recursive expansion limits and no source execution | `test_dynamic_imports.py`, `test_audit_guards.py` |

Test paths in this table are relative to `tests/`. All rules additionally have
portable positive/negative facade and installed-wheel witnesses.

## Defects corrected

- Broad underscore exclusions let real `_private`/`__private` packages escape
  structural and naming checks. Other traversals counted hidden/cache folders
  as slices, collisions or recursively inspected source. All directory scans
  now share the same metadata policy.
- `no-file-segments` treated directories ending `.py` as files;
  `no-layer-public-api` treated a directory named `__init__.py` as an API file.
- Public API sidestep detection excluded every Shared target and inspected
  unconfigured source directories. Shared boundary checks now match the API
  presence rule; off-scope and metadata sources are excluded consistently.
- Mutable export-list aliases, opaque calls and called local mutators could
  leave stale `__all__` values trusted. Such exports are now unknown until a
  fresh static declaration restores knowledge.
- From-import package/child expansion emitted identical sibling diagnostics.
  Sibling violations are deduplicated without losing different siblings.
- Unreadable root enumeration, malformed `[tool]` values and parser recursion
  did not have consistent explicit validation errors. Reserved `__pycache__` cannot be configured as a layer that normal scans would skip.

Focused regressions were observed failing before their fixes. Threshold rules
and other paths that already met their contract were retained and given
additional positive/negative coverage.

## Reference pages are not registered checks

`inconsistent-naming`, `import-locality`, `insignificant-slice`, and
`no-processes` are documentation-only pages, not executable rule modules.
Attempting to enable any of them as an extra rule raises `ValueError`; they
cannot silently appear enabled. Ruff naming/import restrictions do not provide
the same FSD pluralization or slice-locality semantics. An unlisted `processes`
directory is caught by the unknown-layer rule unless explicitly ignored.

The audit does not turn semantic recommendations (for example, deciding whether
code is business logic) into implemented checks. The library inspects configured
Python architecture; it does not execute arbitrary Python or user import hooks.
