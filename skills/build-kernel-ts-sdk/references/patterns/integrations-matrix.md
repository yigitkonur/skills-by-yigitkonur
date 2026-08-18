# Integrations matrix

Most third-party agent libraries connect to a Kernel browser via the **CDP WebSocket URL** (`session.cdp_ws_url`) returned from `kernel.browsers.create`. WebDriver BiDi clients use `session.webdriver_ws_url` instead; vision-loop / VLM agents (Computer Use) bypass CDP entirely and go through `kernel.browsers.computer.*`. The matrix below names the right transport per integration. It also lists a few entries that are **not** drivers (Laminar is instrumentation, 1Password is a credential provider) — those wrap or feed a driver rather than replacing one. There is no vendor lock-in.

| Lib | Language | TS hookup |
|---|---|---|
| **Playwright** (`playwright`) | TS | `chromium.connectOverCDP(session.cdp_ws_url)` — see `references/patterns/playwright-stagehand-integration.md` |
| **Stagehand v4** (`@browserbasehq/stagehand`) | TS | v4 drives through a Chrome extension, so mirror it onto the browser first (`kernel.browsers.fs.uploadZip(session.session_id, { dest_path, zip_file })`), then `const browser = await localBrowser.connect({ cdpUrl: session.cdp_ws_url }); const sh = await Stagehand.create({ browser, model: { modelName: 'openai/gpt-4o', apiKey } })`. `new Stagehand({ env, localBrowserLaunchOptions })` is **v3-only** — v4's constructor is private and has no `env`. See `references/patterns/playwright-stagehand-integration.md` |
| **Puppeteer** (`puppeteer`) | TS | `puppeteer.connect({ browserWSEndpoint: session.cdp_ws_url })` |
| **Claude Agent SDK** (`@anthropic-ai/claude-agent-sdk`) | TS | Template-driven — see *Templates* below for the full non-interactive `kernel create` invocation. Internally exposes an `execute_playwright` MCP tool that calls Kernel's Playwright Execution API (`kernel.browsers.playwright.execute`) against a stealth-mode browser. |
| **Browser Use** | Python only | No TS binding. Deploy a Python Kernel App that hosts Browser Use; invoke from TS via `kernel.invocations.create`. |
| **Vibium** (`vibium`) | TS | WebDriver BiDi — `browser.start(session.webdriver_ws_url)`, not `cdp_ws_url`. |
| **Notte** | TS | CDP via `cdp_ws_url`. |
| **Magnitude** | TS | CDP via `cdp_ws_url`. |
| **Laminar** (`@lmnr-ai/lmnr`) | TS | **Not a driver — observability.** Call `Laminar.initialize({ projectApiKey, instrumentModules: { playwright: { chromium }, kernel: Kernel } })` before your normal `chromium.connectOverCDP(session.cdp_ws_url)`; Playwright owns the CDP connection, Laminar traces it. |
| **Val Town** | TS | Run a Val that calls `@onkernel/sdk` directly; CDP from the Val to the Kernel browser. |
| **Vercel Agent Browser** | TS | `agent-browser -p kernel open <url>` reads `KERNEL_API_KEY`, `KERNEL_HEADLESS`, `KERNEL_STEALTH`, `KERNEL_TIMEOUT_SECONDS`, `KERNEL_PROFILE_NAME`. Programmatic: spawn `agent-browser connect "${session.cdp_ws_url}"`. |
| **1Password** | TS | Credential provider — register via *Integrations → Connect 1Password* in the Kernel dashboard (recommended) or `kernel.credentialProviders.create({ name, provider_type: 'onepassword', token })`. Reference in `auth.connections.create({ credential: { provider: '<name>', auto: true } })`. See `references/patterns/profiles-pools-credentials.md`. |
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

`vibium` exports a `browser` object, not a `Vibium` class, and it has no `.connect()`. The entry point is `browser.start(<bidi ws url>)`.

```ts
import { browser } from 'vibium';

const session = await kernel.browsers.create({ stealth: true });
// browser.start(urlOrOptions?: string | StartOptions) — pass the BiDi URL, not the CDP one
const bro = await browser.start(session.webdriver_ws_url);
const page = await bro.page();          // default page; bro.newPage() would orphan one
await page.go('https://example.com');   // `go`, not `goto`

await bro.stop();
await kernel.browsers.deleteByID(session.session_id);   // still the only real cleanup
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

`kernel create` scaffolds a ready-to-deploy Kernel App for the integration. All three of `--name`, `--language`, `--template` are required in a non-interactive shell — the CLI fails fast instead of prompting when stdin is not a TTY:

```bash
kernel create --name my-app --language typescript --template stagehand --yes
```

The full list from `@onkernel/cli` 0.31.0 (`create --help`):

- `stagehand` — Stagehand SDK [ts]
- `magnitude` — Magnitude.run SDK [ts]
- `browser-use` — Browser Use SDK [py]
- `claude-agent-sdk` — Claude Agent SDK browser-automation agent; wires an in-process MCP server exposing an `execute_playwright` tool backed by `kernel.browsers.playwright.execute` [py, ts]
- `anthropic-computer-use` / `gemini-computer-use` / `openai-computer-use` — computer-use agents [py, ts]
- `openagi-computer-use` — OpenAGI computer-use agent [py]
- `tzafon` — Tzafon Northstar CUA Fast computer-use agent [py, ts]
- `yutori` — Yutori n1.5 computer-use agent [py, ts]
- `captcha-solver` — auto-CAPTCHA solving demo [py, ts]
- `sample-app` — minimal Kernel app skeleton [py, ts]

There is **no** `playwright` template and **no** `bare` template — `sample-app` is the minimal skeleton. Run `kernel create --help` for the live list; templates are added regularly.
