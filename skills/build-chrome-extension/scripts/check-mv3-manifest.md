# check-mv3-manifest.sh

Validate that a built Chrome extension directory contains a loadable Manifest V3 manifest.

## Usage

```bash
scripts/check-mv3-manifest.sh [built-extension-dir]
```

Default directory: `dist`.

Framework examples:

```bash
scripts/check-mv3-manifest.sh .output/chrome-mv3-dev
scripts/check-mv3-manifest.sh .output/chrome-mv3
scripts/check-mv3-manifest.sh build/chrome-mv3-prod
scripts/check-mv3-manifest.sh dist
```

## What It Checks

- `manifest.json` exists and parses as JSON.
- `manifest_version` is exactly `3`.
- required `name` and `version` fields exist.
- MV2-only `background.scripts` is absent.
- manifest-referenced files exist in the built output:
  - `background.service_worker`
  - popup/options/side-panel/devtools pages
  - content-script JS/CSS files
  - declared icons
  - declarativeNetRequest rules
  - concrete web-accessible resource paths
- `web_accessible_resources` glob patterns such as `images/*` or `*.png` are allowed.
- manifest paths do not point at obvious source-only files such as `src/*.ts`.
- extension-page CSP does not allow `unsafe-eval` or remote script sources.
- manifest does not reference remote `.js` / `.mjs` files.

The script also emits `WARN` lines for broad `<all_urls>` permissions so the final report can include permission justifications.

## Output

Success:

```text
PASS MV3 manifest checks: dist/manifest.json
```

Failure:

```text
FAIL manifest_version must be 3
FAIL background.scripts is MV2-only; use background.service_worker
FAIL action.default_popup missing: src/popup/index.html
```

## Limits

This is a deterministic sanity check, not a complete Chrome validator. Still manually load the built directory in `chrome://extensions` for behavior that only Chrome can prove.
