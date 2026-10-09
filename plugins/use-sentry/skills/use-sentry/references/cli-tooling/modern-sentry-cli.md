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
| `sentry issue` | `list`, `view`, `explain`, `plan`, `events`, `resolve`, `archive` | Issue lifecycle, Seer AI diagnosis, and resolution |
| `sentry explore` | `-d errors`, `-d spans`, `-d logs`, `-d replays` | Aggregate analytics and metrics |
| `sentry log` | `list`, `view` | Structured log inspection and live streaming (`-f`) |
| `sentry trace` | `list`, `view`, `logs` | Distributed trace trees and span waterfalls |
| `sentry span` | `list`, `view` | Spans within a project or trace |
| `sentry replay` | `list`, `view` | Frontend Session Replay sessions |
| `sentry api` | `<path>` | Raw REST API escape hatch |

## Seer AI Incident Diagnosis & Fix Planning

The modern `sentry` binary integrates directly with Sentry Seer AI:

```bash
# 1. Automated root-cause analysis
sentry issue explain <ID_OR_@latest>

# 2. Automated step-by-step code remediation plan
sentry issue plan <ID_OR_@latest>
```

- `sentry issue explain`: Analyzes connected repository commits, error stack frames, and breadcrumbs to diagnose the root cause and provide reproduction steps.
- `sentry issue plan`: Generates exact file diffs and code patch recommendations to fix the issue.

## Raw API Escape Hatch

```bash
sentry api 'organizations/<org>/issues/?query=is:unresolved&limit=5'
sentry schema
```
