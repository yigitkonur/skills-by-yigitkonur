# TinaCloud-specific Issues

Issues unique to TinaCloud (vs self-hosted). For self-hosted issues, see other troubleshooting files.

## Indexing not happening

**Symptom:** Content saved but queries return old data. Admin shows the change; deployed site doesn't.

**Causes:**

- TinaCloud's GitHub webhook didn't fire
- Indexing failed mid-process

**Fix:**

1. TinaCloud Project Settings → manually trigger reindex
2. GitHub repo Settings → Webhooks → look for the TinaCloud webhook (should be green/recent)
3. If webhook missing, reinstall the TinaCloud GitHub App on the repo

## "Project not found"

**Cause:** Wrong `NEXT_PUBLIC_TINA_CLIENT_ID`.

**Fix:** Re-check the value matches the project ID in app.tina.io.

## Auth errors / "Invalid credentials"

**Causes:**

- `TINA_TOKEN` expired or revoked
- Used the write token where read-only is expected (or vice versa)
- Token mismatched to project

**Fix:**

1. Regenerate the read-only token from app.tina.io
2. Update Vercel env var
3. Redeploy

## Editor can't log in

**Causes:**

- Editor email not invited to project
- Editor's GitHub OAuth blocked by TinaCloud
- Corporate firewall blocking `app.tina.io`

**Fix:**

1. Project Settings → Users → Invite the email
2. Editor must accept invite + sign in
3. If firewall: see `references/troubleshooting/07-network-and-firewall.md`

## Hit rate limit

**Cause:** Free tier (10k requests/month) exhausted.

**Fix:**

- Add `revalidate: 60` or longer to all client queries
- Use `"use cache"` aggressively
- Pre-render via `generateStaticParams`
- Upgrade tier if traffic genuinely warrants

For high-traffic sites: Team Plus or Business tier.

## Editorial Workflow modal doesn't appear

**Causes:**

- Tier is below Team Plus
- Protected branches not configured

**Fix:**

1. Verify tier: app.tina.io → Project → Billing
2. Project Settings → Configuration → Editorial Workflow → set protected branches
3. Refresh admin

## Search returns nothing

**Cause:**

- Search index not built
- `searchable: false` on critical fields
- Indexer token missing

**Fix:**

1. Run `pnpm tinacms build` to re-index
2. Check schema for `searchable` flags
3. Verify `TINA_SEARCH_INDEXER_TOKEN` env var is set
4. TinaCloud Configuration → Search → re-generate indexer token if needed

## Webhook doesn't fire

**Causes:**

- Webhook URL wrong
- Branch filter mismatch
- Destination returning 5xx

**Fix:**

1. Project Settings → Webhooks → Logs
2. Check recent attempts — note the URL, method, response code
3. Verify destination is reachable: `curl <webhook-url>` (should return 200/2xx for an empty test)
4. If destination 5xx, fix the destination handler
5. If branch filter mismatch, update target branches

## Content commits authored by wrong user

**Cause:** Editor logged into TinaCloud with a different GitHub account than expected.

**Fix:**

- Have editor log out of TinaCloud (`/admin#/logout`)
- Sign back in with the correct GitHub account
- Verify GitHub repo grants the right account write access

## Admin shows old version

**Cause:** TinaCloud's CDN cached an older admin SPA after a deploy.

**Fix:**

1. Hard reload (Cmd+Shift+R)
2. Wait ~10 minutes for CDN cache to clear
3. If persistent: check `tinacms` and `@tinacms/cli` versions match

## Mixed content / SSL errors in admin

**Cause:** Site over HTTPS, admin tries to load HTTP.

**Fix:** Ensure your site is always HTTPS:

- `NEXT_PUBLIC_SITE_URL=https://...`
- Vercel auto-provides SSL — verify cert is valid

## Branch switcher missing

**Cause:** Editorial Workflow not enabled for the editor's tier.

**Fix:** Upgrade to Team Plus and enable in Configuration.

## "Not authorized to write to this branch"

**Cause:** Editor has TinaCloud project access but lacks GitHub write access.

**Fix:** Add editor to the GitHub repo as collaborator/team member.

## Slow indexing (10+ minutes)

**Causes:**

- Very large schema (500+ collections)
- 10k+ documents
- Initial first-time indexing

**Fix:**

- Wait it out for first index
- For repeated slowness: simplify schema; consolidate collections
- For periodic reindex (after a content sync), trigger via API rather than waiting for webhook

## Billing failures

**Cause:** Payment method expired.

**Fix:** Update billing in TinaCloud dashboard. Until updated, project becomes read-only.

## Common mistakes

| Mistake | Fix |
|---|---|
| Wrong env vars | Re-check from dashboard |
| GitHub App not installed | Install via TinaCloud dashboard |
| Forgot `revalidate` | Add to all client queries |
| Two TinaCloud projects on same repo | Conflicting webhooks; use one |
| Editor lacks GitHub write access | Add as repo collaborator |
| Hit rate limit | Cache more aggressively or upgrade |
