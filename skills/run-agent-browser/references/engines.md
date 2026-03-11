# Browser Engines

## Chrome (Default)

Chrome/Chromium is the default engine. Auto-discovered, launched, and managed via CDP.

### Binary Discovery

| Platform | Locations |
|----------|-----------|
| macOS | /Applications/Google Chrome.app, Canary, Chromium.app, Playwright cache |
| Linux | google-chrome, google-chrome-stable, chromium-browser, chromium in PATH, Playwright cache |
| Windows | %LOCALAPPDATA%\Google\Chrome\..., C:\Program Files\..., C:\Program Files (x86)\... |

If not found: `agent-browser install`

### Usage

```bash
agent-browser open example.com                        # default, no flag needed
agent-browser --engine chrome open example.com         # explicit
```

### Custom Binary

```bash
agent-browser --executable-path /path/to/chromium open example.com
# or
AGENT_BROWSER_EXECUTABLE_PATH=/path/to/chromium
```

### Chrome-Specific Features

Extensions (`--extension`), persistent profiles (`--profile`), storage state (`--state`), file URL access (`--allow-file-access`), headed mode (`--headed`), custom launch args (`--args`).

### Containers and CI

```bash
agent-browser --args "--no-sandbox" open example.com
```

Automatically adds `--no-sandbox` in container environments (Docker, Podman, root).

## Lightpanda

Headless browser engine built from scratch in Zig. Instant start, 10x less memory, 10x faster.

### Installation

```bash
# macOS ARM
curl -LO https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-aarch64-macos
chmod +x lightpanda-aarch64-macos
sudo mv lightpanda-aarch64-macos /usr/local/bin/lightpanda

# Linux x86_64
curl -LO https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux
chmod +x lightpanda-x86_64-linux
sudo mv lightpanda-x86_64-linux /usr/local/bin/lightpanda
```

### Usage

```bash
agent-browser --engine lightpanda open example.com
# or
AGENT_BROWSER_ENGINE=lightpanda
# or config
{"engine": "lightpanda"}
```

### Custom Binary Path

```bash
agent-browser --engine lightpanda --executable-path /path/to/lightpanda open example.com
```

### Differences from Chrome

Not supported: extensions, persistent profiles, storage state, file access, headed mode, screenshots (depends on CDP support).

### When to Use

- Fast scraping/data extraction
- Speed + low memory workflows
- CI/CD with constrained resources
- High-volume parallel automation

Use Chrome for full fidelity, extensions, persistent profiles.
