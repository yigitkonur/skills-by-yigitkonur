# init-corpus.sh

Use `scripts/init-corpus.sh` after Phase 0 when the topic slug is known and before Phase 1/2 artifacts need a stable home.

## What It Creates

```bash
bash scripts/init-corpus.sh ai-native-cloud-browsers browserbase anchor-browser
```

Creates:

- the corpus root directory
- `_meta/`
- root `README.md`
- `_meta/research-plan.md`
- `_meta/methodology-and-source-policy.md`
- `_meta/discovered-entities.md`
- `_meta/file-budget.md`
- `_meta/_PRODUCT_TEMPLATE.md`
- `_meta/_COMPARISON_TEMPLATE.md`
- `_cross-product/09-sources/`
- optional entity directories and their `09-sources/` directories

The script does not create entity evidence files, cross-comparison content files, claims ledgers, source maps, or profile pages. Those require source-backed research in later phases.

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

Starter files are non-empty and contain phase-specific prompts. They are allowed only under the corpus root and `_meta/` because they guide the workflow. Do not copy this pattern into entity packs or `_cross-*` comparison folders; those files must be source-backed and independently useful.

If a starter file already exists, the script leaves it untouched and prints `exists: <path>`.
