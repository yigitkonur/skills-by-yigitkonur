# First Run: npx convex dev

## Use This When
- Running the Convex development server for the first time.
- Understanding the hot-reload workflow for backend iteration.
- Troubleshooting first-run issues.

## Starting the Dev Server

```bash
cd YourProject
npx convex dev
```

First run prompts:
1. **Log in** -- opens browser for Convex account (free tier available).
2. **Create project** -- name it (e.g., "my-ios-app").
3. **Choose deployment** -- creates a dev deployment automatically.

Output:
```
Convex functions ready!
  messages:list   (query)
  messages:send   (mutation)
  users:me        (query)
```

**Keep this terminal running** while you develop.

## Hot-Reload Workflow

Every save in `convex/` triggers an automatic deploy:

| File Saved | What Happens |
|---|---|
| `schema.ts` | Validates schema against existing data, deploys if valid |
| `messages.ts` | Type-checks, deploys functions, active subscriptions see new behavior |
| `auth.config.ts` | Auth configuration updated |

Typical feedback loop: save -> 1-2 seconds -> deployed. Faster than an iOS simulator build.

## The Dashboard

While `npx convex dev` runs, open [dashboard.convex.dev](https://dashboard.convex.dev):

- **Data** -- browse tables, see documents in real-time.
- **Functions** -- all deployed functions with types and recent executions.
- **Logs** -- execution logs with timing, errors, and stack traces.
- **Settings** -- environment variables, deployment URL.

The dashboard is your backend's equivalent of Xcode's debug console.

## Common First-Run Issues

| Issue | Fix |
|---|---|
| `convex/` directory not found | Create it: `mkdir convex` |
| Schema validation error | Existing data doesn't match schema -- fix schema or clear data in dashboard |
| `npx convex dev` hangs | Check Node version (`node --version` must be 18+) |
| Auth returns null | Create `convex/auth.config.ts` -- without it, `getUserIdentity()` always returns null |

## Production Deployment

```bash
npx convex deploy
```

This performs an **atomic deployment** -- schema, functions, and indexes all deploy as one unit. If any part fails, nothing changes. Set this up in your CI/CD pipeline.

## Avoid
- Closing the `npx convex dev` terminal while developing -- your backend stops syncing.
- Running `npx convex deploy` during local development -- it targets production.
- Editing files in `convex/_generated/` -- they are auto-generated and overwritten on every deploy.
- Skipping the dashboard logs when debugging -- they show server-side errors with stack traces that the Swift client cannot surface.

## Read Next
- [01-installing-convex-and-node-prerequisites.md](01-installing-convex-and-node-prerequisites.md)
- [../backend/03-queries-mutations-actions-scheduling.md](../backend/03-queries-mutations-actions-scheduling.md)
- [../onboarding/03-mental-model-live-data-functions-and-state.md](../onboarding/03-mental-model-live-data-functions-and-state.md)
