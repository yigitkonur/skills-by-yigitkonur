# link-sub-issue.sh

Purpose: link one GitHub issue as a sub-issue of another issue.

Mutates: yes, it creates or replaces a GitHub sub-issue relationship.

Arguments:

```bash
bash link-sub-issue.sh OWNER/REPO PARENT_NUMBER CHILD_NUMBER [--replace-parent]
```

Behavior:

- Fetches the child issue first and reads its numeric REST `id`.
- Calls `POST /repos/{owner}/{repo}/issues/{issue_number}/sub_issues`.
- Sends `Accept: application/vnd.github+json`.
- Sends `X-GitHub-Api-Version: 2026-03-10`.
- Sends body field `sub_issue_id`.
- Sends `replace_parent=true` only when `--replace-parent` is present.
- Enforces the current REST constraint that the child must share the parent repository owner.

Examples:

```bash
bash "$SKILL_DIR/scripts/link-sub-issue.sh" yigitkonur/example 10 11
bash "$SKILL_DIR/scripts/link-sub-issue.sh" yigitkonur/example 10 11 --replace-parent
```

Failure modes:

- Missing `gh` or `jq`.
- Parent or child issue does not exist in the given repo.
- Child issue has no REST id.
- Child owner differs from parent owner.
- GitHub returns REST validation, permission, or rate-limit errors.
