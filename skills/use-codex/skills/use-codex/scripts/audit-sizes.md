# audit-sizes.sh

Post-batch quality audit. Prints byte-size distribution, bottom decile, below-floor flags. Read-only.

## Inputs

Two invocation shapes. The manifest-aware shape is preferred for any run dispatched through `node scripts/use-codex.mjs batch` because it picks up the dispatcher's `--answers-dir <override>` automatically; the positional shape is preserved for direct/standalone use.

```bash
# Manifest-aware (preferred; reads answers_dir + runner_log_path from manifest):
bash audit-sizes.sh --manifest <manifest.json> [<min-bytes>]

# Positional (back-compat; no manifest knowledge):
bash audit-sizes.sh <answers-dir> [<runner-log>] [<min-bytes>]
```

| Arg | Default | Notes |
|---|---|---|
| `--manifest <path>` | unset | Read `answers_dir` from the manifest's top-level field (or derive from `entries[].answer_path`); read `runner_log` from `paths.runner_log` or `<monitor_root>/logs/<run_id>/_runner.log`. Override avoids the silent-failure path where `--answers-dir custom/` lands outputs at `<cwd>/custom/<slug>.md` but the audit defaults to `./answers/` and reports zero outputs. |
| `<answers-dir>` | `./answers` (env: `ANSWERS`) | Directory containing per-input answer files. Ignored when `--manifest` is set. |
| `<runner-log>` | `./logs/_runner.log` (env: `LOG`) | Optional; for cross-checking DONE/FAIL/SKIP counts. When the dispatcher manages the run, the runner stdout is redirected to `${monitor_root}/logs/<run_id>/_runner.log` — point `LOG=` at that path or use `--manifest` to resolve it automatically. |
| `<min-bytes>` | 10000 (env: `MIN_BYTES`) | Absolute floor for `[BELOW-FLOOR]` flag. With `--manifest`, the FIRST positional becomes `<min-bytes>` (since `--manifest` already provides answers-dir + runner-log). |

## Outputs

stdout (human-readable table):

```
$ audit-sizes.sh answers/

Total entries:    50
DONE:             47
FAIL:             2
SKIP:             1

Size distribution (smallest first):
  50 bytes      tiny.md
  4231 bytes    foo.md            [BELOW-FLOOR]
  4500 bytes    bar.md            [BELOW-FLOOR]
  ...
  18234 bytes   biggest.md

Bottom decile (5 entries):
  tiny.md         50 bytes        [BELOW-FLOOR] [BOTTOM-DECILE]
  foo.md          4231 bytes      [BELOW-FLOOR] [BOTTOM-DECILE]
  bar.md          4500 bytes      [BELOW-FLOOR] [BOTTOM-DECILE]
  baz.md          5500 bytes      [BELOW-FLOOR] [BOTTOM-DECILE]
  qux.md          6000 bytes      [BELOW-FLOOR] [BOTTOM-DECILE]

Min:    50 bytes
Median: 12000 bytes
Max:    18234 bytes
Below floor (<10000): 5 entries
Recommended: inspect bottom-decile manually before deciding to retry
```

Or with `--json`:

```json
{
  "total": 50,
  "done": 47,
  "fail": 2,
  "skip": 1,
  "min_bytes": 10000,
  "stats": {"min": 50, "median": 12000, "max": 18234},
  "below_floor": ["tiny.md", "foo.md", "bar.md", "baz.md", "qux.md"],
  "bottom_decile": ["tiny.md", "foo.md", "bar.md", "baz.md", "qux.md"]
}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Audit ran cleanly |
| 1 | `<answers-dir>` missing |
| 2 | `--manifest` path missing / unreadable / lacks `answers_dir` and entries |

## Behavior

- Read-only: never modifies any file.
- Bottom decile = `ceil(N / 10)` smallest files (always at least 1 if any exist).
- `[BELOW-FLOOR]` flag for files smaller than `<min-bytes>`.
- Files can have both flags simultaneously; the report shows them.

## Notes

Size is a probabilistic quality screen, not a deterministic verdict. Always read the head of any flagged file before deciding to retry. See `references/universal/output-size-signals.md` for the heuristics.

Per-entry overrides via `manifest.entries[i].mode_state.min_bytes` (set per-prompt floor) are read by the runner, not by this audit. The audit uses a single global `<min-bytes>` for the comparison.
