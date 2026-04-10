# Capability Coverage

Separate advertised capability from usable CLI surface.

## Practical matrix

| Area | What `mcpc 0.2.4` can do | Caveat |
|---|---|---|
| tools | `tools-list`, `tools-get`, `tools-call` | inspect `isError` in JSON mode |
| prompts | `prompts-list`, `prompts-get` | prompt schema validation is wired through `--schema` |
| resources | `resources-list`, `resources-read`, `resources-subscribe`, `resources-unsubscribe`, `resources-templates-list` | subscriptions are easiest to observe through JSON or logs |
| logging | `logging-set-level` | the server decides what messages exist |
| tasks | `tools-call --task`, `--detach`, `tasks-list`, `tasks-get`, `tasks-cancel` | no standalone `tasks-result` command |
| grep / discovery | `mcpc grep`, `mcpc @session grep`, `mcpc @session help` | default grep scope is tools plus instructions |
| roots | some servers expose helper tools because the client advertises roots support | no dedicated roots configuration CLI |
| completions | capability can appear in server info | no `mcpc completions` command |
| sampling | some servers expose sampling demo tools | live calls can still return `isError: true` |
| elicitation | not exposed as a first-class CLI workflow | Everything does not register the elicitation demo for `mcpc` |

## Rule of thumb

Live behavior beats static README prose.
The official Everything server is the fastest way to probe these edges.
