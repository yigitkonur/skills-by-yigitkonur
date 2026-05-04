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
| User is at an `AWAITING_EXTERNAL_ACTION` step (push, security key) | Show that explicitly — `flow_step === 'AWAITING_EXTERNAL_ACTION'`. Users assume the page is broken if they can't see the prompt. |
| Site changed login flow; field discovery failed | `flow_step` stays at `DISCOVERING`. Open a support ticket with the connection `id`. |
| Programmatic flow waiting on `submit` | Verify your code submits values when `flow_step === 'AWAITING_INPUT'`. |

## Connection terminal but `status === 'NEEDS_AUTH'`

**Symptom:** `flow_status === 'SUCCESS'` but launching a browser shows the login page.

**Cause:** The flow completed without persisting an authenticated session — usually a captcha or anti-bot redirect that returned a "login successful" page without actually logging in.

**Fix:**

1. `kernel.auth.connections.retrieve(id)` and check `status` directly — if `NEEDS_AUTH`, re-run the flow.
2. Switch to a residential proxy: `kernel.proxies.create({ type: 'residential', name: 'res-1' })` then pass `proxy_id` on `browsers.create`.
3. Use a long-lived profile so the next attempt builds on prior browsing history.
4. Consider Programmatic flow if Hosted UI is being blocked by anti-iframe policies.

## Hosted-page handoff `code` expired

**Symptom:** Loading the embedded `<KernelManagedAuth />` (or hitting `hosted_url` directly) returns "session expired".

**Cause:** Per kernel.sh/docs/auth/hosted-ui, the hosted login session expires after **20 minutes** total, and the flow times out after **10 minutes** of user inactivity. If the user lingers, copies the URL, or you cache the response, the handoff dies.

**Fix:** Re-call `kernel.auth.connections.login(id)` to get a fresh `hosted_url` (and embedded `code`). Then re-mount the React component or redirect again. Don't cache the `hosted_url` longer than the 10-minute idle window.

## React component does not render

**Symptom:** Blank page where `<KernelManagedAuth />` should be. Console errors about `useState`/`useEffect` on the server.

**Cause:** The component is **client-only**. In Next.js App Router (or any RSC-enabled framework), the file must opt out of server rendering.

**Fix:**

```tsx
'use client';                     // FIRST line of the file

import { KernelManagedAuth } from '@onkernel/managed-auth-react';
// …
```

## React component CSP / iframe issues

**Symptom:** The component renders an iframe that fails to load due to CSP or X-Frame-Options.

**Fix:** Configure same-origin proxying with Next rewrites and pass `baseUrl=""` (relative) to the component so the iframe loads from your domain instead of Kernel's origin. Confirm with your CSP allow-list before shipping.

## Profile not found at `browsers.create`

**Symptom:** `browsers.create({ profile: { name: 'foo' } })` errors with profile-not-found, or the browser launches without authenticated state.

**Causes and fixes:**

| Cause | Fix |
|---|---|
| Profile was never created | Either `kernel.profiles.create({ name: 'foo' })` first, or rely on `auth.connections.create({ profile_name: 'foo' })` to create it implicitly. |
| Profile name typo / case mismatch | Profile names are case-sensitive. Echo the exact string from `profiles.list()`. |
| Connection completed, but `status === 'NEEDS_AUTH'` | The profile exists but has no auth state. Re-run the auth flow. |
| Profile was deleted | `kernel.profiles.list()` to confirm; recreate and re-auth. |

## Credentials provisioning silently failed

**Symptom:** `kernel.credentials.create` returns success, but flows never auto-populate fields.

**Causes and fixes:**

| Cause | Fix |
|---|---|
| `domain` mismatch | Credentials are matched on `domain` — check it matches the auth-flow domain exactly. |
| Field names don't match the form | `discovered_fields` in the programmatic flow shows what the site actually wants; rename your `values` keys to match. |
| Wrong `sso_provider` or no `totp_secret` for 2FA-protected accounts | `discovered_fields` will reveal what's missing; fill it in. |

## 1Password provider returns no items

**Symptom:** `kernel.credentialProviders.listItems(id)` is empty, or `auth.connections.create({ credential: { provider, auto: true } })` does not auto-match.

**Causes and fixes:**

| Cause | Fix |
|---|---|
| Service-account token has no vault access | Recreate the service account with read-only access to the relevant vaults. |
| 1Password Login items don't have a `website` URL set | Add the website URL to each Login item — auto-match relies on it. |
| Token expired | `kernel.credentialProviders.test(id)` will surface auth errors; rotate the token. |

## Where to look next

- Hosted UI vs Programmatic decision: `references/guides/managed-auth.md`
- Profile and pool composition patterns: `references/patterns/profiles-pools-credentials.md`
- General error handling and `Kernel.APIError` taxonomy: `references/guides/client-and-config.md`
