# TinaCloud Overview

The default backend for TinaCMS. Managed service: hosting, indexing, auth, search, all handled.

## When to use TinaCloud

Default for ~90% of projects. Pick TinaCloud unless you have a specific reason to self-host (see `references/concepts/03-tinacloud-vs-self-hosted.md`).

Specifically, TinaCloud is the right choice when:

- You want zero backend code
- You need editorial workflow (Team Plus+)
- You want built-in fuzzy search
- You're under the free tier OR willing to pay
- You're using GitHub (the only natively supported git provider)

## Tiers

| Tier | Price | Users | Notable |
|---|---|---|---|
| Free | $0 | 2 | Community support |
| Team | $29/mo | 3 (up to 10) | Team support |
| Team Plus | $49/mo | 5 (up to 20) | **Editorial Workflow**, AI features |
| Business | $299/mo | 20+ | 3 roles, API access |
| Enterprise | Custom | Custom | SSO, GitHub Enterprise |

Always check `https://tina.io/pricing` for current numbers.

## What TinaCloud provides

| Feature | Free | Team | Team Plus | Business | Enterprise |
|---|---|---|---|---|---|
| Unlimited repos | ✓ | ✓ | ✓ | ✓ | ✓ |
| Unlimited documents | ✓ | ✓ | ✓ | ✓ | ✓ |
| GitHub integration | ✓ | ✓ | ✓ | ✓ | ✓ |
| Fuzzy search | ✓ | ✓ | ✓ | ✓ | ✓ |
| Editorial Workflow | – | – | ✓ | ✓ | ✓ |
| AI features | – | – | ✓ | ✓ | ✓ |
| Multiple roles | – | – | – | ✓ | ✓ |
| API access | – | – | – | ✓ | ✓ |
| SSO | – | – | – | – | ✓ |
| GitHub Enterprise | – | – | – | – | ✓ |

## Setup steps

1. Sign up at https://app.tina.io
2. Create a project — point at your GitHub repo
3. Get `Client ID` and `Read-only Token` from project settings
4. Add to `.env`:
   ```env
   NEXT_PUBLIC_TINA_CLIENT_ID=<client-id>
   TINA_TOKEN=<read-only-token>
   NEXT_PUBLIC_TINA_BRANCH=main
   ```
5. Deploy

The admin SPA at `/admin/index.html` connects to TinaCloud at runtime using these env vars.

## How TinaCloud knows about your content

TinaCloud has GitHub access (via GitHub App you install). When you push content:

1. GitHub webhook → TinaCloud
2. TinaCloud re-indexes the content into its DB
3. Queries return fresh data

Indexing takes seconds (small repos) to a minute (large repos).

## Data flow

```
Editor's browser
   ↕ admin SPA (loads via /admin/index.html)
TinaCloud GraphQL API (auth, queries, mutations)
   ↓ on save
GitHub (commits content)
   ↑ webhook
TinaCloud reindexes
```

## Network requirements (corporate firewalls)

TinaCloud uses several domains. If your editors are behind a corporate firewall, allowlist:

- `*.tina.io`
- `*.tinajs.io`
- `content.tinajs.io`
- `app.tina.io`

See `references/tinacloud/02-network-requirements.md`.

## Reading order

| File | Topic |
|---|---|
| `references/tinacloud/02-network-requirements.md` | Domain allowlist for firewalls |
| `references/tinacloud/03-dashboard-registration.md` | Account setup |
| `references/tinacloud/04-projects.md` | Project config tab |
| `references/tinacloud/05-users-and-orgs.md` | User management |
| `references/tinacloud/06-editorial-workflow.md` | Branch-based PR workflow |
| `references/tinacloud/07-webhooks.md` | Content-changed webhooks |
| `references/tinacloud/08-search.md` | Built-in fuzzy search |
| `references/tinacloud/09-git-co-authoring.md` | Editor identity in commits |
| `references/tinacloud/10-api-versioning.md` | GraphQL API version pinning |
| `references/tinacloud/11-github-enterprise.md` | GHE integration |
| `references/tinacloud/12-vercel-deployment.md` | Vercel-specific deployment |
| `references/tinacloud/13-troubleshooting.md` | TinaCloud-specific issues |

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Wrong `NEXT_PUBLIC_TINA_CLIENT_ID` | "Project not found" | Re-check from app.tina.io |
| Used a write-token as `TINA_TOKEN` | Works but exposes write scope to browser | Use read-only token |
| Forgot to install TinaCloud GitHub App | TinaCloud can't access repo | Install app on the repo |
| Editor not added to project | Auth denies | Add via Users tab |
| Used a TinaCloud project for self-hosted backend | Conflicting auth | Pick one |
