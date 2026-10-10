# User Feedback Dialog & Programmatic API

How to collect user crash descriptions, feature requests, and bug reports correlated directly with Sentry errors and session replays.

## 1. Browser User Feedback Widget (`feedbackIntegration`)

Modern Sentry (v8+) provides the native User Feedback integration with customizable floating buttons, modal forms, and screenshot capture:

```typescript
import * as Sentry from '@sentry/browser'; // or @sentry/react / @sentry/nextjs

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  integrations: [
    Sentry.feedbackIntegration({
      // Auto-inject a floating feedback button in the bottom right corner
      autoInject: true,
      colorScheme: 'system',
      formTitle: 'Report an Issue',
      submitButtonLabel: 'Send Feedback',
      isEmailRequired: true,
      showScreenshot: true,
    }),
  ],
});
```

To trigger the feedback modal manually from your own button or error boundary:
```typescript
const feedback = Sentry.getFeedback();
if (feedback) {
  feedback.openDialog();
}
```

## 2. Programmatic User Feedback Submission (`Sentry.captureFeedback`)

When building a custom feedback modal or collecting feedback from a backend/mobile API:

```typescript
import * as Sentry from '@sentry/node'; // or @sentry/browser

export async function submitCrashFeedback(params: {
  eventId?: string;
  name: string;
  email: string;
  message: string;
}) {
  // CRITICAL: Modern Sentry SDK requires 'message' (not 'comments')
  Sentry.captureFeedback({
    message: params.message,
    name: params.name,
    email: params.email,
    associatedEventId: params.eventId,
  });
}
```

## 3. Direct REST API Ingest

`POST https://<sentry-host>/api/0/projects/{org_slug}/{project_slug}/user-feedback/`

Header: `Authorization: Bearer <AUTH_TOKEN>` or Client DSN auth.

Payload:
```json
{
  "event_id": "9ec60100773b4f648b265b1618c774f0",
  "name": "Jane Doe",
  "email": "jane@example.com",
  "comments": "The page crashed when I clicked 'Export to CSV'."
}
```
*Note: In the REST API HTTP payload, `comments` is accepted by the ingest endpoint, but the modern SDK function `Sentry.captureFeedback()` expects `message`.*
