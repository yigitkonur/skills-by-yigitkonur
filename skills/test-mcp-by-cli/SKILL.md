---
name: test-mcp-by-cli
description: Use skill if you need to test MCP servers with philschmid/mcp-cli, inspect tools, call them, or debug config, transport, auth, and arguments.
---

# Test MCP By CLI

Validate MCP servers with `mcp-cli` (philschmid/mcp-cli v0.3.0) using release-verified behavior first, then use official repo source only when it matches what the installed binary actually does.

## Core rules

- Execute commands directly and sequentially.
- Do not write helper scripts unless explicitly requested.
- Treat server work as incomplete until verification checks pass.
- Prefer single-server commands while debugging.
- After rebuilding a server, always retest with `MCP_NO_DAEMON=1`.
- Treat `mcp-cli --help` and real command output as the primary behavioral source for the installed release.
- Remember that `call` returns the raw MCP JSON envelope on stdout in the installed `v0.3.0` binary.

## What to load first

Use this progressive order to keep context tight:

1. **This file (`SKILL.md`)** for command strategy, decision rules, and execution flow.
2. **Skill references** for concrete command blocks:
   - `references/testing-flow.md` — 8-phase verification sequence and checklist
   - `references/configuration-and-arguments.md` — config format, search paths, tool filtering, env var substitution, JSON input methods
   - `references/output-debugging-and-chaining.md` — raw output parsing, stream handling, chaining, CI/CD patterns, verified environment variables
   - `references/errors-and-recovery.md` — common errors, exit codes, daemon behavior, and release inconsistencies
3. **Read only the relevant reference** for the current problem instead of loading all files.
4. Return to this file when you need the overall workflow or decision rules.

## Execution workflow

1. Follow the 8-phase verification order in `references/testing-flow.md`.
2. Use config and JSON argument patterns from `references/configuration-and-arguments.md`.
3. Use stream handling, chaining, and env controls from `references/output-debugging-and-chaining.md`.
4. If any command fails, apply diagnosis from `references/errors-and-recovery.md`.
5. Do not report done until all checklist items pass.

## Decision rules

Apply when things go wrong:

- **If Phase 1 (connect) fails**: stop everything. Fix config or server startup before proceeding.
- **If a tool is missing from inventory**: check `disabledTools` in config — it takes precedence over `allowedTools`. Read `references/configuration-and-arguments.md`.
- **If calls return stale results**: use `MCP_NO_DAEMON=1` — the daemon caches old server processes for 60s. Read daemon section in `references/errors-and-recovery.md`.
- **If calls hang**: lower timeout with `MCP_TIMEOUT=30` (default is 1800s). Read env var section in `references/output-debugging-and-chaining.md`.
- **If debugging protocol issues**: use `MCP_DEBUG=1` to see full protocol traffic on stderr.
- **If `mcp-cli` (no args) hangs**: it connects ALL servers. Use `mcp-cli info <server>` to test one at a time.
- **If you get `AMBIGUOUS_COMMAND`**: always use a subcommand — `call`, `info`, or `grep`.
- **If output parsing looks wrong**: `call` returns raw JSON in this release. Extract content with `jq -r '.content[0].text'`. Read `references/output-debugging-and-chaining.md`.
- **If docs and binary disagree**: trust the installed binary and real command output over inferred internals.

## Repository-specific execution mode

When validating this repository's own source code, run the local CLI implementation:

```bash
bun run src/index.ts -c ./mcp_servers.json info filesystem
bun run src/index.ts -c ./mcp_servers.json call filesystem read_file '{"path":"./README.md"}'
```

Use globally installed `mcp-cli` for all other workflows.

## Minimal quick start

```bash
# Install if missing
which mcp-cli || curl -fsSL https://raw.githubusercontent.com/philschmid/mcp-cli/main/install.sh | bash

# Connect and inspect
mcp-cli info my-server
mcp-cli info my-server my-tool

# Happy path + error path
mcp-cli call my-server my-tool '{"param":"value"}'
mcp-cli call my-server my-tool '{}'

# Fresh-connection check after rebuild
MCP_NO_DAEMON=1 mcp-cli call my-server my-tool '{"param":"value"}'
```

If any step fails, continue debugging; do not claim completion.

## Reference files

| File | When to read |
|---|---|
| `references/testing-flow.md` | Running the full 8-phase verification sequence or the final checklist |
| `references/configuration-and-arguments.md` | Setting up config files, tool filtering, env var substitution, or passing JSON arguments |
| `references/output-debugging-and-chaining.md` | Parsing output, piping between tools, CI/CD scripts, or controlling behavior via env vars |
| `references/errors-and-recovery.md` | Any command fails — error type lookup, exit code interpretation, daemon issues, or release inconsistencies |
