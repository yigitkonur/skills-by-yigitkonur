# Highlighting Critical Diagnostics in Issue Layouts

How to highlight mission-critical log lines and diagnostic context directly at the top of Sentry issue detail layouts for instant contextual triage.

## The Concept

When triaging an issue, an agent or engineer is often forced to dig through dozens of standard info-level breadcrumbs to find the one decisive line (e.g. `Payment gateway response code: 4002 - Expired Card`).

By structuring high-priority diagnostic context into custom Sentry contexts and tags, the key information is immediately rendered in a prominent card at the top of the issue header.

## How to Surface Critical Diagnostics in Sentry

1. **Custom Context Blocks (Surfaced in Top-Level UI Cards):**
   Attach decisive diagnostic state via `scope.setContext()` to render dedicated tables at the top of the Sentry issue page:
   ```typescript
   import * as Sentry from '@sentry/node';

   Sentry.withScope((scope) => {
     scope.setLevel('fatal');
     scope.setTag('critical_failure', 'true');
     scope.setContext('fatal_assertion', {
       message: 'Database transaction rolled back due to dead-lock',
       subsystem: 'payment_engine',
       timestamp: new Date().toISOString(),
     });
     Sentry.captureException(err);
   });
   ```

2. **Top-Level Extra and Tags:**
   Attach key triage markers as searchable tags and extra data:
   ```typescript
   Sentry.withScope((scope) => {
     scope.setTag('triage_priority', 'critical');
     scope.setExtra('watchdog_note', 'Lease terminated due to provider watchdog timeout');
     Sentry.captureException(err);
   });
   ```

3. **Configuring Issue Layout Rules (Sentry UI):**
   Under `Organization Settings -> Issue Details Layout`:
   - Prioritize custom context cards (`fatal_assertion`) above breadcrumbs and stack traces.
   - Configure Tag Highlights to pin key tags (`critical_failure`, `subsystem`, `triage_priority`) to the top summary bar.
   - Show User Feedback cards alongside critical diagnostics.
