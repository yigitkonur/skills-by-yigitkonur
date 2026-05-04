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
  baseURL: undefined,                        // override the base URL outright
  environment: 'production',                 // 'production' | 'development'
  timeout: 60_000,                           // ms; default Kernel.DEFAULT_TIMEOUT
  maxRetries: 2,                             // default 2 with exponential backoff + jitter
  defaultHeaders: { 'X-Kernel-Project-Id': process.env.KERNEL_PROJECT },
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
| `KERNEL_BASE_URL` | Override base URL (overrides `environment:`). |
| `KERNEL_LOG` | Log level (`debug` / `info` / `warn` (default) / `error` / `off`). |
| `KERNEL_CUSTOM_HEADERS` | Newline-separated `Header: value` pairs added to every request. |
| `KERNEL_SUPPRESS_BUN_WARNING` | Suppress Bun + Playwright CDP warning (set when intentional). |
| `KERNEL_PROJECT` | Default project. Sets `X-Kernel-Project-Id` on every request when used with project-scoped keys. |

## Environments

- `production` → `https://api.onkernel.com/`
- `development` → `https://localhost:3001/` (local Kernel dev server)

Setting **both** `baseURL` and `environment` throws. To use `environment` while a `baseURL` was set somewhere upstream, pass `baseURL: null`:

```ts
new Kernel({ environment: 'development', baseURL: null });
```

## Pagination

`list()` methods return `PagePromise<…OffsetPagination, …>`. Two consumption styles:

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
    idempotencyKey: 'my-key',               // SDK auto-sets on non-GET retries
    signal: ac.signal,                      // AbortSignal
    fetchOptions: { keepalive: true },
  }
);
```

Idempotency keys are automatically attached on retried non-GET requests as `stainless-node-retry-${uuid4()}`.

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
  // evt.event: 'log' | 'invocation_state' | 'error' | 'heartbeat'
}
```

The SDK sets `Accept: text/event-stream` and `stream: true` automatically.

## Project scoping

Org-wide API keys see all projects unless you scope each request:

```ts
const kernel = new Kernel({
  defaultHeaders: { 'X-Kernel-Project-Id': process.env.KERNEL_PROJECT },
});
```

Or per-request:

```ts
await kernel.browsers.list({}, { headers: { 'X-Kernel-Project-Id': 'proj_…' } });
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
