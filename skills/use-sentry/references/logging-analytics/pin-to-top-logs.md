# Pin-to-Top Critical Logs in Issue Layouts

How to highlight mission-critical log lines directly at the top of Sentry issue detail layouts for instant contextual triage.

## The Concept

When triaging an issue, an agent or engineer is often forced to dig through dozens of standard info-level breadcrumbs to find the one decisive line (e.g. `Payment gateway response code: 4002 - Expired Card`).

By pinning critical log lines or fatal assertion messages, the key information is immediately visible at the top of the issue header.

## How to Pin Logs in Sentry

1. **Tagging Critical Logs with High Severity:**
   In Sentry Structured Logs, logs with `level: fatal` or with the tag `pinned: true` can be surfaced in custom issue layout rules:
   ```typescript
   Sentry.logger.error('CRITICAL ASSERTION FAILED: Database transaction rolled back due to dead-lock', {
     pinned: 'true',
     severity: 'critical',
     subsystem: 'payment_engine',
   });
   ```

2. **Using Top-Level Sentry Annotations:**
   Attach the crucial message directly to the event's `message` or top-level `culprit`:
   ```typescript
   Sentry.withScope((scope) => {
     scope.setAnnotation('Critical Note', 'Lease terminated due to provider watchdog timeout');
     Sentry.captureException(err);
   });
   ```

3. **Configuring Issue Layout Rules (Sentry UI):**
   Under `Organization Settings -> Issue Details Layout`, enable:
   - **Show Pinned Logs:** Surfaces any log matching `pinned:true` or `severity:critical` above the stack trace.
   - **Show User Feedback:** Displays user-submitted crash comments alongside pinned logs.
