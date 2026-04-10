# Resources Reference

All 7 MCP resource URIs exposed by the codex-worker server.

## 1. task:///all — Scoreboard

**URI:** `task:///all`
**mimeType:** `text/plain`
**When to use:** Track all tasks between waves. Poll every ~30s. Quick status overview.

**Response when tasks exist:**
```
tasks -- 5 total (3 done, 1 busy, 1 fail)

[done] bold-falcon-42     "Create slugify.ts..."              23s   109K tokens (11%)
[done] calm-tiger-88      "Write auth module..."              45s   85K tokens (8.5%)
[done] dark-raven-12      "Add rate limiting..."              18s   42K tokens (4.2%)
[busy] eager-wolf-99      "Refactor billing..."               62s   running
[fail] fast-bear-33       "Complex migration..."              8s    failed: process exit

> Details: read `task:///<id>` · Events: read `task:///<id>/events` · Poll: read `task:///all` every ~30s
```

**Response when empty:**
```
tasks -- 0 total


> Details: read `task:///<id>` · Events: read `task:///<id>/events` · Poll: read `task:///all` every ~30s
```

Shows badges `[done]`, `[busy]`, `[fail]`, `[wait]`, `[stop]`. Includes labels, timing, token usage. Pending questions are flagged.

## 2. task:///{id} — Task detail

**URI:** `task:///{id}` (e.g. `task:///careful-wolf-228`)
**mimeType:** `text/markdown`
**When to use:** Inspect one task's full metadata after completion or failure.

**Response:**
```markdown
# Task: careful-wolf-228 -- echo hello

| Field | Value |
|---|---|
| **Status** | [fail] `failed` |
| **Provider** | codex |
| **Session ID** | `019d76ff-e670-79a2-b477-6203b8df41ae` |
| **Reasoning** | `gpt-5.4(low)` |
| **Task type** | coder |
| **CWD** | `/tmp` |
| **Created** | 2026-04-10T10:46:15.324Z |
| **Started** | 2026-04-10T10:46:15.416Z |
| **Completed** | 2026-04-10T10:46:15.510Z |
| **Updated** | 2026-04-10T10:46:15.510Z |

## Error

\```
Missing environment variable: `CODEX_LB_API_KEY`. [other]
\```

## Recent Output

[03:46:15] ERROR: other — Missing environment variable: `CODEX_LB_API_KEY`.
[03:46:15] turn failed: other — Missing environment variable: `CODEX_LB_API_KEY`.
```

Fields include: status badge, provider, session ID, reasoning level, task type, cwd, timestamps (created, started, completed, updated), labels if present, error if failed, recent output lines.

## 3. task:///{id}/log — Summary log

**URI:** `task:///{id}/log` (e.g. `task:///grotesque-gopher-198/log`)
**mimeType:** `text/plain`
**When to use:** Quick output check. Shows last ~20 lines from the summary log.

**Response:**
```
# Log: grotesque-gopher-198 (from disk)

[10:24:10] cmd: /bin/zsh -lc "rtk find FastNotch ..." (exit 0, 0.0s)
[10:24:10] cmd: /bin/zsh -lc 'rtk pwd && rtk find ...' (exit 0, 0.3s)
[10:24:16] cmd: /bin/zsh -lc "rtk cat AGENTS.md ..." (exit 0, 0.0s)
[10:24:19] cmd: /bin/zsh -lc 'rtk cat FastNotch/...' (exit 1, 0.0s)
[10:24:23] cmd: /bin/zsh -lc 'rtk wc -l ...' (exit 0, 0.0s)
[10:24:27] agent: I inspected the target directory...
[10:24:27] turn completed
```

Format: `[HH:MM:SS] {type}: {detail}`. Types: `cmd`, `agent`, `turn completed`, `turn failed`, `ERROR`.

## 4. task:///{id}/log.verbose — Full verbose log

**URI:** `task:///{id}/log.verbose`
**mimeType:** `text/plain`
**When to use:** Deep inspection. Shows full command output, not just summaries.

**Response:**
```
[10:24:10] === command completed: /bin/zsh -lc "rtk find ..." (exit 0, 0.0s) ===
[10:24:10] started: /bin/zsh -lc "rtk find ..."
[10:24:10] started: /bin/zsh -lc 'rtk pwd && rtk find ...'
471F 471D:

SWComp/ AGENTS.md
SWComp/SWComp/ AGENTS.md
...
```

Includes full stdout/stderr from commands, not just the one-liner summary. Read from disk at `~/.mcp-codex-worker/tasks/{id}/verbose.log`.

## 5. task:///{id}/events — Full event trace

**URI:** `task:///{id}/events`
**mimeType:** `application/jsonl`
**When to use:** Debug trace. Contains every notification including deltas, hooks, and all streaming data.

**Response:** JSONL (one JSON object per line):
```jsonl
{"t":"2026-04-10T17:24:03.487Z","method":"thread/status/changed","params":{"threadId":"...","status":{"type":"active","activeFlags":[]}}}
{"t":"2026-04-10T17:24:03.487Z","method":"turn/started","params":{"threadId":"...","turn":{"id":"...","items":[],"status":"inProgress","error":null}}}
{"t":"2026-04-10T17:24:05.282Z","method":"hook/started","params":{"threadId":"...","turnId":"...","run":{"id":"session-start:0:...","eventName":"sessionStart","status":"running"}}}
{"t":"2026-04-10T17:24:06.349Z","method":"item/started","params":{"item":{"type":"reasoning","id":"rs_...","summary":[],"content":[]}}}
...
```

Read from disk at `~/.mcp-codex-worker/tasks/{id}/events.jsonl`. Can be hundreds of lines for complex tasks due to delta events.

## 6. task:///{id}/events/summary — Filtered event trace

**URI:** `task:///{id}/events/summary`
**mimeType:** `application/jsonl`
**When to use:** Clean events without noise. Good for programmatic analysis.

**Response:** Same JSONL format but with these filtered OUT:
- All delta events (`*Delta`, `*delta`)
- Hook events (`hook/started`, `hook/completed`)
- Streaming events

What remains: thread lifecycle, turn lifecycle, item started/completed (without streaming), token usage, synthetic events, plan updates.

## 7. task:///{id}/timeline — One-liner timeline

**URI:** `task:///{id}/timeline`
**mimeType:** `text/plain`
**When to use:** Progress overview. One meaningful line per event. Primary monitoring tool.

**Response:**
```
10:24:03 STARTED
10:24:03 TURN    019d786c-191e-7cb2-a0d9-70d6a03885e9
10:24:06 THINK   (reasoning...)
10:24:09 TOKENS  18629 / 996147 (1.9%)
10:24:10 CMD     find FastNotch -path '*/AGENTS.md' -print → exit=0 (<1ms)
10:24:10 CMD     pwd && find .. -name AGENTS.md -print → exit=0 (0.3s)
10:24:13 THINK   (reasoning...)
10:24:16 THINK   Inspecting agents' paths
10:24:16 TOKENS  38407 / 996147 (3.9%)
10:24:27 MSG     I inspected the target directory and counted... [+38 chars]
10:24:27 TOKENS  109621 / 996147 (11.0%)
10:24:27 DONE    completed
```

Read from disk at `~/.mcp-codex-worker/tasks/{id}/timeline.log`. See `timeline-format.md` for all 16 line types.

## Disk paths

All resources are backed by files under `~/.mcp-codex-worker/tasks/{id}/`:

| File | Resource URI |
|---|---|
| `meta.json` | `task:///{id}` (metadata source) |
| `summary.log` | `task:///{id}/log` |
| `verbose.log` | `task:///{id}/log.verbose` |
| `events.jsonl` | `task:///{id}/events` and `task:///{id}/events/summary` |
| `timeline.log` | `task:///{id}/timeline` |

The `meta.json` file contains all task metadata including: `id`, `status`, `provider`, `taskType`, `prompt`, `cwd`, `createdAt`, `updatedAt`, `startedAt`, `completedAt`, `labels`, `output` array, `pendingQuestions`, `model`, `effort`, `timeoutMs`, `sessionId`, `tokenUsage`, `lastOutputAt`.
