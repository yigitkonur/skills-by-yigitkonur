---
name: mcp-cli
description: Comprehensive MCP server verification and debugging with mcp-cli. Use when Codex needs to configure MCP servers, inspect tool schemas, run end-to-end tool calls, validate failure behavior, troubleshoot connection/auth/filtering issues, or prove server changes with direct CLI commands (without writing helper scripts).
---

# MCP CLI Testing Playbook

Validate MCP servers with direct terminal commands and a strict pass/fail workflow.

## Core rules

- Execute commands directly and sequentially.
- Do not write helper scripts unless explicitly requested.
- Treat server work as incomplete until verification checks pass.
- Prefer single-server commands while debugging.
- After rebuilding a server, retest with `MCP_NO_DAEMON=1`.

## What to load first

Use this progressive order to keep context tight:

1. **This file (`SKILL.md`)** for command strategy and execution rules.
2. **Skill references** for concrete command blocks:
   - `references/testing-flow.md`
   - `references/configuration-and-arguments.md`
   - `references/output-debugging-and-chaining.md`
   - `references/errors-and-recovery.md`
3. **Project docs** for deeper product behavior:
   - `../docs/getting-started.md`
   - `../docs/configuration.md`
   - `../docs/commands.md`
   - `../docs/testing-guide.md`
   - `../docs/troubleshooting.md`
   - `../docs/advanced-usage.md`
   - `../docs/internals.md`
4. **README files** for user-facing framing and examples:
   - `README.md` (repo CLI guide)
   - `../README.md` (workspace docs index)

## Repository-specific execution mode

When validating this repository source code itself, run the local CLI implementation:

```bash
bun run src/index.ts -c ./mcp_servers.json info filesystem
bun run src/index.ts -c ./mcp_servers.json call filesystem read_file '{"path":"./README.md"}'
```

Use globally installed `mcp-cli` for normal external workflows.

## Execution workflow

1. Follow the five-step verification order in `references/testing-flow.md`.
2. Use config and JSON argument patterns from `references/configuration-and-arguments.md`.
3. Use stream handling, chaining, and env controls from `references/output-debugging-and-chaining.md`.
4. If any command fails unexpectedly, apply fixes in `references/errors-and-recovery.md`.
5. Do not report done until all checklist commands pass.

## Minimal quick start

```bash
# Install if missing
which mcp-cli || curl -fsSL https://raw.githubusercontent.com/philschmid/mcp-cli/main/install.sh | bash

# Inspect server and schema
mcp-cli info my-server
mcp-cli info my-server my-tool

# Happy path + failure path
mcp-cli call my-server my-tool '{"param":"value"}'
mcp-cli call my-server my-tool '{}'

# Fresh-connection check after rebuild
MCP_NO_DAEMON=1 mcp-cli call my-server my-tool '{"param":"value"}'
```

If any step fails, continue debugging; do not claim completion.
