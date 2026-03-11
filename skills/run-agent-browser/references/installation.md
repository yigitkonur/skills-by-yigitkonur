# Installation

## Global Install (recommended)

```bash
npm install -g agent-browser
agent-browser install
```

## Quick Start with npx

```bash
npx agent-browser install
npx agent-browser open example.com
```

> Note: `npx` is slower than a global install due to package resolution on each run.

## Project Install

```bash
npm install agent-browser
npx agent-browser install
```

## Homebrew (macOS)

```bash
brew install agent-browser
agent-browser install
```

## From Source

```bash
git clone https://github.com/vercel-labs/agent-browser.git
cd agent-browser
pnpm install
pnpm build
pnpm build:native
./bin/agent-browser install
pnpm link --global
```

## Linux Dependencies

Install system dependencies required by Chromium:

```bash
# Via agent-browser
agent-browser install --with-deps

# Or via Playwright directly
npx playwright install-deps chromium
```

## Custom Browser Executable

Use a specific browser binary instead of the bundled one:

```bash
# Via CLI flag
agent-browser --executable-path /path/to/chrome open example.com

# Via environment variable
export AGENT_BROWSER_EXECUTABLE_PATH=/path/to/chrome
agent-browser open example.com
```

## Serverless Deployment

Use `@sparticuz/chromium` with the BrowserManager API for serverless environments:

```javascript
import chromium from "@sparticuz/chromium";
import { BrowserManager } from "agent-browser";

const browser = await BrowserManager.launch({
  executablePath: await chromium.executablePath(),
  args: chromium.args,
});
```

## AI Agent Setup

Add agent-browser as a skill for AI coding agents:

```bash
npx skills add vercel-labs/agent-browser
```

Works with: Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, Goose, OpenCode, Windsurf.

### AGENTS.md / CLAUDE.md Snippet

Add to your project's agent instructions file:

```markdown
## Browser Automation

Use `agent-browser` for browser tasks: navigation, form filling, screenshots, data extraction, and testing.

- Run `agent-browser open <url>` to open a page and get its content
- Run `agent-browser act "<instruction>" --url <url>` to perform actions
- Run `agent-browser observe "<instruction>" --url <url>` to find interactive elements
- Run `agent-browser extract "<instruction>" --url <url>` to extract structured data
```
