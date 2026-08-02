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
`mimeType`) prints last, in both modes, whenever the server sets it.

## Error channel behavior

Two different failure shapes land on two different streams:

- A tool call that round-trips and comes back `isError: true` is a normal
  payload — it prints on `stdout` exactly like a success, in both human and
  `--json` mode.
- A pure CLI-usage failure (bad flag, unknown session, a `--schema`/
  `--schema-mode` mismatch caught by mcpc's own validator) never reaches the
  server — it prints on `stderr`. In `--json` mode this shape is
  `{"error": "...", "code": N}`, not the tool-result shape.

A harness that only captures `stdout` will miss CLI-usage errors but will
still see `isError: true` payloads.

## Exit-code rule

Exit code reflects *where* the failure happened, not just whether the
process ran:

| Code | Meaning | Example |
|---|---|---|
| 0 | success | normal call, `isError` absent or `false` |
| 1 | client error, before any round-trip | bad flag, unknown session, `--schema`/`--schema-mode` mismatch |
| 2 | server error, after a round-trip | `isError: true` result, unknown tool, server-rejected arguments, timeout-as-tool-error |
| 3 | network error | connection refused, transport timeout with no response |
| 4 | auth error | expired or invalid OAuth token |

Exit code is a reliable first gate since v0.5.0 — `--json` payload inspection
is still the richer signal for *what* went wrong, not *whether* something did.

## `--max-chars` truncation

`--max-chars <n>` hard-cuts human-mode output at the character count — not
word-aware — and appends a trailer stating the original size and cut point.
Ignored entirely in `--json` mode.

## `--full` note

`tools-list --full` matters in human mode.
When you are already in JSON mode, you often have enough schema detail without extra formatting flags.
