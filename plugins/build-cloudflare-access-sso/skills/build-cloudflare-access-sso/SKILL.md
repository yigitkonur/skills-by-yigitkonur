---
name: build-cloudflare-access-sso
description: "Use if protecting a subdomain with Cloudflare Access + Google SSO, or locking an origin against Access bypass."
---

# build-cloudflare-access-sso

Put a company-only login wall in front of a subdomain you already serve: Cloudflare Access for
authorization, Google Workspace (or Email OTP) for identity, and an origin lockdown so nobody
reaches the app by its IP address.

## When to use

- An internal tool, dashboard, staging site, or agent UI is publicly reachable on
  `app.example.com` and must be restricted to one email domain.
- An app has no login of its own — or its login was disabled — and you need auth in front of it
  without touching application code.
- "Sign in with Google" must gate a hostname, and the Google OAuth client / consent screen has to
  be configured to match.
- Access is already configured but someone can still reach the app by hitting the origin IP with a
  `Host:` header.
- You are auditing an existing Access setup and need to prove it is not bypassable.

Do NOT use for:

- **Private-network access where the origin is not publicly routable** — that is a Cloudflare
  Tunnel + device-client design. This skill assumes a public origin behind a reverse proxy.
- **SaaS SSO federation** (Cloudflare as IdP into Slack/Datadog/etc.) — different app type,
  different setup.
- **Gateway/DNS filtering, device posture, WARP rollout, DLP** — Access controls *who reaches an
  app*; those control *traffic*.
- **Adding auth inside your application** (sessions, password hashing, OAuth in your own code).

## First: three facts that shape every decision

**1. Access only enforces on traffic that flows through Cloudflare.** The Access application is a
rule at the edge, not on your server. If the DNS record is DNS-only (grey cloud), or if a client
resolves your origin IP directly, Access is not in the path at all — it still looks perfectly
configured in the dashboard while enforcing nothing. Cloudflare's own docs say it plainly: if the
app is already publicly routable a tunnel is not required, *"however, you will then need to protect
your origin IP using other methods."*

**2. Access is deny-by-default, and policies are standalone objects.** An application with no Allow
policy blocks everyone. Create the **reusable** policy first
(`POST /accounts/{account_id}/access/policies`), then attach it to the app by id. Policies created
through the app-scoped endpoint come back as `reusable: false` and are legacy — do not create new
ones that way.

**3. Every secret in this flow is shown exactly once.** The Google OAuth client secret is not
re-displayable after creation (Google stopped showing existing secrets), and Cloudflare returns
service-token secrets once. Capture them into a secret store or an env var at the moment of
creation, or plan to rotate.

## The three load-bearing parts

All three are required. Removing any one silently reopens public access with no visible error.

| Part | What it does | If it is missing | Where it lives |
|---|---|---|---|
| **Access app + Allow policy** | Authenticates at the edge and authorizes by email domain | Anyone who reaches the hostname gets in | Cloudflare account (Zero Trust) |
| **Proxied DNS (orange cloud)** | Puts Cloudflare in the request path so Access can run | Access is configured but never evaluated | Cloudflare zone DNS |
| **Origin lockdown** | Rejects requests that did not come from Cloudflare's edge | `curl --resolve` to the origin IP serves the app unauthenticated | Your reverse proxy / firewall / PaaS |

> The origin IP is not a secret. It leaks through TLS-certificate logs, `*.sslip.io`-style
> hostnames, historical DNS, mail headers, and scan databases. Treat "nobody knows the IP" as
> false.

## Prerequisites

- A zone on Cloudflare (the domain's nameservers point at Cloudflare).
- Zero Trust onboarded on the account, which fixes the **team domain**
  `https://<team-name>.cloudflareaccess.com`. The name is chosen once and is globally unique — a
  taken name returns `auth_domain_not_available`.
- An API token, **account-scoped** (there are no zone-scoped Access permissions):

  | Permission | Needed for |
  |---|---|
  | Account → Access: Apps and Policies → Edit | Create the app and the reusable policy |
  | Account → Access: Organizations, Identity Providers, and Groups → Edit | Create the Google IdP (narrower: Access: Identity Providers Edit) |
  | Zone → DNS → Edit | Flip the record to proxied |

  Labels drift between "Edit" and "Write" in the docs; confirm against the account's permission
  groups if a create call returns 403.
- Shell access to the reverse proxy or firewall in front of the origin.

```bash
export CF_API_TOKEN="$(cat ~/.secrets/cf_access_token)"   # never inline the literal
export CF_ACCOUNT_ID="…"                                  # from the dashboard URL
export CF_ZONE_ID="…"
```

## Workflow

### 1. Establish the team domain

If Zero Trust has never been set up on the account, onboarding is dashboard-only: it asks for a
team name and a plan (Free covers 50 seats but still asks for payment details without charging).
Record `<team-name>` — the Google redirect URI in step 2 depends on it and cannot be guessed.

Agent has no browser? See `references/dashboard-via-ego-browser.md` for driving the console.

### 2. Create the Google OAuth client, then the Cloudflare IdP

Google Cloud Console is dashboard-only. The one value that must be exact:

```
https://<team-name>.cloudflareaccess.com/cdn-cgi/access/callback
```

Then register it with Cloudflare:

```bash
curl -sX POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/access/identity_providers" \
  -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
  -d "{\"name\":\"Google\",\"type\":\"google\",
       \"config\":{\"client_id\":\"$GOOGLE_CLIENT_ID\",\"client_secret\":\"$GOOGLE_CLIENT_SECRET\"}}"
```

Read `references/google-oauth-idp.md` before doing this. It covers the consent-screen trap that
costs the most debugging time: a project in **Testing** mode only lets listed test users complete
Google login, and the failure surfaces as a *Google* error before Cloudflare is ever reached — so
it looks nothing like an Access problem.

Also add **Email one-time PIN** as a second IdP. It is not subject to the Google test-user list and
is the escape hatch when Google-side configuration breaks.

### 3. Create the reusable policy, then the application

Order matters — the policy is a standalone object and the app links it by id.

```bash
POLICY_ID=$(curl -sX POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/access/policies" \
  -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Allow example.com email domain","decision":"allow",
       "include":[{"email_domain":{"domain":"example.com"}}]}' | jq -r '.result.id')

curl -sX POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/access/apps" \
  -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
  -d "{\"name\":\"Internal Dashboard\",\"domain\":\"app.example.com\",\"type\":\"self_hosted\",
       \"session_duration\":\"24h\",\"auto_redirect_to_identity\":false,
       \"policies\":[{\"id\":\"$POLICY_ID\",\"precedence\":1}]}"
```

`references/api-recipes.md` has the full set: include/require/exclude selectors, multi-hostname
apps, service tokens for CI, bypass-path carve-outs, and how to migrate a legacy `reusable: false`
policy with `make_reusable`.

> Field names on this API change between versions. Before scripting anything beyond the shapes
> above, read the current schema rather than trusting an example — including this one.

### 4. Put the hostname behind the proxy

```bash
curl -sX PATCH "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"proxied":true}'
```

If the origin terminates TLS with its own certificate (Let's Encrypt via Traefik/Caddy/nginx), the
zone's SSL mode must be **Full** or **Full (strict)**. Flexible causes a redirect loop.

### 5. Lock the origin

This is the step every comparable guide omits, and the reason a "protected" app is often still
open. Verify the bypass exists *before* fixing it so you know the fix did something:

```bash
curl -skI --resolve app.example.com:443:<origin-ip> https://app.example.com/ | head -1
# HTTP/2 200 here means Access is bypassable right now
```

Then apply at least one of — ideally both — the IP allowlist and origin token validation, from
`references/origin-lockdown.md`. It has ready configs for Traefik v3 (`ipallowlist`, note the v2
spelling changed), nginx, Caddy, and cloud firewalls, plus the JWT-validation pattern
(`CF-Access-Jwt-Assertion` verified against the team JWKS), and the PaaS hazard where a
control-plane redeploy regenerates router labels and silently detaches the middleware.

Never paste a static IP list. Fetch it:

```bash
curl -s https://api.cloudflare.com/client/v4/ips | jq -r '.result.ipv4_cidrs[], .result.ipv6_cidrs[]'
```

### 6. Verify — all four checks, or it is not done

| # | Check | Expected |
|---|---|---|
| 1 | `curl -sI https://app.example.com/` | 302 to `<team-name>.cloudflareaccess.com` |
| 2 | `curl -skI --resolve app.example.com:443:<origin-ip> https://app.example.com/` | 403 (was 200) |
| 3 | Log in with an in-domain identity | reaches the app |
| 4 | Log in with an out-of-domain identity | "That account does not have access." |

Check 4 is the one people skip, and it is the only one that proves the *policy* works rather than
the login page rendering. Run the full matrix in `references/verification-matrix.md`, which also
covers other hostnames on the same proxy (regression check) and HTTP :80.

### 7. Write down what is not in git

The Access app, the policy, the IdP, and the DNS proxy flag live in Cloudflare's control plane.
The origin allowlist may live in a PaaS database rather than your repo. Record, in the repo's
`AGENTS.md`/`README.md`: the three parts, which one lives where, how to re-attach the origin
middleware, and how a new employee gets added. Use **names and locations, never values**.

## Credential hygiene (non-negotiable)

This workflow handles an OAuth client secret, an API token, and possibly service-token secrets.

- Read secrets from env vars or a secret manager. Never inline a literal into a command you run,
  a file you write, or a report you print.
- When writing examples or docs, show the *reference* (`$GOOGLE_CLIENT_SECRET`,
  `~/.secrets/cf_token`) or the generation step (`openssl rand -hex 32`), never a value.
- Account IDs, zone IDs, application/policy/IdP UUIDs, team names, and origin IPs are not
  passwords, but they are targeting information — keep them out of anything public. Use
  `example.com`, `app.example.com`, `<team-name>`, `<origin-ip>`.
- Scope the API token to the three permissions above. Do not reuse a Global API Key.
- The Google client secret cannot be re-read after creation. If it is lost, add a new secret on the
  client and update the Cloudflare IdP — do not recreate the client, which would invalidate the
  redirect URI you already registered.
- Before committing anything produced here, grep the diff for `sk-`, `GOCSPX-`, `Bearer `,
  `gho_`/`ghp_`, and 32-hex account-id shapes.

## Failure quick-reference

| Symptom | Cause | Fix |
|---|---|---|
| App loads with no login prompt | DNS record is grey-cloud, or the client hit the origin directly | Set `proxied: true`; then do step 5 |
| Everything 403s after enabling Access | Deny-by-default with no matching Allow policy | Attach a reusable Allow policy to the app |
| Redirect loop on the hostname | Zone SSL mode is Flexible against a TLS origin | Set SSL mode to Full |
| Google login fails *before* Cloudflare, with a Google error page | Consent screen in Testing mode; the user is not a listed test user | Add the test user, or publish the app — see `references/google-oauth-idp.md` |
| `redirect_uri_mismatch` | Redirect URI does not exactly match the team domain callback | Use `https://<team-name>.cloudflareaccess.com/cdn-cgi/access/callback` |
| "That account does not have access." | Identity authenticated but failed the policy | Working as intended — confirm the account's email domain |
| Policy edits do not take effect | Editing a legacy `reusable: false` app-scoped policy | Migrate with `make_reusable`, or replace with a reusable policy |
| Origin 403s Cloudflare too | Allowlist missing current Cloudflare ranges, or proxy reads the wrong client IP | Refetch `/client/v4/ips`; check the proxy's trusted-proxy / real-IP config |
| Bypass reopens after a deploy | PaaS regenerated router labels and dropped the middleware | See the split-brain section in `references/origin-lockdown.md` |
| `auth_domain_not_available` | Team name already taken globally | Pick another; it is one-time and hard to change |

## Recommended: install ego-browser

Two steps here are genuinely dashboard-only — Zero Trust onboarding/team-domain selection, and
Google Cloud Console OAuth-client creation. An agent with a real browser can finish the job instead
of handing you a checklist.

**ego-browser** (from [ego lite](https://lite.ego.app/)) is a Chromium built for agents: it runs
agent work in an isolated task space that reuses your existing login state, so it can drive the
Cloudflare and Google consoles as *you* without taking over your browser windows, and it hands
control back for the parts you must click yourself.

- Skill:
  [`citrolabs/ego-lite → skills/ego-browser/SKILL.md`](https://github.com/citrolabs/ego-lite/blob/main/skills/ego-browser/SKILL.md)
- Install: run the skill's `scripts/install.sh` (macOS), finish onboarding once, then
  `command -v ego-browser`.

Read `references/dashboard-via-ego-browser.md` for the console flows, the credential rules that
apply when a browser session is holding your real logins, and when to hand control back.

## Reference routing

| File | Read when |
|---|---|
| `references/google-oauth-idp.md` | Creating the Google OAuth client, choosing Testing vs Published / Internal vs External, adding test users, rotating the secret, or debugging a Google-side login failure. |
| `references/api-recipes.md` | Writing any Cloudflare API call beyond the three in this file — selectors, multi-hostname apps, service tokens, bypass paths, `make_reusable`, listing and auditing existing objects. |
| `references/origin-lockdown.md` | Step 5. Traefik/nginx/Caddy/cloud-firewall allowlists, JWT validation at the origin, PaaS label split-brain, and keeping IP ranges fresh. |
| `references/verification-matrix.md` | Step 6, or auditing an Access setup someone else built. Full check matrix plus what each failure means. |
| `references/dashboard-via-ego-browser.md` | A step is dashboard-only, or you want an agent to drive the Cloudflare/Google consoles with ego-browser. |

## Guardrails

- Do not declare the subdomain protected until check 2 in step 6 returns 403. A login page proves
  nothing on its own.
- Do not create app-scoped (`reusable: false`) policies.
- Do not disable one of the three parts to "simplify" — each one alone is not a control.
- Do not paste a hardcoded Cloudflare IP list; fetch it and re-fetch it periodically.
- Do not publish a Google OAuth consent screen without checking what else lives in that GCP
  project — publishing is project-wide and can pull unrelated clients into verification.
- Do not print, log, or commit a secret value at any point in this workflow.
