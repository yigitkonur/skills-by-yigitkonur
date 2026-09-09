# Mode 1 — Zero-to-One Stack Research & Initialization

How to autonomously research, provision, architect, and harden Sentry into a new codebase where it is not yet installed.

## When to Enter Mode 1

Trigger Mode 1 when:
- Sentry SDK is not found in dependencies (`package.json`, `requirements.txt`, `go.mod`, etc.).
- The user requests: "Set up Sentry", "Initialize Sentry in this project", "Add Sentry monitoring".
- The repository has no existing Sentry configuration.

## Step 1: Detect Project Stack & Architecture

Before fetching packages or touching code, inspect the repository to determine:
1. **Primary Runtime:** Node.js (ESM / CJS), TypeScript, Python, Go, Rust, Swift.
2. **Framework:** Fastify, Next.js App Router, Express, FastAPI, Django, Gin, NestJS.
3. **Application Topology:**
   - Model Context Protocol (MCP) Server (requires stdio isolation).
   - Cloud browser / scraper / automation engine (Playwright, Puppeteer, Kernel).
   - Backend REST / GraphQL / gRPC API.
   - Background worker / Queue consumer (BullMQ, Celery, Temporal).
   - Standalone CLI or bundled script (`.mjs`).

## Step 2: Execute Web Research Wave via Research MCP (Max 20 Keywords)

Call `research-mcp` (tool: `web-search`) or fallback web search using up to 20 precise keywords tailored to the detected stack:

```bash
# Example query dispatch (up to 20 keywords):
"sentry <framework> best practices"
"sentry <architecture> error handling"
"sentry custom breadcrumbs <framework>"
"sentry async local storage request context"
"sentry structured logging <runtime>"
"sentry envelope tunnel configuration"
"sentry source maps upload release pipeline"
"sentry custom fingerprinting"
```

For detailed protocol and ready-made matrices, see `references/research/research-mcp-protocol.md` and `references/research/stack-keyword-matrices.md`.

## Step 3: Formulate the Project Integration Strategy

Based on research evidence, design the integration blueprint:
1. **Breadcrumb Taxonomy:** Define what domain actions to log (e.g. `mcp.tool_call`, `db.query`, `http.outbound`, `auth.refresh`).
2. **Span Operations:** Define latency-critical operations to wrap in `startSpan` (e.g. `db.query`, `mcp.tool`, `http.client`).
3. **Custom Tags:** Identify business dimensions to attach to scopes (e.g. `tenant_id`, `site`, `user_type`, `region`).
4. **Redaction Matrix:** Identify headers, tokens, and URL parameters requiring redaction.

## Step 4: Authentication & Provisioning

1. Run `bash scripts/detect-creds.sh` to safely inspect `~/.sentryclirc` and discover accessible organizations.
2. Check if a project exists via Sentry API or CLI (`sentry project list <org>/`).
3. If missing, create the project and retrieve the public DSN and numeric Project ID.
4. Save defaults to local `.sentryclirc`:
   ```ini
   [defaults]
   org=your-org-slug
   project=your-project-slug
   ```

## Step 5: Network Hardening — Envelope Tunnel

Derive the direct envelope tunnel URL from the DSN to bypass ISP DNS sinkholes (e.g. TTNet `195.175.254.2` `DEPTH_ZERO_SELF_SIGNED_CERT`):
```typescript
const projectId = dsn.trim().match(/\/(\d+)(?:$|[?#])/)?.[1];
const tunnel = projectId ? `https://sentry.io/api/${projectId}/envelope/` : undefined;
```
See `references/network-tunneling/envelope-tunneling.md`.

## Step 6: Install SDK, Redaction & Context Store

1. Install official SDK (`@sentry/node`, `@sentry/nextjs`, `sentry-sdk`, etc.).
2. Wire `beforeSend` and `beforeBreadcrumb` with redaction filters. See `references/privacy-redaction/credential-redaction-rules.md`.
3. Wire `AsyncLocalStorage` request context store. See `references/performance-replay/asynclocalstorage-context.md`.
4. Apply framework-specific error boundaries. See `references/architectures/`.

## Step 7: Offline Gate & Live Verification

1. Verify `npm test` runs 100% offline with zero network calls when `SENTRY_DSN` is empty. See `references/verification/offline-test-isolation.md`.
2. Run a synthetic error harness (`tools/verify-sentry-live.ts`), assert receipt via CLI, and immediately resolve the issue. See `references/verification/live-synthetic-verification.md`.
