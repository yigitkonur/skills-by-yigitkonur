# Live compatibility: 0.3.28

Checked on 2026-10-27 using a temporary read/write API key limited to one team, without admin access. The key was revoked afterward and a fresh request failed authentication. Disposable records were used for mutations. Issues, project and document were confirmed trashed; the milestone was no longer retrievable. Results describe these tested paths, not every flag or workspace configuration.

| Surface | Observation |
|---|---|
| Identity, teams, statuses, labels, issues, projects, cycles, views, favorites, documents, roadmaps, initiatives | Live reads succeeded. Several returned empty collections, which does not exercise populated-result behavior. |
| Issue create/update/delete, labels, bulk label append, start/stop/unassign | Mutations succeeded; persisted label and state/assignee behavior was checked through independent API reads. |
| Comments, relations, parent/unparent, attachments, history | Commands succeeded on disposable issues; parent changes were independently re-read. |
| Project and document CRUD; milestone create/read/delete | Smoke-tested successfully. |
| Import | One valid row was created despite three unresolved-name warnings; a second row failed with invalid priority. Import still exited 0 and reported results on stderr. |
| Multi-get | A valid ID plus a nonexistent ID returned one successful record with exit 2. |
| List flags | `--id-only` did not produce plain IDs; the NDJSON path ignored field/filter/empty-result transformations. |
| `bulk --dry-run` | Rejected with “not supported”; it is not a preview mechanism for this group. Inspect the exact targets and planned values before an authorized bulk write. |
| `tpl remote-list` | Failed schema validation because the CLI queries `templates { nodes { ... } }` while the current API returns a direct list. Raw `api query '{ templates { id name } }'` succeeded. Other remote-template mutations were not exercised. |
| `time list` | Failed schema validation for issue/time-schedule fields. Do not assume the CLI's suggested “add-on” explanation is established by that error. Time-entry writes were not exercised. |

Use `true`/`false` for boolean environment settings. `LINEAR_CLI_NO_PAGER=1` and `LINEAR_CLI_NO_CACHE=1` are rejected before command dispatch.

OAuth login/refresh, remote webhook lifecycle, Git/PR creation, sprint/cycle mutations, and broad administration were not exercised. Use the task's relevant live checks before claiming those flows work.
