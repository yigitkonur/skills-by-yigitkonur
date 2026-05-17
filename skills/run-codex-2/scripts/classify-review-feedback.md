# classify-review-feedback.py

Major-vs-minor partition of a `codex exec review` findings JSON file. Exit 0 if ≥ 1 major; exit 1 if no major (round converged).

## Inputs

```bash
python3 classify-review-feedback.py --review-json <findings.json> [--output <classified.json>] [--policy <policy.json>] [--json] [--quiet]
```

`--input` is accepted as an alias for `--review-json`; `--out` is accepted as an alias for `--output`.

| Arg | Default | Notes |
|---|---|---|
| `--review-json <path>` (alias: `--input`) | required | The findings JSON from `codex exec review --json -o ...` (or any normalized findings doc with `items[]` or `findings[]`) |
| `--output <path>` (alias: `--out`) | none | Optional. Writes the partitioned `{major[], minor[], counts}` JSON to disk |
| `--policy <path>` | builtin | Path to policy.json overrides (`promote_to_major`, `demote_to_minor`, `additional_major_triggers`, `additional_minor_triggers`) |
| `--json` | text | Emit the partition JSON on stdout instead of a human table |
| `--quiet` | off | Suppress stdout entirely (useful with `--output`) |

## Outputs

The output JSON shape:

```json
{
  "review_id": "...",
  "branch": "feat/auth",
  "round": 1,
  "summary": {"total": 10, "major_n": 3, "minor_n": 6, "unclassified_n": 1},
  "counts": {"major": 4, "minor": 6, "ambiguous_promoted_to_major": 1},
  "major": [{"file": "src/auth.ts", "line": 42, "severity_raw": "major", "body": "..."}, ...],
  "minor": [{"file": "src/util.ts", "line": 11, "severity_raw": "minor", "body": "..."}, ...],
  "unclassified_treated_as_major": [...]
}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | At least one major item (or unclassified→major) — the review round needs evaluator decisions |
| 1 | Zero major items — the round is converged |
| 2 | Bad input (missing `--review-json`, malformed JSON, output write failure) |

## Major vs minor policy

Loop on (major):
- correctness bugs in the changed code
- runtime stability regressions
- data integrity hazards
- security regressions
- regressions of existing behavior
- hygiene that hides bugs
- branch-structure issues that block reviewability

Do not loop on (minor):
- formatting, naming preferences, style nits
- doc-only polish
- speculative perf
- scope creep

Default-when-ambiguous: **major** (conservative). Ambiguous items are promoted to major and recorded under `counts.ambiguous_promoted_to_major` and in `unclassified_treated_as_major[]`.

The classifier reads `severity_raw` / `severity` first; when missing or unknown, scans `title` + `body`/`message`/`description` against a built-in trigger list (overridable via `--policy`).

## Behavior

- Read-only on the worktree: never modifies tracked state.
- Reads the review JSON, partitions per policy.
- With `--output`, writes the classified JSON to disk; otherwise prints to stdout.
- Tolerant of minor schema drift (extra fields preserved; unknown severity values treated as ambiguous).

## Notes

The classifier is mechanical. It runs as a script. Per-item evaluation is the **main agent's** work using `Skill(review-pr)` after the classifier produces its `major[]` partition.

If your repo's `CONTRIBUTING.md` or `AGENTS.md` defines a tighter policy (e.g. "naming nits ARE major in this codebase"), supply a `--policy <path>` JSON with `promote_to_major: ["naming"]`. The skill respects repo-local policy.
