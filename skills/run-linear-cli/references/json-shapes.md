# JSON Shapes

Concrete payload examples for the most-parsed `linear-cli` commands. Use these to know exactly which keys you can rely on without round-tripping to the upstream `docs/json/` samples.

These shapes are stable as of `linear-cli` 0.35+. Always validate against the live binary if a key is load-bearing — `linear-cli i get LIN-123 --output json | jq keys`.

## `linear-cli i list`

```json
[
  {
    "id": "issue_uuid",
    "identifier": "LIN-123",
    "title": "Fix login bug",
    "priority": 2,
    "state": { "name": "In Progress" },
    "assignee": { "name": "Ada Lovelace" }
  }
]
```

Common `--fields` shortlist for agent token-frugality:

```bash
--fields identifier,title,state.name,priority,assignee.name
```

## `linear-cli i get LIN-123`

```json
{
  "id": "issue_uuid",
  "identifier": "LIN-123",
  "title": "Fix login bug",
  "description": "Steps to reproduce...",
  "priority": 2,
  "url": "https://linear.app/team/issue/LIN-123",
  "createdAt": "2024-01-01T12:00:00.000Z",
  "updatedAt": "2024-01-02T12:00:00.000Z",
  "state": { "name": "In Progress" },
  "team": { "name": "Engineering" },
  "assignee": { "name": "Ada Lovelace", "email": "ada@example.com" },
  "labels": { "nodes": [ { "name": "bug", "color": "#F59E0B" } ] },
  "project": { "name": "Auth" },
  "parent": { "identifier": "LIN-1", "title": "Auth workstream" }
}
```

Key gotchas:

- `priority` is `0`–`4` (Linear sets `0` = "no priority", `1` = urgent, `2` = high, `3` = normal, `4` = low).
- `labels` is `{ "nodes": [...] }` — connection style. Use `labels.nodes.name` in `--fields`.
- `assignee`, `project`, `parent` are `null` when unset.
- `state.name` is the human label; `state.id` is the workflow-state UUID.

## `linear-cli i get LIN-1 LIN-2 LIN-3` (batch)

Returns a JSON array shaped like `i get`, one element per ID. Order matches argv order.

## `linear-cli cm list LIN-123`

```json
[
  {
    "id": "comment_uuid",
    "body": "LGTM",
    "createdAt": "2024-01-02T12:00:00.000Z",
    "user": { "name": "Ada Lovelace", "email": "ada@example.com" },
    "issue": { "identifier": "LIN-123" }
  }
]
```

## `linear-cli context`

The most useful command for an agent on a working branch — extracts the current issue from the git branch name.

```json
{
  "branch": "feature/LIN-123-fix-login",
  "issue_id": "LIN-123",
  "found": true,
  "issue": {
    "id": "issue_uuid",
    "identifier": "LIN-123",
    "title": "Fix login bug",
    "state": { "name": "In Progress" },
    "assignee": { "name": "Ada Lovelace" },
    "priority": 2,
    "url": "https://linear.app/team/issue/LIN-123"
  }
}
```

When the branch does not encode an issue, `found: false` and `issue: null`. Always gate on `.found`:

```bash
linear-cli context --output json | jq -e '.found' >/dev/null \
  || { echo "no Linear issue on this branch"; exit 1; }
```

## Error envelope (every command, when `--output json` is set)

```json
{
  "error": true,
  "message": "Issue not found: LIN-999",
  "code": 2,
  "details": { "status": 404, "reason": "Not Found", "request_id": null },
  "retry_after": null
}
```

| Field | Notes |
|---|---|
| `error` | `true` on failure. Always present on failed commands. |
| `message` | Human-readable error. |
| `code` | Same as the process exit code (1/2/3/4). |
| `details.status` | HTTP status when relevant. |
| `details.reason` | HTTP reason phrase. |
| `details.request_id` | Linear request id — surface to users when reporting bugs. |
| `retry_after` | Seconds to wait before retrying. Non-null only when `code == 4`. |

## `linear-cli p list`

```json
[
  {
    "id": "project_uuid",
    "name": "Q1 Roadmap",
    "state": "started",
    "icon": "🚀",
    "priority": 1,
    "startDate": "2025-01-01",
    "targetDate": "2025-03-31",
    "lead": { "name": "Ada Lovelace" }
  }
]
```

## `linear-cli t list`

```json
[
  { "id": "team_uuid", "key": "ENG", "name": "Engineering" },
  { "id": "team_uuid", "key": "DES", "name": "Design" }
]
```

`key` is what you pass to most commands as `-t TEAM` (e.g. `ENG`).

## `linear-cli sp velocity`

```json
{
  "team": "ENG",
  "cycles": [
    { "name": "Sprint 4", "completed": 18, "planned": 22, "completion_rate": 0.82 }
  ],
  "average_completion_rate": 0.85,
  "trend": "stable"
}
```

## `linear-cli api query`

Returns the raw GraphQL response body as-is. The CLI does not add a wrapper. See `advanced.md`.

## See also

- `output-and-scripting.md` — flags that produce these shapes.
- `troubleshooting.md` — what to do when the error envelope appears.
- `issues/lifecycle.md` — `--data -` JSON input shapes for create/update.
