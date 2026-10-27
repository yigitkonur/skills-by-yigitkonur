# JSON shapes

Response paths observed with 0.3.28. Keep stdout and stderr separate; a global JSON flag does not make every mutation emit JSON.

| Command | Successful stdout |
|---|---|
| `i list`, `p list`, `t list`, `l list`, `d list` | Array of records. |
| `i get ID` | Issue object. |
| `i get ID1 ID2` | Array of successful issues; concurrent requests, output sorting, and partial failures mean argv order/completeness is not guaranteed. |
| `cm list ID` | Object with `id`, `identifier`, `title`, and `comments` array. |
| `att list ID` | Object with `issue`, `title`, and `attachments` array. |
| `st list -t TEAM` | Object with `team` and `statuses` array. |
| `c list -t TEAM` | Object with `team` and `cycles` array. |
| `hist issue ID` | Object with `issue` and `history` array. |
| `rel list ID` | Object with `issue`, `relations`, `inverseRelations`, `parent`, and `children`. |
| `api query` | Raw GraphQL response, except `--paginate` returns a collected nodes array. |

Use the wrapper path explicitly, for example:

```bash
linear-cli cm list LIN-123 --output json | jq '.comments'
linear-cli st list -t ENG --output json | jq '.statuses | map({id,name,type})'
```

`i get` fetches fields such as `id`, `identifier`, `title`, `description`, `priority`, `updatedAt`, `state.name`, `assignee`, `labels.nodes`, and `parent`. `i list` fetches a smaller selection; `--fields` cannot add absent properties. Object-path selection does not traverse arrays: select `labels.nodes`, then use `jq` for `.labels.nodes[].name`.

Priority is 0=no priority, 1=urgent, 2=high, 3=normal, 4=low. Unset related objects can be null. The issue query fetches `state.name`, not its ID; resolve workflow-state IDs through `st list`.

## Branch context

`context --output json` has `branch`, `issue_id`, `found`, and `issue`. Confirm a nonempty issue identifier before a branch-driven mutation. The absence of branch context is not a reason to guess a target.

## Runtime error on stderr

```json
{"error":true,"message":"Issue not found","code":2,"details":null,"retry_after":null}
```

Parser errors can be plain text. Partial multi-get stdout may contain valid successful records even when the process exits nonzero. Do not discard that evidence or treat it as complete success.

## Sprint velocity

The 0.3.28 handler emits `team`, `cycles`, `average_points`, and `trend`. Cycle records include `name`, `number`, `issues_completed`, `issues_total`, `points_completed`, `points_total`, `progress`, and `duration_days`. No past cycles produces an empty array and null aggregate values. This shape was source-checked; the live test team had no cycles.
