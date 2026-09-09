# The Modern Sentry CLI (`sentry` binary) Reference

Complete manual for the modern Sentry CLI (`cli.sentry.dev`, installed via `brew install getsentry/tools/sentry`).

## Installation & Configuration

```bash
# macOS
brew install getsentry/tools/sentry

# Linux
curl -fsSL https://cli.sentry.dev/install | bash
```

In `~/.zshrc`:
```bash
export SENTRY_AUTH_TOKEN="sntryu_your_personal_token_here"
export SENTRY_FORCE_ENV_TOKEN=1
```

## Target Syntax

- `<org>/<project>`: Targets a single project (e.g. `zeo-agency/project-noah`).
- `<org>/`: Targets **all** projects in an organization (trailing slash required).

## Core Commands

| Command | Subcommands | Purpose |
|---|---|---|
| `sentry issue` | `list`, `view`, `events`, `resolve`, `archive` | Issue lifecycle and diagnosis |
| `sentry explore` | `-d errors`, `-d spans`, `-d logs`, `-d replays` | Aggregate analytics and metrics |
| `sentry log` | `list`, `view` | Structured log inspection and live streaming (`-f`) |
| `sentry trace` | `list`, `view`, `logs` | Distributed trace trees and span waterfalls |
| `sentry span` | `list`, `view` | Spans within a project or trace |
| `sentry replay` | `list`, `view` | Frontend Session Replay sessions |
| `sentry api` | `<path>` | Raw REST API escape hatch |

## Raw API Escape Hatch

```bash
sentry api 'organizations/<org>/issues/?query=is:unresolved&limit=5'
sentry schema
```
