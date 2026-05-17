# extract-styles.sh

Use `scripts/extract-styles.sh` at the start of Wave 0 to make the page CSS corpus explicit before token extraction or Tailwind re-expression.

## Inputs

```bash
scripts/extract-styles.sh --html ./source-pages/pricing.html --asset-root ./source-pages/pricing_files
```

Options:

| Option | Required | Purpose |
|---|---:|---|
| `--html` | yes | Main page HTML or captured `dom.html` |
| `--asset-root` | yes | `_files/`, mirrored `capture/{route}/mirror/`, or snapshot directory |
| `--out` | no | Output directory; defaults to `.design-soul/wave0/{page}/style-corpus` |

## Detection Order

The script includes every CSS file it can prove belongs to the page:

1. `{page}_files/**/*.css`
2. local stylesheets referenced by `<link href="...css">`
3. mirrored live-capture CSS under `{asset_root}/css`
4. any CSS under `{asset_root}`
5. inline `<style>` blocks extracted to `inline-styles.css`

Remote stylesheet URLs are not downloaded here. Capture or Wave 0 must mirror them first so provenance and permission can be recorded.

## Outputs

| File | Purpose |
|---|---|
| `css-corpus-manifest.json` | CSS file paths, sizes, hashes, and detection reasons |
| `css-files.txt` | Plain list of corpus CSS files for downstream grep commands |
| `inline-styles.css` | Extracted inline styles when present |
| `custom-properties.txt` | Extracted CSS custom property declarations |
| `font-summary.txt` | `@font-face`, font families, font URLs, and `font-display` declarations |
| `media-queries.txt` | Unique `@media` conditions |
| `keyframes.txt` | Unique `@keyframes` names |

## Failure Rules

If no CSS corpus can be found, the script writes a manifest with `status: "no-css-corpus-found"` and exits nonzero. Do not proceed to token extraction from an empty corpus.
