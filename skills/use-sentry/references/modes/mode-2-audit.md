# Mode 2 — Deep Feature Audit & Enterprise Capability Expansion

How to evaluate an existing Sentry setup across all 4 Feature Pillars, identify unutilized capabilities, and explain their concrete project-level benefits.

## When to Enter Mode 2

Trigger Mode 2 when:
- Sentry is already installed in the repository.
- The user asks: "Audit our Sentry setup", "How can we improve error tracking?", "Are we using all of Sentry's features?".
- You want to verify if advanced capabilities (breadcrumbs, structured logs, sourcemaps, custom fingerprinting) are adopted.

## Step 1: Automated Audit across the 4 Pillars

Run the project audit script:
```bash
bash scripts/audit-project.sh
```

Or manually check the codebase against the **18 Enterprise Features**:

### Pillar 1: Core Error Tracking & Resolution
- [ ] **Exception Capture:** Are unhandled promise rejections and process crashes caught? (See `references/error-tracking/exception-capture.md`)
- [ ] **Sourcemaps Pipeline:** Are sourcemaps generated, uploaded during CI, and linked to Git commits? (See `references/error-tracking/sourcemaps-pipeline.md`)
- [ ] **Custom Fingerprinting:** Are custom grouping rules configured to merge identical errors? (See `references/error-tracking/fingerprinting-grouping.md`)
- [ ] **Inbound Filters:** Are web crawlers, browser extensions, and spam errors dropped? (See `references/error-tracking/inbound-filters.md`)
- [ ] **Issue Merges/Splits:** Are duplicate clusters merged? (See `references/error-tracking/merges-and-splits.md`)

### Pillar 2: Contextual Breadcrumbs & Environment Data
- [ ] **System Breadcrumbs:** Are database queries, HTTP outbound calls, and RPC events logged? (See `references/breadcrumbs-context/system-breadcrumbs.md`)
- [ ] **UI Breadcrumbs:** Are user navigation, clicks, and state transitions recorded? (See `references/breadcrumbs-context/ui-breadcrumbs.md`)
- [ ] **Custom Tags:** Are business tags (`tenant_id`, `user_type`, `region`, `plan`) set on scopes? (See `references/breadcrumbs-context/custom-tags-context.md`)
- [ ] **User Feedback API:** Can users submit a crash report description? (See `references/breadcrumbs-context/user-feedback-api.md`)
- [ ] **Device Context:** Are runtime version, OS architecture, and memory stats attached? (See `references/breadcrumbs-context/device-runtime-context.md`)

### Pillar 3: Log Management & Analytics
- [ ] **Structured Logs:** Are application logs indexed into Sentry with `traceId`? (See `references/logging-analytics/structured-logs.md`)
- [ ] **Pin-to-Top Logs:** Are fatal log lines pinned to the issue header? (See `references/logging-analytics/pin-to-top-logs.md`)
- [ ] **Log Explorer Queries:** Can you query logs by severity and trace? (See `references/logging-analytics/log-explorer-queries.md`)
- [ ] **Discover Query Builder:** Are SQL-like queries used for trend analysis? (See `references/logging-analytics/discover-query-builder.md`)

### Pillar 4: Performance, Tracing & Replay
- [ ] **Distributed Tracing & Spans:** Are latency-critical operations wrapped with `startSpan`? (See `references/performance-replay/distributed-tracing-spans.md`)
- [ ] **AsyncLocalStorage Context:** Is context bound to async execution flows? (See `references/performance-replay/asynclocalstorage-context.md`)
- [ ] **Session Replay:** Is DOM recording enabled with rage/dead click detection? (See `references/performance-replay/session-replay.md`)
- [ ] **Cron Monitors:** Are scheduled cron jobs monitored via heartbeats? (See `references/performance-replay/cron-monitors.md`)

## Step 2: Formulate the Project-Level Value Assessment

For every unutilized capability, explain the concrete engineering and business impact:

| Missing Feature | What the Project Misses Today | Project-Level Business & Engineering Benefit |
|---|---|---|
| **Sourcemap Uploads** | Production stack traces show minified code (`app.min.js:1:14231`). | Engineers spend hours mapping obfuscated lines. Uploading sourcemaps instantly pinpoints the exact TypeScript file and line. |
| **Custom Fingerprinting** | Database connection retries create 50 separate issue alerts. | Alert fatigue causes real bugs to be ignored. Custom fingerprinting groups them into 1 canonical issue. |
| **System Breadcrumbs** | An API error shows "500 Internal Error" with zero clue about what led to it. | Breadcrumbs reveal the sequence: User fetched profile -> Cache missed -> External API timed out -> DB query threw. |
| **Envelope Tunneling** | Errors in Turkey or captive networks fail with `DEPTH_ZERO_SELF_SIGNED_CERT`. | Critical production crashes vanish silently. Tunneling guarantees 100% telemetry delivery across restricted networks. |
| **Structured Logs + Tracing** | Logs live in one tool and errors in another with no correlation. | Trace correlation (`trace:<id>`) lets you pivot from an exception to the exact log lines emitted in the same request. |

## Step 3: Stack-Specific Telemetry Research

If the project uses a specialized architecture (such as an MCP server or cloud browser), use `research-mcp` (up to 20 keywords) to research tailored telemetry patterns:
- E.g. for an MCP server: `sentry mcp server tool call breadcrumbs`, `sentry stdio transport error boundary`.
- Review the matched blueprint in `references/architectures/`.

## Step 4: Progressive Upgrade

Implement the highest-impact gaps sequentially:
1. Fix network drops (Envelope Tunneling) & credential leaks (Redaction).
2. Wire AsyncLocalStorage request context and custom tags.
3. Hook system and domain breadcrumbs into major operations.
4. Set up sourcemap uploads in the CI/CD pipeline.
