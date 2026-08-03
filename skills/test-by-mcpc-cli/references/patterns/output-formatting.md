# Output Formatting

## Human mode vs JSON mode

Use human mode for exploration and JSON mode for assertions.

```bash
mcpc @research-test help
mcpc --json @research-test help
```

## What JSON mode gives you

- `mcpc --json` returns `sessions` and `profiles`
- `mcpc --json @session` returns session info, capabilities, and discovered tools
- `mcpc --json @session tools-list` returns tool arrays
- `mcpc --json @session grep search` returns per-session matches plus totals
- `mcpc --json @session tasks-list` returns a `tasks` array

## Human-mode tool-result layout

`tools-call`/`tasks-result` render three sections in order: Content, Structured
content, Metadata. Structured content prints only when Content is empty (since
0.3.1) — a tool returning both text and `structuredContent` shows text only in
human mode; `--json` always includes both fields raw. `_meta` (e.g. a result's
`mimeType`) prints last, in human mode's Metadata section; in raw `--json` it's
an ordinary object key, not guaranteed to sort last.

## Error channel behavior

Failures split across streams and payload shapes:

- A tool call that round-trips and comes back `isError: true` is a normal
  payload — it prints on `stdout` exactly like a success, in both human and
  `--json` mode.
- A timeout/no-result failure can also exit `2`, but emits
  `{"error":"...","code":2}` on `stderr` with no `content`/`isError` keys.
- A pure CLI/session failure (bad flag, unknown session, a `--schema`/
  `--schema-mode` mismatch, or a command against a `reconnecting` session)
  never reaches the server — it prints on `stderr`; `--json` uses the same
  `{error,code}` shape.

A harness that only captures `stdout` will miss CLI/session and timeout errors
but will still see server `isError: true` payloads.

## Exit-code rule

Exit code reflects *where* the failure happened, not just whether the
process ran:

| Code | Meaning | Example |
|---|---|---|
| 0 | success | normal call; an unreachable `connect` can also create a `reconnecting` session with 0 |
| 1 | CLI/session result | bad flag, unknown session, command against a broken connection; `grep` also uses 1 for no matches |
| 2 | MCP result or no-result call failure | stdout `isError:true`, or stderr timeout `{error,code}` |
| 3 / 4 | documented network / auth codes | upstream contract; not independently reproduced in this 0.6.0 audit |

Exit code is a reliable first gate since v0.5.0 — `--json` payload inspection
is still the richer signal for *what* went wrong, not *whether* something did.

## `--max-chars` truncation

`--max-chars <n>` hard-cuts human-mode output at the character count — not
word-aware — and appends a trailer stating the original size and cut point.
Ignored entirely in `--json` mode.

## `--full` note

`tools-list --full` matters in human mode.
When you are already in JSON mode, you often have enough schema detail without extra formatting flags.
