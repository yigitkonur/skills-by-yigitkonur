# Integrations matrix

Most third-party agent libraries connect to a Kernel browser via the **CDP WebSocket URL** (`session.cdp_ws_url`) returned from `kernel.browsers.create`. WebDriver BiDi clients use `session.webdriver_ws_url` instead; vision-loop / VLM agents (Computer Use) bypass CDP entirely and go through `kernel.browsers.computer.*`. The matrix below names the right transport per integration. There is no vendor lock-in.

| Lib | Language | TS hookup |
|---|---|---|
| **Playwright** (`playwright`) | TS | `chromium.connectOverCDP(session.cdp_ws_url)` — see `references/patterns/playwright-stagehand-integration.md` |
| **Stagehand** (`@browserbasehq/stagehand`) | TS | `new Stagehand({ env: 'LOCAL', localBrowserLaunchOptions: { cdpUrl: session.cdp_ws_url } })` — see `references/patterns/playwright-stagehand-integration.md` |
| **Puppeteer** (`puppeteer`) | TS | `puppeteer.connect({ browserWSEndpoint: session.cdp_ws_url })` |
| **Claude Agent SDK** (`@anthropic-ai/agent-sdk`) | TS | Template-driven via `kernel create --template claude-agent-sdk`. Internally exposes an MCP tool that calls `kernel.browsers.playwright.execute(sessionId, { code })` against a stealth-mode browser. |
| **Browser Use** | Python only | No TS binding. Deploy a Python Kernel App that hosts Browser Use; invoke from TS via `kernel.invocations.create`. |
| **Vibium** | TS | WebDriver BiDi — pass `session.webdriver_ws_url` instead of `cdp_ws_url`. |
| **Notte** | TS | CDP via `cdp_ws_url`. |
| **Magnitude** | TS | CDP via `cdp_ws_url`. |
| **Laminar** | TS | CDP via `cdp_ws_url`. |
| **Val Town** | TS | Run a Val that calls `@onkernel/sdk` directly; CDP from the Val to the Kernel browser. |
| **Vercel Agent Browser** | TS | `agent-browser -p kernel open <url>` reads `KERNEL_API_KEY`, `KERNEL_HEADLESS`, `KERNEL_STEALTH`, `KERNEL_TIMEOUT_SECONDS`, `KERNEL_PROFILE_NAME`. Programmatic: spawn `agent-browser connect "${session.cdp_ws_url}"`. |
| **1Password** | TS | Credential provider via `kernel.credentialProviders.create({ type: '1password' })`. See `references/patterns/profiles-pools-credentials.md`. |
| **Computer Use** (Anthropic, OpenAI, custom VLM) | Any | Skip CDP entirely. Use `kernel.browsers.computer.captureScreenshot/clickMouse/typeText/scroll/dragMouse`. |

## Patterns common to most CDP integrations

```ts
const session = await kernel.browsers.create({ stealth: true, timeout_seconds: 600 });
try {
  // Hand the URL to whichever framework
  const yourFramework = await connectFramework(session.cdp_ws_url);
  await yourFramework.run();
} finally {
  await kernel.browsers.deleteByID(session.session_id);
}
```

Two rules carry across all of them:

1. **Use the existing default context and page.** All frameworks call `browser.contexts()[0].pages()[0]` (sometimes wrapped). When a framework offers `newContext()` / `newPage()` helpers, prefer the explicit "use existing" path or you'll lose profile state.
2. **Don't trust the framework's `close()` for cleanup.** Frameworks call CDP's `Browser.close` or `Browser.disconnect`, which sever your local connection but leave the Kernel browser running. Always pair `create` with `deleteByID`.

## Vibium (WebDriver BiDi)

```ts
const session = await kernel.browsers.create({ stealth: true });
// Vibium accepts a WebDriver BiDi WebSocket URL
const driver = await Vibium.connect({ wsUrl: session.webdriver_ws_url });
```

## Browser Use over an invocation

```ts
// Python action deployed as a Kernel App handles Browser Use directly.
// From TS:
const inv = await kernel.invocations.create({
  app_name: 'browser-use-runner',
  action_name: 'run_task',
  version: '1.0.0',
  async: true,
  async_timeout_seconds: 1800,
  payload: JSON.stringify({ task: 'Find me cheap flights from SFO to NYC' }),
});
for await (const evt of await kernel.invocations.follow(inv.id)) {
  if (evt.event === 'invocation_state' && evt.invocation.status !== 'queued' && evt.invocation.status !== 'running') {
    return JSON.parse(evt.invocation.output ?? 'null');
  }
}
```

This is the recommended pattern for any framework that doesn't have a TS port: wrap it in a Python Kernel App, invoke from TS.

## Templates

`kernel create --template <name>` scaffolds a ready-to-deploy Kernel App for the integration:

- `stagehand` — Stagehand-driven agent
- `claude-agent-sdk` — Claude Agent SDK with computer-use MCP tool
- `playwright` — vanilla Playwright app
- `browser-use` — Python Browser Use app
- `bare` — minimal `kernel.app('…').action('…', …)` skeleton

Run `kernel create --help` for the live list — templates are added regularly.
