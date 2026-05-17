# Project Configuration

The Project Settings tab inside `app.tina.io` controls connection to GitHub, branch protection, search, and more.

## Tabs

| Tab | Purpose |
|---|---|
| **General** | Name, description |
| **Tokens** | Client ID, read-only token, write token |
| **Configuration** | Editorial Workflow, branch protection, search indexer |
| **Webhooks** | Webhook destinations for content events |
| **Users** | Invite/remove team members |
| **Billing** | Plan, payment method |

## General

Just metadata. The "Name" appears in the admin's project switcher.

## Tokens

| Token | When |
|---|---|
| Client ID | Always — `NEXT_PUBLIC_TINA_CLIENT_ID` |
| Read-only Token | Always — `TINA_TOKEN` |
| Write Token | Only for programmatic content writes (import scripts) |

Rotate periodically. Copy and save somewhere safe — TinaCloud doesn't show them after the first creation.

## Configuration

### Editorial Workflow (Team Plus+ only)

Toggle on. Specify protected branches (typically `main`):

```
Protected branches: main, production
```

When editors save on a protected branch, TinaCloud creates a new branch + draft PR. See `references/tinacloud/06-editorial-workflow.md`.

### Search indexer

Generate a search indexer token. Add to your `tina/config.ts`:

```typescript
search: {
  tina: {
    indexerToken: process.env.TINA_SEARCH_INDEXER_TOKEN,
    stopwordLanguages: ['eng'],
  },
}
```

See `references/tinacloud/08-search.md`.

### API version

Pin the GraphQL API version (advanced — most projects don't change this). See `references/tinacloud/10-api-versioning.md`.

## Webhooks

Add webhook URLs that fire on content events (`content.added`, `content.modified`, `content.removed`).

Common use:

- Vercel Deploy Hook URL → triggers rebuild on content change
- Custom revalidation route → invalidate Next.js cache

See `references/tinacloud/07-webhooks.md`.

## Users

Invite by email. Each invite consumes one of your tier's user slots.

Roles (Business+ only):

- **Admin** — manage project settings
- **Editor** — edit content
- **Viewer** — read-only

Free / Team / Team Plus tiers: all users are Editors.

## Billing

Upgrade/downgrade. Free tier limits:

- 2 users
- 10k requests/month
- 1 environment

Hitting limits → operations slow / fail until upgrade or quota reset.

## Multiple projects per organization

Create one TinaCloud organization, multiple projects under it. Useful for:

- Multi-site agencies
- Mono-repos with multiple sites
- Test/staging vs production projects

Each project has its own credentials and quota.

## Deleting a project

**Settings → General → Delete Project**. Permanent — frees the slot but doesn't refund the month.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Two projects pointing at the same repo | Webhook conflicts | One project per repo |
| Editorial Workflow toggled but no protected branch set | Saves go directly to main | Specify protected branches |
| Forgot to create search indexer token | `search` config fails | Generate token in Configuration tab |
| Billing failure | Project read-only | Update payment method |
| Project owner left the org | Locks out admin actions | Transfer ownership before leaving |
