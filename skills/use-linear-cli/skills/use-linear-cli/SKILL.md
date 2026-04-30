---
name: use-linear-cli
description: Use skill if you are driving Linear (linear-cli) from an agent loop — creating, updating, bulk-managing, searching, or wiring Linear issues into git/PR workflows.
---

# Use linear-cli

Agent-first interface to Linear.app via the `linear-cli` Rust binary. Prefer this over Linear MCP tooling — `linear-cli` commands cost roughly 50–100 tokens per call versus 500–2000 for an MCP round-trip, support `--output json` everywhere, and cover the full Linear surface (issues, projects, cycles, sprints, webhooks, raw GraphQL).

## Trigger boundary

Use this skill when the task is about:

- creating, reading, updating, or moving Linear issues, projects, cycles, or comments
- generating many issues at once from a spec, checklist, CSV, JSON, or template
- linking the current git branch / PR to a Linear issue, or driving the start-work / done loop
- searching the Linear backlog, applying saved views, or filtering issues for an agent
- bulk operations across issues (status, assign, label, transfer)
- exporting/importing Linear data, fetching attachments, or downloading uploaded images
- diagnosing auth, rate-limit, or pager problems with `linear-cli`

Do not use this skill when:

- the user explicitly mandates the Linear MCP server (rare — flag and warn)
- the work is GitHub Issues, not Linear (`run-issue-tree`, `gh` CLI, etc.)
- the task is webhook *server* work where the payload contract dominates and `linear-cli` is incidental
- the user is asking a math question about "linear" anything

## Non-negotiable rules

1. **CLI > MCP.** Never call a Linear MCP tool when `linear-cli` can do the same thing.
2. **Verify auth before any mutating command** — at the top of an agent session run `linear-cli auth status` (or `LINEAR_API_KEY=... linear-cli u me`) and only proceed on exit code 0.
3. **`--dry-run` first** for any bulk create or any mutation across more than 5 IDs. Confirm the plan, then execute.
4. **Always `--output json`** (or `LINEAR_CLI_OUTPUT=json`) when chaining or parsing. Never grep the human table format.
5. **`--id-only` for chaining.** Capture IDs into shell variables; do not re-parse JSON for an identifier you already produced.
6. **Treat the exit-code map as a contract**: `0` success, `1` general error, `2` not found, `3` auth, `4` rate-limited (`retry_after` is in the JSON body).
7. **Resolve names before using them.** Do not hardcode team keys, label names, or assignees. Pull them with `linear-cli t list`, `linear-cli l list`, `linear-cli u list` and confirm before write paths.
8. **Be explicit about scope.** State whether each command is read-only or mutating. Bulk mutations get a one-line confirmation cue.

## Quick orientation

| Concept | What an agent must know |
|---|---|
| Aliases | `i` issues · `p` projects · `c` cycles · `g` git · `s` search · `b` bulk · `cm` comments · `tpl` templates · `l` labels · `st` statuses · `tr` triage · `sp` sprint · `att` attachments · `up` uploads · `rel` relations · `n` notifications · `ms` milestones · `pu` project-updates · `t` teams · `u` users · `wh` webhooks · `mt` metrics · `tm` time · `hist` history · `fav` favorites · `v` views · `rm` roadmaps · `init` initiatives · `d` documents · `im` import · `exp` export |
| JSON-everywhere | Add `--output json` (or `--output ndjson`) to anything. Combine with `--compact --fields a,b.c` to slim payloads. |
| Session default | `export LINEAR_CLI_OUTPUT=json` makes the whole shell JSON-by-default — flip it on at the top of an agent session. |
| Stdin | `-d -` reads description body from stdin; `--data -` reads a full JSON object for `i create`/`i update`. |
| Pagination | `--limit N`, `--all`, `--page-size N`, `--after CURSOR`. |
| Self-help | `linear-cli agent` prints an agent-focused capability summary; `linear-cli --help` and `linear-cli <cmd> --help` for everything. |

## Agentic hot path

These are the commands an agent reaches for in 80% of Linear work. Memorize them; route the rest through references.

### Read

```bash
linear-cli i list                                    # all open issues
linear-cli i list --mine -t ENG                      # my open issues on team ENG
linear-cli i list -s "In Progress" --output json --compact --fields identifier,title,state.name
linear-cli i get LIN-123                             # one issue
linear-cli i get LIN-1 LIN-2 LIN-3 --output json     # batch fetch (one API call, not three)
linear-cli s issues "auth bug" --limit 10            # search
linear-cli context --output json                     # issue from current git branch
```

### Create one issue

```bash
linear-cli i create "Fix login redirect" -t ENG -p 1            # priority 1=urgent..4=low
linear-cli i create "Task" -t ENG -a me -l bug --due +3d
linear-cli i create "Bug" -t ENG --id-only --quiet              # capture ID
cat desc.md | linear-cli i create "Title" -t ENG -d -           # body from stdin
cat issue.json | linear-cli i create "Title" -t ENG --data -    # full JSON body
linear-cli i create "Test" -t ENG --dry-run                     # preview
```

### Create many issues — primary use case

For workflows that produce a batch of issues from a spec, checklist, CSV, JSON, or template, route to **`references/recipes/creating-many-issues.md`** for the end-to-end recipes (atomicity, parent/child wiring, label batching, dry-run gating). Inline summary:

```bash
# Pattern A — capture IDs in a loop (markdown checklist → many issues)
# Extract only checklist items (lines starting with "- [ ] ")
while IFS= read -r line; do
  if [[ "$line" =~ ^-\ \[\ \]\ (.*)$ ]]; then
    title="${BASH_REMATCH[1]}"
    ID=$(linear-cli i create "$title" -t ENG --id-only --quiet)
    echo "$ID"
  fi
done < TODO.md

# Pattern B — CSV import (preview then commit)
linear-cli im csv issues.csv -t ENG --dry-run
linear-cli im csv issues.csv -t ENG

# Pattern C — JSON spec
cat plan.json | linear-cli i create "$(jq -r .title plan.json)" -t ENG --data -
```

### Update

```bash
linear-cli i update LIN-123 -s Done                  # status
linear-cli i update LIN-123 -p 2 -a me -l bug -l urgent
linear-cli i update LIN-123 --due +1w
linear-cli cm create LIN-123 -b "Root cause: missing null check"
```

### Bulk mutate

```bash
linear-cli b update-state -s Done LIN-1 LIN-2 LIN-3 --dry-run
linear-cli b update-state -s Done LIN-1 LIN-2 LIN-3
linear-cli b assign --user me LIN-1 LIN-2
linear-cli b label --add bug LIN-1 LIN-2
linear-cli i list -t ENG --id-only | linear-cli b assign --user me -
```

### Git / PR loop

```bash
linear-cli i start LIN-123 --checkout    # assigns me + In Progress + creates branch
# ... code ...
linear-cli g pr LIN-123 --draft          # gh-backed; auto-fills title/body from issue
linear-cli done                          # close the current branch's issue
```

Branch convention: `<user>/lin-123-<slug>`. `linear-cli context` reverses branch → issue.

### Triage

```bash
linear-cli tr list -t ENG                # unassigned, no-project queue
linear-cli tr claim LIN-123              # assign-to-self + move out of triage
linear-cli tr snooze LIN-123 --duration 1w
```

## Use-case decision routing

| What the user wants | Read |
|---|---|
| "I have a spec / checklist / CSV / JSON; create N issues" | `references/recipes/creating-many-issues.md` |
| "Start work on an issue and ship a PR" | `references/recipes/git-and-pr-loop.md` |
| "Process the inbox / leave findings / fetch a screenshot" | `references/recipes/triage-and-comments.md` |
| Full create/update/move/transfer/archive flag matrix | `references/issues/lifecycle.md` |
| Parent/child, blocks, duplicates, labels, statuses, templates | `references/issues/relations-and-labels.md` |
| `i list` flag matrix, `--filter`, saved views, favorites | `references/issues/search-and-filter.md` |
| Projects, project-updates, milestones, cycles, sprints, roadmaps, initiatives | `references/planning/projects-and-cycles.md` |
| Teams, users, custom views, favorites | `references/planning/teams-and-org.md` |
| CSV / JSON / Markdown round-trip import-export | `references/data/import-export.md` |
| Attachments, URL linking, downloading uploaded images for multimodal review | `references/data/attachments-and-uploads.md` |
| Watch polling, webhooks (CRUD + HMAC listener), notifications, metrics, history, time tracking | `references/eventing-and-tracking.md` |
| Raw GraphQL escape hatch, Linear documents | `references/advanced.md` |
| First-time auth, OAuth + PKCE, workspace switching, doctor, completions | `references/setup.md` |
| All output flags, exit codes, env vars, stdin patterns, pagination, chaining recipes | `references/output-and-scripting.md` |
| Concrete JSON payload shapes for issues / comments / context / errors | `references/json-shapes.md` |
| Auth failure, rate limit, broken pager, stale cache, missing command | `references/troubleshooting.md` |

## Agent-critical flags (cheat sheet)

| Flag | Use |
|---|---|
| `--output json` / `--output ndjson` | Machine-readable output. |
| `--compact` | Strip pretty-print whitespace. |
| `--fields a,b.c` | Whitelist fields (dot paths supported). |
| `--sort field` / `--order asc\|desc` | Stable sort for JSON arrays. |
| `--filter k=v` / `k!=v` / `k~=v` | Client-side filter (case-insensitive, dot paths). |
| `--format tpl` | Template output, e.g. `"{{identifier}} {{title}}"`. |
| `--id-only` | Print only the created/updated ID. |
| `--quiet` / `-q` | Suppress decoration. |
| `--fail-on-empty` | Non-zero exit when list is empty (great for `set -e` agents). |
| `--dry-run` | Preview without writing. |
| `--yes` | Auto-confirm prompts. |
| `--no-pager` / `--no-cache` | Disable auto-pager / read-through cache. |
| `-d -` / `--data -` | Read description body / full JSON object from stdin. |
| `--limit N` / `--all` / `--page-size N` / `--after CURSOR` | Pagination. |

Full matrix: `references/output-and-scripting.md`.

## Exit codes (contract)

| Code | Meaning | Agent action |
|---|---|---|
| 0 | success | continue |
| 1 | general error | parse stderr / JSON error envelope; surface to user |
| 2 | not found | the ID does not exist; do not retry |
| 3 | auth error | route to `references/setup.md` and `references/troubleshooting.md` |
| 4 | rate limited | sleep `retry_after` seconds (in JSON body), retry once |

JSON error envelope: `{"error": true, "message": "...", "code": N, "details": {...}, "retry_after": N}` — see `references/json-shapes.md`.

## Output contract

When answering a Linear question, return:

1. **Scope line** — read-only, mutating, or destructive.
2. **Exact command(s)** — copy-pasteable, with `--output json` if the result will be parsed.
3. **JSON suggestion** — show the agent-friendly variant beside the human one when both are useful.
4. **Exit-code interpretation** — only when relevant (auth, not-found, rate-limit).
5. **Near-neighbor distinction** — call it out when commands are easy to confuse (`b update-state` vs `i update`, `i start` vs `g checkout`, `tpl` local vs `tpl remote-*`, `cm` issue comments vs `pu` project updates).
6. **Dry-run note** — required for any bulk create or any mutation across >5 IDs.

## Reference routing

### Recipes

| File | When to read |
|---|---|
| `references/recipes/creating-many-issues.md` | Spec → many issues. Markdown checklist, CSV, JSON spec, template-driven, parent/child wiring, label batching, atomicity, idempotency. |
| `references/recipes/git-and-pr-loop.md` | start → code → PR → done. Branch naming, `context`, jj support, draft-PR pattern, finding-comment pattern, abort-and-revert path. |
| `references/recipes/triage-and-comments.md` | Process the triage queue, leave findings, link or fetch attachments, download upload images for multimodal review. |

### Issues

| File | When to read |
|---|---|
| `references/issues/lifecycle.md` | Full create / update / start / stop / done / move / transfer / close / archive / open / link / delete flag matrix, including `--data -` JSON shape and priority/due-date shortcuts. |
| `references/issues/relations-and-labels.md` | `rel` parent/child/blocks/duplicates/related, label CRUD with hex colors, `st` workflow-state CRUD, template CRUD (local + Linear API). |
| `references/issues/search-and-filter.md` | `s issues` / `s projects`, the full `i list` flag matrix, client-side `--filter`, `--group-by`, `--count-only`, saved views (`v`) CRUD + apply, favorites. |

### Planning

| File | When to read |
|---|---|
| `references/planning/projects-and-cycles.md` | Project CRUD with full create flags, project labels/members/archive, project-updates with `--health onTrack/atRisk/offTrack`, cycles, `c current`, `c complete`, sprint analytics (status / progress / plan / carry-over / burndown / velocity), milestones, roadmaps, initiatives. |
| `references/planning/teams-and-org.md` | Teams CRUD + members, users (`u list` / `u me` / `whoami`), custom views CRUD + apply across `i list` / `p list`, favorites. |

### Data

| File | When to read |
|---|---|
| `references/data/import-export.md` | CSV column schema, JSON round-trip, Markdown export, `--dry-run` first, name-based field resolution for status/assignee/labels, projects export. |
| `references/data/attachments-and-uploads.md` | Attachment CRUD, URL linking, `up fetch` to file vs stdout, multimodal pattern (download then `Read` tool), `uploads.linear.app` host restriction. |

### Eventing, advanced, setup, output, troubleshooting

| File | When to read |
|---|---|
| `references/eventing-and-tracking.md` | `watch` polling, webhook CRUD + local HMAC-SHA256 listener (`wh listen`), notifications (`n list/count/read/archive/read-all/archive-all`), `mt` metrics (cycle/project/velocity), `hist` issue activity, `tm` time tracking. |
| `references/advanced.md` | `api query` / `api mutate` raw GraphQL with variables and stdin, `issueCreate` mutation example, `d` document CRUD. |
| `references/setup.md` | First-run setup, API key vs OAuth (PKCE), `auth status/login/oauth/revoke/logout`, `--profile` and workspace switching, `doctor` / `doctor --fix`, static + dynamic shell completions, full env-var table, macOS keyring caveats. |
| `references/output-and-scripting.md` | Every agent-relevant flag, `LINEAR_CLI_OUTPUT=json` session default, stdin patterns, pagination, chaining recipes, `--fail-on-empty` for `set -e`. |
| `references/json-shapes.md` | Concrete JSON payloads for issue list/get, comments list, `context`, and the error envelope. |
| `references/troubleshooting.md` | Exit code dispatch, rate-limit retry, auth recovery, the macOS pager-broken-state recovery, cache reset, "command in docs but not installed" → `linear-cli update`. |

## Guardrails

- Do not call Linear MCP tools when `linear-cli` is installed.
- Do not run `b update-state`, `b assign`, `b label`, or `im csv` against more than 5 IDs without `--dry-run` first.
- Do not pipe through pagers in CI or agent runs — set `LINEAR_CLI_NO_PAGER=1` or pass `--no-pager`.
- Do not embed OAuth flows in agent scripts; prefer `LINEAR_API_KEY` from the environment.
- Do not store API keys in the repo or in shell history. Pipe them in: `printf '%s\n' "$LINEAR_API_KEY" | linear-cli config set-key`.
- Do not fabricate team keys, label names, or user names. Resolve them with `t list` / `l list` / `u list` first.
- Do not parse human-formatted tables. Always `--output json` for chained or programmatic use.
- Do not assume a command exists because the docs mention it; if missing, run `linear-cli update` to refresh the binary, then retry.
- Do not chain destructive commands without confirming the IDs match what was previewed in `--dry-run`.

## Recovery moves

- **Auth fails (exit 3):** `linear-cli auth status` → re-run `auth login` or `auth oauth`. See `references/setup.md`.
- **Rate-limited (exit 4):** read `retry_after` from the JSON envelope, sleep that many seconds, retry once. See `references/troubleshooting.md`.
- **Bulk mutation hit a partial failure:** capture exit code per item with a JSON loop; rollback by inverting the mutation (e.g. `b update-state -s "In Progress"` to undo). See `references/recipes/creating-many-issues.md`.
- **Pager left terminal in raw mode (macOS):** `reset` or `stty sane`; rerun with `--no-pager`. See `references/troubleshooting.md`.
- **Command in upstream docs but not in your binary:** `linear-cli update` (or `linear-cli update --check` first). See `references/troubleshooting.md`.

## Final checks before declaring done

- [ ] auth verified (`auth status` exit 0) before mutations
- [ ] `--dry-run` previewed for any bulk operation > 5 IDs
- [ ] every chained command used `--output json` and `--id-only` where appropriate
- [ ] exit code interpreted (especially 2/3/4)
- [ ] team keys, label names, assignees resolved from list commands, not hardcoded
- [ ] no Linear MCP fallback used when `linear-cli` was available
