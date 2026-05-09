#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: parse-pr-comments.sh --repo owner/name --pr N --out DIR

Fetch GitHub PR review feedback into raw snapshots and normalized JSONL.

Required:
  --repo owner/name   GitHub repository, always explicit
  --pr N             Pull request number
  --out DIR          Output directory for snapshots

Outputs:
  reviews.raw.json
  inline-comments.raw.json
  discussion-comments.raw.json
  normalized.jsonl
EOF
}

repo=""
pr=""
out_dir=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --pr)
      pr="${2:-}"
      shift 2
      ;;
    --out)
      out_dir="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$repo" ] || [ -z "$pr" ] || [ -z "$out_dir" ]; then
  echo "error: --repo, --pr, and --out are required" >&2
  usage >&2
  exit 2
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI is required" >&2
  exit 127
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "error: gh auth status failed; run gh auth login before fetching PR feedback" >&2
  exit 1
fi

mkdir -p "$out_dir"

reviews_raw="$out_dir/reviews.raw.json"
inline_raw="$out_dir/inline-comments.raw.json"
discussion_raw="$out_dir/discussion-comments.raw.json"
normalized="$out_dir/normalized.jsonl"

gh pr view "$pr" --repo "$repo" --json reviews > "$reviews_raw"
gh api "repos/$repo/pulls/$pr/comments" --paginate --slurp > "$inline_raw"
gh api "repos/$repo/issues/$pr/comments" --paginate --slurp > "$discussion_raw"

python3 - "$reviews_raw" "$inline_raw" "$discussion_raw" "$normalized" <<'PY'
import json
import sys

reviews_path, inline_path, discussion_path, out_path = sys.argv[1:5]

BOT_MARKERS = (
    "[bot]",
    "bot",
    "coderabbit",
    "copilot",
    "cubic",
    "devin",
    "greptile",
    "bito",
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def flatten_pages(value):
    if isinstance(value, list) and value and all(isinstance(page, list) for page in value):
        return [item for page in value for item in page]
    if isinstance(value, list):
        return value
    return []


def source_type(login, user_type=None):
    login = login or ""
    lowered = login.lower()
    if user_type == "Bot":
        return "bot"
    if any(marker in lowered for marker in BOT_MARKERS):
        return "bot"
    return "human"


def emit(record):
    return json.dumps(record, ensure_ascii=False, sort_keys=True)


records = []

reviews = load_json(reviews_path).get("reviews", [])
for review in reviews:
    body = review.get("body") or ""
    if not body.strip():
        continue
    author = review.get("author") or {}
    login = author.get("login") or author.get("name") or "unknown"
    records.append(
        {
            "channel": "review",
            "id": review.get("id"),
            "source": login,
            "source_type": source_type(login, author.get("__typename")),
            "path": None,
            "line": None,
            "original_line": None,
            "commit_id": None,
            "body": body,
            "review_state": review.get("state"),
            "created_at": review.get("submittedAt"),
        }
    )

inline_comments = flatten_pages(load_json(inline_path))
for comment in inline_comments:
    user = comment.get("user") or {}
    login = user.get("login") or "unknown"
    records.append(
        {
            "channel": "inline",
            "id": comment.get("id"),
            "source": login,
            "source_type": source_type(login, user.get("type")),
            "path": comment.get("path"),
            "line": comment.get("line"),
            "original_line": comment.get("original_line"),
            "commit_id": comment.get("commit_id"),
            "body": comment.get("body") or "",
            "created_at": comment.get("created_at"),
        }
    )

discussion_comments = flatten_pages(load_json(discussion_path))
for comment in discussion_comments:
    user = comment.get("user") or {}
    login = user.get("login") or "unknown"
    records.append(
        {
            "channel": "discussion",
            "id": comment.get("id"),
            "source": login,
            "source_type": source_type(login, user.get("type")),
            "path": None,
            "line": None,
            "original_line": None,
            "commit_id": None,
            "body": comment.get("body") or "",
            "created_at": comment.get("created_at"),
        }
    )

with open(out_path, "w", encoding="utf-8") as out:
    for record in records:
        out.write(emit(record) + "\n")
PY

printf 'wrote %s\n' "$reviews_raw"
printf 'wrote %s\n' "$inline_raw"
printf 'wrote %s\n' "$discussion_raw"
printf 'wrote %s\n' "$normalized"
