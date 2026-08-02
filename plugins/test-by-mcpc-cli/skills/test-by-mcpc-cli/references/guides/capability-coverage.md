# Capability Coverage

Separate advertised capability from usable CLI surface.

## Practical matrix

| Area | What `mcpc 0.6.0` can do | Caveat |
|---|---|---|
| tools | `tools-list`, `tools-get`, `tools-call` | `isError:true` sets exit code 2 (since v0.5.0); `--json` still carries the full payload |
| prompts | `prompts-list`, `prompts-get` | no `--schema` on `prompts-get` — schema validation is `tools-get`/`tools-call` only (removed from prompts in v0.2.5) |
| resources | `resources-list`, `resources-read`, `resources-subscribe <uri> <file>`, `resources-unsubscribe`, `resources-templates-list` | `resources-subscribe` does real file sync since v0.4.0 — downloads now, rewrites `<file>` on every server change notification, survives session restarts; `<file>` is a required positional arg |
| skills | `skills-list`, `skills-get` | `[EXPERIMENTAL]` SEP-2640 server-published skills — unrelated to this pack's own SKILL.md; see `references/guides/skills-testing.md` |
| tasks | `tools-call --task`, `--detach`, `tasks-list`, `tasks-get`, `tasks-cancel`, `tasks-result` | `tasks-result <taskId>` (since v0.2.6) blocks for the final result across process invocations; task commands aren't supported yet on 2026-07-28 connections |
| discovery | `mcpc grep`, `mcpc @session grep`, `mcpc @session help`, `mcpc @session server-discover`, JSON-RPC method aliases (`tools/list`, `tools/call`, ...) | default grep scope is tools plus instructions; `server-discover` needs a 2026-07-28 connection — see `references/guides/protocol-versions.md` |
| logging | `logging-set-level` | deprecated in v0.6.0; works only on 2025-11-25 (and older) servers, errors on 2026-07-28 |
| roots | no dedicated roots configuration CLI | `mcpc` does not advertise the `roots` client capability (since v0.5.0); a server can still expose roots-aware demo tools as ordinary tool calls |
| completions | capability can appear in server info | no `mcpc completions` command exists — confirmed live: `mcpc completions` exits 1, "Unknown command" |
| sampling | some servers expose sampling demo tools | `mcpc` does not advertise the `sampling` client capability (since v0.5.0); demo tool calls can still return `isError: true` |
| elicitation | not exposed as a first-class CLI workflow | still planned upstream, not shipped — no elicitation demo wired for `mcpc` |

## Rule of thumb

Live behavior beats static README prose.
The official Everything server is the fastest way to probe these edges.

## Reality-check sequence

Use this order when capability claims matter:

```bash
mcpc --json @session | jq '.capabilities'
mcpc --json @session tools-list | jq '.[] | {name, taskSupport: (.execution.taskSupport // "unspecified")}'
mcpc @session tools-list --full
```

Then prove the edge with one real command:

- `task:required` -> run one `tools-call --task` or `--detach`, then `tasks-result <taskId>` if detached
- `skills` -> `mcpc @session skills-list`
- `server-discover` -> only on a 2026-07-28 connection; older connections get an educational error (exit 2) — use `mcpc @session` there instead
- `completions` -> treat as informational because there is no CLI command
- sampling or roots -> the client advertises neither capability; a demo tool call is the only way to probe related behavior, and it can still return `isError: true`
