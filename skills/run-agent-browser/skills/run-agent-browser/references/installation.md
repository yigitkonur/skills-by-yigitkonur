# Installation

## Quick Install

```bash
npm install -g agent-browser    # Global (recommended, native Rust binary)
agent-browser install            # Downloads Chromium

# Alternative: Homebrew (macOS)
brew install agent-browser
agent-browser install

# Alternative: no install (slower, runs via Node.js)
npx agent-browser open example.com
```

## Linux System Dependencies

Chromium requires system libraries on Linux:

```bash
# Install Chromium + all required system dependencies
agent-browser install --with-deps

# Alternative: Playwright dependency installer
npx playwright install-deps chromium
```

## Platform Support

| Platform | Architecture | Native Binary | Node.js Fallback |
|----------|-------------|--------------|-----------------|
| macOS | ARM64 (Apple Silicon) | ✅ | ✅ |
| macOS | x64 (Intel) | ✅ | ✅ |
| Linux | ARM64 | ✅ | ✅ |
| Linux | x64 | ✅ | ✅ |
| Windows | x64 | ✅ | ✅ |

The native Rust binary is preferred when available. The CLI automatically falls back to the Node.js + Playwright daemon when it's not.

## Version Pinning (CI / Production)

```bash
# Pin to exact version for reproducibility
npm install -g agent-browser@0.17.1

# Verify
agent-browser --version
```

## From Source

```bash
git clone https://github.com/vercel-labs/agent-browser.git
cd agent-browser
pnpm install
pnpm build
pnpm build:native  # Optional: compile Rust binary (requires Rust toolchain)
pnpm link --global
agent-browser install
```

## Container / Docker

```dockerfile
FROM node:20-slim

# System dependencies for Chromium
RUN apt-get update && apt-get install -y \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libasound2 libpangocairo-1.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Install with pinned version
RUN npm install -g agent-browser@0.17.1
RUN agent-browser install

# Non-root user (recommended)
RUN useradd -m agent
USER agent
```

## GitHub Actions

```yaml
- name: Install agent-browser
  run: |
    npm install -g agent-browser@0.17.1
    agent-browser install --with-deps

- name: Run browser automation
  run: |
    agent-browser open https://localhost:3000
    agent-browser snapshot -i
    agent-browser screenshot ./results/home.png
    agent-browser close
```

## Verify Installation

```bash
agent-browser --version                        # Check CLI version
agent-browser open https://example.com         # Test browser launch
agent-browser snapshot -i                      # Test snapshot
agent-browser close                            # Clean up
```

## Configuration Precedence

Config is loaded from (lowest to highest priority):

1. Built-in defaults
2. `~/.agent-browser/config.json` — user-level defaults
3. `./agent-browser.json` — project-level config
4. Environment variables (`AGENT_BROWSER_*`)
5. CLI flags

```json
{
  "headed": false,
  "defaultTimeout": 30000,
  "proxy": "http://proxy.example.com:8080",
  "colorScheme": "dark",
  "viewport": { "width": 1280, "height": 720 }
}
```

## Updating

```bash
# Check current version
agent-browser --version

# Update to latest
npm update -g agent-browser

# Update Chromium after CLI update
agent-browser install
```
