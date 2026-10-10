# The Modern Sentry CLI (`sentry` binary) Reference

Complete manual for the modern Sentry CLI (`cli.sentry.dev`, installed via `curl -fsSL https://cli.sentry.dev/install | bash` or `brew install getsentry/tools/sentry`).

---

## Installation & Authentication

```bash
# Official installer (macOS / Linux)
curl -fsSL https://cli.sentry.dev/install | bash

# Homebrew (macOS)
brew install getsentry/tools/sentry
```

### Interactive & Automated Login

```bash
# Interactive browser OAuth login (saves session to SQLite ~/.config/sentry/cli.db)
sentry auth login

# Check authentication status
sentry auth status
```

In headless CI or automated terminal environments (`~/.zshrc`):
```bash
export SENTRY_AUTH_TOKEN="sntryu_your_personal_token_here"
export SENTRY_FORCE_ENV_TOKEN=1
```

---

## Target Syntax

- `<org>/<project>`: Targets a single project (e.g. `my-org/backend-api`).
- `<org>/`: Targets **all** projects in an organization (trailing slash required).
- `(omitted)`: Auto-detected from local project config or DSN.

---

## Core Commands

| Command | Subcommands | Purpose |
|---|---|---|
| `sentry issue` | `list`, `view`, `explain`, `plan`, `events`, `resolve`, `archive` | Issue lifecycle, Seer AI diagnosis, and resolution |
| `sentry mcp` | *(default)* | Starts local stdio MCP server for AI coding assistants |
| `sentry explore` | `-d errors`, `-d spans`, `-d metrics`, `-d logs`, `-d replays` | Aggregate analytics across Sentry datasets |
| `sentry log` | `list`, `view` | Structured log inspection and live streaming (`-f`) |
| `sentry trace` | `list`, `view`, `logs` | Distributed trace trees and span waterfalls |
| `sentry span` | `list`, `view` | Spans within a project or trace |
| `sentry replay` | `list`, `view` | Frontend Session Replay sessions |
| `sentry monitor` | `list`, `view`, `checkin` | Cron and Uptime monitors |
| `sentry dsn` | `list`, `create`, `view` | Client key (DSN) management |
| `sentry api` | `<path>` | Raw REST API escape hatch |

---

## Seer AI Incident Diagnosis & Fix Planning

The modern `sentry` binary integrates directly with Sentry Seer AI:

```bash
# 1. Automated root-cause analysis
sentry issue explain <ID_OR_@latest>

# 2. Automated step-by-step code remediation plan
sentry issue plan <ID_OR_@latest>
```

> [!TIP]
> Seer AI requires repository context. If the project repo is not linked via Sentry UI, upload code mappings using `sentry code-mappings upload`.

---

## Built-In Model Context Protocol (MCP) Server

Any AI coding assistant can run Sentry's MCP server directly through the CLI without extra npm dependencies:

```json
{
  "mcpServers": {
    "sentry": {
      "command": "sentry",
      "args": ["mcp"]
    }
  }
}
```

---

## Raw API Escape Hatch

```bash
sentry api 'organizations/<org>/issues/?query=is:unresolved&limit=5'
sentry schema
```
