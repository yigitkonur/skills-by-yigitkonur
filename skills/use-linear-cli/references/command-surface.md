# Command surface: linear-cli 0.3.28

Every public command group and subcommand discovered from the installed release help is listed below. `help` and hidden completion internals are excluded. A listed command is discoverable; this does not establish live API support, permissions, complete pagination, or flag semantics.

Run `linear-cli GROUP COMMAND --help` for exact options and required arguments. Standalone root commands have no subcommands in the second column.

| Group | Subcommands |
|---|---|
| `common` | — |
| `agent` | — |
| `update` | — |
| `attachments` | `list`, `get`, `create`, `update`, `delete`, `link-url` |
| `auth` | `login`, `logout`, `status`, `migrate`, `oauth`, `revoke` |
| `doctor` | — |
| `api` | `query`, `mutate` |
| `projects` | `list`, `get`, `open`, `create`, `update`, `delete`, `add-labels`, `remove-labels`, `set-labels`, `archive`, `unarchive`, `members` |
| `project-updates` | `list`, `get`, `create`, `update`, `archive`, `unarchive` |
| `issues` | `list`, `get`, `open`, `create`, `update`, `delete`, `start`, `stop`, `close`, `archive`, `unarchive`, `comment`, `link`, `assign`, `move`, `transfer` |
| `labels` | `list`, `create`, `delete`, `update` |
| `teams` | `list`, `get`, `members`, `create`, `update`, `delete` |
| `users` | `list`, `me`, `get` |
| `cycles` | `list`, `get`, `current`, `create`, `update`, `delete`, `complete` |
| `comments` | `list`, `create`, `update`, `delete` |
| `documents` | `list`, `get`, `create`, `update`, `delete` |
| `search` | `issues`, `projects` |
| `sync` | `status`, `push` |
| `statuses` | `list`, `get`, `update` |
| `git` | `checkout`, `branch`, `create`, `commits`, `review-url`, `pr` |
| `bulk` | `update-state`, `assign`, `label`, `unassign` |
| `cache` | `clear`, `status` |
| `notifications` | `list`, `read`, `read-all`, `count`, `archive`, `archive-all` |
| `templates` | `list`, `create`, `show`, `delete`, `remote-list`, `remote-get`, `remote-create`, `remote-update`, `remote-delete` |
| `time` | `log`, `list`, `delete`, `update` |
| `uploads` | `fetch` |
| `interactive` | — |
| `context` | — |
| `favorites` | `list`, `add`, `remove` |
| `roadmaps` | `list`, `get`, `create`, `update`, `delete` |
| `initiatives` | `list`, `get`, `create`, `update`, `delete` |
| `triage` | `list`, `claim`, `snooze` |
| `metrics` | `cycle`, `project`, `velocity` |
| `milestones` | `list`, `get`, `create`, `update`, `delete` |
| `export` | `csv`, `markdown`, `json`, `projects-csv` |
| `import` | `csv`, `json` |
| `history` | `issue` |
| `views` | `list`, `get`, `create`, `update`, `delete` |
| `webhooks` | `list`, `get`, `create`, `update`, `delete`, `rotate-secret`, `listen` |
| `watch` | `issue`, `project`, `team` |
| `relations` | `list`, `add`, `remove`, `parent`, `unparent` |
| `whoami` | — |
| `done` | — |
| `setup` | — |
| `sprint` | `status`, `progress`, `plan`, `carry-over`, `burndown`, `velocity` |
| `completions` | `static`, `dynamic` |
| `config` | `set-key`, `get`, `set`, `show`, `completions`, `workspace-add`, `workspace-list`, `workspace-switch`, `workspace-current`, `workspace-remove` |

## Repeat discovery

```bash
python3 scripts/check-surface.py
```

Run from this skill’s directory, or use the script’s absolute path. The script only invokes `--version` and `--help`, compares the discovered tree with this index, emits JSON, and exits nonzero on drift. It does not execute domain commands or validate behavior.

## Less common surfaces

- `sync status` compares local folders and Linear projects. `sync push` creates remote projects. Resolve the target directory and team, inspect the preview, and obtain authorization before pushing.
- `interactive` is a human TUI. Use explicit commands in unattended workflows.
- `common` and `agent` print guidance; `agent --schema` returns CLI output schema metadata.
- `doctor --fix`, `setup`, `update`, config and completion commands can modify local state. Some can prompt.
- `bulk unassign`, initiative/roadmap/document mutations and `time update` exist in this release; check their own help rather than inferring flags from related handlers.

## Verification boundary

The second audit checked all help paths, parsed Bash examples, inspected the pinned release source and ran selected upstream unit tests. Offline probes cover parser and local rejection paths only. No authenticated Linear API read/write, OAuth login/refresh, webhook lifecycle, time-entry mutation or end-to-end import was exercised. Validate the task’s relevant live flow before claiming it works in a specific workspace.
