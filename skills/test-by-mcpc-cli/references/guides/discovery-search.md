# Discovery and Search

Start with the native discovery surface before building custom filters.

## First look

```bash
mcpc @session
mcpc @session help
mcpc @session tools-list
mcpc @session tools-list --full
mcpc @session resources-list
mcpc @session prompts-list
mcpc @session resources-templates-list
```

`mcpc @session` (no subcommand) prints server title, description, website URL, capabilities, instructions, and a ready-to-run command cheat-sheet. `mcpc @session help` prints the full options/commands reference instead — reach for it when you need the flag list, not the server summary.

## Modern session-scoped commands (0.7.0)

- `server-discover` — live `server/discover` request; needs MCP 2026-07-28+, fails with an explanatory exit 2 on older-protocol sessions. Detail: `references/guides/protocol-versions.md`.
- `skills-list` / `skills-get <skill> [file]` — official `io.modelcontextprotocol/skills` extension with SHA-256 and byte-size verification. Detail: `references/guides/skills-testing.md`.
- `resources-directory-read <uri>` — reads directory resources advertising `"directoryRead": true`.
- `completion-complete prompt|resource <ref>` — requests completions for prompt arguments and resource templates.

## Before a session exists

`mcpc connect` with no arguments scans standard config locations (`.mcp.json`, `.cursor/mcp.json`, `~/.claude.json`, Claude Desktop, Windsurf, etc.) and connects every entry found — see `mcpc help connect` and `references/patterns/config-resolution.md`. In 0.7.0, entries in `./` with `${VAR}` are skipped for safety unless an explicit path is supplied.

## Native grep

```bash
mcpc grep search
mcpc @session grep actor
mcpc grep config --resources --prompts
mcpc grep 'search|find' -E
mcpc grep file -m 5 --json
```

Current behavior:

- default grep scope is tools plus instructions; `--instructions` isolates instructions only
- `--resources` and `--prompts` change the search domain; combine flags when needed
- matches text inside descriptions too, not just names — expect false positives if you wanted an exact name filter
- instruction matches show a bounded, highlighted snippet, not just a yes/no
- session grep (`mcpc @session grep ...`) searches one connection; bare `mcpc grep ...` searches every active session with a per-session breakdown
- exit `0` on match, `1` on no match (grep convention)

## JSON-RPC method-name aliases

Session subcommands also accept raw MCP JSON-RPC method names as aliases for the hyphenated form. In 0.7.0, `mcpc help tools/list` correctly resolves command help:

```bash
mcpc @session tools/list                               # == tools-list
mcpc @session tools/call web-search 'queries:=["x"]'   # == tools-call
mcpc @session resources/list                           # == resources-list
```

## Removed: bare `tools`/`resources`/`prompts` shorthand

`mcpc @session tools`, `resources`, `prompts` (no `-list` suffix) were removed in v0.3.0 — they now error with a "did you mean" suggestion. Always teach the explicit `*-list` form.

## When to switch to `jq`

Use JSON filtering after native discovery when you need:

- exact schema field extraction
- diffable machine output
- batch assertions in CI
- complex filters across annotations or task metadata

For exact JSON extraction and filters, continue with `references/patterns/jq-patterns.md` and `references/patterns/tool-filtering.md`.
