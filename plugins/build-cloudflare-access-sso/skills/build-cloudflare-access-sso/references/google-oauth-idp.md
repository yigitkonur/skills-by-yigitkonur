# Google OAuth client → Cloudflare identity provider

Everything on the Google side of "Sign in with Google" for a Cloudflare Access application, plus
the failure modes that look like Cloudflare problems but are not.

## Create the OAuth client

Google Cloud Console → **APIs & Services / Google Auth Platform**. There is no API for creating an
OAuth *client* — this is console work.

1. Pick or create a project. **Read "Which project" below before reusing an existing one.**
2. Configure the consent screen (Google Auth Platform → Branding / Audience) if the project has
   none: app name, support email, developer contact.
3. Credentials → Create credentials → **OAuth client ID** → **Web application**.
4. Authorized redirect URI — exactly one, exactly this:

   ```
   https://<team-name>.cloudflareaccess.com/cdn-cgi/access/callback
   ```

   `<team-name>` is the Zero Trust team domain, visible in the Cloudflare Zero Trust dashboard
   under Settings → Custom Pages / General. Anything else produces `redirect_uri_mismatch`.
5. Copy the client ID and client secret into env vars immediately.

Scopes: `email`, `profile`, `openid`. Cloudflare requests these itself; you do not add them to the
client.

## Register it with Cloudflare

```bash
curl -sX POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/access/identity_providers" \
  -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
  -d "{\"name\":\"Google\",\"type\":\"google\",
       \"config\":{\"client_id\":\"$GOOGLE_CLIENT_ID\",\"client_secret\":\"$GOOGLE_CLIENT_SECRET\"}}"
```

Test it from the dashboard's IdP list ("Test") or by loading the protected hostname. A successful
create returns an IdP `id` — record the id, not the secret.

> `type: "google"` is a plain Google OAuth login and accepts any Google account; the Cloudflare
> policy is what restricts the domain. `type: "google-apps"` is the Google Workspace variant and
> takes an additional `apps_domain` in `config`. Use `google-apps` only if you specifically want
> Google to enforce the Workspace domain as well — the Access policy still has to.

## The consent-screen trap (most expensive failure in this workflow)

A Google Auth Platform project is either in **Testing** or **In production**.

| Mode | Who can complete login | Notes |
|---|---|---|
| Testing | Only accounts on the **Test users** list (cap 100) | Everyone else gets a Google error page |
| In production | Anyone the app's audience allows | External + sensitive scopes may require Google verification |

In Testing mode, a user who is not on the list is stopped **by Google, before Cloudflare is ever
involved**. The error is a Google screen, not an Access screen — so it reads as "Google is broken",
not "I'm not allowed in", and it is easy to misdiagnose as a Cloudflare policy problem.

Symptoms that mean "consent screen, not Access":

- Error appears on `accounts.google.com`, not on `<team-name>.cloudflareaccess.com`.
- Wording is about the app not completing verification / not being allowed, not
  "That account does not have access."
- A different account works, and the difference is the test-user list rather than the email domain.

Fixes, in order of preference:

1. **Add the user** at Google Auth Platform → Audience → Test users. Instant, no side effects,
   works up to 100 users.
2. **Give the OAuth client its own GCP project** and publish that one. Cleanest permanent fix.
3. **Publish the existing project** — only after auditing it (next section).

Add **Email one-time PIN** as a second Cloudflare IdP regardless. It bypasses this entire class of
problem and is the working path for anyone not on the test-user list:

```bash
curl -sX POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/access/identity_providers" \
  -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Email OTP","type":"onetimepin","config":{}}'
```

## Which project — audit before you publish

The Testing/Published setting is **project-wide**, not per-client. Before publishing, list every
OAuth client in the project and what scopes each uses. If any of them touch sensitive or restricted
scopes (Analytics, Search Console, Ads, Drive, Gmail), publishing can pull those clients into
Google's verification process — a multi-week review that can interrupt working integrations.

Publishing is also blocked by policy violations anywhere in the project, including on unrelated
clients (a non-HTTPS homepage or privacy-policy URL on some other client will block the whole
project).

A dedicated project for the Access OAuth client avoids all of this. Note that **Internal** audience
is only offered when the Google account belongs to a Cloud organization; a personal or
unorganized Workspace account gets External-plus-published instead, which is fine — the Cloudflare
policy is still the gate.

## Rotating the secret

Google does not display an existing client secret after creation. If it is lost:

1. On the OAuth client detail page → **Add secret**. The old one keeps working until you delete it.
2. Update the Cloudflare IdP:

   ```bash
   curl -sX PUT "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/access/identity_providers/$IDP_ID" \
     -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
     -d "{\"name\":\"Google\",\"type\":\"google\",
          \"config\":{\"client_id\":\"$GOOGLE_CLIENT_ID\",\"client_secret\":\"$GOOGLE_CLIENT_SECRET\"}}"
   ```
3. Verify a real login, then delete the old secret in Google.

Do not delete and recreate the *client* — that changes the client ID and forces the redirect URI to
be re-registered for no benefit.

## Onboarding a new person, later

Write this into the repo docs, because the failure is silent:

- Their email must be in the Access policy's domain (or explicitly included).
- **If the consent screen is still in Testing, they must also be on the Google test-user list.**
- If either is missing they cannot log in, and the two failures look completely different.
