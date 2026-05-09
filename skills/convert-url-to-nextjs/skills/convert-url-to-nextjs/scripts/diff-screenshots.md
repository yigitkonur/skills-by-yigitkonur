# diff-screenshots.sh

Use `scripts/diff-screenshots.sh` in Wave 4 to make visual QA artifacts repeatable and machine-readable.

## Explicit Pair

```bash
scripts/diff-screenshots.sh \
  --route homepage \
  --viewport desktop-full \
  --source .design-soul/visual/homepage/source-desktop-full.png \
  --build .design-soul/visual/homepage/build-desktop-full.png
```

## Paired Directories

```bash
scripts/diff-screenshots.sh \
  --route homepage \
  --source-dir .design-soul/visual/homepage/source \
  --build-dir .design-soul/visual/homepage/build \
  --threshold 0.02
```

Directory mode pairs:

- `source-desktop-full.png` with `build-desktop-full.png`
- otherwise, same basename in both directories

## Outputs

The script writes `.design-soul/visual/{route}/summary.json` unless `--out` is supplied.

Each pair entry includes:

- `route`
- `viewport`
- `sourceScreenshot`
- `buildScreenshot`
- `diffArtifact` when ImageMagick produced one
- `comparatorAvailable`
- `measuredMetric`
- `knownDrift`
- `status`
- `pass`

## Comparator Behavior

- Uses `magick compare -metric RMSE` when available.
- Falls back to `compare -metric RMSE` when available.
- If neither command exists, writes `comparatorAvailable: false` and `status: "missing-comparator"` without inventing a metric.
- Missing required image pairs always exit nonzero.

`--threshold` is optional. Without it, the script records measured metrics but does not turn them into a pass/fail gate.
