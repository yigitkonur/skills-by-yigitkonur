# Contextual Breadcrumbs: UI & User Interactions

How to capture user navigation, clicks, component mounts, and rage clicks to diagnose frontend crashes.

## 1. Automatic UI Breadcrumbs in Browser SDK

`@sentry/react`, `@sentry/browser`, and `@sentry/nextjs` automatically capture:
- **Navigation:** URL changes, hash updates, pushState.
- **DOM Clicks:** Element tag names, CSS IDs, classes, and aria-labels.
- **Console Logs:** `console.log`, `console.warn`, `console.error`.

```typescript
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  integrations: [
    Sentry.breadcrumbsIntegration({
      dom: true,        // Log click events
      history: true,    // Log URL changes
      console: true,    // Log console output
    }),
  ],
});
```

## 2. Manual UI Action Recording

For custom components, modal dialogs, or workflow steps:

```typescript
export function recordUiAction(action: string, component: string, meta?: Record<string, any>) {
  Sentry.addBreadcrumb({
    category: 'ui.action',
    type: 'user',
    message: `${action} on ${component}`,
    level: 'info',
    data: meta,
  });
}
```

## 3. Scrubbing Sensitive Input Fields

To avoid capturing passwords or credit card numbers in DOM breadcrumbs, add `data-sentry-mask` or configure `beforeBreadcrumb`:

```html
<!-- Automatically masked in breadcrumbs and Session Replay -->
<input type="text" data-sentry-mask />
```

In `beforeBreadcrumb`:
```typescript
beforeBreadcrumb(crumb) {
  if (crumb.category === 'ui.click' && crumb.data?.target?.includes('password')) {
    crumb.data.target = '[Filtered Input]';
  }
  return crumb;
}
```
