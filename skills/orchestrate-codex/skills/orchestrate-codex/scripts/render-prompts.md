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
- Stderr summary: `wrote N prompt files; first: <output-dir>/<first-slug>.md`.

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

If two inputs render to the same slug, the script writes a stderr warning and **skips the second**:

```
WARN: slug collision 'foo-bar' on row 17 — keeping row 4; row 17 dropped
```

Disambiguate the input (add a discriminator) before re-rendering, or you'll lose work silently. The script does not auto-resolve collisions.

## Substitution

The template's `XXXXXXXXXXXXX` placeholder (13 X's) is replaced by the input row's content. The substitution is literal — no regex, no backslash interpretation. Implementation uses `awk` with `ENVIRON["CONTENT"]` to carry the substitution safely across special characters.

## Notes

The placeholder is intentionally distinctive (13 X's) to avoid colliding with template prose. If your template legitimately contains 13 X's in a row, the subagent broke the world; pick a different placeholder and update both the template and this script.
