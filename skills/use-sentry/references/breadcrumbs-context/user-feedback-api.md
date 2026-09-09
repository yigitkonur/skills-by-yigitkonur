# User Feedback Dialog & Programmatic API

How to collect user crash descriptions following an unhandled error and link feedback directly to the Sentry event ID.

## 1. Browser User Feedback Dialog (React / Next.js)

When an error boundary catches a render crash, prompt the user for feedback:

```typescript
import * as Sentry from '@sentry/react';

function ErrorFallback({ error, resetErrorBoundary, eventId }: any) {
  return (
    <div>
      <h2>Something went wrong.</h2>
      <button onClick={() => Sentry.showReportDialog({ eventId })}>
        Report feedback
      </button>
      <button onClick={resetErrorBoundary}>Try again</button>
    </div>
  );
}
```

## 2. Programmatic User Feedback Submission (REST API)

If you collect feedback through a custom in-app modal or backend API:

```typescript
import * as Sentry from '@sentry/node';

export async function submitUserCrashFeedback(params: {
  eventId: string;
  name: string;
  email: string;
  comments: string;
}) {
  const userFeedback = {
    event_id: params.eventId,
    name: params.name,
    email: params.email,
    comments: params.comments,
  };

  Sentry.captureFeedback(userFeedback);
}
```

## REST API Direct Ingest:
`POST https://sentry.io/api/0/projects/{org_slug}/{project_slug}/user-feedback/`
```json
{
  "event_id": "9ec60100773b4f648b265b1618c774f0",
  "name": "Jane Doe",
  "email": "jane@example.com",
  "comments": "The page crashed when I clicked 'Export to CSV'."
}
```
Sentry automatically pins the user's comments to the top of the issue layout in the dashboard.
