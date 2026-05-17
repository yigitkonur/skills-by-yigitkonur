# Validation and Rollback

The migration is staged code, not a feature flag. This is the playbook for testing it before production traffic and the playbook for unwinding it if production breaks.

## Validation rungs

Climb these in order. Don't claim a rung you haven't reached.

### Rung 1 — type-check passes

```bash
npx tsc --noEmit
```

A clean type check after the import/handler rewrite catches the largest class of mechanical errors (missing properties on `ctx`, wrong import paths, mismatched Zod versions). Most v1→v2 mistakes show up here.

Common findings at this rung:

- `Property 'authInfo' does not exist on ServerContext` — you wrote `ctx.authInfo` instead of `ctx.http?.authInfo`.
- `Argument of type '{ name: ZodString }' is not assignable to parameter of type 'AnySchema'` — you didn't wrap a raw shape in `z.object()`.
- `Module '"@modelcontextprotocol/sdk/server/mcp.js"' has no exported member 'McpServer'` — you assumed a v2 meta-package shim exists, but the target alpha may not publish one. Check npm and the alpha changelog.

### Rung 2 — unit tests pass

Run your existing test suite. The Zod schema rewrite often surfaces stricter validation here — input that v1 accepted with raw shapes may need explicit type narrowing in v2.

If you don't have tests, write at least one per tool:

```typescript
import { test, expect } from "vitest";

test("greet tool returns a greeting", async () => {
  const result = await callTool(server, "greet", { name: "Ada" });
  expect(result.content[0]).toMatchObject({ type: "text", text: /Ada/ });
});
```

A single per-tool happy-path test is enough to catch most regressions during the port.

### Rung 3 — Inspector smoke test

```bash
npx @anthropic-ai/mcp-inspector npx tsx src/index.ts
```

Open the inspector, walk every tool, every resource, every prompt. Record any field that displays differently from v1 — `outputSchema`-validated structured content, `_meta` round-trip, capability negotiation.

For HTTP transport, point the inspector at `http://localhost:PORT/mcp` and repeat.

### Rung 4 — integration with a real client

Connect the migrated server to whatever real MCP client your users actually run (Claude Desktop, Cursor, Continue, Cline, custom). Don't assume the inspector covers client behavior — clients differ in capability handling, especially around `outputSchema`, sampling, elicitation, and resource subscriptions.

### Rung 5 — staging environment, realistic traffic

Deploy the migrated server to a staging environment that matches production topology (load balancer, TLS termination, auth provider, observability). Replay last week's request log if you have one, or run synthetic traffic at production rates for at least one week.

What to watch:

- Error rate compared to v1 baseline.
- Latency p50/p95/p99 — handler context restructuring shouldn't change these but does occasionally reveal slow ServerContext field access.
- Memory growth — different transport class, different per-session allocation pattern.

### Rung 6 — production canary

Route a small percentage of production traffic to v2 (e.g. one of N replicas, or a percentage-based split at the load balancer). Watch error rates for at least 48 hours before increasing the share.

## Dual-version coexistence

During staged migration you may need to run v1 and v2 side-by-side — for example, a v1 stable backend with a v2 endpoint exposed on a separate route while you test.

Two approaches, in order of preference:

### Approach A — Two processes

Run v1 and v2 as separate Node processes behind a reverse proxy. Routes `/mcp/v1` and `/mcp/v2` to each. Cleanest separation; no module-resolution risk.

### Approach B — Meta-package shim, only if published

Single process, depend on the v2 `@modelcontextprotocol/sdk` meta-package only if the target alpha publishes it. Existing v1 imports keep working; new v2 imports use direct package paths. Verify there's no class-identity mixing — handlers must consistently use one shape, not both.

```typescript
// In a meta-package process, this works:
import { McpServer as V1Server } from "@modelcontextprotocol/sdk/server/mcp.js";
import { McpServer as V2Server } from "@modelcontextprotocol/server";
// V1Server === V2Server  →  true  (under the meta-package shim)
```

In a non-shim setup, the two are different classes and `instanceof` checks across the boundary will fail. The shim is the only safe way to mix imports.

## Rollback playbook

Trigger criteria (any of):

- Error rate on staging or canary exceeds v1 baseline by more than 2x for over 30 minutes.
- A v2 alpha publishes a breaking change that affects code you've already migrated and a fix isn't available within 24 hours.
- Auth flow regression — tokens that worked under v1 fail under v2.
- A downstream MCP client team reports they can't connect.

Roll-back sequence:

1. Revert the deployment to the last v1-stable image (kept warm by your CI).
2. Revert the dependency bumps (`@modelcontextprotocol/sdk` from v2 alpha back to `^1.x`) on the migration branch.
3. Revert handler rewrites (git revert the per-handler commits — atomic commits make this cheap).
4. Re-run rung 1-3 on the rolled-back branch to confirm v1 still passes.
5. File the regression against the v2 alpha milestone.

If you used the meta-package strategy, individual handler reverts are isolated commits. If you used the full-rewrite strategy, the rollback is "revert the migration PR." Plan accordingly when picking the strategy.

## Keep the v1 branch deployable

Until v2 publishes a non-alpha stable release:

- Don't delete the v1 branch.
- Don't delete `package-lock.json` or `pnpm-lock.yaml` from the v1 branch.
- Don't garbage-collect the v1 Docker image from your registry.
- Keep CI green on the v1 branch so an emergency rollback build is one click away.

This is the cheapest insurance you have during the alpha window.

## Pre-flight checklist for this stage

- [ ] Type check (`tsc --noEmit`) passes.
- [ ] Existing test suite passes.
- [ ] Inspector smoke test walked every tool, resource, prompt.
- [ ] At least one real MCP client tested end-to-end.
- [ ] Staging environment runs the migrated server for at least one week with realistic traffic.
- [ ] Production canary plan documented (percentage, duration, error-rate trigger).
- [ ] Rollback playbook tested at least once on staging (revert and redeploy succeed).
- [ ] v1 branch and lockfile preserved.
- [ ] Last v1-stable Docker image kept warm.
- [ ] v2 changelog subscribed to / monitored for the duration of the migration.
