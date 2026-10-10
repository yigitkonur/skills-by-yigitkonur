# Cloudflare Workers (`workerd`) Cleanup & Invariant Protocol

Comprehensive guide for dead-code pruning, Knip configuration, and invariant preservation in Cloudflare Workers applications running on the `workerd` V8 isolate runtime.

---

## 1. The `workerd` Execution Model vs. Node.js Invariants

Cloudflare Workers does not execute on Node.js or Bun; it executes on Cloudflare's open-source `workerd` runtime based on V8 isolates:

```
+-------------------------------------------------------------------------------+
|                      WORKERD V8 ISOLATE RUNTIME BOUNDARY                     |
+-------------------------------------------------------------------------------+
|  NODE.JS INVARIANTS (BROKEN AT EDGE)   |  WORKERD ISOLATE INVARIANTS          |
|  - Global process.env populated       |  - No global process.env (undefined)  |
|  - Process lives indefinitely         |  - Isolate suspends on response settle|
|  - Event loop drains floating tasks   |  - Floating promises aborted mid-flight|
|  - Monolithic shared memory state     |  - Request-scoped env and isolate state|
|  - Filesystem access (fs/promises)    |  - Ephemeral sandbox, bindings for I/O|
+-------------------------------------------------------------------------------+
```

Standard static analysis engines (Knip, ESLint) and AI cleanup agents built with Node.js assumptions frequently introduce critical edge failures:
1. **Entry Point & RPC Class Deletion**: Pruning handler exports (`fetch`, `scheduled`, `queue`) or class exports (`DurableObject`, `WorkerEntrypoint`, `WorkflowEntrypoint`) because no local `.ts` file imports them.
2. **Ambient Type Destruction**: Deleting `worker-configuration.d.ts` or pruning `@cloudflare/workers-types` as "unused dependencies".
3. **`process.env` Leakage**: Hallucinating Node.js `process.env` calls that return `undefined` at runtime.
4. **Async Boundary Severing**: Stripping or unwrapping `ctx.waitUntil()` calls as "redundant wrappers", causing background writes to silently abort.

---

## 2. Entry Point & RPC Protection Protocol

In Cloudflare Workers, entry points and RPC classes are invoked by the platform runtime or external service bindings—not local TypeScript imports. Standard Knip passes will report them as unused exports or dead files unless explicitly protected.

### 2.1 Manifest Configuration & Main Module
Wrangler manifests define the code entry point:
- Files: `wrangler.json`, `wrangler.jsonc`, or `wrangler.toml`
- Configuration field: `"main": "src/index.ts"` (or `main = "src/index.ts"` in TOML)

Knip provides a built-in `wrangler` plugin that automatically reads `config.main`. Always ensure the plugin is enabled in `knip.jsonc`:
```jsonc
{
  "wrangler": true
}
```

### 2.2 Root Handler: `ExportedHandler<Env>`
The entry module must default-export an object implementing the `ExportedHandler` interface:

```typescript
// src/index.ts
import type { ExportedHandler, ExecutionContext } from "@cloudflare/workers-types";

export default {
  // HTTP Fetch Handler
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    return new Response("OK");
  },

  // Scheduled Cron Handler (Wrangler Triggers)
  async scheduled(controller: ScheduledController, env: Env, ctx: ExecutionContext): Promise<void> {
    ctx.waitUntil(doScheduledCleanup(env));
  },

  // Queue Consumer Handler
  async queue(batch: MessageBatch<unknown>, env: Env, ctx: ExecutionContext): Promise<void> {
    for (const message of batch.messages) {
      await processMessage(message, env);
    }
  },

  // Email Worker Handler
  async email(message: ForwardableEmailMessage, env: Env, ctx: ExecutionContext): Promise<void> {
    await message.forward("team@example.com");
  },
} satisfies ExportedHandler<Env>;
```

> [!IMPORTANT]
> Never strip `export default` or prune handler lifecycle methods (`scheduled`, `queue`, `email`, `tail`) during dead-code remediation. Even if no internal file calls `scheduled`, the Cloudflare runtime invokes it when cron triggers fire.

### 2.3 RPC & Stateful Primitives Protection
Cloudflare Workers supports stateful actors and service binding RPC through named exported classes. These classes are referenced in `wrangler.json` rather than imported in code:

#### 1. Durable Objects
```typescript
import { DurableObject } from "cloudflare:workers";

/** @public */
export class CounterDurableObject extends DurableObject<Env> {
  async getCount(): Promise<number> {
    return (await this.ctx.storage.get<number>("count")) ?? 0;
  }

  async increment(delta = 1): Promise<number> {
    const current = await this.getCount();
    const next = current + delta;
    await this.ctx.storage.put("count", next);
    return next;
  }
}
```
Bound in `wrangler.json`:
```json
{
  "durable_objects": {
    "bindings": [{ "name": "COUNTER", "class_name": "CounterDurableObject" }]
  }
}
```

#### 2. WorkerEntrypoint (Service Bindings RPC)
```typescript
import { WorkerEntrypoint } from "cloudflare:workers";

/** @public */
export class AuthService extends WorkerEntrypoint<Env> {
  async verifySession(token: string): Promise<UserSession | null> {
    return validateToken(token, this.env.AUTH_SECRET);
  }
}
```

#### 3. WorkflowEntrypoint (Cloudflare Workflows)
```typescript
import { WorkflowEntrypoint, WorkflowStep, WorkflowEvent } from "cloudflare:workers";

export type OrderParams = { orderId: string; amount: number };

/** @public */
export class OrderProcessingWorkflow extends WorkflowEntrypoint<Env, OrderParams> {
  async run(event: WorkflowEvent<OrderParams>, step: WorkflowStep) {
    const payment = await step.do("process-payment", async () => {
      return chargePayment(event.payload.orderId, event.payload.amount);
    });

    await step.do("send-receipt", async () => {
      await sendReceiptEmail(event.payload.orderId, payment.receiptId);
    });
  }
}
```

#### Knip Defense for RPC Exports
Because `CounterDurableObject`, `AuthService`, and `OrderProcessingWorkflow` are exported from entry files but never imported internally, Knip's `rules.exports` will report them as unused exports. 

**Correct Defense**:
1. Tag each RPC class with `/** @public */` JSDoc annotation.
2. In `knip.jsonc`, configure:
   ```jsonc
   {
     "includeEntryExports": false,
     "ignoreExportsUsedInFile": true
   }
   ```
3. Alternatively, designate entry classes in `entry`:
   ```jsonc
   {
     "entry": [
       "src/index.ts",
       "src/workflows/**/*.ts!"
     ]
   }
   ```

---

## 3. Ambient Type Generation Protection (`wrangler types`)

Wrangler automatically inspects `wrangler.json` (KV namespaces, D1 databases, R2 buckets, Queues, Hyperdrive, AI bindings) and generates ambient type declarations:

```bash
npx wrangler types
```

Output: `worker-configuration.d.ts` (or custom `env.d.ts`):
```typescript
// Generated by Wrangler by running `wrangler types`
interface Env {
  USERS_KV: KVNamespace;
  PROD_DB: D1Database;
  UPLOADS_BUCKET: R2Bucket;
  ORDERS_QUEUE: Queue;
  SESSION_SECRET: string;
}
```

### False Positive Hazards & Remediation
1. **`worker-configuration.d.ts` is Ambient**: It contains no `import` or `export` statements. Knip or file cleanup sweeps may flag it as an unreferenced, dead file.
   - **Remediation**: Explicitly exclude from deletion passes. It is required for the TypeScript compiler to bind `env: Env`.
2. **`@cloudflare/workers-types` Unused Dependency**:
   Declared in `package.json#devDependencies` and referenced strictly via `tsconfig.json`:
   ```json
   {
     "compilerOptions": {
       "types": ["@cloudflare/workers-types/2023-07-01"]
     }
   }
   ```
   Because no `.ts` source file contains `import ... from "@cloudflare/workers-types"`, Knip flags it as an **unused devDependency**.
3. **`@cloudflare/vitest-pool-workers` Unused Dependency**:
   Referenced in `vitest.config.ts` pool options and virtual package `cloudflare:test`.

**Remediation in `knip.jsonc`**:
Always include both packages in `ignoreDependencies`:
```jsonc
{
  "ignoreDependencies": [
    "@types/*",
    "@cloudflare/workers-types",
    "@cloudflare/vitest-pool-workers"
  ]
}
```

---

## 4. Runtime Leakage: `process.env` Eradication

In `workerd`, `process.env` is **not** populated with bindings or secrets. Even with `nodejs_compat` enabled, environment variables and Cloudflare bindings (KV, D1, Queues) exist solely on the `env` object.

### The Defect: Silent Runtime `undefined`
```typescript
// ❌ DANGEROUS NODE.JS PATTERN (Fails at runtime in Cloudflare Workers)
import { createClient } from "@supabase/supabase-js";

export async function getSupabase() {
  const url = process.env.SUPABASE_URL; // Returns undefined!
  const key = process.env.SUPABASE_ANON_KEY; // Returns undefined!
  return createClient(url!, key!); // Throws runtime TypeError: Invalid URL
}
```

### The Edge-Native Remediation: Request-Scoped `env`
Bindings must be drilled from handler inputs or class instances:

```typescript
// ✅ EDGE-NATIVE INVARIANT (Request-scoped env drilling)
import { createClient, SupabaseClient } from "@supabase/supabase-js";

export function getSupabase(env: Env): SupabaseClient {
  return createClient(env.SUPABASE_URL, env.SUPABASE_ANON_KEY);
}

export default {
  async fetch(request, env, ctx): Promise<Response> {
    const supabase = getSupabase(env);
    const { data } = await supabase.from("users").select("*");
    return Response.json(data);
  }
} satisfies ExportedHandler<Env>;
```

In `DurableObject` and `WorkerEntrypoint` classes, access bindings via `this.env`:
```typescript
export class AnalyticsWorker extends WorkerEntrypoint<Env> {
  async recordMetric(name: string, value: number) {
    await this.env.PROD_DB.prepare(
      "INSERT INTO metrics (name, value, recorded_at) VALUES (?, ?, ?)"
    ).bind(name, value, Date.now()).run();
  }
}
```

> [!TIP]
> Audit rule in `scripts/audit-ts-health.py`: Any occurrence of `process.env.*` inside `src/` (excluding build configs) in a Cloudflare Workers project is flagged as a high-severity `process-env-in-worker` defect.

---

## 5. Async Boundary Safety: `ctx.waitUntil()`

In `workerd`, when the Promise returned by `fetch()` settles with a `Response`, the V8 isolate execution is immediately suspended or terminated.

### The Defect: Aborted Floating Promises
```typescript
// ❌ DANGEROUS PATTERN: Background task killed mid-flight
export default {
  async fetch(request, env, ctx): Promise<Response> {
    // BUG: This promise is floating and un-awaited.
    // The moment Response is returned, workerd suspends the isolate.
    // The metric is never written to the queue!
    env.AUDIT_QUEUE.send({ path: request.url, timestamp: Date.now() });

    return new Response("Accepted", { status: 202 });
  }
} satisfies ExportedHandler<Env>;
```

### The Edge-Native Remediation: `ctx.waitUntil()`
All asynchronous tasks intended to run in the background without delaying the HTTP response must be registered with `ctx.waitUntil()`:

```typescript
// ✅ PROTECTED ASYNC BOUNDARY
export default {
  async fetch(request, env, ctx): Promise<Response> {
    // Tells workerd to keep the isolate alive until this promise resolves
    ctx.waitUntil(
      env.AUDIT_QUEUE.send({ path: request.url, timestamp: Date.now() }).catch(err => {
        console.error("Failed to enqueue audit metric:", err);
      })
    );

    return new Response("Accepted", { status: 202 });
  }
} satisfies ExportedHandler<Env>;
```

> [!CAUTION]
> AI cleanup agents must never strip `ctx.waitUntil()` calls or unwrap them into floating promises. `ctx.waitUntil()` is a runtime lifecycle contract, not an unnecessary wrapper.

---

## 6. Testing Infrastructure: `@cloudflare/vitest-pool-workers`

Cloudflare Workers projects test edge logic using `@cloudflare/vitest-pool-workers`, which spins up real `workerd` isolates inside Vitest:

```typescript
// vitest.config.ts
import { defineWorkersConfig } from "@cloudflare/vitest-pool-workers/config";

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        wrangler: { configPath: "./wrangler.json" },
      },
    },
  },
});
```

In test suites, bindings are imported from the virtual module `cloudflare:test`:
```typescript
// test/index.spec.ts
import { env, createExecutionContext, waitOnExecutionContext } from "cloudflare:test";
import { describe, it, expect } from "vitest";
import worker from "../src/index";

describe("Worker Test Suite", () => {
  it("responds with greeting", async () => {
    const request = new Request("http://example.com/");
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    expect(await response.text()).toBe("OK");
  });
});
```

### Preservation Rules
- Never delete `cloudflare:test` imports.
- Never remove `@cloudflare/vitest-pool-workers` from `devDependencies`.
- Keep `vitest` plugin enabled in `knip.jsonc`.

---

## 7. Canonical `knip.jsonc` for Cloudflare Workers

Complete, production-tested Knip configuration for Cloudflare Workers projects:

```jsonc
{
  "$schema": "https://unpkg.com/knip@5/schema.json",
  // Wrangler plugin automatically parses wrangler.json / wrangler.toml
  "wrangler": true,
  // Vitest plugin parses vitest.config.ts
  "vitest": true,
  "entry": [
    "src/index.ts",
    // Workflows or scheduled tasks if separated
    "src/workflows/**/*.ts!"
  ],
  "project": [
    "src/**/*.{ts,tsx}",
    "test/**/*.{ts,tsx}"
  ],
  // Retain exported RPC classes and entry handlers
  "includeEntryExports": false,
  "ignoreExportsUsedInFile": {
    "interface": true,
    "type": true
  },
  // Protect ambient definitions and virtual test harnesses
  "ignoreDependencies": [
    "@types/*",
    "@cloudflare/workers-types",
    "@cloudflare/vitest-pool-workers"
  ],
  // Protect ambient generated types and build state
  "ignore": [
    "worker-configuration.d.ts",
    "env.d.ts",
    ".wrangler/**"
  ],
  "rules": {
    "files": "error",
    "dependencies": "error",
    "devDependencies": "error",
    "unlisted": "error",
    "exports": "error",
    "types": "error",
    "duplicates": "error"
  }
}
```

---

## 8. Workers Pre-Flight & Triage Decision Matrix

Before deleting files or modifying exports in a Cloudflare Workers project, run this triage matrix:

| Finding | Engine Rule | Cause in Workers | Correct Remediation |
|---|---|---|---|
| `CounterDurableObject` unused export | `exports` | Bound via `wrangler.json`, not imported in JS | Add `/** @public */` JSDoc or set `includeEntryExports: false` |
| `AuthService` unused export | `exports` | Service binding RPC class | Add `/** @public */` JSDoc or set `includeEntryExports: false` |
| `worker-configuration.d.ts` unused file | `files` | Ambient type generated by `wrangler types` | Add to `ignore` in `knip.jsonc`. Never delete! |
| `@cloudflare/workers-types` unused dep | `devDependencies` | Referenced via `tsconfig.json` `compilerOptions.types` | Add to `ignoreDependencies` in `knip.jsonc` |
| `@cloudflare/vitest-pool-workers` unused dep | `devDependencies` | Consumed via vitest pool options | Add to `ignoreDependencies` in `knip.jsonc` |
| `process.env.VAR` in handler | Linter / Audit | Leaked Node.js assumption | Refactor to `env.VAR` parameter or `this.env.VAR` |
| `ctx.waitUntil(promise)` call | Code smell / bloat check | Asynchronous execution boundary | Retain untouched. Mandatory for background task completion |
