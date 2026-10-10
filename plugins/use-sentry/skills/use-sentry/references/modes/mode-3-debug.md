# Mode 3 — Empirical Diagnosis & Agent-Driven Root Cause Resolution

How to triage production incidents, extract stack traces token-efficiently, correlate logs, and discover root causes independently.

## When to Enter Mode 3

Trigger Mode 3 when:
- The user reports: "There are 500 errors in production", "Why is the API crashing?", "Investigate recent Sentry alerts".
- You have an issue ID (e.g. `PROJECT-1234`), a Sentry URL, or an alert to resolve.
- An endpoint is experiencing latency regressions or timeouts.

## The 4-Rung Token-Efficient Funnel

Stop at the shallowest rung that answers the question. Never dump raw, unparsed JSON into your context.

```
Rung 0  Triage        sentry issue list    -> rank by frequency and priority (token-efficient)
Rung 1  Diagnose      sentry issue explain -> Seer AI identifies root cause, culprit files & repro steps
Rung 2  Plan & Verify sentry issue plan    -> Seer AI generates code fix plan; corroborate with trace logs
Rung 3  Deep Discover explore / replay     -> trace waterfall inspection or raw rrweb replay reproduction
```

## Rung 0: Triage (Find & Rank)

```bash
bash scripts/triage-issues.sh <org>/<project>
```
Or via modern CLI (`cli.sentry.dev`):
```bash
# Valid sort options: recommended, freq, new, date, user
sentry issue list <org>/<project> -q 'is:unresolved' -s freq -t 24h -n 15
```
Prioritize high frequency (`-s freq`) combined with recent activity (`lastSeen:-1h`).

## Rung 1: Diagnose with Seer AI (The Single Call That Solves 80% of Bugs)

Run automated root-cause analysis with the issue ID:
```bash
sentry issue explain <ISSUE_ID>
```
Seer AI inspects git history, error frames, and preceding breadcrumbs to report the root cause and culprit files.

Fallback: Deep JSON diagnostic inspection if Seer is unavailable or offline:
```bash
sentry issue view <ISSUE_ID> --json > /tmp/sentry_issue.json
jq -r '"\(.title)\nCulprit: \(.culprit)\nOccurrences: \(.count) | Last Seen: \(.lastSeen)"' /tmp/sentry_issue.json
jq -r '.event.entries[] | select(.type=="exception") | .data.values[].stacktrace.frames[]? | select(.inApp==true) | "  \(.filename):\(.lineNo) in \(.function)"' /tmp/sentry_issue.json
```

## Rung 2: Plan & Corroborate (Fix Planning & Trace Correlation)

Generate automated code remediation:
```bash
# Accepts specific issue ID, @latest, or @most_frequent
sentry issue plan <ISSUE_ID_OR_@latest>
```
If the stack trace is inside a generic library or worker loop, corroborate with correlated logs:
```bash
TRACE_ID=$(jq -r '.trace.traceId // .event.contexts.trace.trace_id // empty' /tmp/sentry_issue.json)
sentry log list <org>/<project> -q "trace:${TRACE_ID}" --json | jq -r '.data[] | "[\(.timestamp)] [\(.severity)] \(.message)"'
```

## Rung 3: Deep Discovery & Independent Solution Engineering

Do not wait passively for Sentry's Seer AI. The agent must:
1. Use the `file:line` frame and preceding breadcrumbs to open the local source code.
2. Reproduce the failure path locally using a unit or integration test.
3. Apply the targeted fix.
4. Run the local verification suite (`npm test`, `pytest`, `swift test`).

## Post-Fix Verification

After deployment, confirm the issue ceases firing:
```bash
# Check that no events occurred after deploy
sentry issue events <ISSUE_ID> --json | jq '.data[0:3][] | {eventID, dateCreated}'

# Verify no new unhandled regressions appeared
sentry issue list <org>/<project> -q 'is:unresolved firstSeen:-1h' -s new

# Mark resolved with confirmation
sentry issue resolve <ISSUE_ID>
```
See `references/verification/post-fix-verification.md`.
