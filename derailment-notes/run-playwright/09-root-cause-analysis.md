# Root Cause Analysis

## Distribution

| Code | Count | Pct | Description |
|---|---|---|---|
| M4 | 3 | 27% | Missing prerequisite knowledge |
| S3 | 3 | 27% | Missing or incorrect specification |
| O2 | 3 | 27% | External tool behavior mismatch |
| M1 | 1 | 9% | Missing step |
| S2 | 1 | 9% | Contradiction between documents |

## Systemic pattern

Three structural changes fix 9 of 11 friction points:

1. **Add invocation model callout** — fixes F-01 (P0) and sets foundation for all commands
2. **Add command summary table** — fixes F-05, F-09 (P1) and makes all commands discoverable
3. **Update snapshot documentation** — fixes F-03, F-04, F-07 (P0+P1) and explains artifact pattern

The remaining 2 fixes (F-06 mousewheel, F-08 --clear) are external-tool quirks that
need documentation but don't reflect structural skill issues.

## Key insight

The skill was written for someone who already knows playwright-cli's invocation model
and output patterns. The friction is concentrated at the boundary between "reading
instructions" and "executing the first command" — a classic M4 (missing prerequisite)
pattern.
