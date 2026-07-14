# cluster-feedback.py

## Purpose

Prepare normalized review feedback for code verification. The script clusters nearby file/line comments, deduplicates repeated text fingerprints, classifies source types, normalizes severity labels into hints, and assigns stable IDs.

It does not assign final ACCEPT / PUSHBACK / CLARIFY / DEFER / DISMISS verdicts. Verdicts require code verification by the agent.

## Arguments

```bash
scripts/cluster-feedback.py --input normalized.jsonl --output clusters.json
```

| Argument | Required | Meaning |
|---|---|---|
| `--input normalized.jsonl` | yes | JSONL from `parse-pr-comments.sh` or an equivalent source. |
| `--output clusters.json` | yes | Structured cluster output. |
| `--help` | no | Print usage. |

## Input Schema

Each JSONL line should include:

```json
{
  "channel": "review | inline | discussion",
  "id": "comment id",
  "source": "reviewer name or bot name",
  "source_type": "human | bot | self-review | markdown doc",
  "path": "file path or null",
  "line": 42,
  "original_line": 42,
  "commit_id": "sha or null",
  "body": "verbatim reviewer text"
}
```

Missing `source_type` is inferred from the source name when possible.

## Output Schema

`clusters.json` contains:

```json
{
  "generated_by": "cluster-feedback.py",
  "cluster_rule": "same path and line within +/-5; pathless comments grouped by content fingerprint",
  "verdict_policy": "no final verdicts assigned",
  "clusters": [
    {
      "id": "CR-001",
      "location": {"path": "src/auth.ts", "start_line": 40, "end_line": 45},
      "concern": "null-check-user",
      "source_types": ["bot", "human"],
      "sources": [{"source": "copilot-pull-request-reviewer", "source_type": "bot"}],
      "severity_hints": ["important"],
      "dedupe_groups": [{"dedupe_key": "add-null-check", "item_ids": ["CR-001-01"]}],
      "items": [
        {
          "id": "CR-001-01",
          "channel": "inline",
          "comment_id": 123,
          "source": "copilot-pull-request-reviewer",
          "source_type": "bot",
          "path": "src/auth.ts",
          "line": 42,
          "original_line": 42,
          "commit_id": "abc123",
          "severity_hint": "important",
          "body": "verbatim reviewer text"
        }
      ],
      "final_verdict": null
    }
  ]
}
```

## Example

```bash
scripts/cluster-feedback.py \
  --input /tmp/pr-42-feedback/normalized.jsonl \
  --output /tmp/pr-42-feedback/clusters.json
```

## Failure Modes

- Invalid JSONL -> exits non-zero with the failing line number.
- Missing input file -> Python file error; rerun capture or pass the correct path.
- Pathless comments -> grouped by content fingerprint rather than file/line.
- Repeated bot labels -> preserved as independent signals; never converted into final verdict votes.
