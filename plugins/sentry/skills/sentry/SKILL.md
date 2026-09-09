---
name: sentry
description: "Use if initializing Sentry from scratch, auditing an existing setup across 4 pillars, or triaging production errors with token-efficient CLI recipes."
metadata:
  author: Yigit Konur
  version: 2.0.0
  category: observability
  tags: [sentry, monitoring, error-tracking, tracing, debugging, mcp]
---

# Sentry

The complete Sentry observability lifecycle: autonomous stack research & zero-to-one setup, deep 4-pillar feature auditing, and agent-driven production incident triage.

## Decision tree (The 3 Modes)

```
What is your objective?
├── Mode 1: Sentry is NOT in the project OR user says "set up / initialize Sentry"
│   ├── Step 1: Detect runtime, framework & architecture (MCP, crawler, API, CLI)
│   ├── Step 2: Research stack patterns via research-mcp (max 20 keywords): `references/research/research-mcp-protocol.md`
│   ├── Step 3: Choose keyword matrix: `references/research/stack-keyword-matrices.md`
│   ├── Step 4: Step-by-step setup guide: `references/modes/mode-1-init.md`
│   └── Step 5: Stack blueprint: `references/architectures/` (mcp, playwright, fastify, nextjs, cli, python, go)
│
├── Mode 2: Sentry IS already installed OR user asks "audit / improve our Sentry"
│   ├── Step 1: Run feature audit scanner: `bash scripts/audit-project.sh`
│   ├── Step 2: Full 4-pillar audit & gap analysis guide: `references/modes/mode-2-audit.md`
│   ├── Pillar 1 (Error Tracking): `references/error-tracking/` (capture, sourcemaps, fingerprints, inbound-filters, merges)
│   ├── Pillar 2 (Breadcrumbs & Context): `references/breadcrumbs-context/` (system, ui, tags, feedback, device)
│   ├── Pillar 3 (Logging & Analytics): `references/logging-analytics/` (structured-logs, pin-to-top, log-explorer, discover)
│   └── Pillar 4 (Performance & Replay): `references/performance-replay/` (spans, asynclocalstorage, replay, crons)
│
└── Mode 3: "Something is broken in prod" / Triage alerts / Debug incident
    ├── Step 1: Run triage scanner: `bash scripts/triage-issues.sh`
    ├── Step 2: 4-rung triage guide: `references/modes/mode-3-debug.md`
    ├── Step 3: Fast diagnosis in 1 call: `references/cli-tooling/modern-sentry-cli.md`
    ├── Step 4: Trace-to-log correlation: `references/logging-analytics/log-explorer-queries.md`
    └── Step 5: Safe mutations & post-fix verification: `references/verification/post-fix-verification.md`
```

## Quick start

### Mode 1: Setup in New Project
```bash
# 1. Check credentials safely (~/.sentryclirc)
bash scripts/detect-creds.sh

# 2. Test envelope tunnel connectivity & ISP sinkhole defense
bash scripts/verify-tunnel.sh <PROJECT_ID_OR_DSN>
```

### Mode 2: Audit Existing Project
```bash
# Run automated feature adoption scanner across 4 pillars
bash scripts/audit-project.sh .
```

### Mode 3: Triage Production Errors
```bash
# List top unresolved errors ranked by frequency
bash scripts/triage-issues.sh <org>/<project>

# Diagnose specific issue in 1 single token-efficient call
sentry issue view <ID> --json > /tmp/iss.json
jq -r '.event.entries[] | select(.type=="exception") | .data.values[].stacktrace.frames[]? | select(.inApp) | "\(.filename):\(.lineNo) in \(.function)"' /tmp/iss.json
```

## The 4-Rung Debugging Funnel

```
Rung 0  Triage        issue list   -> what is broken, ranked by frequency (cheap)
Rung 1  Diagnose      issue view   -> ONE issue + embedded latest event   (usually solves it)
Rung 2  Corroborate   explore/logs -> multi-event tag patterns, trace logs (only if Rung 1 is thin)
Rung 3  Deep Discover queries/repro-> agent discovers root cause locally   (independent reasoning)
```

## Key patterns

### 1. Mandatory Envelope Tunneling (Defeating ISP DNS Sinkholes)
In Turkey (TTNet `195.175.254.2`) and captive networks, `*.ingest.*sentry.io` is intercepted, throwing `DEPTH_ZERO_SELF_SIGNED_CERT`. Deriving `tunnel: https://sentry.io/api/${projectId}/envelope/` routes through trusted Cloudflare edge IPs and guarantees 100% delivery.

### 2. Defense-in-Depth Redaction
Hook sanitizers into `beforeSend` and `beforeBreadcrumb`. Scrub `authorization`, `x-api-key`, session cookies, and strip bearer JWTs in WebSocket or browser URLs (`cdpWsUrl?jwt=...`).

### 3. Zero-Network Offline Test Gate
If `SENTRY_DSN` is empty or missing, `initSentry()` must cleanly no-op. Offline test suites (`npm test`) must run 100% network-free and spend $0.

### 4. Standalone CLI Guaranteed Flush
CLI scripts terminate immediately on exit. Always wrap the execution pipeline in try/catch and execute `await flushSentry(3000)` before `process.exit()`.

## Common pitfalls

| Pitfall | Root Cause | Fix |
|---|---|---|
| `DEPTH_ZERO_SELF_SIGNED_CERT` | ISP DNS hijacking on `*.ingest.*sentry.io` | Set `tunnel: https://sentry.io/api/<projectId>/envelope/` |
| Token leak in logs | `cdpWsUrl` logged with `?jwt=...` | Scrub query parameters; log opaque `sessionId` instead |
| CLI drops error reports | Process exits before async HTTP envelope finishes | `await flushSentry(3000)` before `process.exit(1)` |
| MCP client crashes on start | Sentry debug or console logs written to stdout | Set `debug: false`; isolate logging to stderr in stdio mode |
| Tests fail when offline | SDK attempts live HTTP calls in unit tests | No-op `initSentry()` when `SENTRY_DSN` is missing |
| Alert fatigue from retries | Identical errors grouped under separate issues | Use `scope.setFingerprint(['db-outage', error.code])` |

## Minimal reading sets

### "I need to initialize Sentry in a new repository"
- `references/modes/mode-1-init.md`
- `references/research/research-mcp-protocol.md`
- `references/network-tunneling/envelope-tunneling.md`
- `references/privacy-redaction/credential-redaction-rules.md`

### "I need to audit our Sentry setup and implement missing features"
- `references/modes/mode-2-audit.md`
- `references/error-tracking/sourcemaps-pipeline.md`
- `references/breadcrumbs-context/system-breadcrumbs.md`
- `references/logging-analytics/structured-logs.md`
- `references/performance-replay/distributed-tracing-spans.md`

### "I need to debug an MCP server or cloud browser application"
- `references/architectures/mcp-server-sentry.md`
- `references/architectures/cloud-browsers-playwright.md`
- `references/privacy-redaction/url-jwt-sanitization.md`

### "Production is throwing 500s right now"
- `references/modes/mode-3-debug.md`
- `references/cli-tooling/modern-sentry-cli.md`
- `references/logging-analytics/log-explorer-queries.md`
- `references/verification/post-fix-verification.md`

## Reference files

| File | When to read |
|---|---|
| `references/modes/mode-1-init.md` | Guide for zero-to-one stack research, provisioning, and setup. |
| `references/modes/mode-2-audit.md` | Comprehensive 4-pillar audit protocol and business value assessment. |
| `references/modes/mode-3-debug.md` | 4-rung debugging funnel and empirical root-cause analysis. |
| `references/research/research-mcp-protocol.md` | How to drive research-mcp with up to 20 keywords for stack research. |
| `references/research/stack-keyword-matrices.md` | Ready-to-use search keyword matrices for MCP, Fastify, Next.js, etc. |
| `references/error-tracking/exception-capture.md` | Capturing unhandled rejections, uncaught exceptions, and edge crashes. |
| `references/error-tracking/sourcemaps-pipeline.md` | Uploading sourcemaps and linking releases to Git commits. |
| `references/error-tracking/fingerprinting-grouping.md` | Configuring custom fingerprinting rules to eliminate alert fatigue. |
| `references/error-tracking/inbound-filters.md` | Dropping web crawlers, browser extensions, and noise. |
| `references/error-tracking/merges-and-splits.md` | Merging duplicate clusters or splitting mistakenly grouped errors. |
| `references/breadcrumbs-context/system-breadcrumbs.md` | Recording HTTP, database, cache, and RPC system breadcrumbs. |
| `references/breadcrumbs-context/ui-breadcrumbs.md` | Capturing user clicks, navigations, and DOM interactions. |
| `references/breadcrumbs-context/custom-tags-context.md` | Attaching searchable key-value tags (tenant, user tier, driver). |
| `references/breadcrumbs-context/user-feedback-api.md` | In-app crash dialog and programmatic user feedback submission. |
| `references/breadcrumbs-context/device-runtime-context.md` | Capturing OS, runtime version, memory stats, and container metadata. |
| `references/logging-analytics/structured-logs.md` | Ingesting, indexing, and querying application structured logs. |
| `references/logging-analytics/pin-to-top-logs.md` | Pinning critical log lines to the top of issue layouts. |
| `references/logging-analytics/log-explorer-queries.md` | Sentry Log Explorer query syntax and live tail streaming. |
| `references/logging-analytics/discover-query-builder.md` | Running SQL-like Discover queries for latency and error trends. |
| `references/performance-replay/distributed-tracing-spans.md` | Instrumenting spans, trace headers, and latency percentiles. |
| `references/performance-replay/asynclocalstorage-context.md` | Ambient request context propagation across async call trees. |
| `references/performance-replay/session-replay.md` | Video-like DOM reconstruction correlated with error IDs. |
| `references/performance-replay/cron-monitors.md` | Background job heartbeats, check-ins, and missed execution alerts. |
| `references/architectures/mcp-server-sentry.md` | MCP Server architecture: stdio isolation, tool breadcrumbs, token redaction. |
| `references/architectures/cloud-browsers-playwright.md` | Playwright/Kernel browser tracing and strict cdpWsUrl JWT scrubbing. |
| `references/architectures/fastify-rest-api.md` | Fastify 4/5 request context plugin and 4xx vs 5xx separation. |
| `references/architectures/nextjs-app-router.md` | Next.js 14/15 client, server, edge configs and tunnel rewrites. |
| `references/architectures/cli-bundled-scripts.md` | Standalone CLIs, unhandled exception traps, and guaranteed flush. |
| `references/architectures/python-fastapi.md` | Python FastAPI and Flask instrumentation with custom transports. |
| `references/architectures/go-gin.md` | Go Gin middleware, panic recovery, and trace propagation. |
| `references/network-tunneling/isp-dns-sinkhole.md` | Diagnosing TTNet/ISP DNS sinkholes and certificate interception. |
| `references/network-tunneling/envelope-tunneling.md` | Official envelope tunneling architecture and SDK configuration. |
| `references/network-tunneling/application-proxy-routes.md` | Implementing internal tunnel endpoints in Next.js, Fastify, Express. |
| `references/privacy-redaction/credential-redaction-rules.md` | Defense-in-depth sanitization of auth headers, Bearer tokens, cookies. |
| `references/privacy-redaction/url-jwt-sanitization.md` | Scrubbing sensitive query parameters (?jwt=..., ?token=...) from URLs. |
| `references/cli-tooling/modern-sentry-cli.md` | Full manual for the modern sentry binary (cli.sentry.dev). |
| `references/cli-tooling/legacy-sentry-cli.md` | Complete manual for sentry-cli (/usr/local/bin/sentry-cli). |
| `references/cli-tooling/project-mapping-config.md` | Mapping repositories to Sentry slugs via local config. |
| `references/cli-tooling/cli-troubleshooting.md` | Resolving auth failures, 404s on whoami, and timeouts. |
| `references/verification/offline-test-isolation.md` | Guaranteeing test suites run 100% offline with zero network calls. |
| `references/verification/live-synthetic-verification.md` | Synthetic error verification harnesses and CLI confirmation. |
| `references/verification/post-fix-verification.md` | Proving a deployed fix stopped the error before closing the issue. |
| `references/verification/security-audit-checklist.md` | Verification protocol to ensure zero credentials leak into git. |

## Guardrails

- Never commit real auth tokens (`sntryu_`, `sntrys_`) to git; store them in `~/.sentryclirc` or `.env`.
- In MCP servers using `stdio`, NEVER write Sentry logs or debug output to `stdout`; always use `stderr`.
- Never log raw WebSocket URLs containing JWT tokens (`cdpWsUrl?jwt=...`).
- Never disable TLS verification (`NODE_TLS_REJECT_UNAUTHORIZED=0`); use envelope tunneling instead.
- Never let an offline test suite make network requests to Sentry; no-op when `SENTRY_DSN` is empty.
- Always call `await flushSentry(3000)` before calling `process.exit()` in CLI scripts.
- Never resolve, archive, or merge an issue without explicit user authorization or empirical proof.
