# render-prompts.sh

Template substitution: input file + template file → one prompt file per input row.

## Inputs

```bash
bash render-prompts.sh <inputs-file> <template-file> <output-dir>
```

| Arg | Notes |
|---|---|
| `<inputs-file>` | Tab-delimited (`name<TAB>content`) OR plain lines. |
| `<template-file>` | Markdown template containing the placeholder `XXXXXXXXXXXXX`. |
| `<output-dir>` | Directory to write `<slug>.md` files into. Created if missing. |

## Outputs

- One file `<output-dir>/<slug>.md` per input row.
- Stdout summary: `rendered: N file(s) into <output-dir>`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Render succeeded |
| 1 | I/O error (missing inputs / template; output dir not writable) |
| 2 | Usage error (wrong number of args) |

## Slug derivation

- Tab-delimited input: `name` becomes the slug (lowercased, sanitized to `[a-z0-9-]`).
- Plain-line input: the whole line becomes both the slug and the substituted content. Sanitization same as above.

## Slug collisions

If two inputs render to the same slug, the script writes an error and exits non-zero:

```
error: collision on foo-bar.md (line 17); disambiguate input
```

Disambiguate the input before re-rendering. The dispatcher treats collisions as preflight failures.

## Substitution

The template's `XXXXXXXXXXXXX` placeholder (13 X's) is replaced by the input row's content. The substitution is literal — no regex, no backslash interpretation. Implementation uses `awk` with `ENVIRON["CONTENT"]` to carry the substitution safely across special characters.

## Notes

The placeholder is intentionally distinctive (13 X's) to avoid colliding with template prose. If your template legitimately contains 13 X's in a row, the subagent broke the world; pick a different placeholder and update both the template and this script.

### Two slug spaces (bash render vs dispatcher batch)

Two callers produce prompt slugs and they intentionally use different shapes:

- **`render-prompts.sh` (this script)** produces **bare slugs** — whatever the
  input row sanitises to (`hello.md`, `feat-auth.md`, `01-foo.md` if the user
  numbered them). No automatic numeric prefix. The first occurrence wins on
  collision.
- **The dispatcher's batch path** (`run-codex-2.mjs` → `buildBatchEntries`)
  produces `NNN-<slug>.md` per row, where `NNN` is the input row index zero-padded
  to 3 digits (`001-foo.md`, `002-bar.md`, …). This guarantees a stable order
  and avoids collisions even on identical inputs.

Don't try to unify them — they serve different callers. If you mix the two
runtimes against the same `prompts/` directory, the run-batch.sh idempotent
skip-existing guard treats files identically by basename, which means a
re-render with the alternate prefix style produces twice the artefacts.
