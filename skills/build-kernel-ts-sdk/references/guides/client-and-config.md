# Client and config

Constructing the `Kernel` client, configuring environment, retries, pagination, errors, and request options.

## Install

```bash
npm install @onkernel/sdk@0.123.0
# Optional: managed-auth and vault React components
npm install @onkernel/managed-auth-react@0.5.5 @onkernel/vault-react@0.2.0
# Common pairings:
npm install playwright @browserbasehq/stagehand
```

Pin to `@onkernel/sdk@0.123.0` — the SDK is auto-generated from Kernel's OpenAPI spec by Stainless and rev's frequently.

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
| `KERNEL_BROWSER_ROUTING_SUBRESOURCES` | Comma-separated allowlist of `/browsers/{id}/<tail>` prefixes routed straight to the browser VM's `base_url` instead of the API. Default `curl,telemetry/stream,computer,playwright,process,fs,logs/stream`; set to an empty string to disable direct-to-VM routing. |
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

`idempotencyKey` is accepted by `RequestOptions`, but **the Kernel client never sends an idempotency header**. `buildHeaders` emits one only when `this.idempotencyHeader` is set, and `Kernel` declares `protected idempotencyHeader?: string` without ever assigning it (verified in v0.92.0 through v0.123.0) — so the key you pass is dropped, and the `stainless-node-retry-${uuid4()}` value from `defaultIdempotencyKey()` is never used either. The guard is `method !== 'get'`, not a retry check, so none of this is retry-specific.

Consequence: automatic retries (`maxRetries`, default 2) of non-GET calls are **not** de-duplicated by the client. Treat `browsers.create` and `invocations.create` as at-least-once and reconcile yourself instead of assuming server-side de-dup:

```ts
const tags = { run_id: runId };
await kernel.browsers.create({ stealth: true, tags });

// After an ambiguous failure or retry, find what actually got created:
const existing = await kernel.browsers.list({ tags, status: 'active' });
```

For invocations, narrow with `kernel.invocations.list({ app_name: 'my-agent', status: 'running' })`.

## Timeouts and retries on long or side-effecting calls

`Kernel.DEFAULT_TIMEOUT` is 60 000 ms and `maxRetries` is 2. A request is retried on a timeout, `408`, `409`, `429`, any status `>= 500`, or `x-should-retry: true`. Calls that the SDK routes straight to the browser VM (`playwright.execute`, `computer.*`, `process.*`, `fs.*`, `curl`, `telemetry.stream`, `logs.stream`) and the ones that go through the API (`repl`, `webmcp.*`, `telemetry.events`) all use the same client, so the same timeout and retry policy apply.

Consequences:

- A `timeout_sec` above ~50 (`playwright.execute` and `repl` accept up to 300) outlives the 60 s client timeout. The client aborts, retries, and the script can run again.
- A retry after a lost response repeats clicks, form submissions, `webmcp.invokeTool`, `invocations.create`, `deployments.create`, and `search.create`. Kernel's own docs and CLI disable retries for these calls.

```ts
// Long in-VM script: client timeout above timeout_sec, no retry.
await kernel.browsers.repl(
  session.session_id,
  { code, timeout_sec: 120 },
  { timeout: 135_000, maxRetries: 0 },
);

// Side-effecting call: never retry.
const noRetry = kernel.withOptions({ maxRetries: 0 });
await noRetry.browsers.webmcp.invokeTool(session.session_id, { tool_ref, input: {}, timeout_sec: 30 });
```

`kernel.browsers.fetch(id, url)` only works for a session this client already saw through `create`, `retrieve`, or `list` (it throws `KernelError` otherwise).

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
await kernel.extensions.upload({ file: await toFile(buffer, 'ext.zip'), name: 'my-ext' }); // name: optional, unique per project
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
const kernel = new Kernel({ projectID: 'proj_…' });   // or project: 'proj_…' | 'exact-project-name' → X-Kernel-Project
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

`projectID` sends `X-Kernel-Project-Id` (ID only); `project` sends `X-Kernel-Project`, which accepts a project ID or an exact project name. In the CLI, the global `--project` flag and `KERNEL_PROJECT` send `X-Kernel-Project` as-is, so both an ID and an exact name work in v0.47.0 (the CLI projects docs page still says IDs only; the CLI source wins). Project-management commands take `<id-or-name>` arguments (e.g. `kernel projects get`).

> **REST Routing Note:** Project endpoints are routed under `/org/projects/*` (e.g. `GET /org/projects`, `POST /org/projects`, `GET /org/projects/{id}`). The legacy `/projects/*` routes are `@deprecated`.

## Organization limits and entitlements

Inspect real concurrency caps and entitlements rather than guessing:

```ts
// Unified concurrency limits (counts on-demand sessions and pool reservations together)
const limits = await kernel.organization.limits.retrieve();
console.log(limits.concurrent_sessions_used);      // currently active sessions + pool reservations
console.log(limits.concurrent_sessions_available); // available concurrency slots
console.log(limits.max_concurrent_sessions);       // effective plan limit

// Note: max_pooled_sessions is @deprecated in favor of unified max_concurrent_sessions.

// Entitlements (active features, regional permissions, plans)
const entitlements = await kernel.organization.entitlements.retrieve();
```

## API Key Management & Rotation

Provision and rotate API keys under `/org/api_keys`:

```ts
// Rotate an active key (issues replacement, sets expiration on old key)
// Invariant: days_to_expire (lifetime of new key) must be >= expire_in_days (grace period of old key)
const rotated = await kernel.apiKeys.rotate('key_123', {
  days_to_expire: 30, // lifetime of new key (must be >= expire_in_days)
  expire_in_days: 7,  // grace period before old key revokes
});
console.log('New key:', rotated.key);

// Delete an old key (cannot delete authenticating key -> HTTP 400 cannot_delete_current_key)
await kernel.apiKeys.delete('key_old');
```

## Audit Logs & Export Destinations

Search and download need the Start-Up or Enterprise plan; continuous S3 export needs Enterprise. Events are retained 1 year, API pages hold up to 100 events, and one download covers a window of up to 30 days.

```ts
// Helper with per-chunk verification. The 2nd argument is any object with write(chunk: Uint8Array),
// not a path; the SDK does not close it, and a failed download can leave a partial file.
import { open } from 'node:fs/promises';

const file = await open('./audit-logs.jsonl.gz', 'w');
try {
  await kernel.auditLogs.download(
    { start: '2026-10-01T00:00:00Z', end: '2026-10-09T00:00:00Z' },
    file,
  );
} finally {
  await file.close();
}

// Continuous S3 export destinations: create, retrieve, list, update, delete, test.
// There is no pause/resume method: destinations are created paused; activate or pause with
// kernel.auditLogs.exportDestinations.update(id, { status: 'active' | 'paused' }).
```

## Web Search API

Searches are billable; the CLI sends `search.create` with retries disabled to avoid duplicate billable searches. See [search.md](search.md).

```ts
const search = await kernel.search.create(
  { query: 'Kernel browser automation' },
  { maxRetries: 0 },
);
for (const item of search.results) {
  console.log(item.title, item.url);
}
```

## Runtime support

- Node 20 LTS+ and TypeScript ≥ 4.9
- Deno 1.28+, Bun 1.0+ (set `KERNEL_SUPPRESS_BUN_WARNING=true` if Playwright + Bun is intentional)
- Cloudflare Workers, Vercel Edge, Nitro 2.6+
- Jest 28+ with the `node` test environment (jsdom is unsupported by `fetch`)
- **Not** supported: React Native

## Where to look next

- For browser create/use/terminate: `references/guides/browsers-lifecycle.md`
- For proxy subsystem, routing, and tiers: `references/guides/proxies.md`
- For multi-provider web search and extraction: `references/guides/search.md`
- For in-VM REPL and Code Mode: `references/patterns/browser-repl.md`
- For WebMCP page tool discovery: `references/patterns/webmcp.md`
- For dedicated CLI reference: `references/guides/cli-reference.md`
- For vaults, autofill, and payments: `references/patterns/vaults-and-payments.md`
- For session telemetry and OTLP: `references/guides/telemetry.md`
- For stealth, the config registry, Web Bot Auth, and SSH: `references/guides/stealth-and-config-registry.md`
- For `deployments.*` / `invocations.*`: `references/guides/apps-deploy-invoke.md`
- For typical errors and root causes: `references/troubleshooting/pitfalls.md`

