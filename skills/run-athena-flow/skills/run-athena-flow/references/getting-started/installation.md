# Installation

## Prerequisites

- **Node.js 20+** — verify with `node --version`
- **git** — required for marketplace plugin/workflow resolution
- **Claude Code** and/or **OpenAI Codex** — at least one agent runtime installed and authenticated

## Install

```bash
npm install -g @athenaflow/cli
```

This installs three binaries:

| Binary | Purpose |
|--------|---------|
| `athena` | Short alias for the CLI |
| `athena-flow` | Full command name |
| `athena-hook-forwarder` | Internal hook bridge (called by Claude Code) |

Verify:

```bash
athena --version
```

## First Run

```bash
cd /your/project
athena
```

On first launch, the setup wizard runs automatically.

### Step 1: Theme

| Theme | Description |
|-------|-------------|
| `dark` | Default. Dark terminal backgrounds. |
| `light` | Light terminal backgrounds. |
| `high-contrast` | Maximum contrast for accessibility. |

### Step 2: Harness

| Harness | Status |
|---------|--------|
| `claude-code` | Production |
| `openai-codex` | Production |
| `opencode` | Coming soon |

The wizard detects which agent runtimes are installed.

### Step 3: Workflow (optional)

Optionally activate a workflow for your sessions. You can skip this and activate workflows later with `--workflow`.

Choices are saved to `~/.config/athena/config.json`. Re-run the wizard any time:

```bash
athena-flow setup
```

## Common Launch Patterns

```bash
# Resume the most recent session
athena-flow resume

# Resume a specific session
athena-flow resume <session-uuid>

# Pick a session interactively
athena-flow sessions

# Start with a workflow
athena-flow --workflow=e2e-test-builder

# Run non-interactively (CI/scripts)
athena-flow exec "run all tests"

# Change isolation level
athena-flow --isolation=permissive

# ASCII-safe glyphs for limited terminals
athena-flow --ascii
```

## Updating

```bash
npm update -g @athenaflow/cli
```

## Platform Support

macOS and Linux. On Windows, use WSL (Unix Domain Socket requirement).
