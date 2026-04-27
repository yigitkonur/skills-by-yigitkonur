# classify-review-feedback.py

Apply the major-vs-minor policy to a normalized Codex review JSON. Single arbiter of "loop again vs DONE" — the per-branch loop calls this every round and decides on the exit code.

## Usage

```bash
python3 scripts/classify-review-feedback.py --review-json <path>
python3 scripts/classify-review-feedback.py --review-json <path> --policy <path>
python3 scripts/classify-review-feedback.py --review-json <path> --json
```

## Inputs

A normalized review JSON file as written by `run-codex-review.py`. Schema in `references/codex-review-contract.md`.

## Behavior

For each item in `review.items[]`:

1. **Severity short-circuit**: if `severity_raw` is in the major set (`critical`, `high`, `error`, `blocker`, `must-fix`) → major; if in the minor set (`low`, `info`, `style`, `nit`, `polish`, `optional`) → minor; else fall through to keyword scan.
2. **Keyword scan** over `item.body` (case-insensitive regex). Count distinct major triggers, count distinct minor triggers.
3. **Decide**: more major triggers → major. More minor triggers → minor. Both zero → unclassified→major. Tie with both > 0 → major (conservative).

When `items[]` is empty (Codex emitted unstructured text), the script falls back to scanning `raw_text` as a single virtual item.

Output partitions: `major[]`, `minor[]`, `unclassified_treated_as_major[]`.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--review-json <path>` | required | Path to the normalized review JSON. |
| `--policy <path>` | (built-in) | Override the default policy via a JSON file. |
| `--json` | off | Emit machine-readable JSON instead of the human report. |

## Policy overrides

`policy.json` schema:

```json
{
  "promote_to_major": ["naming", "rename"],
  "demote_to_minor": [],
  "additional_major_triggers": ["my-custom-keyword"],
  "additional_minor_triggers": []
}
```

- `promote_to_major`: keywords that should classify as major (also removed from the minor list if present).
- `demote_to_minor`: keywords that should classify as minor (also removed from the major list if present).
- `additional_*_triggers`: extras added without removing from the other list.

If `--policy` is omitted (or the file is absent), the defaults from `references/major-vs-minor-policy.md` apply.

## Exit codes

| Code | Meaning | Caller action |
|---|---|---|
| `0` | ≥1 major item (major or unclassified-treated-as-major) | Continue loop. |
| `1` | No major items | Mark branch DONE. |
| `2` | Fatal parse error (malformed input JSON) | Subagent retries the round (max 3); else FAILED. |

The exit-code contract is the canonical signal for the per-branch loop. Don't infer DONE from the JSON output; trust the exit code.

## When to run

Per round, after `run-codex-review.py` writes the round JSON. Once. The same JSON should produce the same classification deterministically.

## Safety

Read-only. Never mutates the repo, the manifest, or the round logs. Only opens the review JSON for reading.

## Sample output (text mode)

```
branch:        feat/foo
review:        cdx-job-abc123
head:          deadbeef1234...
summary:       4 total  (1 major, 2 minor, 1 unclassified→major)

MAJOR (1):
  • [high] src/foo.ts:42  Off-by-one in slice() — drops the last element

UNCLASSIFIED → MAJOR (1):
  • [unknown] src/bar.ts:88  This might be racey under heavy load.

minor (2):
  • [nit] src/foo.ts:10  Trailing whitespace
  • [low] src/foo.ts:30  Consider renaming `tmp` to `pendingResult`

→ continue loop (≥1 major)
```

## Tuning the policy

If the same minor-y item keeps surfacing as `unclassified_treated_as_major`, edit `references/major-vs-minor-policy.md` to add it to the minor list, then mirror the change in this script's `DEFAULT_MINOR_TRIGGERS` constant. Don't bypass per branch — the policy is repo-wide.

## Extending

- To add a per-line pattern (e.g. file extension blocklist), edit `classify_item()`.
- To support a new severity vocabulary (e.g. Codex starts emitting `severity_raw: "P0"`), update `SEVERITY_MAJOR` / `SEVERITY_MINOR`.
- To emit structured stats for monitoring, run with `--json` and pipe into your dashboard.
