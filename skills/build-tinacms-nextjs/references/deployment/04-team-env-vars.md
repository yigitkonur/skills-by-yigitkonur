# Vercel Team Environment Variables

Share TinaCloud credentials and other env vars across multiple Vercel projects without duplicating.

## When to use

- Agency / org with multiple Vercel projects sharing one TinaCloud account
- Multi-site deployments (one TinaCloud project per site, but shared base config)
- Common env vars across staging + production projects

## Setup

1. Vercel → Team → Settings → Environment Variables
2. Add a variable (e.g. `NEXT_PUBLIC_TINA_CLIENT_ID`)
3. Scope to which environments (Production, Preview, Development)
4. Optionally restrict to specific projects in the team

All projects in the team inherit the variable.

## Common shared vars

```env
# Set at team level — shared across projects:
TINA_TOKEN=<one read-only token, used everywhere>
NEXT_PUBLIC_TINA_CLIENT_ID=<one project ID>
NEXTAUTH_SECRET=<shared secret>
GITHUB_OWNER=<your org>
```

## Per-project overrides

Project-level env vars override team-level. So you can set a default at the team level and override per-project:

```
Team:    NEXT_PUBLIC_TINA_BRANCH=main      ← default
Project: NEXT_PUBLIC_TINA_BRANCH=staging   ← overrides for staging project
```

## When NOT to use

- Each project has genuinely different credentials (different TinaCloud projects)
- You want stricter isolation (per-project secrets)

## Rotating shared tokens

When you rotate a shared token:

1. Update at team level
2. All projects pick up the new value on next deploy
3. Trigger a manual redeploy if you don't want to wait for the next push

## Self-hosted considerations

For self-hosted projects sharing infrastructure (Vercel KV, GitHub PAT):

```env
# Team-level shared:
GITHUB_PERSONAL_ACCESS_TOKEN=<shared PAT with access to all repos>
NEXTAUTH_SECRET=<shared>

# Per-project:
GITHUB_OWNER=<varies>
GITHUB_REPO=<varies>
KV_REST_API_URL=<per-project KV>
KV_REST_API_TOKEN=<per-project>
```

KV credentials are auto-injected per-project (since you create one KV per project).

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Shared token with too-broad scope | Security risk | Use scoped tokens per project |
| Overrode team var unintentionally | Wrong value used | Check both team + project levels |
| Forgot to redeploy after rotating | Old token still active | Trigger redeploys |
| Used Team vars for project-unique values | Confusion | Override at project level instead |
