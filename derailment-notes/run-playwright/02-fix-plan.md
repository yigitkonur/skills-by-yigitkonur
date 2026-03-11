# Fix Plan: run-playwright

## P0 fixes (must fix)

1. **F-01** — Add invocation-model blockquote to SKILL.md (after intro paragraph)
2. **F-03/F-04** — Update snapshot documentation:
   - SKILL.md step 3: add YAML file + cat pattern
   - selectors.md: replace HTML tree with YAML format
   - selectors.md: update "Inline snapshot" to "YAML file" with cat instructions

## P1 fixes (should fix)

3. **F-02** — Add `install` comment + isolated-session bootstrap to step 1
4. **F-05/F-09** — Expand step 4 command list with keyboard, viewport, uploads, dialogs + summary table
5. **F-06** — Add mousewheel parameter-order warning to screenshots.md
6. **F-07** — Add artifact-inspection callout to step 5
7. **F-10** — Add session-stop note to step 1 cleanup + isolated bootstrap

## P2 fixes (nice to have)

8. **F-08** — Add --clear silent-success note to SKILL.md and debugging.md
9. **F-11** — Add tab-new reliability reason in step 2

## Affected files

| File | Fixes |
|---|---|
| `skills/run-playwright/SKILL.md` | F-01, F-02, F-03, F-05, F-07, F-08, F-09, F-10, F-11 |
| `skills/run-playwright/references/selectors.md` | F-03, F-04 |
| `skills/run-playwright/references/screenshots.md` | F-06 |
| `skills/run-playwright/references/debugging.md` | F-08 |

All fixes applied successfully.
