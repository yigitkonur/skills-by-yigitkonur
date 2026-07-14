# parse-pr-comments.sh

## Purpose

Fetch all GitHub PR feedback channels into a repeatable local snapshot before evaluation:

- PR reviews
- inline review comments
- issue/PR discussion comments

The script is read-only against GitHub. It does not post replies, edit files outside the output directory, apply patches, or mutate git state.

## Arguments

```bash
scripts/parse-pr-comments.sh --repo owner/name --pr N --out DIR
```

| Argument | Required | Meaning |
|---|---|---|
| `--repo owner/name` | yes | GitHub repository. Always explicit; no repo inference. |
| `--pr N` | yes | Pull request number. |
| `--out DIR` | yes | Directory for raw snapshots and normalized JSONL. |
| `--help` | no | Print usage without checking GitHub auth. |

## Output Schema

Writes:

```text
DIR/reviews.raw.json
DIR/inline-comments.raw.json
DIR/discussion-comments.raw.json
DIR/normalized.jsonl
```

Each `normalized.jsonl` line contains:

```json
{
  "channel": "review | inline | discussion",
  "id": "GitHub comment or review id",
  "source": "reviewer login",
  "source_type": "human | bot",
  "path": "file path when available",
  "line": "new-side line when available",
  "original_line": "original line when available",
  "commit_id": "reviewed commit when available",
  "body": "verbatim reviewer text"
}
```

Extra fields such as `created_at` and `review_state` may appear when GitHub provides them.

## Example

```bash
scripts/parse-pr-comments.sh \
  --repo yigitkonur/skills-by-yigitkonur \
  --pr 42 \
  --out /tmp/pr-42-feedback
```

Then cluster:

```bash
scripts/cluster-feedback.py \
  --input /tmp/pr-42-feedback/normalized.jsonl \
  --output /tmp/pr-42-feedback/clusters.json
```

## Failure Modes

- `gh` missing -> exits 127.
- `gh auth status` fails -> exits 1 with an auth message.
- Missing required args -> exits 2 and prints usage.
- GitHub API failure -> exits non-zero from `gh`; keep the partial output directory for inspection.
