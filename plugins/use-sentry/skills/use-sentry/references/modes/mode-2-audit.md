# Mode 2 — Deep Feature Audit & Enterprise Capability Expansion

How to evaluate an existing Sentry setup across the Enterprise Observability Pillars, identify unutilized capabilities, and explain their concrete engineering impact.

## When to Enter Mode 2

Trigger Mode 2 when:
- Sentry is already installed in the repository.
- The user asks: "Audit our Sentry setup", "How can we improve error tracking?", "Are we using all of Sentry's features?".
- You want to verify if advanced capabilities (breadcrumbs, structured logs, sourcemaps, continuous profiling, metrics, AI/MCP monitoring) are adopted.

## Step 1: Automated Audit across Enterprise Pillars

Run the project audit scanner:
```bash
bash scripts/audit-project.sh
```

Or manually check the codebase against the enterprise features:

### Pillar 1: Core Error Tracking & Resolution
- [ ] **Exception Capture:** Are unhandled promise rejections, crashes, and edge workers (Cloudflare/Node) monitored? (See `references/error-tracking/exception-capture.md` & `references/architectures/cloudflare-workers.md`)
- [ ] **Sourcemaps Pipeline:** Are sourcemaps generated with Debug IDs and uploaded during CI (or via `upload_source_maps` in Wrangler)? (See `references/error-tracking/sourcemaps-pipeline.md`)
- [ ] **Custom Fingerprinting:** Are custom grouping rules configured to merge redundant alerts? (See `references/error-tracking/fingerprinting-grouping.md`)
- [ ] **Inbound Filters:** Are web crawlers, browser extensions, and noise errors dropped before quota billing? (See `references/error-tracking/inbound-filters.md`)
- [ ] **Issue Merges/Splits:** Are duplicate clusters merged? (See `references/error-tracking/merges-and-splits.md`)

### Pillar 2: Contextual Breadcrumbs & Environment Data
- [ ] **System Breadcrumbs:** Are database queries, HTTP outbound calls, and RPC events logged? (See `references/breadcrumbs-context/system-breadcrumbs.md`)
- [ ] **UI Breadcrumbs:** Are user navigations, clicks, and state transitions recorded? (See `references/breadcrumbs-context/ui-breadcrumbs.md`)
- [ ] **Custom Tags:** Are business tags (`tenant_id`, `plan`, `region`) attached to scopes? (See `references/breadcrumbs-context/custom-tags-context.md`)
- [ ] **User Feedback API:** Can users submit crash reports with screenshots? (See `references/breadcrumbs-context/user-feedback-api.md`)
- [ ] **Device Context:** Are runtime version, OS architecture, and memory stats attached? (See `references/breadcrumbs-context/device-runtime-context.md`)

### Pillar 3: Log Management & Analytics
- [ ] **Structured Logs:** Are application logs indexed into Sentry via `Sentry.logger` or `pinoIntegration()` with `traceId` correlation? (See `references/logging-analytics/structured-logs.md`)
- [ ] **Pin-to-Top Logs:** Are fatal log lines pinned to the issue header? (See `references/logging-analytics/pin-to-top-logs.md`)
- [ ] **Log Explorer Queries:** Can you query logs by severity and trace? (See `references/logging-analytics/log-explorer-queries.md`)
- [ ] **Discover Query Builder:** Are SQL-like queries used for trend analysis? (See `references/logging-analytics/discover-query-builder.md`)

### Pillar 4: Distributed Tracing & OpenTelemetry
- [ ] **Distributed Tracing & Spans:** Are latency-critical operations wrapped with `startSpan` and propagated over HTTP or Cloudflare RPC? (See `references/performance-replay/distributed-tracing-spans.md` & `references/architectures/cloudflare-workers.md`)
- [ ] **AsyncLocalStorage Context:** Is context bound across async execution flows (`nodejs_compat` enabled on Workers)? (See `references/performance-replay/asynclocalstorage-context.md`)
- [ ] **Spotlight Local Development:** Is the local sidecar enabled for zero-network local tracing? (See `references/performance-replay/spotlight-local-dev.md`)

### Pillar 5: Continuous Profiling & Runtime Diagnostics
- [ ] **Continuous Profiling:** Is service-lifetime CPU profiling enabled (`profileSessionSampleRate` or manual start/stop)?
- [ ] **Transaction Profiling (Legacy):** Is trace-coupled profiling configured via `profilesSampleRate`?
- [ ] **Native Diagnostics (Mobile/Apple/Android):** Are Apple MetricKit, Watchdog OOM, Android ANRs, and TTID/TTFD tracked? (See `references/architectures/swift-apple-ecosystem.md` & `references/architectures/expo-mobile.md`)

### Pillar 6: Cron & Uptime Monitors
- [ ] **Cron Monitors:** Are scheduled cron jobs monitored via heartbeats (`withMonitor`, `captureCheckIn`, or Cloudflare Worker `scheduled` handlers)? (See `references/performance-replay/cron-monitors.md`)

### Pillar 7: Application Metrics
- [ ] **Trace-Connected Metrics:** Are application counters, distributions, and span measurements tracked (`span.setMeasurement`, OTel metrics)?

### Pillar 8: Session Replay & Privacy Redaction
- [ ] **Session Replay:** Is DOM or mobile view recording enabled with rage/dead click detection and strict privacy shields (`mobileReplayIntegration`, `maskAllText`, `maskAllImages`)? (See `references/performance-replay/session-replay.md` & `references/architectures/expo-mobile.md`)
- [ ] **Privacy Redaction:** Are passwords, auth headers, and query JWTs scrubbed? (See `references/privacy-redaction/credential-redaction-rules.md` & `references/privacy-redaction/url-jwt-sanitization.md`)

### Pillar 9: AI, LLM & Model Context Protocol (MCP) Observability
- [ ] **AI / LLM Monitoring:** Are token counts, prompts, completions, and model latencies tracked? (See `references/architectures/ai-llm-monitoring.md`)
- [ ] **MCP Server Monitoring:** Are MCP tools auto-instrumented with stdio isolation (`mcpServerIntegration`)? (See `references/architectures/mcp-server-sentry.md`)
- [ ] **AI Assistant Integration:** Are AI agents connected via Claude Code plugin (`getsentry/sentry-mcp`), `sentry mcp`, or remote `mcp.sentry.dev`? (See `references/architectures/sentry-mcp-integration.md`)

### Pillar 10: Edge & Mobile Specialized Architecture
- [ ] **Cloudflare Workers:** Are build-time AST instrumentation (`sentryCloudflareVitePlugin`), `nodejs_compat`, Durable Objects, and Workflows instrumented? (See `references/architectures/cloudflare-workers.md`)
- [ ] **Expo & React Native:** Are Hermes Debug IDs (`getSentryExpoConfig`), Expo Router navigation tracing (`expoRouterIntegration`), EAS Build secrets, and OTA update sourcemaps configured? (See `references/architectures/expo-mobile.md`)

---

## Step 2: Formulate the Project-Level Value Assessment

For every unutilized capability, explain the concrete engineering impact:

| Missing Feature | What the Project Misses Today | Project-Level Business & Engineering Benefit |
|---|---|---|
| **Sourcemap Uploads** | Production stack traces show minified code (`app.min.js:1:14231`). | Engineers spend hours mapping obfuscated lines. Debug IDs pinpoint the exact source file and line. |
| **Custom Fingerprinting** | Database connection retries create 50 separate issue alerts. | Alert fatigue causes real bugs to be ignored. Custom fingerprinting groups them into 1 canonical issue. |
| **System Breadcrumbs** | An API error shows "500 Internal Error" with zero clue about what led to it. | Breadcrumbs reveal the sequence: User fetched profile -> Cache missed -> External API timed out -> DB threw. |
| **Envelope Tunneling** | Errors in restricted networks or browsers fail due to ad-blockers / DNS sinkholes. | Critical production crashes vanish silently. Tunneling guarantees 100% telemetry delivery. |
| **Structured Logs + Tracing** | Logs live in one tool and errors in another with no correlation. | Trace correlation (`trace:<id>`) lets you pivot from an exception to the exact log lines emitted in the same request. |
| **Application Metrics** | No real-time counters or latency distributions connected to traces. | Correlate metric spikes (e.g. checkout volume or API latency) directly to underlying trace waterfalls. |
| **Continuous Profiling** | Slow functions are undetectable without guessing. | Flamegraphs pinpoint exact line-level CPU execution bottlenecks across production requests. |
| **Sentry MCP Server** | AI agents cannot directly query issues or Seer AI plans. | Connect Cursor/Antigravity to `mcp.sentry.dev` for autonomous incident investigation and fix application. |

---

## Step 3: Progressive Upgrade Plan

Implement the highest-impact gaps sequentially:
1. Fix network drops (Envelope Tunneling) & credential leaks (Redaction).
2. Wire AsyncLocalStorage request context and custom tags.
3. Hook system and domain breadcrumbs into major operations.
4. Set up sourcemap uploads with Debug IDs in the CI/CD pipeline.
5. Enable Profiling, Metrics, and Cron monitors for background queues.
