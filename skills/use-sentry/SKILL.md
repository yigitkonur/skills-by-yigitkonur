---
name: use-sentry
description: "Use if setting up or auditing modern Sentry observability with OpenTelemetry, Continuous Profiling, Crons, Metrics, Replay, Spotlight, or triaging production incidents using Seer AI and modern CLI recipes."
metadata:
  author: Yigit Konur
  version: 3.0.0
  category: observability
  tags: [sentry, monitoring, error-tracking, tracing, debugging, mcp, opentelemetry, profiling, seer-ai]
---

# Sentry

The complete enterprise Sentry observability lifecycle: autonomous stack research & zero-to-one setup, multi-pillar observability auditing (OpenTelemetry, Continuous Profiling, Crons, Metrics, Session Replay, Spotlight), and AI-accelerated production incident triage with Seer AI.

## The 7 Enterprise Observability Pillars

Modern Sentry extends beyond basic error catching into a unified, full-stack observability platform:
1. **Error Monitoring & Exception Capture**: Automated unhandled exception capture, source maps, contextual breadcrumbs, and semantic issue grouping.
2. **OpenTelemetry & Distributed Tracing**: Native OpenTelemetry engine (`@sentry/opentelemetry`), W3C `traceparent` and `baggage` propagation, and end-to-end distributed span waterfall trees (`Sentry.startSpan`).
3. **Continuous Profiling**: Low-overhead runtime CPU and memory profiling (`@sentry/profiling-node`, `profileSessionSampleRate`) decoupled from individual transactions.
4. **Cron & Uptime Monitoring**: Heartbeat check-ins and missed execution alerts for background queues and scheduled tasks (`Sentry.withMonitor`, `Sentry.captureCheckIn`).
5. **Application Metrics**: Real-time telemetry counters, distributions, gauges, and sets (`Sentry.metrics.increment`, `distribution`, `gauge`, `set`).
6. **Session Replay & Privacy Redaction**: Video-like DOM reconstruction correlated with error traces, enforced with strict privacy shields (`maskAllText`, `blockAllMedia`) and network allowlists.
7. **Spotlight Local Development Overlay**: Zero-overhead local development sidecar and interactive browser overlay (`@spotlightjs/spotlight`, `spotlight: true`) for instant trace visibility.

## Decision tree (The 3 Modes)

```
What is your objective?
├── Mode 1: Sentry is NOT in the project OR user says "set up / initialize Sentry"
│   ├── Step 1: Detect runtime, framework & architecture (Node, Next.js, Fastify, MCP, Python, Go)
│   ├── Step 2: Research stack patterns via research-mcp (max 20 keywords): `references/research/research-mcp-protocol.md`
│   ├── Step 3: Choose keyword matrix: `references/research/stack-keyword-matrices.md`
│   ├── Step 4: Step-by-step setup guide: `references/modes/mode-1-init.md`
│   ├── Step 5: Stack blueprints: `references/architectures/` (mcp, playwright, fastify, nextjs, cli, python, go)
│   ├── Step 6: Application reverse proxy tunneling: `references/network-tunneling/application-proxy-routes.md` & `references/network-tunneling/envelope-tunneling.md`
│   └── Step 7: Local development with Spotlight: `references/performance-replay/distributed-tracing-spans.md`
│
├── Mode 2: Sentry IS already installed OR user asks "audit / improve our Sentry"
│   ├── Step 1: Run feature audit scanner: `bash scripts/audit-project.sh`
│   ├── Step 2: Full enterprise audit & gap analysis guide: `references/modes/mode-2-audit.md`
│   ├── Pillar 1 (Error Tracking & Sourcemaps): `references/error-tracking/` (capture, sourcemaps, fingerprints, inbound-filters, merges)
│   ├── Pillar 2 (Breadcrumbs & Rich Context): `references/breadcrumbs-context/` (system, ui, tags, feedback, device)
│   ├── Pillar 3 (Logging & Analytics): `references/logging-analytics/` (structured-logs, pin-to-top, log-explorer, discover)
│   ├── Pillar 4 (Tracing, Profiling, Crons, Replay): `references/performance-replay/` (spans, asynclocalstorage, replay, crons)
│   └── Pillar 5 (Privacy & Redaction): `references/privacy-redaction/` (credentials, url-jwt)
│
└── Mode 3: "Something is broken in prod" / Triage alerts / Debug incident
    ├── Step 1: Run triage scanner: `bash scripts/triage-issues.sh <org>/<project>`
    ├── Step 2: 4-rung triage guide: `references/modes/mode-3-debug.md`
    ├── Step 3: Seer AI root cause analysis: `sentry issue explain <ID>`
    ├── Step 4: Seer AI automated fix planning: `sentry issue plan <ID>`
    ├── Step 5: Modern CLI reference: `references/cli-tooling/modern-sentry-cli.md` (vs `references/cli-tooling/legacy-sentry-cli.md`)
    ├── Step 6: Trace & log correlation: `references/logging-analytics/log-explorer-queries.md` & `references/logging-analytics/discover-query-builder.md`
    └── Step 7: Safe mutations & post-fix verification: `references/verification/post-fix-verification.md` & `references/verification/live-synthetic-verification.md`
```

## Quick start

### Mode 1: Setup in New Project
```bash
# 1. Check credentials safely (~/.sentryclirc or SENTRY_AUTH_TOKEN)
bash scripts/detect-creds.sh

# 2. Test application reverse proxy route & ISP sinkhole defense
bash scripts/verify-tunnel.sh <PROJECT_ID_OR_DSN>

# 3. Launch local developer sidecar (Spotlight)
npx @spotlightjs/spotlight
```

### Mode 2: Audit Existing Project
```bash
# Run automated feature adoption scanner across enterprise pillars
bash scripts/audit-project.sh .
```

### Mode 3: Triage Production Errors with Seer AI & Modern CLI
```bash
# 1. List top unresolved errors ranked by frequency & Seer fixability
sentry issue list <org>/<project> -s freq -t 24h -n 10

# 2. One-call root cause analysis powered by Seer AI
sentry issue explain @latest

# 3. Generate automated step-by-step code remediation plan
sentry issue plan @latest

# 4. Fallback: Deep JSON diagnostic inspection
sentry issue view <ID> --json > /tmp/iss.json
jq -r '.event.entries[] | select(.type=="exception") | .data.values[].stacktrace.frames[]? | select(.inApp) | "\(.filename):\(.lineNo) in \(.function)"' /tmp/iss.json
```

## The 4-Rung Debugging Funnel

```
Rung 0  Triage        sentry issue list    -> rank by frequency and seerFixabilityScore (token-efficient)
Rung 1  Diagnose      sentry issue explain -> Seer AI identifies root cause, culprit files & repro steps
Rung 2  Plan & Verify sentry issue plan    -> Seer AI generates code fix plan; corroborate with trace logs
Rung 3  Deep Discover explore / replay     -> trace waterfall inspection or raw rrweb replay reproduction
```

## Key patterns & Architecture

### 1. Application-Hosted Reverse Proxy Tunneling (Defeating DNS Sinkholes & Ad-Blockers)
In regions with captive ISP DNS sinkholes (e.g. TTNet `195.175.254.2` in Turkey hijacking DNS and returning self-signed certificates) and client browsers running content blockers (uBlock Origin, Brave Shields), direct requests to `*.ingest.*sentry.io` or `sentry.io` are blocked or fail TLS validation (`DEPTH_ZERO_SELF_SIGNED_CERT`).
- **Antipattern**: Setting `tunnel: https://sentry.io/api/${projectId}/envelope/` directly in the client SDK still issues cross-origin requests to Sentry domains and will be intercepted.
- **Architectural Solution**: Client SDKs must point `tunnel` to an **application-hosted reverse proxy route** (e.g. `/api/monitoring/tunnel` or Next.js `tunnelRoute: '/monitoring-tunnel'`).
- The application backend parses the envelope header, validates the destination host and `projectId` against an allowlist (preventing open proxy relay exploits), and proxies raw envelope bytes server-to-server to Sentry's edge.

### 2. Defense-in-Depth Redaction
Hook sanitizers into `beforeSend` and `beforeBreadcrumb`. Scrub `authorization`, `x-api-key`, session cookies, and strip sensitive query parameters (`?jwt=...`, `?token=...`) in WebSocket URLs and HTTP routes.

### 3. Zero-Network Offline Test Gate
When `SENTRY_DSN` is empty or missing, `Sentry.init({ dsn: process.env.SENTRY_DSN })` natively operates in clean no-op mode: captures no events, sends zero network requests, and spends $0. Offline test suites (`npm test`) run 100% network-free without custom mocking wrappers.

### 4. Standalone CLI Guaranteed Bounded Flush
CLI scripts and serverless functions terminate Node processes immediately on exit. Always wrap the execution pipeline in try/catch and execute `await Sentry.flush(3000)` or `await Sentry.close(3000)` before `process.exit()` to ensure buffered async HTTP envelopes leave the network buffer.

### 5. CLI Disambiguation: Modern `sentry` vs Legacy `sentry-cli`
- **Modern `sentry` CLI** (`cli.sentry.dev` / `getsentry/toolkit`): Built for developers and AI coding agents. Uses singular noun commands (`sentry issue`, `sentry log`, `sentry trace`, `sentry explore`, `sentry replay`, `sentry api`). Features Seer AI integration (`sentry issue explain`, `sentry issue plan`), live log streaming (`-f`), and automatic OAuth token refresh via SQLite (`~/.config/sentry/cli.db`).
- **Legacy `sentry-cli`** (`getsentry/sentry-cli`): Rust-based build utility. Uses plural noun commands (`sentry-cli releases`, `sentry-cli sourcemaps`, `sentry-cli issues`). Intended strictly for CI/CD asset injection, sourcemap uploads, and release finalization.

### 6. Seer AI Root-Cause Analysis & Fix Planning
Sentry Seer is an integrated AI engine analyzing traces, breadcrumbs, correlated logs, and source code:
- `sentry issue explain <ID>`: Analyzes incident telemetry and connected repositories to pinpoint root causes, culprit files, line numbers, and reproduction steps in a single call.
- `sentry issue plan <ID>`: Synthesizes a step-by-step code remediation plan, providing exact file modifications and diff context.
- **Vector Grouping**: Uses high-dimensional embeddings to semantically group error variations, eliminating alert storms.
- `seerFixabilityScore`: Quantifies the likelihood of automated fix resolution.

### 7. Quota Bleed & Runaway Loop Circuit Breakers (Archiving/Muting ≠ Quota Relief)
Muting (`sentry-cli issues mute`) or archiving (`sentry issue archive`) only silences notifications. Events are still ingested at Sentry's edge and consume monthly quota. To halt runaway quota bleed:
1. **Server-Side Inbound Filters (`filters:error_messages`)**: Discard events matching error patterns before quota billing via Sentry REST API (`PUT /api/0/projects/<org>/<project>/`) or UI settings.
2. **Client Key (DSN) Rate Limiting & Deactivation**: Throttle (`rateLimit: { window, count }`) or disable (`isActive: false`) in Project Settings -> Client Keys. Dropped events return HTTP 429/403 at the edge with 0 quota consumed.
3. **Queue & Retry Storm Defense**: Background queues (Upstash QStash, BullMQ, Celery) retrying unhandled 500 exceptions create exponential error multipliers. Add SDK `ignoreErrors`, validate payloads, and suppress poison pills before queue retries.
4. **Project Deletion**: When retiring an unused service, delete it via Sentry REST API (`DELETE /api/0/projects/<org>/<project>/`) to immediately invalidate its DSNs and eliminate zombie traffic.

### 8. Regional Multi-Tenant Host Awareness
Sentry SaaS operates regional clusters (e.g. EU cluster `https://de.sentry.io` vs US cluster `https://sentry.io`). When an organization is hosted on a regional cluster, API queries and CLI commands must target `https://de.sentry.io/` (`--url https://de.sentry.io/` or `url = https://de.sentry.io/` in `~/.sentryclirc`). Pointing to `https://sentry.io/` will return `404 Not Found` for legitimate issues and projects.

## Common pitfalls

| Pitfall | Root Cause | Fix |
|---|---|---|
| `DEPTH_ZERO_SELF_SIGNED_CERT` | ISP DNS hijacking or content blockers on `*.ingest.*sentry.io` | Route client envelopes through application reverse proxy (`/api/monitoring/tunnel` or Next.js `tunnelRoute`) |
| CLI drops error reports on exit | Process exits before async HTTP envelope leaves transport buffer | Execute `await Sentry.flush(3000)` or `await Sentry.close(3000)` before `process.exit(1)` |
| Tests fail when offline | SDK attempts live HTTP calls in unit tests | Initialize with `Sentry.init({ dsn: process.env.SENTRY_DSN })` which natively no-ops when DSN is unset |
| Quota drained despite issue mute | `sentry issue archive` or mute silences alerts but still ingests events | Use Inbound Filters (`filters:error_messages`) or Client Key rate limits |
| 404 on API/CLI issue lookup | Organization is on EU cluster (`de.sentry.io`), CLI defaults to US | Set `url = https://de.sentry.io/` in `~/.sentryclirc` or pass `--url` |
| Queue retry flood exhausts quota | Queue retries failed jobs in a loop; SDK reports on every attempt | Add SDK `ignoreErrors`, guard handlers against `undefined`, rate-limit DSN |
| Seer AI plan fails with repo error | GitHub/GitLab integration or Code Mappings missing | Upload mappings via `sentry code-mappings upload` and link repository |
| MCP client crashes on start | Sentry debug or console logs written to stdout in stdio mode | Set `debug: false`; isolate logging to stderr in stdio mode |
| Spotlight active in production | `spotlight: true` sends requests to localhost sidecar in prod | Guard with `spotlight: process.env.NODE_ENV === 'development'` |
| Token leak in logs | `cdpWsUrl` logged with `?jwt=...` query parameters | Scrub query parameters; log opaque `sessionId` instead |
| Zombie project burning quota | Old deployment or background job sending events to stale project | Delete project via REST API (`DELETE /api/0/projects/<org>/<project>/`) |

## Minimal reading sets

### "I need to initialize Sentry in a new repository"
- `references/modes/mode-1-init.md`
- `references/research/research-mcp-protocol.md`
- `references/network-tunneling/envelope-tunneling.md`
- `references/network-tunneling/application-proxy-routes.md`
- `references/privacy-redaction/credential-redaction-rules.md`

### "I need to audit our Sentry setup and implement missing features"
- `references/modes/mode-2-audit.md`
- `references/error-tracking/sourcemaps-pipeline.md`
- `references/breadcrumbs-context/system-breadcrumbs.md`
- `references/logging-analytics/structured-logs.md`
- `references/performance-replay/distributed-tracing-spans.md`
- `references/performance-replay/session-replay.md`
- `references/performance-replay/cron-monitors.md`

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
| `references/modes/mode-2-audit.md` | Comprehensive enterprise audit protocol across all observability pillars. |
| `references/modes/mode-3-debug.md` | 4-rung debugging funnel with Seer AI root cause analysis and fix planning. |
| `references/research/research-mcp-protocol.md` | How to drive research-mcp with up to 20 keywords for stack research. |
| `references/research/stack-keyword-matrices.md` | Ready-to-use search keyword matrices for MCP, Fastify, Next.js, OTel, etc. |
| `references/error-tracking/exception-capture.md` | Capturing unhandled rejections, uncaught exceptions, and edge crashes. |
| `references/error-tracking/sourcemaps-pipeline.md` | Uploading sourcemaps and linking releases to Git commits. |
| `references/error-tracking/fingerprinting-grouping.md` | Configuring custom fingerprinting rules and Seer AI semantic grouping. |
| `references/error-tracking/inbound-filters.md` | Dropping web crawlers, browser extensions, and quota-draining noise. |
| `references/error-tracking/merges-and-splits.md` | Merging duplicate clusters or splitting mistakenly grouped errors. |
| `references/breadcrumbs-context/system-breadcrumbs.md` | Recording HTTP, database, cache, and RPC system breadcrumbs. |
| `references/breadcrumbs-context/ui-breadcrumbs.md` | Capturing user clicks, navigations, and DOM interactions. |
| `references/breadcrumbs-context/custom-tags-context.md` | Attaching searchable key-value tags (tenant, user tier, driver). |
| `references/breadcrumbs-context/user-feedback-api.md` | In-app crash dialog and programmatic user feedback submission. |
| `references/breadcrumbs-context/device-runtime-context.md` | Capturing OS, runtime version, memory stats, and container metadata. |
| `references/logging-analytics/structured-logs.md` | Ingesting, indexing, and querying application structured logs. |
| `references/logging-analytics/pin-to-top-logs.md` | Highlighting critical log context and fatal assertion tags. |
| `references/logging-analytics/log-explorer-queries.md` | Sentry Log Explorer query syntax and live tail streaming. |
| `references/logging-analytics/discover-query-builder.md` | Running SQL-like Discover queries for latency and error trends. |
| `references/performance-replay/distributed-tracing-spans.md` | OpenTelemetry native spans, trace headers, and latency percentiles. |
| `references/performance-replay/asynclocalstorage-context.md` | Ambient request context propagation across async call trees. |
| `references/performance-replay/session-replay.md` | Video-like DOM reconstruction correlated with error traces & privacy masks. |
| `references/performance-replay/cron-monitors.md` | Background job heartbeats, check-ins, and missed execution alerts. |
| `references/architectures/mcp-server-sentry.md` | MCP Server architecture: stdio isolation, tool breadcrumbs, token redaction. |
| `references/architectures/cloud-browsers-playwright.md` | Playwright/Kernel browser tracing and strict cdpWsUrl JWT scrubbing. |
| `references/architectures/fastify-rest-api.md` | Fastify 4/5 request context plugin and 4xx vs 5xx separation. |
| `references/architectures/nextjs-app-router.md` | Next.js 14/15 client, server, edge configs and tunnel rewrites. |
| `references/architectures/cli-bundled-scripts.md` | Standalone CLIs, unhandled exception traps, and guaranteed flush. |
| `references/architectures/python-fastapi.md` | Python FastAPI and Flask instrumentation with custom transports. |
| `references/architectures/go-gin.md` | Go Gin middleware, panic recovery, and trace propagation. |
| `references/network-tunneling/isp-dns-sinkhole.md` | Diagnosing TTNet/ISP DNS sinkholes and certificate interception. |
| `references/network-tunneling/envelope-tunneling.md` | Reverse proxy envelope tunneling architecture and SDK configuration. |
| `references/network-tunneling/application-proxy-routes.md` | Implementing internal tunnel endpoints in Next.js, Fastify, Express. |
| `references/privacy-redaction/credential-redaction-rules.md` | Defense-in-depth sanitization of auth headers, Bearer tokens, cookies. |
| `references/privacy-redaction/url-jwt-sanitization.md` | Scrubbing sensitive query parameters (?jwt=..., ?token=...) from URLs. |
| `references/cli-tooling/modern-sentry-cli.md` | Full manual for the modern sentry binary (cli.sentry.dev) and Seer AI. |
| `references/cli-tooling/legacy-sentry-cli.md` | Complete manual for legacy sentry-cli (/usr/local/bin/sentry-cli). |
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
- Never disable TLS verification (`NODE_TLS_REJECT_UNAUTHORIZED=0`); configure an application reverse proxy tunnel instead.
- Never let an offline test suite make network requests to Sentry; `Sentry.init` natively no-ops when `SENTRY_DSN` is empty.
- Always call `await Sentry.flush(3000)` or `await Sentry.close(3000)` before calling `process.exit()` in CLI scripts.
- In Mode 3 incident triage, run Seer AI (`sentry issue explain`, `sentry issue plan`) before falling back to manual frame digging.
- Never resolve, archive, or merge an issue without explicit user authorization or empirical proof.
- Never rely on `sentry issue archive` or legacy `sentry-cli issues mute` to stop quota exhaustion; use Inbound Filters or Client Key rate limits.
- Always verify the Sentry organization cluster (`de.sentry.io` vs `sentry.io`) when configuring CLI or investigating API 404s.
- Never let queue/cron/workflow handlers throw unhandled 500s in an infinite retry loop without SDK `ignoreErrors` or poison-pill suppression.
