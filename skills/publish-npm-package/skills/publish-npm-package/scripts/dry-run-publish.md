# dry-run-publish.sh

Run publish dry-runs without publishing for real.

## Usage

```bash
bash scripts/dry-run-publish.sh [package-dir]
bash scripts/dry-run-publish.sh [package-dir] --publish --access public
```

## Behavior

- always runs `npm pack --dry-run`
- runs `npm publish --dry-run` only when `--publish` is passed
- accepts an optional package directory
- never runs a real `npm publish`

Use this after `check-package-json.mjs` and before enabling a release workflow.
