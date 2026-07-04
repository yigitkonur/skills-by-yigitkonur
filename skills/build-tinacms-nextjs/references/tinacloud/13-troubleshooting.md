# TinaCloud Troubleshooting

TinaCloud-specific issues. For general TinaCMS issues, see `references/troubleshooting/`.

## Indexing not happening

Content saved but queries return old data.

**Cause:** TinaCloud's GitHub webhook didn't fire, or indexing failed.

**Fix:**

1. Project Settings → Indexer → manually trigger reindex
2. Check the webhook in your GitHub repo (Settings → Webhooks → TinaCloud) — should be green
3. Re-install the TinaCloud GitHub App if the webhook is missing

## "Project not found" or auth errors

**Cause:** Wrong `NEXT_PUBLIC_TINA_CLIENT_ID` or expired token.

**Fix:**

- Re-check Client ID matches what's in TinaCloud dashboard
- Regenerate the read-only token
- Verify GitHub App is installed on the repo

## Editor can't log in

**Cause:** Editor email not invited to project, or GitHub OAuth blocked.

**Fix:**

- Project Settings → Users → invite the email
- Editor must sign in via TinaCloud OAuth at least once
- If using a corporate firewall, allowlist `app.tina.io`

## Hit rate limit

**Cause:** Free tier 10k requests/month exhausted.

**Fix:**

- Add `revalidate: 60+` to all client queries
- Use `"use cache"` aggressively
- Upgrade tier if traffic genuinely warrants

## Editorial Workflow modal doesn't appear

**Cause:** Not on Team Plus tier OR protected branches not configured.

**Fix:**

- Verify tier is Team Plus or above
- Project Settings → Configuration → Editorial Workflow → set protected branches

## Search returns nothing

**Cause:** Search index not built, or `searchable: false` on critical fields.

**Fix:**

- Run `pnpm tinacms build` to re-index
- Check `searchable` flags on schema fields
- Verify `TINA_SEARCH_INDEXER_TOKEN` env var is set

## Webhook doesn't fire

**Cause:** Webhook URL wrong, branch filter mismatch, or destination returning 5xx.

**Fix:**

- Project Settings → Webhooks → Logs → check recent attempts
- Verify the destination URL is reachable (curl from outside)
- Check destination returns 2xx (TinaCloud retries on 5xx, gives up after several tries)

## Content commits authored by wrong user

**Cause:** Editor signed in with a different GitHub account than expected.

**Fix:**

- Have editor log out / log back in
- Verify GitHub repo grants them write access via the right account

## Admin shows old admin SPA

**Cause:** CDN cached an old admin SPA version after a deploy.

**Fix:**

- Hard reload in browser (Cmd+Shift+R)
- If persistent: TinaCloud's CDN is cached for ~10 minutes; wait it out
- Check TinaCloud version vs `@tinacms/cli` version — pin both

## "Mixed content" error in admin iframe

**Cause:** Site over HTTPS but admin tries to load HTTP.

**Fix:**

- Ensure your site serves over HTTPS
- Check `NEXT_PUBLIC_SITE_URL` env var is `https://...`
- Vercel auto-provides SSL

## Branch switcher missing in admin

**Cause:** Editorial Workflow not enabled, or branch protection not set.

**Fix:**

- Enable in Project Settings → Configuration
- Specify protected branches

## "Not authorized to write to this branch"

**Cause:** Editor has TinaCloud access but lacks GitHub write access on the repo.

**Fix:**

- Add editor as collaborator/team member on the GitHub repo
- For org repos, ensure the team they're in has write access

## Large schema → slow build

**Cause:** Schema with hundreds of collections, blocks, field types.

**Fix:**

- Run `pnpm tinacms audit` and look for unused/duplicate collections
- Consolidate where possible
- For 500+ docs, ensure indexing completes (might take 5–10 minutes initially)

## When to contact TinaCMS support

Contact support for:

- Persistent webhook failures despite correct config
- Unexplained quota usage
- Billing issues
- Enterprise / GHE setup help

For day-to-day issues, the [Discord](https://discord.gg/zumN63Ybpf) is faster.

## Common mistakes (recap)

| Mistake | Fix |
|---|---|
| Wrong env vars | Re-check from dashboard |
| GitHub App not installed | Install via TinaCloud dashboard |
| Forgot `revalidate` in production | Add to all client queries |
| Two TinaCloud projects on same repo | Conflicting webhooks; use one |
| Editor lacks GitHub write access | Add as repo collaborator |
