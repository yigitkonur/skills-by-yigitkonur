# Session Replay: Correlating Errors with Video-Like DOM Recordings

How to configure Sentry Session Replay to capture user actions, DOM mutations, network calls, and rage clicks preceding client errors.

## What is Session Replay?

Session Replay provides a visual, video-like reproduction of user interactions before, during, and after an error occurred:
- Exact cursor movement, scrolling, and clicks.
- Real-time DOM mutations and responsive layout shifts.
- Rage clicks (user clicking repeatedly on an unresponsive element).
- Correlated console errors and network request statuses.

## 1. Configuring Session Replay (Browser / Next.js)

```typescript
import * as Sentry from '@sentry/react'; // or @sentry/nextjs

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  // 10% sampling for normal healthy sessions (cost control)
  replaysSessionSampleRate: 0.1,
  // 100% sampling whenever an error occurs (guarantees reproduction)
  replaysOnErrorSampleRate: 1.0,
  integrations: [
    Sentry.replayIntegration({
      maskAllText: true,           // Masks all text content by default for privacy
      blockAllMedia: true,         // Blocks images/videos from being recorded
      maskAllInputs: true,         // Masks form inputs
    }),
  ],
});
```

## 2. Unmasking Safe UI Elements

If you want specific non-sensitive elements visible in replays:
```html
<div class="product-title" data-sentry-unmask>
  Wireless Noise-Cancelling Headphones
</div>
```

Or explicitly mask sensitive elements:
```html
<div class="user-private-data" data-sentry-mask>
  Sensitive Account Information
</div>
```

## 3. Querying Replays via CLI

```bash
# List recent replays with error counts and rage clicks
sentry replay list <org>/<project> -t 24h -n 10 --json \
  | jq -r '.data[] | "ID: \(.id) | Duration: \(.duration)s | Errors: \(.count_errors) | Rage Clicks: \(.count_rage_clicks)"'

# Inspect details for a specific replay
sentry replay view <REPLAY_ID> --json
```

## 4. Connecting Errors to Replays

When inspecting an issue with `sentry issue view <ID> --json`, read `.replayIds`:
```bash
jq -r '.replayIds[]? // empty' /tmp/sentry_issue.json
```
If present, this directly gives you the exact user session recording where the error occurred.
