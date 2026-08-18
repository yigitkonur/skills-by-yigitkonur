# Client and config

Constructing the `Kernel` client, configuring environment, retries, pagination, errors, and request options.

## Install

```bash
npm install @onkernel/sdk
# Optional: managed-auth React component
npm install @onkernel/managed-auth-react
# Common pairings:
npm install playwright @browserbasehq/stagehand
```

Pin to a minor range — the SDK is auto-generated from Kernel's OpenAPI spec by Stainless and rev's frequently.

## Construct the client

```ts
import Kernel from '@onkernel/sdk';

const kernel = new Kernel(); // reads KERNEL_API_KEY from env
```

Full options:

```ts
new Kernel({
  apiKey: process.env.KERNEL_API_KEY,        // explicit value; if omitted, the SDK falls back to KERNEL_API_KEY env. Throws if both missing.
  projectID: process.env.KERNEL_PROJECT,     // sets X-Kernel-Project-Id on every request
  project: undefined,                        // sets X-Kernel-Project (name form)
  baseURL: undefined,                        // override the base URL outright
  environment: 'production',                 // 'production' | 'development'
  timeout: 60_000,                           // ms; default Kernel.DEFAULT_TIMEOUT
  maxRetries: 2,                             // default 2 with exponential backoff + jitter
  defaultHeaders: {},                        // extra headers; not needed for project scoping
  defaultQuery: {},
  fetch: customFetch,                        // bring your own fetch
  fetchOptions: { /* per-request RequestInit */ },
  logLevel: 'warn',                          // 'debug' | 'info' | 'warn' | 'error' | 'off'
  logger: console,                           // default globalThis.console
});
```

## Environment variables

| Variable | Purpose |
|---|---|
| `KERNEL_API_KEY` | API key. Required if `apiKey:` option not set; throws `KernelError` otherwise. |
| `KERNEL_BASE_URL` | Default for `baseURL`. **Mutually exclusive with `environment:`** — passing both throws `KernelError('Ambiguous URL…')`. Pass `baseURL: null` to use `environment` while this var is set. |
| `KERNEL_LOG` | Log level (`debug` / `info` / `warn` (default) / `error` / `off`). |
| `KERNEL_CUSTOM_HEADERS` | Newline-separated `Header: value` pairs added to every request. |
| `KERNEL_SUPPRESS_BUN_WARNING` | Suppress Bun + Playwright CDP warning (set when intentional). |
| `KERNEL_BROWSER_ROUTING_SUBRESOURCES` | Comma-separated allowlist of `/browsers/{id}/<tail>` prefixes routed straight to the browser VM's `base_url` instead of the API. Default `curl,telemetry/stream`; set to an empty string to disable direct-to-VM routing. |
| `KERNEL_PROJECT` | **Not read by the SDK** — wire it through the first-class `projectID:` client option (see "Project scoping" below). The `kernel` CLI's `--project` flag *does* read it, so this spelling keeps SDK and CLI consistent. |

## Environments

- `production` → `https://api.onkernel.com/`
- `development` → `https://localhost:3001/` (local Kernel dev server)

Setting **both** `baseURL` and `environment` throws. To use `environment` while a `baseURL` was set somewhere upstream, pass `baseURL: null`:

```ts
new Kernel({ environment: 'development', baseURL: null });
```

## Pagination

Most `list()` methods return `PagePromise<…OffsetPagination, …>` — `{ offset, limit }` in, `{ items, has_more, next_offset }` out. `kernel.auditLogs.list({ start, end })` is the exception: it returns a `PageTokenPagination` (`{ page_token, limit }` in, `{ items, has_more, next_page_token }` out), and its `start`/`end` timestamp bounds are required. Both support the same two consumption styles:

```ts
// Auto-paginate
for await (const browser of kernel.browsers.list({ limit: 100 })) {
  console.log(browser.session_id);
}

// Manual
let page = await kernel.browsers.list({ limit: 100 });
while (true) {
  for (const item of page.items) console.log(item.session_id);
  if (!page.hasNextPage()) break;
  page = await page.getNextPage();
}
```

## Per-request options

Every method takes an optional second argument:

```ts
await kernel.browsers.create(
  { stealth: true },
  {
    timeout: 30_000,
    maxRetries: 5,
    headers: { 'X-Kernel-Project-Id': 'proj_…' },
    query: {},
    body: undefined,                        // override (rare)
    idempotencyKey: 'my-key',               // accepted, but never sent — see note below
    signal: ac.signal,                      // AbortSignal
    fetchOptions: { keepalive: true },
  }
);
```

`idempotencyKey` is accepted by `RequestOptions`, but **the Kernel client never sends an idempotency header**. `buildHeaders` emits one only when `this.idempotencyHeader` is set, and `Kernel` declares `protected idempotencyHeader?: string` without ever assigning it (verified in v0.92.0) — so the key you pass is dropped, and the `stainless-node-retry-${uuid4()}` value from `defaultIdempotencyKey()` is never used either. The guard is `method !== 'get'`, not a retry check, so none of this is retry-specific.

Consequence: automatic retries (`maxRetries`, default 2) of non-GET calls are **not** de-duplicated by the client. Treat `browsers.create` and `invocations.create` as at-least-once and reconcile yourself instead of assuming server-side de-dup:

```ts
const tags = { run_id: runId };
await kernel.browsers.create({ stealth: true, tags });

// After an ambiguous failure or retry, find what actually got created:
const existing = await kernel.browsers.list({ tags, status: 'active' });
```

For invocations, narrow with `kernel.invocations.list({ app_name: 'my-agent', status: 'running' })`.

## Errors

All error classes are reachable as `Kernel.*` and importable:

```ts
import Kernel, {
  KernelError,           // base, non-API
  APIError,              // base for HTTP
  APIConnectionError,
  APIConnectionTimeoutError,
  APIUserAbortError,
  BadRequestError,       // 400
  AuthenticationError,   // 401
  PermissionDeniedError, // 403
  NotFoundError,         // 404
  ConflictError,         // 409
  UnprocessableEntityError, // 422
  RateLimitError,        // 429
  InternalServerError,   // 5xx
} from '@onkernel/sdk';
```

Idiomatic catch:

```ts
try {
  const session = await kernel.browsers.create({ stealth: true });
} catch (err) {
  if (err instanceof Kernel.APIError) {
    console.error(err.status, err.name, err.message, err.headers);
    if (err instanceof Kernel.RateLimitError) {
      // back off, the SDK already retried `maxRetries` times
    }
  } else {
    throw err;
  }
}
```

`err.headers` is useful for `x-request-id` when filing support tickets.

## Raw response access

```ts
// Just the Response object (no body parse):
const resp = await kernel.browsers.create({ stealth: true }).asResponse();

// Both the parsed data and the Response:
const { data, response } = await kernel.browsers.create({ stealth: true }).withResponse();
```

Use these when you need rate-limit headers, ETags, or to stream the body yourself.

## File uploads

The SDK accepts `fs.createReadStream`, `File`, `Response`, or `Buffer`/`Uint8Array` via the `toFile` helper:

```ts
import Kernel, { toFile } from '@onkernel/sdk';
import fs from 'node:fs';

await kernel.deployments.create({
  file: fs.createReadStream('./build.zip'),
  entrypoint_rel_path: 'app.ts',
  env_vars: { OPENAI_API_KEY: process.env.OPENAI_API_KEY! },
  region: 'aws.us-east-1a',
  version: '1.0.0',
});

// Buffer / Uint8Array:
await kernel.extensions.upload({ file: await toFile(buffer, 'ext.zip') });
```

Multipart is wired automatically — do not hand-build a `FormData`.

## Streaming (Server-Sent Events)

`.follow(id)` methods return an async iterable of events:

```ts
const events = await kernel.invocations.follow(invocation.id);
for await (const evt of events) {
  // evt.event: 'log' | 'invocation_state' | 'error' | 'sse_heartbeat'
}
```

The SDK sets `Accept: text/event-stream` and `stream: true` automatically.

## Project scoping

Org-wide API keys see all projects unless you scope each request. Use the first-class client option — the SDK sets `X-Kernel-Project-Id` itself:

```ts
const kernel = new Kernel({ projectID: 'proj_…' });   // or project: 'my-project' → X-Kernel-Project
```

Or per-request:

```ts
await kernel.browsers.list({}, { headers: { 'X-Kernel-Project-Id': 'proj_…' } });
```

Hand-rolling `defaultHeaders: { 'X-Kernel-Project-Id': … }` still works but is the inferior idiom — it silently no-ops when the value is `undefined`.

To check what a key is actually scoped to, read the auth context:

```ts
const ctx = await kernel.auth.context.retrieve();
ctx.authorization.credential_scope.project_id;  // null = organization-wide
ctx.authorization.effective_scope.project_id;   // scope selected for this request
```

OAuth (CLI) is always org-wide; only API keys can be project-scoped.

## Runtime support

- Node 20+ with `tsconfig.json` `target: 'es2017'+` and TypeScript ≥ 4.9
- Deno 1.28+, Bun 1.0+ (set `KERNEL_SUPPRESS_BUN_WARNING=true` if Playwright + Bun is intentional)
- Cloudflare Workers, Vercel Edge, Nitro 2.6+
- Jest 28+ with the `node` test environment (jsdom is unsupported by `fetch`)
- **Not** supported: React Native

## Where to look next

- For browser create/use/terminate: `references/guides/browsers-lifecycle.md`
- For `deployments.*` / `invocations.*`: `references/guides/apps-deploy-invoke.md`
- For typical errors and root causes: `references/troubleshooting/pitfalls.md`
