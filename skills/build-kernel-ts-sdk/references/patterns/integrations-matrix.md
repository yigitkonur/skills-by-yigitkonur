# Integrations matrix

Most third-party agent libraries connect to a Kernel browser via the **CDP WebSocket URL** (`session.cdp_ws_url`) returned from `kernel.browsers.create`. WebDriver BiDi clients use `session.webdriver_ws_url` instead; vision-loop / VLM agents (Computer Use) bypass CDP entirely and go through `kernel.browsers.computer.*`. The matrix below names the right transport per integration. It also lists a few entries that are **not** drivers (Laminar is instrumentation, 1Password is a credential provider) — those wrap or feed a driver rather than replacing one. There is no vendor lock-in.

| Lib | Language | TS hookup |
|---|---|---|
| **Playwright** (`playwright`) | TS | `chromium.connectOverCDP(session.cdp_ws_url)` — see `references/patterns/playwright-stagehand-integration.md` |
| **Stagehand v4** (`@browserbasehq/stagehand`) | TS | v4 drives through a Chrome extension that must exist on the Kernel browser at the same absolute path Stagehand reads locally (`kernel.browsers.fs.uploadZip(id, { dest_path, zip_file })`, see *Stagehand v4* below), then `const browser = await localBrowser.connect({ cdpUrl: session.cdp_ws_url }); const sh = await Stagehand.create({ browser, model: { modelName: 'openai/gpt-4o', apiKey } })`. `new Stagehand({ env, localBrowserLaunchOptions })` is **v3-only**. |
| **Puppeteer** (`puppeteer`) | TS | `puppeteer.connect({ browserWSEndpoint: session.cdp_ws_url })` (standard CDP client; Kernel docs only show Puppeteer on Val Town) |
| **Claude Agent SDK** (`@anthropic-ai/claude-agent-sdk`) | TS | Template-driven — see *Templates* below for the full non-interactive `kernel create` invocation. Internally exposes an `execute_playwright` MCP tool that calls Kernel's Playwright Execution API (`kernel.browsers.playwright.execute`) against a stealth-mode browser. |
| **Browser Use** | Python only | No TS binding. Deploy a Python Kernel App that hosts Browser Use; invoke from TS via `kernel.invocations.create`. |
| **Vibium** (`vibium`) | TS | WebDriver BiDi — `browser.start(session.webdriver_ws_url)`, not `cdp_ws_url`. |
| **Laminar** (`@lmnr-ai/lmnr`) | TS | **Not a driver — observability.** Call `Laminar.initialize({ projectApiKey, instrumentModules: { playwright: { chromium }, kernel: Kernel } })` before your normal `chromium.connectOverCDP(session.cdp_ws_url)`; Playwright owns the CDP connection, Laminar traces it. |
| **Val Town** | TS | Run a Val that calls `@onkernel/sdk` directly; CDP from the Val to the Kernel browser. |
| **Vercel Agent Browser** | TS | `agent-browser -p kernel open <url>` reads `KERNEL_API_KEY`, `KERNEL_HEADLESS`, `KERNEL_STEALTH`, `KERNEL_TIMEOUT_SECONDS`, `KERNEL_PROFILE_NAME`. Programmatic: spawn `agent-browser connect "${session.cdp_ws_url}"`. |
| **1Password** | TS | Credential provider — register via *Integrations → Connect 1Password* in the Kernel dashboard (recommended) or `kernel.credentialProviders.create({ name, provider_type: 'onepassword', token })`. Reference in `auth.connections.create({ credential: { provider: '<name>', auto: true } })`. See `references/patterns/profiles-pools-credentials.md`. |
| **Vercel Marketplace** | Any | Installing Kernel from the Marketplace provisions an org and syncs `KERNEL_API_KEY` into the connected Vercel project. |
| **Vercel Connect** (MCP connector) | Any | `vercel connect create kernel --connection-method mcp` brokers per-user OAuth to the Kernel MCP server; no API key in your app (used by `@onkernel/eve-extension`). |
| **Terraform Provider** (`kernel/kernel`) | HCL | Manages durable config: projects and browser pools as resources; profiles, proxies and extensions are read-only data sources. Env: `KERNEL_API_KEY`, optional `KERNEL_PROJECT_ID`. Registry: `registry.terraform.io/providers/kernel/kernel/latest`. Use the SDK for runtime operations. |
| **Claude Managed Agents** | TS / Python | Anthropic-hosted agent loop; the sandbox runs the Kernel CLI (`kernel browsers create --stealth`, `playwright execute`, ...) with `KERNEL_API_KEY` held in a Managed Agents vault. Cookbook: `https://github.com/kernel/cookbooks/tree/main/integrations/claude-managed-agents`. |
| **`@onkernel/cua-agent`** (+ `@onkernel/cua-ai`) 0.10.0 | TS | `new CuaAgent({ browser, client, initialState: { model: 'anthropic:claude-opus-4-7', systemPrompt } })` then `await agent.prompt('...')`; model refs `anthropic:`, `openai:`, `google:`, `tzafon:`, `yutori:`. Needs the provider's API key next to `KERNEL_API_KEY`. |
| **Vercel AI SDK** (`@onkernel/ai-sdk`) | TS | `playwrightExecuteTool({ client: kernel, sessionId })` returns an AI SDK tool (`{ code, timeout_sec? }` -> `browsers.playwright.execute`). See *Vercel AI SDK* below. |
| **MCP-hosted agents** (OpenAI Agents SDK, Codex, Replit, fx, Eve, Claude Code) | Any | Connect them to `https://mcp.onkernel.com/mcp` (OAuth or `Authorization: Bearer <KERNEL_API_KEY>`). See [mcp-server.md](../guides/mcp-server.md). |
| **Hermes Agent** | Python agent | `hermes plugins install kernel/hermes-browser-plugin --enable`; env `KERNEL_API_KEY`, optional `KERNEL_PROFILE_NAME`, `KERNEL_PROXY_NAME`; set `browser.inactivity_timeout 600`. |
| **Docker Sandboxes** | Any | `sbx secret set kernel`, `sbx run claude --kit docker.io/sbx/kernel-kit:latest`; the key stays on the host (`proxy-managed` placeholder in the sandbox). |
| **e2e** (`@e2e-dev/kernel`) | TS | `kernel({ viewport })` as the web target's browser; reads `KERNEL_API_KEY`. |
| **Official skills** (`kernel/skills`) | Agents | `npx skills add kernel/skills`; plugins `kernel-cli`, `kernel-sdks`. |
| **Computer Use** (Anthropic, OpenAI, Gemini, custom VLM) | Any | Skip CDP entirely. Use `kernel.browsers.computer.captureScreenshot/clickMouse/typeText/scroll/dragMouse`. |

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

## Stagehand v4

The extension ships inside the `@browserbasehq/stagehand` package and is loaded from a path on the **browser's** filesystem, so upload it to the same absolute path it has locally (docs `integrations/stagehand`):

```ts
import { createReadStream } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import Kernel from '@onkernel/sdk';
import { Stagehand, localBrowser } from '@browserbasehq/stagehand';
import { z } from 'zod';

const stagehandDist = dirname(fileURLToPath(import.meta.resolve('@browserbasehq/stagehand')));
const kernel = new Kernel();
const session = await kernel.browsers.create({ stealth: true });

await kernel.browsers.fs.uploadZip(session.session_id, {
  dest_path: join(stagehandDist, 'extension'),
  zip_file: createReadStream(join(stagehandDist, 'assets/stagehand-extension.zip')),
});

const browser = await localBrowser.connect({ cdpUrl: session.cdp_ws_url });
const stagehand = await Stagehand.create({
  browser,
  model: { modelName: 'anthropic/claude-sonnet-4-5', apiKey: process.env.MODEL_API_KEY },
});
try {
  const page = await browser.context.activePage();
  if (!page) throw new Error('No active page in the Kernel browser');
  await page.goto('https://example.com');
  await stagehand.act('Click the first link');
  const { data } = await stagehand.extract('Page title', z.object({ title: z.string() })); // v4: result under `data`
  console.log(data.title);
} finally {
  // v4 only closes browsers it launched: close the connection, then delete the Kernel browser
  try { await stagehand.close(); } finally {
    try { await browser.close(); } finally { await kernel.browsers.deleteByID(session.session_id); }
  }
}
```

`@browserbasehq/stagehand@4.2.0` depends on `zod` 4.4.3 exactly; passing a schema built from a different top-level `zod` minor (4.6.5 was tried) fails type-checking at `stagehand.extract` (TS2769, `_zod.version.minor` mismatch). Install the same `zod` version as Stagehand's.

`kernel create -t stagehand` scaffolds the same wiring (`index.ts` + `stagehand-extension.ts`, env `MODEL`, `MODEL_API_KEY`).

## Vercel AI SDK (`@onkernel/ai-sdk`)

```ts
import { openai } from '@ai-sdk/openai';
import { playwrightExecuteTool } from '@onkernel/ai-sdk';
import Kernel from '@onkernel/sdk';
import { generateText } from 'ai';

const kernel = new Kernel();
const browser = await kernel.browsers.create({});
try {
  const result = await generateText({
    model: openai('gpt-5.1'),
    prompt: 'Open news.ycombinator.com and get the title of the top story.',
    tools: { playwright_execute: playwrightExecuteTool({ client: kernel, sessionId: browser.session_id }) },
  });
  console.log(result.toolResults[0]?.output);
} finally {
  await kernel.browsers.deleteByID(browser.session_id);
}
```

Peer deps: `npm install @onkernel/ai-sdk zod ai @onkernel/sdk` (`@onkernel/ai-sdk` peers `ai@^5`, so pair it with `@ai-sdk/openai@2`). The tool input is `{ code: string; timeout_sec?: number }` and runs `client.browsers.playwright.execute(sessionId, { code, timeout_sec })`.

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
import Kernel from '@onkernel/sdk';

const kernel = new Kernel();

// Python action deployed as a Kernel App handles Browser Use directly. From TS:
async function runBrowserUse() {
  const inv = await kernel.invocations.create(
    {
      app_name: 'browser-use-runner',
      action_name: 'run_task',
      version: '1.0.0',
      async: true,
      async_timeout_seconds: 1800,
      payload: JSON.stringify({ task: 'Find me cheap flights from SFO to NYC' }),
    },
    { maxRetries: 0 },
  );
  for await (const evt of await kernel.invocations.follow(inv.id)) {
    if (evt.event === 'invocation_state' && evt.invocation.status !== 'queued' && evt.invocation.status !== 'running') {
      return JSON.parse(evt.invocation.output ?? 'null');
    }
  }
}
```

This is the recommended pattern for any framework that doesn't have a TS port: wrap it in a Python Kernel App, invoke from TS.

## Templates

`kernel create` scaffolds a ready-to-deploy Kernel App for the integration. `--name`, `--language` and `--template` are all required in a non-interactive shell (pass `--yes` to overwrite an existing directory) — the CLI fails fast with one error listing what is missing instead of prompting:

```bash
kernel create --name my-app --language typescript --template stagehand
```

The full list from `@onkernel/cli` (`create --help`):

- `stagehand` — Stagehand v4 SDK [ts] (the CLI help string still says v3; the template pins `@browserbasehq/stagehand ^4.0.0`)
- `browser-use` — Browser Use SDK [py]
- `claude-agent-sdk` — Claude Agent SDK browser-automation agent; wires an in-process MCP server exposing an `execute_playwright` tool backed by `kernel.browsers.playwright.execute` [py, ts]
- `anthropic-computer-use` / `gemini-computer-use` / `openai-computer-use` — computer-use agents [py, ts]
- `openagi-computer-use` — OpenAGI computer-use agent [py]
- `tzafon` — Tzafon Northstar CUA Fast computer-use agent [py, ts]
- `yutori` — Yutori n1.5 computer-use agent [py, ts]
- `captcha-solver` — auto-CAPTCHA solving demo [py, ts]
- `sample-app` — minimal Kernel app skeleton [py, ts]

There is **no** `playwright`, `bare` or `magnitude` template in 0.47.0 (the docs list `magnitude`; the CLI does not ship it) — `sample-app` is the minimal skeleton. Run `kernel create --help` for the live list; templates are added regularly.
