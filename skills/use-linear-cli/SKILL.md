---
name: use-linear-cli
description: Use when driving Linear through linear-cli for issues, bulk operations, search, or git and PR workflows.
disable-model-invocation: true
---

# Use linear-cli

Drive [nesszer/linear-cli](https://github.com/nesszer/linear-cli), whose executable is `linear-cli`. This skill targets release **0.3.28**. Check `linear-cli --version`; use the installed command's help when versions differ.

## Workflow

1. **Discover.** Run `linear-cli <group> --help`, then `linear-cli <group> <command> --help`. Use [command-surface.md](references/command-surface.md) for every public command group and subcommand in 0.3.28. An accepted global flag does not prove the handler implements it.
2. **Authenticate before API work.** Confirm a successful `linear-cli u me --output json` response with a nonempty `id`, and verify the intended profile/team. `auth status --validate` is diagnostic: it can exit 0 with `validated: false`, and `configured` excludes an environment-only API key. See [setup.md](references/setup.md) for OAuth/API-key precedence.
3. **Resolve scope.** Resolve team keys, assignees, labels, workflow states, project names, and issue identifiers from actual data. Never pick the first team or invent IDs. Respect the user's chosen tool and workspace.
4. **Read before changing.** Fetch current values and the exact target set. For generated bulk sets, save and inspect IDs, count them, and preview the intended changes. Use `--dry-run` where supported; its coverage differs by command. For bulk creation or more than five targets, obtain confirmation of the concrete plan before executing unless already authorized.
5. **Execute and reconcile.** Capture successful IDs and per-item results. Re-read changed resources. Partial failures are not transactions: restore a previous value only if it was captured and the follow-up change is authorized.
6. **Report evidence.** State what changed, which commands succeeded, and what remains unverified. Exit 0, parser acceptance, and a successful dry run each establish different things.

## Output rules

- Request `--output json` for structured results, and keep stdout and stderr separate. Runtime JSON errors go to **stderr**; parser failures are plain text. Some handlers still emit prose or no JSON.
- Use `--id-only` only on handlers that implement it, such as issue create/update. `i list --id-only` does not produce a plain ID list; extract identifiers from JSON with `jq`.
- For `i list`, JSON mode supports field selection/filtering/sorting. Its NDJSON path bypasses `--fields`, `--filter`, `--sort`, `--count-only`, and `--fail-on-empty`; perform those operations in `jq` or use JSON mode.
- Dot paths traverse objects, not array elements. Select `labels.nodes`, then use `jq` for `.labels.nodes[].name`.
- Set `LINEAR_CLI_NO_PAGER=1` in agent runs. Use `--yes` or a command's `--force` only for an authorized operation; there is no global `-y` alias.
- Interpret exit codes together with results: 1 general error, 2 not-found or parser error, 3 auth, 4 rate-limit. Error categorization is partly heuristic. Import may exit 0 after per-item failures; auth status may exit 0 without validated credentials.

## Common reads

```bash
linear-cli --version
linear-cli u me --output json
linear-cli t list --output json
linear-cli i list --mine -t ENG --output json --fields identifier,title,state.name
linear-cli i get LIN-123 --output json
linear-cli context --output json
```

`ENG` and `LIN-123` are placeholders to replace with resolved values. `i list` defaults to a limited page and does not filter to open issues. `i get LIN-1 LIN-2` performs concurrent per-ID requests; JSON results may be sorted and partial failures still exit nonzero.

## Route to the task

Read only the relevant reference. Bash recipes use Bash syntax; the checklist recipes support macOS's Bash 3.2.

| Task | Reference |
|---|---|
| Checklist, CSV, JSON, template, or parent/child bulk creation | [creating-many-issues.md](references/recipes/creating-many-issues.md) |
| Start work, create a GitHub PR, branch context, jj, stop work | [git-and-pr-loop.md](references/recipes/git-and-pr-loop.md) |
| Triage queue, comments, screenshots, attachments | [triage-and-comments.md](references/recipes/triage-and-comments.md) |
| Issue create/update, JSON input, transitions, move/transfer, archive/delete | [lifecycle.md](references/issues/lifecycle.md) |
| Search/list filters, saved views, favorites | [search-and-filter.md](references/issues/search-and-filter.md) |
| Relations, labels, statuses, local and remote templates | [relations-and-labels.md](references/issues/relations-and-labels.md) |
| Projects, updates, cycles, sprints, milestones, roadmaps, initiatives | [projects-and-cycles.md](references/planning/projects-and-cycles.md) |
| Teams, users, views, favorites | [teams-and-org.md](references/planning/teams-and-org.md) |
| Import/export formats, duplicate creation, preview and partial-failure limits | [import-export.md](references/data/import-export.md) |
| Attachment CRUD, authenticated upload downloads, URL extraction | [attachments-and-uploads.md](references/data/attachments-and-uploads.md) |
| Watch events, temporary webhooks, notifications, metrics, history, time | [eventing-and-tracking.md](references/eventing-and-tracking.md) |
| Raw GraphQL, pagination, documents | [advanced.md](references/advanced.md) |
| Installation, auth, profiles, config paths, diagnostics, completions | [setup.md](references/setup.md) |
| Output handling, stdin, pagination, retries, safe chaining | [output-and-scripting.md](references/output-and-scripting.md) |
| JSON shapes and command-specific limitations | [json-shapes.md](references/json-shapes.md) |
| Auth errors, rate limits, partial results, missing commands, cache | [troubleshooting.md](references/troubleshooting.md) |
| Full command discovery and local verification | [command-surface.md](references/command-surface.md) |

## Completion gate

- Intended identity, profile/team and target IDs verified.
- Preview and mutation scope match; existing authorization covers the operation.
- Output parsed according to the specific handler; stderr and exit code checked.
- Successful resources re-read; partial failures reconciled without assuming rollback.
- Report distinguishes parser/source/offline verification from live Linear API results.
