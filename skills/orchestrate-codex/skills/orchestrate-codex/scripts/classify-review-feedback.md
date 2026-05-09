# classify-review-feedback.py

Major-vs-minor partition of a `codex exec review` findings JSON file. Exit 0 if ≥ 1 major; exit 1 if no major (round converged).

## Inputs

```bash
python3 classify-review-feedback.py --input <findings.json> --output <classified.json> [--policy <strict|default|loose>]
```

| Arg | Default | Notes |
|---|---|---|
| `--input <path>` | required | The findings JSON from `codex exec review --json -o ...` |
| `--output <path>` | required | Where to write the partitioned `{major[], minor[], counts}` JSON |
| `--policy <name>` | `default` | `strict` (everything ambiguous → major); `default` (ambiguous → major, conservative); `loose` (ambiguous → minor) |

## Outputs

The output JSON:

```json
{
  "policy": "default",
  "counts": {"major": 3, "minor": 7, "ambiguous_promoted_to_major": 1, "total": 10},
  "major": [
    {"file": "src/auth.ts", "line": 42, "severity": "major", "category": "correctness", "body": "...", "suggestion": "..."},
    ...
  ],
  "minor": [
    {"file": "src/util.ts", "line": 11, "severity": "minor", "category": "naming", "body": "..."},
    ...
  ]
}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | At least one major item — the review round needs evaluator decisions |
| 1 | Zero major items — the round is converged |
| 2 | Bad input (missing `--input`, malformed JSON) |

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

Default-when-ambiguous: **major** (conservative). The `default` policy promotes ambiguous items to major and records the count in `counts.ambiguous_promoted_to_major`.

## Behavior

- Read-only: never modifies state.
- Reads `findings.json`, partitions per policy, writes `classified.json`.
- Tolerant of minor schema drift (extra fields preserved; unknown severity values treated as ambiguous).

## Notes

The classifier is mechanical. It runs as a script. Per-item evaluation is the **main agent's** work using `Skill(do-review)` after the classifier produces its `major[]` partition.

If your repo's `CONTRIBUTING.md` or `AGENTS.md` defines a tighter policy (e.g. "naming nits ARE major in this codebase"), pass `--policy strict`. The skill respects repo-local policy.
