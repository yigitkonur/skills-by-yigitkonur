# init-corpus.sh

Use `scripts/init-corpus.sh` after Phase 0 when the topic slug is known and before Phase 1/2 artifacts need a stable home.

## What It Creates

```bash
bash scripts/init-corpus.sh ai-native-cloud-browsers browserbase anchor-browser
```

Creates:

- the corpus root directory
- root `README.md`
- `_meta/`
- `_meta/manifest.json` (Machine index catalog)
- `_meta/claims.jsonl` (Machine-readable claims ledger)
- `_meta/01-charter.md`
- `_meta/02-entities.md`
- `_meta/03-axes.md`
- `_meta/04-product-template.md`
- `_meta/05-axis-templates.md`
- `_meta/06-file-budget.md`
- `_meta/07-dispatch-log.md`
- `_cross/`
- optional entity directories (`<topic-slug>/<entity-slug>/`)

The script follows the **Dual-Layer Architecture**: it creates directory scaffolding and machine metadata without creating premature evidence files, cross-comparison files, or stub files. Those are populated via wave subagents into consolidated dossiers (`dossier.md` and `sources.md`).

## Slug Rules

`<topic-slug>` and optional entity slugs must be lowercase kebab-case:

```text
ai-native-cloud-browsers
browserbase
anchor-browser
```

Invalid examples:

```text
AI Native Cloud Browsers
anchor_browser
browserbase/
```

## Starter File Policy

Starter files are non-empty and contain phase-specific prompts. They are allowed only under the corpus root and `_meta/` because they guide the workflow. Do not copy this pattern into entity packs or `_cross/` comparison folders; those files must be source-backed and independently useful.

If a starter file already exists, the script leaves it untouched and prints `exists: <path>`.
