# JSONL streaming — codex `--json` event format and consumption

`codex exec --json` (and `codex exec review --json`) emits newline-delimited JSON to stdout. Each line is one event. The skill captures the stream to disk via `tee`, parses it through `codex-json-filter.sh` for human-readable Monitor lines, and reads the structured events for manifest updates (e.g. capturing `thread_id`).

## Event types and their payloads

Authoritative for codex-cli 0.129.0+. Verify with a smoke test if codex bumps:

```bash
codex exec --dangerously-bypass-approvals-and-sandbox --json --skip-git-repo-check \
    -m gpt-5.5 -c model_reasoning_effort=xhigh \
    "compute 2+2 and exit. answer with just the number." \
    2>&1 | tee /tmp/smoke.jsonl
```

| Event `type` | Payload (selected fields) | When emitted |
|---|---|---|
| `thread.started` | `thread_id` | First event. Capture into `manifest.entries[i].codex_thread_id` for rescue. |
| `turn.started` | `{}` | Beginning of a model turn. |
| `item.started` | `item.{type, id}` and per-type fields | A new item begins. See item types below. |
| `item.updated` | same as `item.started` plus partial state | Streaming progress on a long item (rare). |
| `item.completed` | same as `item.started` plus terminal fields | Item finished. |
| `turn.completed` | `usage:{input_tokens, cached_input_tokens, output_tokens}` | End of a model turn. Token accounting. |
| `error` | `message` (or `error.message`) | Failure signal. |
| `task.started` / `task.completed` | task envelope (background tasks via codex-companion) | Only when running through codex-companion's `task` subcommand; the dispatcher's modes don't trigger these directly. |

## Item types

`item.type` values inside `item.started` / `item.completed`:

| `item.type` | Selected fields | Filter line |
|---|---|---|
| `agent_message` | `text`, `phase` (`final_answer` / others) | `[SAID]` for `phase=final_answer`; `[MSG]` for others |
| `reasoning` | `text` | `[THINK]` (first line of text only) |
| `command_execution` | `command`, `exit_code` (on completed), `aggregated_output` | `[CMD>]` on started; `[CMD✓]` (exit 0) or `[CMD✗]` on completed |
| `file_change` | `changes:[{path, action}]` | `[FILE]` with path count |
| `mcp_tool_call` | `server`, `tool`, `arguments`, `result` | `[MCP>]` / `[MCP✓]` |
| `dynamic_tool_call` | similar to mcp | `[TOOL>]` / `[TOOL✓]` |
| `web_search` | `query`, `results_count` | `[WEB]` |
| `plan_update` | `plan` (markdown) | `[PLAN]` |

## Terminal success signal

Two equally valid signals:
1. `item.completed` with `item.type=agent_message` AND `phase=final_answer`.
2. `turn.completed` with non-empty `usage`.

The runner accepts either. In practice, both arrive within a few hundred milliseconds of each other.

If neither arrives and the codex process exits 0, the agent likely produced output via `-o` but the JSONL stream lost the terminal events. See "MCP-active dropout" below.

## MCP-active dropout (upstream issue [#15451](https://github.com/openai/codex/issues/15451))

When MCP servers are configured in the user's `~/.codex/config.toml`, the `codex exec --json` stream may silently drop events. Specifically:
- The `agent_message phase=final_answer` event sometimes never appears.
- `turn.completed` may also be missing.
- The non-terminal events (`thread.started`, `item.completed (command_execution)`) usually still arrive.

Mitigation:
- The skill **always pairs `--json` with `-o <file>`**. The `-o` file is unaffected by the JSONL dropout. The runner reads the file as truth for "did codex produce output."
- If the file is non-empty AND codex exit code is 0, mark the entry `done` with advisory `last_error="json_event_dropped"`. The audit surfaces this so a human can spot-check.
- If the file is empty AND no `turn.completed`, mark `failed`.

The JSONL stream is supplementary. Do not block on it.

## Filter pipeline (`codex-json-filter.sh`)

Reads JSONL on stdin, emits one human-readable line per event with a UTC timestamp prefix:

```
02:08:25Z [START] thread=019e0a7e
02:08:25Z [TURN>] model-turn begin
02:08:26Z [CMD>] git status
02:08:26Z [CMD✓] git status (exit 0, 0.1s)
02:08:28Z [THINK] Plan: 1) read schema, 2) ...
02:08:29Z [SAID] Done. New migration is at db/migrations/20260508_add_users.sql.
02:08:30Z [TURN<] tokens: in=8234 out=1567 cached=1200
```

Verbosity levels:

| Level | Includes |
|---|---|
| `minimal` | `[START]`, `[SAID]`, `[ERR]` only |
| `normal` (default) | minimal + `[CMD>]`, `[CMD✓]`, `[TURN<]` |
| `verbose` | normal + `[THINK]`, `[FILE]`, `[MCP>]`, full `aggregated_output` |

Set via `--level <minimal|normal|verbose>` flag or `LEVEL=verbose` env.

## Line buffering

The filter uses `awk '{...; fflush();}'` and `grep --line-buffered` whenever it pipes through grep. Without these, a 4 KB pipe buffer means events arrive in batches separated by minutes. Test before shipping any custom filter:

```bash
( for i in 1 2 3; do printf '{"type":"item.completed","item":{"type":"agent_message","text":"line %d"}}\n' "$i"; sleep 1; done ) \
    | bash codex-json-filter.sh
```

Lines should arrive at 1-second intervals. If they all arrive together at the end, buffering is broken.

## Capturing `thread_id`

The runner captures `thread_id` from the first JSONL event:

```bash
thread_id=$(jq -r 'select(.type == "thread.started") | .thread_id' < "$jsonl_path" | head -1)
python3 manifest-update.py --manifest "$MANIFEST" --entry "$slug" \
    --set "codex_thread_id=$thread_id"
```

Rescue uses `codex_thread_id` to invoke `codex exec resume <id>` for single-mode entries.

## Capturing token usage

`turn.completed.usage` carries the token spend per turn:

```bash
usage=$(jq -c 'select(.type == "turn.completed") | .usage' < "$jsonl_path" | tail -1)
# usage = {"input_tokens": 8234, "cached_input_tokens": 1200, "output_tokens": 1567}
```

The runner records this into `manifest.entries[i].mode_state.tokens_used`. Audit surfaces the total.

## Custom event handling

If you need to react to a specific event type beyond what the filter does:

```bash
# Tail the JSONL file in another process; jq-extract specific events.
tail -F "$jsonl_path" | jq --unbuffered 'select(.type == "item.completed" and .item.type == "file_change")'
```

The `--unbuffered` flag on jq is the equivalent of `--line-buffered` for grep.

## Anti-patterns

- Reading `turn.completed` as the only success signal. `agent_message phase=final_answer` is equivalent and sometimes arrives first.
- Treating MCP-active dropout as a runner bug. It's an upstream codex issue. The `-o` file is the truth.
- Tailing JSONL with `tail -f` instead of `tail -F`. `-f` follows the inode; if codex rotates or replaces the file, the tail dies.
- Filtering only success events. Coverage rule from `monitor-contract.md`: filter must surface failures.
- Re-parsing the JSONL on every Monitor tick. The filter parses once; downstream consumers read parsed lines.

## Forensics

If a run claims success but the user can't find the answer:

```bash
# Did codex emit a final-answer agent_message?
jq 'select(.type == "item.completed" and .item.type == "agent_message" and .item.phase == "final_answer")' < <jsonl-path>

# Or did the JSONL stream silently drop?
ls -la <answer-path>  # is -o file non-empty?
jq 'select(.type == "turn.completed")' < <jsonl-path>  # is turn.completed present?
```

If the answer file is non-empty but JSONL events are missing, MCP dropout is the likely culprit. Surface "advisory: json_event_dropped" and confirm the answer matches expectations.
