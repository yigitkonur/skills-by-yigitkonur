# Choosing What to Capture (Deep, Not Basic)

The failure mode this skill exists to prevent: shipping `SentrySDK.capture(error:)` and
calling it "monitoring." Real observability picks the **right signal for each question** and
ties every event to the context the app already knows. Adapted from Sentry's own
"choosing a signal" guidance, scoped to a macOS/Swift app.

## The signal picker

Signals are **not interchangeable**. Pick by the question you're answering.

| You want to know… | Signal | Notes |
|---|---|---|
| Something broke — what/where/why? | **Error** | Exception/crash → grouped issue + stack trace. Baseline, always on. |
| Why slow? What did it call? | **Span / trace** | Timing + structure across calls. Powers perf-issue detection. |
| What happened leading up to it? | **Breadcrumb** (in-event trail) or **Log** (searchable, standalone) | Narrative context, not timing. |
| How many / what trend? | **Metric** | Aggregate counter/gauge/distribution for a KPI you alert on. |
| Which function burns CPU? | **Profile** | Samples inside traced transactions — tracing must be on. |
| What does the user think broke? | **User feedback** | macOS: **API only**, no widget — build your own form. |

### Distinctions that keep quota clean

- **Error vs log:** an exception your code can't handle is an *error* (groups into an issue,
  gets a stack). A noteworthy non-failure is a *log*. Don't capture routine events as errors
  (pollutes the issue stream); don't log-spam things that should be errors.
- **Log vs span:** a log says *what happened*; a span says *how long / what it called*. If
  you're logging start/end timestamps to measure duration, you want a span.
- **Metric vs derived data:** don't emit a custom metric for something Sentry already derives
  (issue counts, latency percentiles, crash-free rate). Reserve metrics for business/health
  KPIs Sentry can't see.
- **Profiling rides on tracing** — not standalone.

## What to instrument where (macOS app)

- **Errors:** everywhere, always. Get one real error landing first — that's the job until it works.
- **Tracing:** request/operation **boundaries** — outbound HTTP, file I/O, Core Data. On
  macOS there's no auto app-start/UIViewController transaction, so wrap meaningful business
  operations in **manual transactions** (`tracing-releases-dsym.md`).
- **Breadcrumbs:** a few high-signal lifecycle/operation events — not a firehose. Fixed
  strings + numbers only (`advanced-instrumentation.md`).
- **Logs:** structured, high-signal, opt-in. Never interpolate user content.
- **Metrics:** a small deliberate set mapping to a real alert.
- **Feedback:** only if you'll build the AppKit form; ties a user report to an event.

## Recommended baseline (when the user says "set it up properly")

**Errors + uncaught NSException + tracing at a modest rate + releases + dSYM upload +
privacy scrubbing + opt-in**, then add breadcrumbs/logs/metrics/profiling as the real use
case warrants. Present this as a concrete proposal, not an open question.

## Deciding for *this* app

Map the Phase 1 fact sheet to signals:

| If the app… | Add |
|---|---|
| Makes network calls to a backend/proxy | Network tracing + `tracePropagationTargets` (+ backend correlation if it's yours) |
| Does heavy local work (media, parsing, DB) | Manual transactions around those operations; consider profiling |
| Already logs via `os.Logger` | Selective structured-log or breadcrumb mirroring at failure sites (no auto-bridge exists) |
| Has meaningful lifecycle states | Breadcrumbs at those transitions |
| Ships to users (not just you) | Release health / crash-free sessions; user-feedback API if you want reports |

Reject "just errors" (too shallow) and "turn everything on" (quota + noise + PII surface).
