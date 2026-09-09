# Post-Fix Verification Protocol

How to prove empirically that a deployed code fix resolved the production error and that no new regressions were introduced.

## The Verification Loop

Never declare a bug fixed based solely on code changes. Verify against production telemetry:

1. **Deploy the fix** or trigger the test workload in staging.
2. **Inspect `lastSeen` & Event Count:** Prove that the targeted issue has stopped advancing.
3. **Check for Regression Spikes:** Verify no new `is:unresolved` errors appeared with `firstSeen:-1h`.
4. **Mark Resolved in Sentry:** With user authorization, mark the issue resolved.

## Verification Checklist & Commands

### 1. Check if the Target Issue Reappeared
Query recent events for the issue to ensure no events occurred after your deployment timestamp:

```bash
sentry issue events <ID> --json | jq '.data[0:3][] | {eventID, dateCreated}'
```

If `dateCreated` is older than your deployment time, no new events have fired.

### 2. Check for New Unhandled Regressions
```bash
sentry issue list <org>/<project> -q 'is:unresolved firstSeen:-1h' -s new --json \
  | jq -r '.data[] | "\(.shortId) [\(.level)] \(.title)"'
```

### 3. Record Resolution with Release Tag
```bash
sentry issue resolve <ID> --in "<release-tag>"
```
