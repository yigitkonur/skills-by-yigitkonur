# Installation Guide

Install and verify `mcpc` (the Apify MCP CLI) for testing MCP servers.

## Requirements

- **Node.js 20.0.0+** (required)
- **npm** or **Bun** (package manager)

## Global install (recommended for regular use)

```bash
# npm
npm install -g @apify/mcpc

# Bun
bun install -g @apify/mcpc

# Verify
mcpc --version
# Expected: mcpc 0.1.10 (or later)
```

## Local install from cloned repo (for development/testing)

```bash
# Clone the repository
git clone https://github.com/apify/mcp-cli.git
cd mcp-cli

# Install dependencies
npm install

# Build TypeScript to dist/
npm run build

# Link globally for local testing
npm link

# Verify the linked version
mcpc --version

# Watch mode during development
npm run build:watch
```

### Local development scripts

```bash
npm run build              # Compile TypeScript to dist/
npm run build:watch        # Watch mode (auto-rebuild on changes)
npm run clean              # Remove dist/ directory
npm run lint               # ESLint + Prettier check
npm run lint:fix           # Auto-fix linting issues
npm run format             # Format with Prettier
npm run test:unit          # Run unit tests
npm run test:unit -- --watch  # Unit tests in watch mode
npm test                   # All tests (unit + e2e)
```

### Running e2e tests locally

```bash
./test/e2e/run.sh                 # Run all e2e tests
./test/e2e/run.sh -p 4            # Parallel (4 workers)
./test/e2e/run.sh --keep          # Keep test artifacts for inspection
./test/e2e/run.sh --runtime bun   # Run with Bun instead of Node
```

## Bun runtime

mcpc supports Bun as an alternative runtime. Install Bun if needed:

```bash
curl -fsSL https://bun.sh/install | bash
```

## Verify installation

Run this checklist after installing:

```bash
# 1. Version check
mcpc --version

# 2. Help text
mcpc --help

# 3. No active sessions (clean state)
mcpc
# Expected: "No active sessions"

# 4. Quick connectivity test (if you have a server URL)
mcpc https://your-mcp-server.com connect @verify-test
mcpc @verify-test ping
mcpc @verify-test close
```

## Environment variables

| Variable | Purpose | Example |
|---|---|---|
| `MCPC_VERBOSE` | Enable debug logging | `MCPC_VERBOSE=1` |
| `MCPC_JSON` | Default to JSON output | `MCPC_JSON=1` |
| `MCPC_HOME_DIR` | Override `~/.mcpc` data directory | `MCPC_HOME_DIR=/tmp/mcpc-test` |
| `HTTP_PROXY` | HTTP proxy for outbound connections | `HTTP_PROXY=http://proxy:8080` |
| `HTTPS_PROXY` | HTTPS proxy for outbound connections | `HTTPS_PROXY=http://proxy:8080` |
| `NO_PROXY` | Bypass proxy for these hosts | `NO_PROXY=localhost,127.0.0.1` |

## Troubleshooting installation

| Symptom | Cause | Fix |
|---|---|---|
| `mcpc: command not found` | Not in PATH | `npm install -g @apify/mcpc` or check `npm bin -g` |
| `node: unsupported engine` | Node.js too old | Upgrade to Node.js 20+ |
| Permission denied on global install | npm permissions | `sudo npm install -g @apify/mcpc` or fix npm prefix |
| `npm link` doesn't work | Build not run | Run `npm run build` first, then `npm link` |
| Stale version after update | npm cache | `npm cache clean --force && npm install -g @apify/mcpc` |

## Data directories

mcpc stores data in `~/.mcpc/` (overridable via `MCPC_HOME_DIR`):

```
~/.mcpc/
├── sessions.json          # Active session metadata
├── profiles.json          # OAuth profile metadata
├── credentials            # Fallback credential storage (Linux headless)
├── history                # Interactive shell history
├── bridges/               # Unix sockets for bridge IPC
│   └── <session-name>.sock
└── logs/                  # Bridge process logs
    └── bridge-<session-name>.log
```

For isolated testing, set a custom home directory:

```bash
export MCPC_HOME_DIR=/tmp/mcpc-isolated-test
mcpc <server> connect @isolated
```
