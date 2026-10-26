# Command surface (linear-cli 0.3.28)

This index is derived from the installed release help. Run `linear-cli <group> --help` and `linear-cli <group> <command> --help` for current subcommands and flags. Presence here does not prove a Linear API feature is supported or that every operation supports JSON or dry-run.

| Command | Purpose |
|---|---|
| `common` | Show common tasks and examples |
| `agent` | Show agent-focused capabilities and examples |
| `update` | Check for and install the latest released version of linear-cli |
| `attachments` | Manage issue attachments - list, create, update, delete, link URLs |
| `auth` | Authenticate and manage API keys |
| `doctor` | Diagnose configuration and connectivity |
| `api` | Execute raw GraphQL queries and mutations against the Linear API |
| `projects` | Manage projects - list, create, update, delete projects |
| `project-updates` | Manage project status updates - list, create, update, archive |
| `issues` | Manage issues - list, create, update, assign, track issues |
| `labels` | Manage labels - create and organize project/issue labels |
| `teams` | Manage teams - list and view team details |
| `users` | Manage users - list workspace users and view profiles |
| `cycles` | Manage cycles - view sprint cycles and current cycle |
| `comments` | Manage comments - add and view issue comments |
| `documents` | Manage documents - create, update, delete documentation |
| `search` | Search across Linear - find issues and projects |
| `sync` | Sync operations - compare local folders with Linear |
| `statuses` | Manage issue statuses - view workflow states |
| `git` | Git branch operations - checkout branches, create PRs |
| `bulk` | Bulk operations - update multiple issues at once |
| `cache` | Manage cache - clear cached data or view status |
| `notifications` | Manage notifications - view and mark as read |
| `templates` | Manage issue templates - create and use templates |
| `time` | Time tracking - log and view time entries |
| `uploads` | Fetch uploads from Linear with authentication |
| `interactive` | Interactive mode - TUI for browsing and managing issues |
| `context` | Detect current Linear issue from git branch - for AI agents |
| `favorites` | Manage favorites - quick access to issues/projects |
| `roadmaps` | Manage roadmaps - view and manage roadmap planning |
| `initiatives` | Manage initiatives - create, update, and track initiatives |
| `triage` | Triage inbox - manage unassigned issues |
| `metrics` | View metrics - velocity, burndown, progress |
| `milestones` | Manage project milestones - list, create, update, delete milestones |
| `export` | Export issues to CSV, JSON, or Markdown |
| `import` | Import issues from CSV or JSON files |
| `history` | View issue history and activity |
| `views` | Manage custom views - create, apply, and manage saved views |
| `webhooks` | Manage webhooks - create, update, delete, listen for events |
| `watch` | Watch for updates (polling) |
| `relations` | Manage issue relationships - parent/child, blocking, related |
| `whoami` | Show current authenticated user (alias for `users me`) |
| `done` | Mark the current branch's issue as Done |
| `setup` | Guided onboarding wizard - configure auth, team, and output format |
| `sprint` | Sprint planning - manage cycle-based sprints |
| `completions` | Generate shell completions |
| `config` | Configure CLI settings - API keys, default team, and workspaces |
| `help` | Print this message or the help of the given subcommand(s) |

`sync status` compares local folders with projects; `sync push` creates projects. Inspect its help and preview behavior before use.
