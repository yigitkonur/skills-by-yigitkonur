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

- manifest-declared icons exist (both dictionary maps and single-string `default_icon` paths).
- PNG icons match their declared manifest sizes when dimensions can be read.
- `manifest.default_locale` is declared and `_locales/*/messages.json` exists and parses when `_locales/` exists.
- broad permissions and host permissions (e.g. `<all_urls>`, `*://*/*`) are surfaced as `REVIEW` lines.
- extension-page CSP does not allow `unsafe-eval` or remote script sources.
- package input does not contain common junk:
  - `.DS_Store`
  - `__MACOSX`
  - tests or `__tests__`
  - `node_modules`, `.git`, or `.github`
- source maps (`.map`) trigger a `REVIEW` notice (strip before upload unless intentionally shipped, or silence with `ALLOW_SOURCE_MAPS=1`).

## Output

Success:

```text
PASS extension package preflight: dist
```

Review-only signal:

```text
REVIEW permission needs review justification: tabs
REVIEW broad host permission needs review justification: https://*/*
REVIEW package input contains source map (strip before upload unless intentionally shipped): app.js.map
PASS extension package preflight: dist
```

Failure:

```text
FAIL icons.16 is not a valid PNG: icons/icon-16.png
FAIL CSP extension_pages script-src allows remote scripts
FAIL package input contains .DS_Store: .DS_Store
```

## Limits

This script is a package sanity preflight, not a Chrome Web Store policy engine. Use it to catch deterministic mistakes before manual review, then complete the Web Store Privacy practices, permission justification, data-use, remote-code, and test-instructions review.
