# preflight-extension.sh

Run package-readiness checks before zipping a built Chrome MV3 extension for Web Store review.

## Usage

```bash
scripts/preflight-extension.sh [built-extension-dir]
```

Default directory: `dist`.

Run it after the production build and before creating the zip:

```bash
npm run build
scripts/check-mv3-manifest.sh dist
scripts/preflight-extension.sh dist
(cd dist && zip -r ../extension.zip .)
```

## What It Checks

- manifest-declared icons exist.
- PNG icons match their declared manifest sizes when dimensions can be read.
- `_locales/*/messages.json` exists and parses when `_locales/` exists.
- broad permissions and host permissions are surfaced as `REVIEW` lines.
- extension-page CSP does not allow `unsafe-eval` or remote script sources.
- package input does not contain common junk:
  - `.DS_Store`
  - `__MACOSX`
  - source maps
  - tests or `__tests__`
  - `node_modules`, `.git`, or `.github`

## Output

Success:

```text
PASS extension package preflight: dist
```

Review-only signal:

```text
REVIEW permission needs review justification: tabs
REVIEW host permission needs review justification: https://*/*
PASS extension package preflight: dist
```

Failure:

```text
FAIL icons.16 is not a valid PNG: icons/icon-16.png
FAIL CSP script-src allows remote scripts
FAIL package input contains source map: app.js.map
```

## Limits

This script is a package sanity preflight, not a Chrome Web Store policy engine. Use it to catch deterministic mistakes before manual review, then complete the Web Store Privacy practices, permission justification, data-use, remote-code, and test-instructions review.
