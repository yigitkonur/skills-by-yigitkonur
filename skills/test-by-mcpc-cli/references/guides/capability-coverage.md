# Capability Coverage

Separate advertised capability from usable CLI surface.

## Practical matrix

| Area | What `mcpc 0.7.0` can do | Caveat |
|---|---|---|
| tools | `tools-list`, `tools-get`, `tools-call` | `isError:true` sets exit code 2 (since v0.5.0); `--json` still carries the full payload; paid tools include settlement receipts in `_meta["x402/payment-response"]` |
| prompts | `prompts-list`, `prompts-get` | no `--schema` on `prompts-get` — schema validation is `tools-get`/`tools-call` only (removed from prompts in v0.2.5) |
| resources | `resources-list`, `resources-read`, `resources-directory-read <uri>`, `resources-subscribe <uri> <file>`, `resources-unsubscribe`, `resources-templates-list` | `resources-directory-read` reads directory resources (`"directoryRead": true`). `resources-subscribe` does real file sync — downloads now, rewrites `<file>` on server change notifications, survives session restarts |
| skills | `skills-list`, `skills-get <skill> [file] [--raw]` | Official `io.modelcontextprotocol/skills` extension (MCP 2026-07-28+) — validates frontmatter, file manifests, byte size, and SHA-256 digests; see `references/guides/skills-testing.md` |
| tasks | `tools-call --task`, `--detach`, `tasks-list`, `tasks-get`, `tasks-cancel`, `tasks-result` | `tasks-result <taskId>` blocks for the final result across process invocations; task commands aren't supported yet on 2026-07-28 connections |
| discovery | `mcpc grep`, `mcpc @session grep`, `mcpc @session help`, `mcpc @session server-discover`, JSON-RPC method aliases (`tools/list`, `tools/call`, ...) | default grep scope is tools plus instructions; `server-discover` needs a 2026-07-28 connection; `mcpc help tools/list` works in 0.7.0 |
| logging | `logging-set-level` | deprecated in v0.6.0; works only on 2025-11-25 (and older) servers, errors on 2026-07-28 |
| roots | no dedicated roots configuration CLI | `mcpc` does not advertise the `roots` client capability (since v0.5.0), so a capability-gated roots tool never registers in `tools-list` — confirmed live: Everything's `get-roots-list` is absent even though the server's own instructions mention it; this is `mcpc` design, not a server bug |
| completions | `mcpc @session completion-complete prompt|resource <ref>` | Dedicated session command for `completion/complete` (shipped in upstream / PR #436); root-level `mcpc completions` does not exist as mcpc is session-first |
| sampling | mcpc has no LLM access | `mcpc` does not advertise the `sampling` client capability (since v0.5.0), so a capability-gated sampling tool never registers either — confirmed live: Everything's `trigger-sampling-request` is absent from `tools-list` |
| elicitation | not exposed as a first-class CLI workflow, not driveable from the CLI | `mcpc` advertises no `elicitation` client capability; a gated demo tool (e.g. `trigger-elicitation-request`) never registers, same as roots/sampling above |

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
- `skills` -> `mcpc @session skills-list` or `mcpc @session skills-get <skill> [file]`
- `directory resources` -> `mcpc @session resources-directory-read <uri>`
- `server-discover` -> only on a 2026-07-28 connection; older connections get an educational error (exit 2) — use `mcpc @session` there instead
- `completions` -> `mcpc @session completion-complete prompt|resource <ref> [arg:=val ...]` to query completion suggestions
- sampling, roots, or elicitation -> the client advertises none of these; confirm via `tools-list` that any capability-gated demo tool (e.g. `trigger-sampling-request`, `get-roots-list`) is simply absent, not erroring
