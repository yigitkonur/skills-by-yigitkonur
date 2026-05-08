# Migration Strategy

Pick the right path *before* touching code. Wrong choice here costs days of churn later.

## Pre-migration audit

Before choosing, answer four questions about the v1 server in scope:

1. **Surface area.** How many `@modelcontextprotocol/sdk/*` import sites? How many handler files? More than ~10 import sites or ~5 handlers tilts toward the meta-package shim — staged migration beats big-bang.
2. **OAuth.** Does the server use `mcpAuthRouter`, `OAuthServerProvider`, or `requireBearerAuth`? If yes, the auth path becomes the critical decision (see "Server-auth-legacy" below).
3. **Production traffic.** Live customers, or a side project? Live traffic forces a staged migration with a working rollback. Side projects can take the full-rewrite hit.
4. **Alpha tolerance.** v2 is at `2.0.0-alpha.2` as of 2026-05-08, milestone `v2.0.0-bc`. If your team can't accept "the SDK might break between alpha versions," delay the migration entirely.

## Four strategies

### 1. Stay on v1 (do nothing yet)

The right call when:

- Server is in production with live traffic.
- v2 alpha cadence (breaking changes between alphas) is unacceptable.
- OAuth router usage is heavy and `server-auth-legacy` doesn't cover your custom provider.

You lose nothing by waiting. v1 is still on `main` (well, the `v1.x` branch) and supports the latest spec (2025-11-25). Re-evaluate when v2 publishes its first non-alpha release. Use the `build-mcp-server-sdk-v1` skill for ongoing work.

### 2. Full rewrite (small servers)

Replace every v1 import with v2, rewrite every handler, remove `mcpAuthRouter`, ship in one PR.

Right when:

- ≤200 LOC of tool/resource code.
- ≤2 transports.
- No OAuth router, or you're happy to replace it with HTTP-layer auth.
- Comprehensive test suite that gives confidence in one large diff.

Wrong when any of those don't hold. The temptation is "it'll be cleaner" — true, but the cleanup cost is paid in a single fragile PR.

### 3. Meta-package shim (medium servers, the recommended default)

The v2 alpha publishes a `@modelcontextprotocol/sdk` meta-package that re-exports v1 import paths under v2 internals. Install v2 packages, point your `@modelcontextprotocol/sdk` dependency at the meta-package, and your existing v1 imports keep working — you can then migrate handlers one at a time.

```jsonc
// package.json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "2.0.0-alpha.2"  // the meta-package, not v1
  }
}
```

Migration sequence:

1. Bump `@modelcontextprotocol/sdk` to the v2 meta-package version. Keep all imports as `@modelcontextprotocol/sdk/server/mcp.js` etc. Run tests — they should pass.
2. Pick one handler. Rewrite its imports to the new packages, schema to Zod v4 / `z.object()`, handler to `(args, ctx)`. Run that handler's tests.
3. Repeat per handler.
4. After all handlers are migrated, move transport, then framework wiring, then auth.
5. Remove the meta-package dependency. Pin to direct v2 packages.

Right when: medium codebase, OAuth absent or replaceable, you want to test runtime behavior on v2 *before* committing to the full rewrite.

### 4. Server-auth-legacy (OAuth-heavy production servers)

`@modelcontextprotocol/server-auth-legacy` is a frozen v1 AuthorizationServer package published alongside v2 specifically for users who can't drop server-side OAuth on the v1→v2 path. v2 server connects through the legacy auth router; everything else (transports, handlers, schemas) migrates to v2.

```typescript
// v1: built-in
import { mcpAuthRouter } from "@modelcontextprotocol/sdk/server/auth/router.js";

// v2 transition: same router, frozen package
import { mcpAuthRouter } from "@modelcontextprotocol/server-auth-legacy";
```

Right when: existing OAuth router is load-bearing for live customers and you're not also rewriting the auth stack in this migration window.

The legacy package is a transition tool, not a destination. Plan a follow-up to migrate auth to a dedicated AS (custom Bearer + jose, Passport, Auth0/Okta external, or better-auth's eventual OAuth Provider Plugin) once v2 reaches stable.

## Strategy decision matrix

| Server profile | Recommended strategy |
|---|---|
| Side project, <200 LOC, no OAuth | Full rewrite |
| Internal tool, <500 LOC, basic Bearer auth | Full rewrite or meta-package |
| Production, <1000 LOC, no OAuth router | Meta-package shim |
| Production, OAuth router in use | Meta-package + server-auth-legacy |
| Production, custom OAuth provider | Stay on v1 until v2 stable |
| OAuth-heavy enterprise | Stay on v1 until v2 stable |

## Recording the choice

Whatever you pick, write it in the migration PR description and commit it to the repo (e.g. `MIGRATION.md` or in `CHANGELOG`). Future maintainers — including you in three months — need to know which strategy is in flight to make sense of the import paths and dependency versions.

## When to abort and roll back

Abort criteria during the migration:

- A v2 alpha publishes a breaking change to an API you depend on (check the v2 changelog before each migration sprint).
- Test coverage drops below your team's threshold during the port.
- Production error rates rise on the staging environment.

Roll-back path: revert the `@modelcontextprotocol/*` dependency bumps, revert handler rewrites, redeploy. The meta-package strategy makes this cheaper than the full-rewrite strategy because un-migrated code paths still match v1 shapes.
