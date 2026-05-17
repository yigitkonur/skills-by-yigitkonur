# Dashboard Registration

Creating a TinaCloud account, project, and getting your credentials.

## Sign up

1. Visit https://app.tina.io
2. Sign in with GitHub (recommended) or email
3. Authorize the TinaCloud GitHub App when prompted

## Create a project

1. From the dashboard, click "Create Project"
2. Name the project
3. Choose your GitHub organization or personal account
4. Select the repo
5. Pick the default branch (usually `main`)

## Install the GitHub App

If not done during sign-up, TinaCloud needs access to your repo. From the dashboard:

1. Click "Install GitHub App"
2. Pick the org/account
3. Choose specific repos OR all repos (more flexible later if you choose all)

The app needs: repo read/write, contents access, webhooks.

## Get credentials

After project creation, navigate to **Project Settings → Tokens**:

| Token | Purpose | Scope |
|---|---|---|
| **Client ID** | Identifies the project | Public — okay to expose in `NEXT_PUBLIC_*` |
| **Read-only Token** | Server-side queries | Read content via GraphQL |
| **Write Token** | Programmatic content writes | Optional — for import scripts only |

For the standard editor flow, you only need the first two.

## Local environment

```env
# .env (Tina build reads from .env, not .env.local)
NEXT_PUBLIC_TINA_CLIENT_ID=<from dashboard>
TINA_TOKEN=<read-only token>
NEXT_PUBLIC_TINA_BRANCH=main
```

## Vercel environment

In Vercel project settings → Environment Variables, add the same three. Scope to Production + Preview.

For multiple Vercel projects sharing one TinaCloud project, use Vercel **Team Environment Variables**.

## Verify connectivity

After setup:

1. `pnpm dev` and open `/admin/index.html`
2. Click "Login" — redirects to TinaCloud OAuth
3. After login, you should see your collections

If login fails:

- Check `NEXT_PUBLIC_TINA_CLIENT_ID` matches the project
- Check the GitHub App is installed
- Check your TinaCloud account email matches the project's authorized users

## Inviting users

Project Settings → Users → Invite. Free tier: 2 users; paid tiers go higher.

Users sign in via TinaCloud OAuth and gain access to the admin.

## Multiple environments

Common pattern:

| Env | TinaCloud project | Branch |
|---|---|---|
| Production | `acme-prod` | `main` |
| Staging | `acme-staging` | `staging` |
| Per-developer dev | Same prod project | feature branches |

Or one project with branch-based isolation. Both work.

## Switching plans

Upgrade/downgrade through Billing. Changes apply immediately. Downgrading from Team Plus removes Editorial Workflow access.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| GitHub App not installed | TinaCloud can't access repo | Install via dashboard |
| Wrong Client ID | "Project not found" | Re-check |
| Used the write token for `TINA_TOKEN` | Works but exposes too much | Use read-only |
| Two TinaCloud projects on the same repo | Conflicting webhooks | Use one |
| Forgot to add team members to the project | They can't log in | Invite via Users tab |
