# Managed Auth

Kernel **Managed Auth** lets a Kernel browser log into a third-party SaaS on behalf of an end-user. Two flow shapes share the same `kernel.auth.connections.*` SDK surface; pick one early.

Source note: Verified against `@onkernel/sdk@0.123.0` types, `@onkernel/managed-auth-react@0.5.5` types (peer deps react/react-dom >= 18), and Kernel docs in October 2026.

Kernel has two auth paths: **Managed Auth** (Kernel runs the login in its own browser, saves state to a profile, health-checks and re-auths) and **Fill from Vault / Fill from Managed Auth** (your app or agent drives the login in its own browser and Kernel only writes stored values into fields; see [vaults-and-payments.md](../patterns/vaults-and-payments.md)). Use Managed Auth for unattended or recurring logins; use fill when the user is present and your workflow must own navigation, submission and recovery.

## Flow shapes

| | Hosted UI | Programmatic |
|---|---|---|
| Where credentials are entered | Kernel-hosted page (or `<KernelManagedAuth />` embed on your domain) | Your own UI |
| What you write | Backend `create` + `login`; frontend `redirect` (or embed) | Backend `create` + `login` + `follow` + `submit`; you build the input UI |
| MFA / SSO support | Built in | You render `choices` / `fields` from the event and submit one interaction at a time |
| When to pick | Default: fastest to ship, covers SSO, 2FA, security keys | You need design control, headless flows, or you already store credentials and only want to answer what Kernel cannot resolve |

## SDK surface

| Method | Purpose |
|---|---|
| `kernel.auth.connections.create({ domain, profile_name, login_url?, allowed_domains?, save_credentials?, credential?, health_checks?, health_check_interval?, auto_reauth?, record_session?, browser? })` | Create a connection scoping a `domain` to a browser `profile_name` (the profile is created if missing). `health_checks` and `auto_reauth` default to **true**; see the cost note below. |
| `kernel.auth.connections.login(id, { browser?, record_session?, skill_mode?, browser_telemetry?, proxy? })` | Start a login session; returns `hosted_url`, `handoff_code?`, `flow_type` (`LOGIN` \| `REAUTH`), `flow_expires_at`, `live_view_url?`. A new `login` call **cancels** a flow already in progress. |
| `kernel.auth.connections.retrieve(id)` | Current `flow_status`, `flow_step`, connection `status`, `interaction_id`, `can_reauth` / `can_reauth_reason`, `post_login_url`, and `fields` / `choices` (plus legacy `discovered_fields`, `pending_sso_buttons`, `mfa_options`, `sign_in_options`). |
| `kernel.auth.connections.submit(id, { interaction_id, field_values?, selected_choice_id?, ... })` | Programmatic only. Canonical submits need `interaction_id` (SDK v0.93.0+) and **either** `field_values` (keyed by `Field.id`) **or** `selected_choice_id` (a `Choice.id`). Legacy params (`fields`, `sso_provider`, `mfa_option_id`, `sign_in_option_id`, `sso_button_selector`) work only when `choices` / `fields` are absent. |
| `kernel.auth.connections.update(id, { login_url?, credential?, allowed_domains?, health_check_interval?, health_checks?, auto_reauth?, save_credentials?, record_session?, browser? })` | Edit a connection; `health_check_interval`, `health_checks`, `auto_reauth` and the browser proxy take effect immediately. |
| `kernel.auth.connections.list({ domain?, profile_name?, query? })` / `delete(id)` | Standard list (offset-paginated `.items`) and delete. |
| `kernel.auth.connections.follow(id)` | SSE stream of state events; closes when the flow reaches a terminal status. |
| `kernel.auth.connections.timeline(id, { type?: 'login' \| 'reauth' \| 'health_check' })` | Paginated, newest-first history. First stop when a connection keeps flipping to `NEEDS_AUTH`. |

`kernel.auth.context.retrieve()` reports the caller's principal, organization, and `authorization.credential_scope` / `effective_scope` project ids.

**The `follow()` stream is a union.** Events are `managed_auth_state` (carries `flow_status`, `flow_step`, `fields`, `choices`, `interaction_id`, `external_action_message`, `error_code`, `error_message`, `post_login_url`), `error` (`ev.error.code` / `ev.error.message`) and `sse_heartbeat`. Always narrow on `ev.event` before reading flow fields.

**Cost and re-auth defaults.** `health_checks` defaults to **true**: Kernel runs a background browser session against the target site on `health_check_interval` (default 3600 s or your plan minimum, whichever is larger; minimum Enterprise 300 / Startup 1200 / Hobbyist 3600 / Free 21600 (the pricing page calls the free plan Developer); max 86400) for the life of the connection. Managed Auth has no per-connection fee but these sessions count toward browser usage and concurrency (about 5-30 s each). Pass `health_checks: false` for one-shot connections. Connections with no check URL show as `Unverified` (`health_check_unavailable_reason: 'no_auth_check_url'`). `auto_reauth` also defaults to true but is a **no-op when `health_checks: false`**, because re-auth only fires after a failed scheduled health check. Plan caps: `organization.limits.retrieve()` returns `max_auth_connections` / `auth_connections_used`; creating past the cap is rejected with `403 insufficient_plan` (Developer plan: 3 connections).

`browser` (`ManagedAuthBrowserConfig`) holds the browser settings for login, re-auth and health-check sessions: `proxy` (typed `{ id } | { name } | { mode }`), `telemetry`, `stealth` (defaults true; `false` skips stealth mode and the CAPTCHA solver), and `region` (`'us-east' | 'us-west' | 'eu-west' | 'ap-southeast'` in the SDK types; docs list only `us-east`, `eu-west`, `ap-southeast`; non-default regions need Start-Up/Enterprise and org access). Top-level `proxy`, `proxy_id` and `browser_telemetry` on create/update/login are `@deprecated` in favor of `browser.proxy` / `browser.telemetry`. Region changes apply to browsers created afterward; a per-login `browser` override applies to that login only.

`auth.connections.create` returns 409 if a connection with the same `domain` + `profile_name` already exists. Reuse it (`list({ domain, profile_name })`) or pick a different `profile_name`. Profile names are 1-255 characters of letters, numbers, `.`, `_`, `-` (`BrowserProfile.name`), so do not build `profile_name` from raw emails.

## States

**`flow_status`:** `IN_PROGRESS` | `SUCCESS` | `FAILED` | `EXPIRED` | `CANCELED`. Anything other than `IN_PROGRESS` is terminal. On `FAILED`, read `error_code` / `error_message`.

**`flow_step`:** `DISCOVERING`, `AWAITING_INPUT`, `AWAITING_EXTERNAL_ACTION` (push approval / hardware key), `SUBMITTING`, `COMPLETED`. The flow can move between these in any order and revisit `AWAITING_INPUT`; branch on the current `flow_step`.

**Connection `status`:** `AUTHENTICATED` (browsers using `profile_name` are ready) | `NEEDS_AUTH` (re-auth required). It reflects the latest completed health check, so it can lag the real session. `conn.can_reauth` says whether an unattended attempt is eligible, not whether it will succeed; `conn.can_reauth_reason` is one of 17 values: 8 affirmative (`'external_credential'`, `'cua_has_credential'`, `'has_credential'`, `'viable_plans_found'`, `'no_requirements_recorded'`, `'totp_reauth_allowed'`, `'optimistic_totp_attempt'`, `'requirements_satisfiable'`) and 9 blockers (`'no_prior_successful_login'`, `'no_credential'`, `'no_viable_plans'`, `'viable_plans_require_external_action'`, `'requires_external_action'`, `'requires_totp_without_secret'`, `'requires_sms_code'`, `'requires_email_code'`, `'requires_customer_input'`).

**Dashboard reauthentication status tiers** (display labels only, not API fields; the docs changelog names them but does not define them, so read `can_reauth` / `can_reauth_reason` in code):
- `Auto`, `Best effort` (depends on an optimistic TOTP retry), `Needs human`.
- `Unverified`: the health check was skipped because no check URL is set.

**Failure `error_code`s** (login, health-check re-auth, manual `login`):

| Code | Retried by Kernel | Recovery |
|---|---|---|
| `credentials_invalid` | No | Update the linked credential, call `login`; interactive logins ask for the rejected field again |
| `totp_code_rejected` | No | Retry with a code from a new window; reconnect and update the secret if fresh codes keep failing |
| `totp_required` / `sms_code_required` / `email_code_required` | No | Start an interactive login and supply the code; add `totp_secret` to make authenticator codes automatic |
| `account_choice_required` / `customer_input_required` / `external_action_required` | No | Interactive login: pick, fill or approve |
| `account_locked` | No | Unlock on the site; calling `login` again can extend the lockout |
| `unsupported_auth_method` | No | Passkey-only is unsupported; switch the account to password + TOTP |
| `rate_limited` | No | Wait for the site's retry window |
| `website_error` | Once | Retry later; check `login_url` |
| `bot_detected` / `captcha_blocked` | No | Pin an ISP or custom proxy on the connection's `browser.proxy` |

## Hosted UI: the simple path

```ts
// 1. Backend route: POST /api/auth/connect
import Kernel from '@onkernel/sdk';
const kernel = new Kernel();

const conn = await kernel.auth.connections.create({
  domain: 'netflix.com',
  profile_name: `netflix-${userId}`,
  save_credentials: true,                  // default true; false opts out of credential capture
});

const login = await kernel.auth.connections.login(conn.id);
if (!login.handoff_code) throw new Error('missing managed-auth handoff_code');

// Return the connection id plus login-session fields. Never expose KERNEL_API_KEY.
return Response.json({
  connectionId: conn.id,
  profileName: `netflix-${userId}`,
  hostedUrl: login.hosted_url,
  handoffCode: login.handoff_code,
  flowExpiresAt: login.flow_expires_at,
});
```

```ts
// 2. Frontend: redirect or embed
window.location.href = hostedUrl;           // simplest: redirect away

// OR embed Kernel's login UI in your own page:
//   import { KernelManagedAuth } from '@onkernel/managed-auth-react';
//   Required props: sessionId={connectionId} and handoffCode={handoffCode}.
//   Optional: appearance, localization, onSuccess, onError, baseUrl, fetch.
//   See `references/examples/managed-auth-flow.md` for the full embed pattern.
```

To bounce the user back to your app, append `success_url` and/or `error_url` query params to `hosted_url` (any scheme, e.g. `myapp://auth/done`). `success_url` gets `profile_name` and `domain` appended; `error_url` gets `code` (when present) and `message`. Set them only from your trusted backend; the hosted page redirects to whatever URL it is given.

```ts
// 3. Backend: follow events until terminal, then launch a browser
for await (const ev of await kernel.auth.connections.follow(conn.id)) {
  if (ev.event === 'error') throw new Error(ev.error.message);
  if (ev.event !== 'managed_auth_state') continue;   // skip sse_heartbeat
  if (ev.flow_status !== 'IN_PROGRESS') break;       // SUCCESS | FAILED | EXPIRED | CANCELED
}
const state = await kernel.auth.connections.retrieve(conn.id);
if (state.status !== 'AUTHENTICATED') {
  throw new Error(`auth ${state.flow_status}: ${state.error_code ?? 'unknown'}`);
}
// state.post_login_url is the page the login landed on.

// Any browser launched with this profile_name is now logged in.
const session = await kernel.browsers.create({
  profile: { name: `netflix-${userId}` },
  stealth: true,
});
```

The hosted session expires after 20 minutes; the flow times out after 10 minutes of waiting for user input. The SSE stream closes on success, failure, expiry or cancel. Prefer `follow()` over polling `retrieve`.

Security and lifecycle rules:

- Never expose `KERNEL_API_KEY` to the browser or React component.
- Treat `handoff_code` as short-lived and single-use; call `login` again for a fresh one (this cancels the previous flow).
- Distinguish the connection id (`conn.id`) from login-session fields (`hosted_url`, `handoff_code`, `flow_expires_at`, `live_view_url`).
- Store only stable ids needed later: connection id and profile name. Do not persist handoff codes or raw credentials.
- Finish reports must include connection id, profile name, final `flow_status`/`status`, and any browser `session_id` launched from the profile.

## Programmatic: your own UI

Follow the connection's SSE stream, render the canonical `fields` and `choices`, and submit **one** interaction at a time. Every actionable pause has a new `interaction_id`; stale ids are rejected.

```ts
declare function collectFromUser(
  fields: { id: string; ref: string; type: string; label?: string; hint?: string; reason: 'missing' | 'rejected' }[],
): Promise<Record<string, string>>;
declare function pickChoice(
  choices: { id: string; label: string; type: string; masked_destination?: string | null; description?: string | null }[],
): Promise<{ id: string }>;
declare function showUser(message: string): void;

const conn = await kernel.auth.connections.create({
  domain: 'example.com',
  profile_name: `user-${userId}`,
});
await kernel.auth.connections.login(conn.id);

for await (const ev of await kernel.auth.connections.follow(conn.id)) {
  if (ev.event === 'error') throw new Error(ev.error.message);
  if (ev.event !== 'managed_auth_state') continue;
  if (ev.flow_status === 'FAILED') throw new Error(`${ev.error_code}: ${ev.error_message}`);
  if (ev.flow_step === 'AWAITING_EXTERNAL_ACTION') {
    showUser(ev.external_action_message ?? 'Approve the request on your device');
  }
  // External-action screens can also carry fallback fields/choices; they use the same contract.
  if (!ev.interaction_id || (ev.flow_step !== 'AWAITING_INPUT' && ev.flow_step !== 'AWAITING_EXTERNAL_ACTION')) continue;

  if (ev.fields?.length) {
    // Field: { id, ref, type: 'identifier'|'password'|'code'|'totp_code'|'totp_secret'|'text',
    //          reason: 'missing'|'rejected', label?, hint?, required?, input_mode?, observed_selector? }
    // reason === 'rejected': the site refused the previous value; ask for a corrected one.
    const field_values = await collectFromUser(ev.fields);   // Field.id -> value
    await kernel.auth.connections.submit(conn.id, { interaction_id: ev.interaction_id, field_values });
  } else if (ev.choices?.length) {
    // Choice: { id, label, type: 'mfa_method'|'sso_provider'|'sign_in_method'|'auth_method'|
    //           'identifier_method'|'account'|'other', mfa_type?, masked_destination?, description? }
    // Submit the exact id: two choices can share a type (e.g. two SMS destinations).
    const choice = await pickChoice(ev.choices);
    await kernel.auth.connections.submit(conn.id, { interaction_id: ev.interaction_id, selected_choice_id: choice.id });
  }
}
```

Submit `field_values` **or** `selected_choice_id` per `interaction_id`, never both. Legacy submit params apply only when the event has no `fields` / `choices`: `mfa_option_id` (the option's `type`), `sign_in_option_id`, `sso_provider`, `sso_button_selector`. Unattended re-auth never asks for a corrected credential; it reports the terminal rejection (`credentials_invalid`, `totp_code_rejected`).

## Verify before starting work

`status` can be stale. Before a task that needs the account, call `login` (it runs the verifier first when the connection has a previous successful login and a saved check URL; a still-signed-in profile reaches `SUCCESS` without prompting) and follow it:

```ts
async function ensureAuthenticated(connectionId: string): Promise<void> {
  const login = await kernel.auth.connections.login(connectionId);
  for await (const ev of await kernel.auth.connections.follow(connectionId)) {
    if (ev.event !== 'managed_auth_state') continue;
    if (ev.flow_status === 'SUCCESS') return;
    if (ev.flow_step === 'AWAITING_INPUT' || ev.flow_step === 'AWAITING_EXTERNAL_ACTION') {
      throw new Error(`user action required at ${login.hosted_url}`);   // continue this flow; do NOT call login again
    }
  }
  throw new Error('authentication did not complete successfully');
}
```

## Stored credentials: re-auth without prompting

```ts
const credential = await kernel.credentials.create({
  name: 'netflix-user-123',
  domain: 'netflix.com',
  values: { email: 'user@example.com', password: '…' },
  totp_secret: 'JBSWY3DPEHPK3PXP',   // base32 (16-128 chars) or an otpauth://totp/ URI
  sso_provider: 'google',            // open string; examples: google, github, microsoft
  // Non-default authenticator settings (URI parameters override these):
  // totp_algorithm: 'SHA256', totp_digits: 8, totp_period: 60,   // SHA1|SHA256|SHA512, 6-9, 15-300
});

// Link it when creating the connection
await kernel.auth.connections.create({
  domain: 'netflix.com',
  profile_name: 'netflix-user-123',
  credential: { name: credential.name },
});
```

Notes:

- `values` is never returned after creation (encrypted at rest with per-org keys); responses expose `has_values`, `has_totp_secret`, `value_keys`. Generated TOTP codes can be longer than 6 digits; `kernel.credentials.totpCode(name)` returns `{ code, expires_at }`.
- `credentials.update(idOrName, { values, remove_value_keys, totp_secret, ... })` merges `values`; removals apply first. `totp_secret: ''` removes the secret.
- Partial credentials are allowed: missing fields trigger user input during the flow (hybrid auto-fill + user input).
- A credential is linked to a connection by `credential: { name }`, so its `domain` need not equal the connection's domain (an SSO credential uses the identity provider's domain, e.g. `accounts.google.com`).
- Provisioning paths: (1) captured during login when `save_credentials: true` (one-time codes are never saved), (2) pre-stored via `kernel.credentials.create`, (3) an external provider (1Password), see [profiles-pools-credentials.md](../patterns/profiles-pools-credentials.md).
- Deleting a credential unlinks it; its connections can no longer auto-authenticate.

## Profile interop

Once a connection's `status === 'AUTHENTICATED'`, the saved session is attached to the **profile**. Launch a browser with the same `profile.name`:

```ts
await kernel.browsers.create({
  profile: { name: 'netflix-user-123' },
  stealth: true,
});
```

A profile can carry connections for many domains (one per domain); a browser loads all of them. Managed Auth saves tab state on success; failed and canceled sessions leave the profile unchanged. A running browser keeps the snapshot it started with, so after a re-auth start a new browser (or load the profile into a profile-less running browser; see [profiles-pools-credentials.md](../patterns/profiles-pools-credentials.md)). Set `start_url` if automation needs a specific first page.

Most authenticated sessions stay valid for days. Auto-refresh needs both `health_checks` (default true) and `auto_reauth` (default true). Read `can_reauth` and `can_reauth_reason` to find out whether a human is required, and `timeline(id, { type: 'reauth' })` to see recent attempts. When `status === 'NEEDS_AUTH'`, start a new login and bring the user back when a code, choice or approval is required. A code the user supplied once does not give Kernel future codes.

## Connection options at a glance

`login_url` (skip discovery), `allowed_domains` (extra hostnames for credential entry; common SSO providers such as Google, Microsoft, Okta, Auth0, Apple, GitHub, Facebook, LinkedIn, Cognito, OneLogin, Ping are allowed by default), `record_session` (replays of every auth session; also per login), `browser.proxy` (pin logins, health checks and re-auths to one proxy; ISP gives a stable IP), `post_login_url` (read after success), `skill_mode` on `login`.

## When to skip Managed Auth

- Fully public scraping (no login)
- You would handle raw end-user passwords and storage yourself (do not)
- The site only supports OAuth and you already have tokens: call the API directly
- The user is present mid-task and your agent must control navigation and submission: use Fill from Vault / Fill from Managed Auth

## Where to look next

- Embedded React component walk-through: `references/examples/managed-auth-flow.md`
- Vaults, fill, and 1Password Agentic Autofill: `references/patterns/vaults-and-payments.md`
- CLI reference for auth commands: `references/guides/cli-reference.md`
- 1Password and other credential providers: `references/patterns/profiles-pools-credentials.md`
- Common auth errors (409, expired handoff, NEEDS_AUTH loops): `references/troubleshooting/auth-and-profile-errors.md`
