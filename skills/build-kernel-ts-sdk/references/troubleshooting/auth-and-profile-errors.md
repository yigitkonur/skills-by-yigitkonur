# Auth and profile errors

Errors specific to Managed Auth, profiles, credentials, and credential providers — and how to diagnose them.

## 409 Conflict on `auth.connections.create`

**Symptom:** `Kernel.ConflictError` thrown when calling `auth.connections.create({ domain, profile_name, … })`.

**Cause:** A connection with the same `(domain, profile_name)` already exists. Connections are unique per pair.

**Fix — three options:**

```ts
// (a) Reuse the existing connection
const existing = await kernel.auth.connections.list({ domain, profile_name });
const conn = existing.items[0];

// (b) Pick a different profile_name
const conn = await kernel.auth.connections.create({ domain, profile_name: `${profile_name}-v2` });

// (c) Delete the old one first (loses prior auth state)
const old = (await kernel.auth.connections.list({ domain, profile_name })).items[0];
if (old) await kernel.auth.connections.delete(old.id);
const conn = await kernel.auth.connections.create({ domain, profile_name });
```

## Connection stuck in `IN_PROGRESS`

**Symptom:** `flow_status` never transitions out of `IN_PROGRESS`. Polling forever.

**Causes and fixes:**

| Cause | Fix |
|---|---|
| User abandoned the Hosted UI tab | Add a hard timeout in your poll loop; on expiry, `kernel.auth.connections.delete(id)` and prompt the user to retry. |
| User is at an `AWAITING_EXTERNAL_ACTION` step (push, security key) | Show `external_action_message` explicitly. Users assume the page is broken if they can't see the prompt. |
| Site changed login flow; field discovery failed | `flow_step` stays at `DISCOVERING` (unverified). Check `timeline(id)` and contact Kernel support with the connection `id`. |
| Programmatic flow waiting on `submit` | Submit one `field_values` or `selected_choice_id` per `interaction_id` when `flow_step` is `AWAITING_INPUT` (or `AWAITING_EXTERNAL_ACTION` with fallback `fields` / `choices`). Stale ids are rejected. |
| Your code called `login()` again | A new `login` cancels the flow in progress. Continue the original flow through its `hosted_url`; call `login` again only after a terminal status. |

## Connection terminal but `status === 'NEEDS_AUTH'`

**Symptom:** `flow_status === 'SUCCESS'` (or a task after a successful login) but a launched browser shows the login page.

**Causes and fixes:**

| Cause | Fix |
|---|---|
| `status` lags (it reflects the latest completed health check) | Call `login(id)` and `follow` it; a still-signed-in profile reaches `SUCCESS` without prompting (`ensureAuthenticated` in [managed-auth.md](../guides/managed-auth.md)). |
| Browser started before the login or re-auth finished | A running browser keeps the profile snapshot it started with; start a new browser with the same `profile.name`. |
| Flow ended `FAILED`, `EXPIRED` or `CANCELED` | The profile is unchanged. Read `error_code` / `error_message` (below) and `timeline(id)`, then start a new `login`. |
| `profile.name` differs from the connection's `profile_name` | Use the exact `profile_name` from the connection. |

**Failure `error_code` fixes:**

| Code | Fix |
|---|---|
| `credentials_invalid`, `totp_code_rejected` | Update the linked credential or secret, then `login`. |
| `totp_required`, `sms_code_required`, `email_code_required`, `account_choice_required`, `customer_input_required`, `external_action_required` | Start an interactive login and supply the code, choice or approval; add `totp_secret` to the credential to automate authenticator codes. |
| `account_locked` | Unlock on the site; calling `login` again can extend the lockout. |
| `unsupported_auth_method` | Passkey-only is unsupported; switch the account to password + TOTP. |
| `rate_limited`, `website_error` | Wait for the site's retry window; check `login_url`. |
| `bot_detected`, `captcha_blocked` | Pin an ISP or custom proxy on the connection, not on `browsers.create`: `await kernel.auth.connections.update(conn.id, { browser: { proxy: { id: isp.id } } })`, then `login` again. Login, health-check and re-auth browsers are launched by Managed Auth, so the proxy and `browser.stealth` (default true) are connection settings. |

Note: `<KernelManagedAuth />` renders native DOM directly on the host origin, never an iframe, so anti-iframe policies (`X-Frame-Options` or CSP `frame-ancestors`) never apply.

## Hosted-page handoff `code` expired

**Symptom:** Loading the embedded `<KernelManagedAuth />` (or hitting `hosted_url` directly) returns "session expired".

**Cause:** Per kernel.sh/docs/auth/hosted-ui, the hosted login session expires after **20 minutes** total, and the flow times out after **10 minutes** of user inactivity. If the user lingers, copies the URL, or you cache the response, the handoff dies.

**Fix:** Once the flow is terminal (`EXPIRED`, `CANCELED`, `FAILED`), call `kernel.auth.connections.login(id)` for a fresh `hosted_url` and `handoff_code`, then re-mount the React component or redirect again. `login` cancels any flow still in progress, so do not call it to "refresh" a live flow. Don't cache the `hosted_url` longer than the 10-minute idle window.

## React component does not render

**Symptom:** Blank page where `<KernelManagedAuth />` should be. Console errors about `useState`/`useEffect` on the server.

**Cause:** The component is **client-only**. In Next.js App Router (or any RSC-enabled framework), the file must opt out of server rendering.

**Fix:**

```tsx
'use client';                     // FIRST line of the file

import { KernelManagedAuth } from '@onkernel/managed-auth-react';
// …
```

## React component blocked by your CSP

**Symptom:** `connect-src` CSP violations in the console on requests to `https://api.onkernel.com`, and the flow stalls at the consent or discovery step.

**Cause:** `<KernelManagedAuth />` does **not** render an iframe — it renders native DOM on your own origin, so `X-Frame-Options` and `frame-ancestors` are never involved. It does call the Kernel API cross-origin by default (`baseUrl` defaults to `https://api.onkernel.com`), and your own `connect-src` policy can block that.

**Fix — either:**

1. Allow `https://api.onkernel.com` in your `connect-src` directive; or
2. Keep auth traffic same-origin: pass `baseUrl=""` and proxy the endpoints the package hits through your framework's rewrites.

```tsx
<KernelManagedAuth sessionId={id} handoffCode={code} baseUrl="" {...rest} />
```

The `rewrites()` block in `node_modules/@onkernel/managed-auth-react/README.md` (0.5.5) covers the four endpoints the component calls: `POST /auth/connections/:id/exchange`, `GET /auth/connections/:id`, `POST /auth/connections/:id/submit`, `GET /auth/connections/:id/events` (the SSE progress stream, `Accept: text/event-stream`). Proxy all four; a single-segment `:id` rewrite does not match `/events`.

## Profile not found at `browsers.create`

**Symptom:** `browsers.create({ profile: { name: 'foo' } })` errors with profile-not-found, or the browser launches without authenticated state.

**Causes and fixes:**

| Cause | Fix |
|---|---|
| Profile was never created | Either `kernel.profiles.create({ name: 'foo' })` first, or rely on `auth.connections.create({ profile_name: 'foo' })` to create it implicitly. |
| Profile name typo | `profiles.list({ name })` is an exact match using the database collation (case- and accent-insensitive in production). Names are 1-255 characters of letters, numbers, `.`, `_`, `-`. |
| Connection completed, but `status === 'NEEDS_AUTH'` | The profile exists but has no auth state. Re-run the auth flow. |
| Profile was deleted | `kernel.profiles.list()` to confirm; recreate and re-auth. |

## Credentials provisioning silently failed

**Symptom:** `kernel.credentials.create` returns success, but flows never auto-populate fields.

**Causes and fixes:**

| Cause | Fix |
|---|---|
| Credential not linked | Link by name: `auth.connections.create({ ..., credential: { name } })`. The credential's `domain` need not equal the connection's (an SSO credential uses the identity provider's domain, e.g. `accounts.google.com`); domain auto-matching applies only to external providers (`credential: { provider, auto: true }`). |
| Field names don't match the form | `retrieve(id).fields` (`ManagedAuth.Field`: `id`, `ref`, `type`, `reason`) shows what the site is asking for; rename your `values` keys to match. |
| Wrong `sso_provider` or no `totp_secret` for 2FA-protected accounts | `fields` returned by `auth.connections.retrieve` will reveal what is missing; fill it in. A code the user supplied once does not give Kernel future codes. |

## 1Password provider returns no items

**Symptom:** `kernel.credentialProviders.listItems(id)` is empty, or `auth.connections.create({ credential: { provider, auto: true } })` does not auto-match.

**Causes and fixes:**

| Cause | Fix |
|---|---|
| Service-account token has no vault access | Recreate the service account with read-only access to the relevant vaults. |
| 1Password Login items don't have a `website` URL set | Add the website URL to each Login item; auto-match relies on it. `*.example.com` item URLs match subdomains. If several items match a domain, the first match is used. |
| Vault or item names contain `/`, or the login uses a linked "sign in with" reference | Unsupported by the provider; rename the vault or item, or store a direct login. |
| Token expired | `kernel.credentialProviders.test(id)` will surface auth errors; rotate the token. |

## Where to look next

- Hosted UI vs Programmatic decision: `references/guides/managed-auth.md`
- Profile and pool composition patterns: `references/patterns/profiles-pools-credentials.md`
- General error handling and `Kernel.APIError` taxonomy: `references/guides/client-and-config.md`
