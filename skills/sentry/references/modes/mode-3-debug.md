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
Rung 0  Triage        issue list   -> what is broken, ranked by frequency (cheap)
Rung 1  Diagnose      issue view   -> ONE issue + embedded latest event   (usually solves it)
Rung 2  Corroborate   explore/logs -> multi-event tag patterns, trace logs (only if Rung 1 is thin)
Rung 3  Deep Discover queries/repro-> agent discovers root cause locally   (independent reasoning)
```

## Rung 0: Triage (Find & Rank)

```bash
bash scripts/triage-issues.sh <org>/<project>
```
Or via modern CLI:
```bash
sentry issue list <org>/<project> -q 'is:unresolved' -s freq -t 24h -n 15 \
  --json --fields shortId,title,level,priority,seerFixabilityScore \
| jq -r '.data[] | "\(.shortId)\t[\(.priority)]\tseer=\(.seerFixabilityScore // 0)\t\(.title)"' \
| column -t -s $'\t'
```
Prioritize high frequency (`-s freq`) combined with recent activity (`lastSeen:-1h`).

## Rung 1: Diagnose (The Single Call That Solves 80% of Bugs)

Run `sentry issue view` and redirect to a temporary file:
```bash
sentry issue view <ID> --json > /tmp/sentry_issue.json
```

Extract the actionable facts with `jq`:

```bash
# 1. Headline & occurrences
jq -r '"\(.title)\nCulprit: \(.culprit)\nOccurrences: \(.count) | Last Seen: \(.lastSeen)"' /tmp/sentry_issue.json

# 2. In-App stack frames only (skips vendor node_modules noise)
jq -r '.event.entries[] | select(.type=="exception") | .data.values[].stacktrace.frames[]? | select(.inApp==true) | "  \(.filename):\(.lineNo) in \(.function)"' /tmp/sentry_issue.json

# 3. Context tags & preceding breadcrumbs
jq -r '.event.tags[]? | "\(.key)=\(.value)"' /tmp/sentry_issue.json | head -10
jq -r '.event.entries[] | select(.type=="breadcrumbs") | .data.values[-6:][] | "[\(.category // .type)] \(.message // (.data|tostring))"' /tmp/sentry_issue.json
```

## Rung 2: Corroborate (Trace & Log Correlation)

If the stack trace is inside a generic library or worker loop:
1. **Extract Trace ID:**
   ```bash
   TRACE_ID=$(jq -r '.trace.traceId // .event.contexts.trace.trace_id // empty' /tmp/sentry_issue.json)
   ```
2. **Query Correlated Logs:**
   ```bash
   sentry log list <org>/<project> -q "trace:${TRACE_ID}" --json | jq -r '.data[] | "[\(.timestamp)] [\(.severity)] \(.message)"'
   ```
3. **Explore Multi-Event Patterns:**
   ```bash
   sentry explore <org>/<project> -d errors -F release -F 'count()' -q 'is:unresolved' -t 7d
   ```

## Rung 3: Deep Discovery & Independent Solution Engineering

Do not wait passively for Sentry's Seer AI. The agent must:
1. Use the `file:line` frame and preceding breadcrumbs to open the local source code.
2. Reproduce the failure path locally using a unit or integration test.
3. Apply the targeted fix.
4. Run the local verification suite (`npm test`).

## Post-Fix Verification

After deployment, confirm the issue ceases firing:
```bash
# Check that no events occurred after deploy
sentry issue events <ID> --json | jq '.data[0:3][] | {eventID, dateCreated}'

# Verify no new unhandled regressions appeared
sentry issue list <org>/<project> -q 'is:unresolved firstSeen:-1h' -s new

# Mark resolved with confirmation
sentry issue resolve <ID>
```
See `references/verification/post-fix-verification.md`.
