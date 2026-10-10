# Architecture: Cloudflare Workers & Pages Observability

Complete guide for instrumenting Cloudflare Workers, Pages, Durable Objects, Workflows, and Agents using `@sentry/cloudflare`, Vite build-time instrumentation, Wrangler, and OpenTelemetry drains.

---

## 1. Runtime Isolation & Architectural Foundation

Cloudflare Workers run in V8 isolates (`workerd`), not standard Node.js runtimes:
- **No Runtime Monkey-Patching:** The Workers runtime prevents SDKs from dynamically patching bundled modules at runtime. Packages like database drivers, ORMs, and AI client libraries can **only** be instrumented during build-time bundling.
- **Async Execution Lifecycle:** All background asynchronous work (including Sentry envelope flushes) must be registered with `ctx.waitUntil()` or managed by an automated SDK wrapper. Unregistered background promises are killed immediately when the response completes.
- **AsyncLocalStorage Requirement:** Distributed trace propagation and ambient request context rely on Node.js `AsyncLocalStorage`. The worker must enable the `nodejs_compat` compatibility flag with a modern `compatibility_date`.

---

## 2. Approach A: Modern Vite Build-Time Instrumentation (Recommended)

Sentry strongly recommends building Cloudflare Workers with Vite. The `sentryCloudflareVitePlugin` automatically wraps the Worker entry, Durable Objects, and Workflows at build time and rewrites bundled dependencies for end-to-end tracing.

### Installation

```bash
npm install @sentry/cloudflare --save
npm install @cloudflare/vite-plugin vite --save-dev
```

### 1. Configure `vite.config.ts`

Add `sentryCloudflareVitePlugin` next to `cloudflare()`:

```typescript
import { defineConfig } from "vite";
import { cloudflare } from "@cloudflare/vite-plugin";
import { sentryCloudflareVitePlugin } from "@sentry/cloudflare/vite";

export default defineConfig({
  plugins: [
    cloudflare(),
    sentryCloudflareVitePlugin({
      // Enabled by default:
      // autoInstrumentation: wraps worker entry, Durable Objects, Workflows, and Agents
      // buildTimeInstrumentation: rewrites bundled dependencies (DB, AI clients) for tracing
    }),
  ],
});
```

### 2. Configure `wrangler.jsonc` (or `wrangler.toml`)

```jsonc
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "name": "my-worker",
  "main": "src/index.ts",
  "compatibility_date": "2026-10-10",
  "compatibility_flags": ["nodejs_compat"],
  "upload_source_maps": true,
  "version_metadata": {
    "binding": "CF_VERSION_METADATA"
  }
}
```

> [!IMPORTANT]
> - `compatibility_flags = ["nodejs_compat"]` is mandatory for `AsyncLocalStorage`.
> - `upload_source_maps: true` enables Wrangler to generate and upload source maps.
> - `CF_VERSION_METADATA` enables automatic release detection from Cloudflare version IDs.

### 3. Create `src/instrument.server.ts`

Create `instrument.server.ts` in the **same directory as your worker entry file** (`src/index.ts` -> `src/instrument.server.ts`). The Vite plugin detects this file automatically:

```typescript
import { defineCloudflareOptions } from "@sentry/cloudflare";

export default defineCloudflareOptions((env: Env) => ({
  dsn: env.SENTRY_DSN,
  tracesSampleRate: 1.0,
  sendDefaultPii: false,
  // Bindings that propagate trace context over Cloudflare Service/RPC bindings
  rpcTracePropagationBindings: ["AUTH_SERVICE", "BILLING_SERVICE"],
}));
```

### 4. Write Your Worker (`src/index.ts`)

With the Vite plugin, your Worker code remains 100% clean and unwrapped:

```typescript
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/error") {
      throw new Error("Simulated edge failure on Cloudflare Workers");
    }
    return new Response("Worker operational");
  },
};
```

---

## 3. Approach B: Wrangler Direct Instrumentation (`withSentry` Fallback)

If deploying with Wrangler directly without Vite, you must manually wrap the exported handlers and classes.

```typescript
import * as Sentry from "@sentry/cloudflare";
import { DurableObject, WorkflowEntrypoint } from "cloudflare:workers";
import { Agent } from "agents";

interface Env {
  SENTRY_DSN: string;
  MY_DO: DurableObjectNamespace;
}

const sentryOptions = (env: Env) => ({
  dsn: env.SENTRY_DSN,
  tracesSampleRate: 1.0,
  rpcTracePropagationBindings: ["AUTH_SERVICE"],
});

// 1. Wrap Fetch / Scheduled / Queue handlers
export default Sentry.withSentry(sentryOptions, {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    return new Response("Hello from manual wrapper");
  },

  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    // Sentry automatically instruments cron triggers and reports errors
    console.log("Cron executed at:", event.cron);
  },

  async queue(batch: MessageBatch<any>, env: Env, ctx: ExecutionContext) {
    // Sentry captures batch failures and links queue spans
    for (const message of batch.messages) {
      console.log("Processed message:", message.id);
    }
  },
});

// 2. Wrap Durable Objects
class MyDurableObjectBase extends DurableObject<Env> {
  async sayHello() {
    return "Hello from DO";
  }
}
export const MyDurableObject = Sentry.instrumentDurableObjectWithSentry(
  sentryOptions,
  MyDurableObjectBase,
);

// 3. Wrap Workflows
class MyWorkflowBase extends WorkflowEntrypoint<Env> {
  async run(event: any, step: any) {
    await step.do("step1", async () => ({ status: "ok" }));
  }
}
export const MyWorkflow = Sentry.instrumentWorkflowWithSentry(
  sentryOptions,
  MyWorkflowBase,
);

// 4. Wrap Agents SDK (Cloudflare Agents / AIChatAgent / McpAgent)
class MyAgentBase extends Agent<Env> {
  // Agentic logic
}
export const MyAgent = Sentry.instrumentAgentWithSentry(
  sentryOptions,
  MyAgentBase,
);
```

---

## 4. Cloudflare Pages Middleware

For Cloudflare Pages applications, use `sentryPagesPlugin` middleware rather than wrapping `fetch`:

```typescript
// functions/_middleware.ts
import { sentryPagesPlugin } from "@sentry/cloudflare/pages";

export const onRequest = [
  sentryPagesPlugin((context) => ({
    dsn: context.env.SENTRY_DSN,
    tracesSampleRate: 1.0,
  })),
];
```

---

## 5. Cron & Scheduled Job Monitoring on Cloudflare

Monitor cron triggers with check-ins or `Sentry.withMonitor`:

```typescript
export default Sentry.withSentry(sentryOptions, {
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    await Sentry.withMonitor(
      "cleanup-daily-cache",
      async () => {
        await purgeStaleCache(env);
      },
      {
        schedule: { type: "crontab", value: "0 0 * * *" },
      }
    );
  },
});
```

---

## 6. Source Maps Pipeline with Wrangler

1. In `wrangler.jsonc`:
   ```jsonc
   {
     "upload_source_maps": true
   }
   ```
2. Configure automated upload via Sentry Wizard:
   ```bash
   npx @sentry/wizard@latest -i sourcemaps
   ```
   Or use `@sentry/esbuild-plugin` / `@sentry/vite-plugin` with `SENTRY_AUTH_TOKEN` during CI deployments.

---

## 7. Cloudflare OpenTelemetry Log & Trace Drains

Cloudflare Workers Observability natively supports exporting traces and logs via OpenTelemetry directly to Sentry without adding SDK weight:
1. In Cloudflare Dashboard: **Workers & Pages > Your Worker > Settings > Observability**.
2. Add OpenTelemetry Drain targeting Sentry's OTLP ingest endpoint.
3. Correlates CPU duration, memory metrics, and uncaught exceptions with zero runtime overhead.
