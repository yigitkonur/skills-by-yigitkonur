---
name: use-sentry
description: "Use if setting up or auditing modern Sentry observability with OpenTelemetry, Continuous Profiling, Crons, Metrics, Replay, Spotlight, Swift/Apple, AI/LLM, MCP, or triaging incidents using Seer AI and CLI recipes."
disable-model-invocation: true
metadata:
  author: Yigit Konur
  version: 3.1.0
  category: observability
  tags: [sentry, monitoring, error-tracking, tracing, debugging, mcp, opentelemetry, profiling, seer-ai, swift, apple, ai, llm]
---

# Sentry

The complete enterprise Sentry observability lifecycle: autonomous stack research & zero-to-one setup, multi-pillar observability auditing (OpenTelemetry, Continuous Profiling, Crons, Metrics, Session Replay, Spotlight, Swift/Apple Ecosystem, AI/LLM, MCP Server Telemetry), and AI-accelerated production incident triage with Seer AI.

## The Enterprise Observability Pillars

Modern Sentry extends beyond basic error catching into a unified, full-stack observability platform:
1. **Error Monitoring & Exception Capture**: Automated unhandled exception capture, source maps with Debug IDs, contextual breadcrumbs, semantic issue grouping, and inbound noise filters.
2. **OpenTelemetry & Distributed Tracing**: Native OpenTelemetry engine (`@sentry/opentelemetry`), W3C `traceparent` and `baggage` propagation, and end-to-end distributed span waterfall trees (`Sentry.startSpan`).
3. **Continuous Profiling**: Low-overhead runtime CPU and memory profiling (`profilesSampleRate`, `profileSessionSampleRate`, `@sentry/profiling-node`) decoupled from individual transactions.
4. **Cron & Uptime Monitoring**: Heartbeat check-ins and missed execution alerts for background queues and scheduled tasks (`Sentry.withMonitor`, `Sentry.captureCheckIn`).
5. **Application Metrics**: Real-time telemetry counters, distributions, and gauges (`Sentry.metrics.count`, `Sentry.metrics.gauge`, `Sentry.metrics.distribution`). *(Note: Legacy beta `increment` and `set` were superseded).*
6. **Session Replay & Privacy Redaction**: Video-like DOM and mobile view reconstruction correlated with error traces, enforced with strict privacy shields (`maskAllText`, `blockAllMedia`) and network allowlists.
7. **Structured Logging & Analytics**: Log explorer queries, live streaming (`sentry log list -f`), trace-correlated log ingestion, and Discover SQL analytics.
8. **AI & LLM Observability**: Native integrations for OpenAI, Anthropic, and LangChain tracking token usage (prompt/completion), latency, cost, and PII-sanitized prompt pipelines.
9. **Model Context Protocol (MCP) Ecosystem**: Out-of-the-box MCP server auto-instrumentation (`McpServer` / `FastMCP`) with strict stdio isolation, and connecting AI coding assistants directly to Sentry's remote MCP server (`mcp.sentry.dev`).
10. **Swift & Apple Ecosystem**: Native macOS, iOS, visionOS instrumentation via `sentry-cocoa` SPM, App Hang tracking, MetricKit OS crash/diagnostic payloads, Watchdog OOM detection, and SwiftUI `.sentryTrace`.
11. **Spotlight Local Development Overlay**: Zero-overhead local developer sidecar (`@spotlightjs/spotlight`, `spotlight: true`) for instant browser trace visibility with zero SaaS quota consumption.

## Decision tree (The 3 Modes)

```
What is your objective?
├── Mode 1: Sentry is NOT in the project OR user says "set up / initialize Sentry"
│   ├── Step 1: Detect runtime, framework & architecture (Node, Next.js, Fastify, MCP, Python, Go, Swift, AI/LLM)
│   ├── Step 2: Research stack patterns via research-mcp (max 20 keywords): references/research/research-mcp-protocol.md
│   ├── Step 3: Choose keyword matrix: references/research/stack-keyword-matrices.md
│   ├── Step 4: Step-by-step setup guide: references/modes/mode-1-init.md
│   ├── Step 5: Stack blueprints: references/architectures/
│   │   ├── Swift / Apple: references/architectures/swift-apple-ecosystem.md
│   │   ├── MCP Server & Remote MCP: references/architectures/sentry-mcp-integration.md & references/architectures/mcp-server-sentry.md
│   │   ├── AI / LLM Observability: references/architectures/ai-llm-monitoring.md
│   │   ├── Next.js App Router: references/architectures/nextjs-app-router.md
│   │   ├── Python / FastAPI: references/architectures/python-fastapi.md
│   │   ├── Fastify REST API: references/architectures/fastify-rest-api.md
│   │   ├── Go Gin: references/architectures/go-gin.md
│   │   ├── Cloud Browsers / Playwright: references/architectures/cloud-browsers-playwright.md
│   │   └── Standalone CLI Scripts: references/architectures/cli-bundled-scripts.md
│   ├── Step 6: Application reverse proxy tunneling: references/network-tunneling/application-proxy-routes.md & references/network-tunneling/envelope-tunneling.md
│   └── Step 7: Local development with Spotlight: references/performance-replay/spotlight-local-dev.md
│
├── Mode 2: Sentry IS already installed OR user asks "audit / improve our Sentry"
│   ├── Step 1: Run feature audit scanner: bash scripts/audit-project.sh
│   ├── Step 2: Full enterprise audit & gap analysis guide: references/modes/mode-2-audit.md
│   ├── Pillar 1 (Error Tracking & Sourcemaps): references/error-tracking/ (capture, sourcemaps, fingerprints, inbound-filters, merges)
│   ├── Pillar 2 (Breadcrumbs & Rich Context): references/breadcrumbs-context/ (system, ui, tags, feedback, device)
│   ├── Pillar 3 (Logging & Analytics): references/logging-analytics/ (structured-logs, pin-to-top, log-explorer, discover)
│   ├── Pillar 4 (Tracing, Profiling, Crons, Replay): references/performance-replay/ (spans, asynclocalstorage, replay, crons, spotlight)
│   └── Pillar 5 (Privacy & Redaction): references/privacy-redaction/ (credentials, url-jwt)
│
└── Mode 3: "Something is broken in prod" / Triage alerts / Debug incident
    ├── Step 1: Run triage scanner: bash scripts/triage-issues.sh <org>/<project>
    ├── Step 2: 4-rung triage guide: references/modes/mode-3-debug.md
    ├── Step 3: Seer AI root cause analysis: sentry issue explain <ID>
    ├── Step 4: Seer AI automated fix planning: sentry issue plan <ID_OR_@latest>
    ├── Step 5: Modern CLI reference: references/cli-tooling/modern-sentry-cli.md (vs references/cli-tooling/legacy-sentry-cli.md)
    ├── Step 6: Trace & log correlation: references/logging-analytics/log-explorer-queries.md & references/logging-analytics/discover-query-builder.md
    └── Step 7: Safe mutations & post-fix verification: references/verification/post-fix-verification.md & references/verification/live-synthetic-verification.md
```

## Quick start

### Mode 1: Setup in New Project
```bash
# 1. Check credentials safely (~/.sentryclirc or SENTRY_AUTH_TOKEN)
bash scripts/detect-creds.sh

# 2. Test application reverse proxy route & ISP sinkhole defense
bash scripts/verify-tunnel.sh <PROJECT_ID_OR_ENDPOINT>

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
# 1. List top unresolved errors ranked by frequency
sentry issue list <org>/<project> -s freq -t 24h -n 10

# 2. One-call root cause analysis powered by Seer AI
sentry issue explain <ID>

# 3. Generate automated step-by-step code remediation plan
sentry issue plan <ID_OR_@latest>

# 4. Fallback: Deep JSON diagnostic inspection
sentry issue view <ID> --json > /tmp/iss.json
jq -r '.event.entries[] | select(.type=="exception") | .data.values[].stacktrace.frames[]? | select(.inApp) | "\(.filename):\(.lineNo) in \(.function)"' /tmp/iss.json
```

## The 4-Rung Debugging Funnel

```
Rung 0  Triage        sentry issue list    -> rank by frequency or recommended (token-efficient)
Rung 1  Diagnose      sentry issue explain -> Seer AI identifies root cause, culprit files & repro steps
Rung 2  Plan & Verify sentry issue plan    -> Seer AI generates code fix plan; corroborate with trace logs
Rung 3  Deep Discover explore / replay     -> trace waterfall inspection or raw rrweb replay reproduction
```

## Key patterns & Architecture

### 1. Application-Hosted Reverse Proxy Tunneling (Defeating DNS Sinkholes & Ad-Blockers)
In regions with captive ISP DNS sinkholes (e.g. TTNet `195.175.254.2` hijacking DNS and returning self-signed certificates) and client browsers running content blockers (uBlock Origin, Brave Shields), direct requests to `*.ingest.*sentry.io` or `sentry.io` are blocked or fail TLS validation (`DEPTH_ZERO_SELF_SIGNED_CERT`).
- **Antipattern**: Setting `tunnel: https://sentry.io/api/${projectId}/envelope/` directly in the client SDK still issues cross-origin requests to Sentry domains and will be intercepted.
- **Architectural Solution**: Client SDKs must point `tunnel` to an **application-hosted reverse proxy route** (e.g. `/api/monitoring/tunnel` or Next.js `tunnelRoute: '/monitoring-tunnel'`).
- The application backend parses the envelope header, validates the destination host and `projectId` against an allowlist (preventing open proxy relay exploits), and proxies raw envelope bytes server-to-server to Sentry's edge.

### 2. Defense-in-Depth Redaction
Hook sanitizers into `beforeSend`, `beforeSendSpan`, and `beforeBreadcrumb`. Scrub `authorization`, `x-api-key`, session cookies, strip sensitive query parameters (`?jwt=...`, `?token=...`) in WebSocket URLs and HTTP routes, and filter PII from LLM prompts.

### 3. Zero-Network Offline Test Gate
When `SENTRY_DSN` is empty or missing, `Sentry.init({ dsn: process.env.SENTRY_DSN })` natively operates in clean no-op mode: captures no events, sends zero network requests, and spends $0. Offline test suites run 100% network-free without custom mocking wrappers.

### 4. Standalone CLI & Serverless Guaranteed Bounded Flush
CLI scripts, worker jobs, and serverless functions terminate processes immediately on completion. Always wrap execution in try/catch and execute `await Sentry.flush(3000)` or `await Sentry.close(3000)` before `process.exit()` to ensure buffered async HTTP envelopes leave the network buffer.

### 5. CLI Disambiguation: Modern `sentry` vs Legacy `sentry-cli`
- **Modern `sentry` CLI** (`cli.sentry.dev` / `getsentry/toolkit`): Built for developers and AI coding agents. Uses singular noun commands (`sentry issue`, `sentry log`, `sentry trace`, `sentry explore`, `sentry replay`, `sentry api`). Features Seer AI integration (`sentry issue explain`, `sentry issue plan`), live log streaming (`-f`), and automatic OAuth token refresh via SQLite (`~/.config/sentry/cli.db`).
- **Legacy `sentry-cli`** (`getsentry/sentry-cli`): Rust-based build utility. Uses plural noun commands (`sentry-cli releases`, `sentry-cli sourcemaps`, `sentry-cli issues`). Intended strictly for CI/CD asset injection, sourcemap uploads, and release finalization.

### 6. Seer AI Root-Cause Analysis & Fix Planning
Sentry Seer is an integrated AI engine analyzing traces, breadcrumbs, correlated logs, and source code:
- `sentry issue explain <ID>`: Analyzes incident telemetry and connected repositories to pinpoint root causes, culprit files, line numbers, and reproduction steps in a single call.
- `sentry issue plan <ID_OR_@latest>`: Synthesizes a step-by-step code remediation plan, providing exact file modifications and diff context.
- **Semantic Grouping**: Uses high-dimensional embeddings to semantically group error variations, eliminating alert storms.

### 7. Model Context Protocol (MCP) Ecosystem
- **Connecting AI Agents to Sentry (`mcp.sentry.dev`)**: Point Cursor, Claude Code, or Antigravity to `https://mcp.sentry.dev/mcp/<org>/<project>` to query unresolved issues, inspect stack traces, fetch correlated logs, and read Seer AI fix plans autonomously.
- **Monitoring Custom MCP Servers**: Modern Sentry SDKs (Node.js 9.46.0+ / 11.1.0+, Python `sentry-sdk`) auto-instrument `@modelcontextprotocol/sdk` (`McpServer`). In `stdio` mode, `debug: false` is mandatory; never write non-JSON-RPC telemetry to `stdout`.

### 8. Apple Platform Native Telemetry (`sentry-cocoa`)
Native Swift / Apple apps benefit from deep OS-level diagnostics:
- **App Hang Tracking**: Detects main-thread UI blocks exceeding threshold (default: 2.0s).
- **MetricKit Integration**: Captures Apple OS crash diagnostics, CPU spikes, thermal throttling, and disk write anomalies.
- **Watchdog OOM Tracking**: Reports terminations caused by OS memory limits or slow startup.
- **SwiftUI View Tracing**: Instruments view lifecycles using `.sentryTrace("ViewName")`.

### 9. Quota Bleed & Runaway Loop Circuit Breakers (Archiving/Muting ≠ Quota Relief)
Muting (`sentry-cli issues mute`) or archiving (`sentry issue archive`) only silences notifications. Events are still ingested at Sentry's edge and consume monthly quota. To halt runaway quota bleed:
1. **Server-Side Inbound Filters (`filters:error_messages`)**: Discard events matching error patterns before quota billing via Sentry REST API (`PUT /api/0/projects/<org>/<project>/`) or UI settings.
2. **Client Key (DSN) Rate Limiting & Deactivation**: Throttle (`rateLimit: { window, count }`) or disable (`isActive: false`) in Project Settings -> Client Keys. Dropped events return HTTP 429/403 at the edge with 0 quota consumed.
3. **Queue & Retry Storm Defense**: Background queues (Upstash QStash, BullMQ, Celery) retrying unhandled 500 exceptions create exponential error multipliers. Add SDK `ignoreErrors`, validate payloads, and suppress poison pills before queue retries.
4. **Project Deletion**: When retiring an unused service, delete it via Sentry REST API (`DELETE /api/0/projects/<org>/<project>/`) to immediately invalidate its DSNs and eliminate zombie traffic.

### 10. Regional Multi-Tenant Host Awareness
Sentry SaaS operates regional clusters (e.g. EU cluster `https://de.sentry.io` vs US cluster `https://sentry.io`). When an organization is hosted on a regional cluster, API queries and CLI commands must target `https://de.sentry.io/` (`--url https://de.sentry.io/` or `url = https://de.sentry.io/` in `~/.sentryclirc`). Pointing to `https://sentry.io/` will return `404 Not Found` for legitimate issues and projects.

## Common pitfalls

| Pitfall | Root Cause | Fix |
|---|---|---|
| `DEPTH_ZERO_SELF_SIGNED_CERT` | ISP DNS hijacking or content blockers on `*.ingest.*sentry.io` | Route client envelopes through application reverse proxy (`/api/monitoring/tunnel` or Next.js `tunnelRoute`) |
| CLI / Serverless drops error reports | Process exits before async HTTP envelope leaves transport buffer | Execute `await Sentry.flush(3000)` or `await Sentry.close(3000)` before `process.exit(1)` |
| Tests fail when offline | SDK attempts live HTTP calls in unit tests | Initialize with `Sentry.init({ dsn: process.env.SENTRY_DSN })` which natively no-ops when DSN is unset |
| Quota drained despite issue mute | `sentry issue archive` or mute silences alerts but still ingests events | Use Inbound Filters (`filters:error_messages`) or Client Key rate limits |
| 404 on API/CLI issue lookup | Organization is on EU cluster (`de.sentry.io`), CLI defaults to US | Set `url = https://de.sentry.io/` in `~/.sentryclirc` or pass `--url` |
| Queue retry flood exhausts quota | Queue retries failed jobs in a loop; SDK reports on every attempt | Add SDK `ignoreErrors`, guard handlers against `undefined`, rate-limit DSN |
| Seer AI plan fails with repo error | GitHub/GitLab integration or Code Mappings missing | Upload mappings via `sentry code-mappings upload` and link repository |
| MCP client crashes on start | Sentry debug or console logs written to stdout in stdio mode | Set `debug: false`; isolate all logging to stderr in stdio mode |
| Spotlight active in production | `spotlight: true` sends requests to localhost sidecar in prod | Guard with `spotlight: process.env.NODE_ENV === 'development'` |
| Token leak in logs | URLs logged with raw `?jwt=...` query parameters | Scrub query parameters in `beforeSend` / `beforeSendSpan` |
| Duplicate error reports in Node.js | Manually registering `process.on('uncaughtException')` alongside SDK | Sentry Node SDK registers them automatically; configure via integrations |
| App Hangs going untracked in Swift | Synchronous blocking work executed on main thread | Enable `options.enableAppHangTracking = true` and offload heavy tasks to Swift tasks |

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

### "I need to build or monitor an MCP server, or connect an AI agent"
- `references/architectures/sentry-mcp-integration.md`
- `references/architectures/mcp-server-sentry.md`
- `references/architectures/ai-llm-monitoring.md`

### "I need to monitor a Swift / Apple application"
- `references/architectures/swift-apple-ecosystem.md`
- `references/performance-replay/session-replay.md`
- `references/error-tracking/sourcemaps-pipeline.md`

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
| `references/research/stack-keyword-matrices.md` | Ready-to-use search keyword matrices for Swift, MCP, AI, Next.js, etc. |
| `references/architectures/swift-apple-ecosystem.md` | Swift & Apple ecosystem (macOS, iOS, visionOS), App Hangs, MetricKit, SwiftUI tracing. |
| `references/architectures/sentry-mcp-integration.md` | Hosted Sentry MCP (mcp.sentry.dev) for AI agents and MCP server auto-instrumentation. |
| `references/architectures/ai-llm-monitoring.md` | OpenAI, Anthropic, LangChain token tracking, latency, and prompt PII redaction. |
| `references/architectures/mcp-server-sentry.md` | MCP Server architecture: stdio isolation, tool breadcrumbs, token redaction. |
| `references/architectures/cloud-browsers-playwright.md` | Playwright/Kernel browser tracing and strict cdpWsUrl JWT scrubbing. |
| `references/architectures/fastify-rest-api.md` | Fastify 4/5 request context plugin and 4xx vs 5xx separation. |
| `references/architectures/nextjs-app-router.md` | Next.js 14/15 client, server, edge configs and tunnel rewrites. |
| `references/architectures/cli-bundled-scripts.md` | Standalone CLIs, unhandled exception traps, and guaranteed flush. |
| `references/architectures/python-fastapi.md` | Python FastAPI and Flask instrumentation with custom transports. |
| `references/architectures/go-gin.md` | Go Gin middleware, panic recovery, and trace propagation. |
| `references/error-tracking/exception-capture.md` | Capturing unhandled rejections, uncaught exceptions, and edge crashes. |
| `references/error-tracking/sourcemaps-pipeline.md` | Debug IDs, bundler plugins (Vite/Webpack), and sourcemap uploads. |
| `references/error-tracking/fingerprinting-grouping.md` | Configuring custom fingerprinting rules and Seer AI semantic grouping. |
| `references/error-tracking/inbound-filters.md` | Dropping web crawlers, browser extensions, and quota-draining noise. |
| `references/error-tracking/merges-and-splits.md` | Merging duplicate clusters or splitting mistakenly grouped errors. |
| `references/breadcrumbs-context/system-breadcrumbs.md` | Recording HTTP, database, cache, and RPC system breadcrumbs. |
| `references/breadcrumbs-context/ui-breadcrumbs.md` | Capturing user clicks, navigations, and DOM interactions. |
| `references/breadcrumbs-context/custom-tags-context.md` | Attaching searchable key-value tags (tenant, user tier, driver). |
| `references/breadcrumbs-context/user-feedback-api.md` | In-app feedback widget (`feedbackIntegration`) and programmatic submission. |
| `references/breadcrumbs-context/device-runtime-context.md` | Capturing OS, runtime version, memory stats, and container metadata. |
| `references/logging-analytics/structured-logs.md` | Ingesting, indexing, and querying application structured logs. |
| `references/logging-analytics/pin-to-top-logs.md` | Highlighting critical log context and fatal assertion tags. |
| `references/logging-analytics/log-explorer-queries.md` | Sentry Log Explorer query syntax and live tail streaming. |
| `references/logging-analytics/discover-query-builder.md` | Running SQL-like Discover queries for latency and error trends. |
| `references/performance-replay/distributed-tracing-spans.md` | OpenTelemetry native spans, trace headers, and latency percentiles. |
| `references/performance-replay/spotlight-local-dev.md` | Spotlight local developer sidecar (@spotlightjs/spotlight) setup and overlay. |
| `references/performance-replay/asynclocalstorage-context.md` | Ambient request context propagation across async call trees. |
| `references/performance-replay/session-replay.md` | Video-like DOM and mobile reconstruction correlated with errors & privacy masks. |
| `references/performance-replay/cron-monitors.md` | Background job heartbeats, check-ins, and missed execution alerts. |
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
- Never log raw URLs containing JWT tokens, API keys, or credentials (`?jwt=...`, `?token=...`).
- Never disable TLS verification (`NODE_TLS_REJECT_UNAUTHORIZED=0`); configure an application reverse proxy tunnel instead.
- Never let an offline test suite make network requests to Sentry; `Sentry.init` natively no-ops when `SENTRY_DSN` is empty.
- Always call `await Sentry.flush(3000)` or `await Sentry.close(3000)` before calling `process.exit()` in CLI scripts or serverless tasks.
- In Mode 3 incident triage, run Seer AI (`sentry issue explain <ID>`, `sentry issue plan <ID>`) before falling back to manual frame digging.
- Never resolve, archive, or merge an issue without explicit user authorization or empirical proof.
- Never rely on `sentry issue archive` or legacy `sentry-cli issues mute` to stop quota exhaustion; use Inbound Filters or Client Key rate limits.
- Always verify the Sentry organization cluster (`de.sentry.io` vs `sentry.io`) when configuring CLI or investigating API 404s.
- Never let queue/cron/workflow handlers throw unhandled 500s in an infinite retry loop without SDK `ignoreErrors` or poison-pill suppression.
- In modern Sentry SDKs, use `Sentry.metrics.count(...)`, `Sentry.metrics.gauge(...)`, and `Sentry.metrics.distribution(...)` for application metrics.
