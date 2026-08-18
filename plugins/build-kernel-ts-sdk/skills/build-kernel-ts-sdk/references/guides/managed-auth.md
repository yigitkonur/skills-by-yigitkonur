# Managed Auth

Kernel **Managed Auth** lets a Kernel browser log into a third-party SaaS on behalf of an end-user. Two flow shapes share the same `kernel.auth.connections.*` SDK surface; pick one early.

Source note: Verified against `@onkernel/sdk@0.92.0` types, `@onkernel/managed-auth-react@0.4.1` types (peer deps react/react-dom >= 18), and Kernel docs on 2026-08-19.

## Flow shapes

| | Hosted UI | Programmatic |
|---|---|---|
| Where credentials are entered | Kernel-hosted page (or `<KernelManagedAuth />` embed on your domain) | Your own UI |
| What you write | Backend `create` + `login`; frontend `redirect` (or embed) | Backend `create` + `login` + poll + `submit`; you build the input UI |
| MFA / SSO support | Built in | You handle: detect from `choices` (canonical) or the legacy `mfa_options` / `pending_sso_buttons`, route the user, submit |
| When to pick | Default — fastest to ship, covers SSO, 2FA, security keys | You need design control, headless flows, or you already have credentials and just want to drive submit |

## SDK surface

| Method | Purpose |
|---|---|
| `kernel.auth.connections.create({ domain, profile_name, login_url?, allowed_domains?, save_credentials?, credential?, health_checks?, health_check_interval?, auto_reauth?, record_session?, browser? })` | Create a connection scoping a `domain` to a browser `profile_name`. See the cost note below — `health_checks` and `auto_reauth` both default to **true**. |
| `kernel.auth.connections.login(id)` | Start a login session for an auth connection id; returns login-session fields including `hosted_url`, `handoff_code`, `flow_type`, and `flow_expires_at`. |
| `kernel.auth.connections.retrieve(id)` | Returns current `flow_status`, `flow_step`, connection `status`, `can_reauth` / `can_reauth_reason`, and (in programmatic mode) the canonical `choices` and `fields` plus their legacy counterparts `discovered_fields`, `pending_sso_buttons`, `mfa_options`, `sign_in_options`. |
| `kernel.auth.connections.submit(id, { field_values?, selected_choice_id?, fields?, sso_provider?, mfa_option_id?, sign_in_option_id?, sso_button_selector? })` | Programmatic only: submit user-collected values. **Prefer the canonical pair** — `field_values` (keyed by `Field.id`) and `selected_choice_id` (a `Choice.id`). Fall back to the legacy params (`fields` keyed by field name, `sso_provider`/`sso_button_selector`, `mfa_option_id`, `sign_in_option_id`) only when `choices`/`fields` are absent; pick the one matching the current `flow_step`. |
| `kernel.auth.connections.update(id, …)` | Edit a connection (e.g. switch credential). |
| `kernel.auth.connections.list()` / `delete(id)` / `follow(id)` | Standard list/delete plus an SSE feed for state. |
| `kernel.auth.connections.timeline(id, { type?: 'login' \| 'reauth' \| 'health_check' })` | Paginated, newest-first history of login attempts, automatic re-auths, and health checks. First stop when a connection keeps flipping to `NEEDS_AUTH`. |

`kernel.auth.context.retrieve()` is the other half of the `auth.*` surface — it reports the caller's principal, organization, and `authorization.credential_scope` / `effective_scope` project ids.

**Cost and re-auth defaults.** `health_checks` defaults to **true**: Kernel runs a background browser session against the target site on `health_check_interval` (default 3600s or your plan minimum, whichever is larger — Enterprise 300 / Startup 1200 / Hobbyist 3600 / Free 21600; max 86400) for the life of the connection. Budget for it, or pass `health_checks: false` for one-shot connections. `auto_reauth` also defaults to true but is a **no-op when `health_checks: false`**, because re-auth only fires after a failed scheduled health check. `browser` (`ManagedAuthBrowserConfig`) is where proxy and telemetry for login, re-auth, and health-check sessions now go; the top-level `proxy` and `browser_telemetry` params are deprecated.

`auth.connections.create` returns 409 if a connection with the same `domain` + `profile_name` already exists. Either reuse the existing one (`retrieve`/`list`) or pick a different `profile_name`.

## States

**`flow_status`:** `IN_PROGRESS` | `SUCCESS` | `FAILED` | `EXPIRED` | `CANCELED`. Anything other than `IN_PROGRESS` is terminal — stop polling.

**`flow_step`** (programmatic): `DISCOVERING`, `AWAITING_INPUT`, `SUBMITTING`, `AWAITING_EXTERNAL_ACTION` (push approval / hardware key), `COMPLETED`. The flow can move between these in any order — `AWAITING_EXTERNAL_ACTION` can precede `SUBMITTING` for SSO, and the loop may revisit `AWAITING_INPUT` multiple times. Branch on the current `flow_step`, do not assume a fixed sequence.

**Connection `status`:** `AUTHENTICATED` (logged in, browsers using `profile_name` are ready) | `NEEDS_AUTH` (re-auth required).

## Hosted UI — the simple path

```ts
// 1. Backend route — POST /api/auth/connect
import Kernel from '@onkernel/sdk';
const kernel = new Kernel();

const conn = await kernel.auth.connections.create({
  domain: 'netflix.com',
  profile_name: `netflix-${userId}`,
  save_credentials: true,                  // default true — set false to opt out of credential capture
});

const login = await kernel.auth.connections.login(conn.id);
if (!login.handoff_code) throw new Error('missing managed-auth handoff_code');

// Return the auth connection id plus login-session fields. Do not expose KERNEL_API_KEY.
return Response.json({
  connectionId: conn.id,
  profileName: `netflix-${userId}`,
  hostedUrl: login.hosted_url,
  handoffCode: login.handoff_code,
  flowExpiresAt: login.flow_expires_at,
});
```

```ts
// 2. Frontend — redirect or embed
window.location.href = hostedUrl;           // simplest: redirect away

// OR embed Kernel's hosted UI in your own page:
//   import { KernelManagedAuth } from '@onkernel/managed-auth-react';
//   Required props: sessionId={connectionId} and handoffCode={handoffCode}.
//   Optional: appearance, localization, onSuccess, onError, baseUrl, fetch.
//   See `references/examples/managed-auth-flow.md` for the full embed pattern.
```

```ts
// 3. Backend — poll until terminal, then launch a browser
let state = await kernel.auth.connections.retrieve(conn.id);
while (state.flow_status === 'IN_PROGRESS') {
  await new Promise(r => setTimeout(r, 2000));
  state = await kernel.auth.connections.retrieve(conn.id);
}
if (state.status !== 'AUTHENTICATED') {
  throw new Error(`auth ${state.flow_status}`);
}

// Now any browser launched with this profile_name is logged in.
const session = await kernel.browsers.create({
  profile: { name: `netflix-${userId}` },
  stealth: true,
});
```

For long-running waits, prefer `kernel.auth.connections.follow(id)` SSE over a polling loop.

Security and lifecycle rules:

- Never expose `KERNEL_API_KEY` to the browser or React component.
- Treat `handoff_code` as short-lived and single-use; request a fresh login session instead of caching it.
- Distinguish the auth connection id (`conn.id`) from login-session fields (`hosted_url`, `handoff_code`, `flow_expires_at`).
- Store only stable ids needed later: auth connection id and profile name. Do not persist handoff codes or raw credentials.
- Finish reports must include auth connection id, profile name, final `flow_status`/`status`, and any browser `session_id` launched from the profile.

## Programmatic — your own UI

Use this when you need design control, are running fully headless, or have credentials already stored.

```ts
const conn = await kernel.auth.connections.create({
  domain: 'example.com',
  profile_name: `user-${userId}`,
});
await kernel.auth.connections.login(conn.id);

let state = await kernel.auth.connections.retrieve(conn.id);
while (state.flow_status === 'IN_PROGRESS') {
  // Canonical path — id-keyed, and the only shape that carries the newer choice
  // types ('auth_method', 'identifier_method', 'account', 'other').
  if (state.fields?.length) {
    // Field: { id, ref, type: 'identifier'|'password'|'code'|'totp_code'|'totp_secret'|'text',
    //          label?, hint?, required?, observed_selector?, replace_existing? }
    const field_values = await collectFromUser(state.fields);   // Field.id -> value
    await kernel.auth.connections.submit(conn.id, { field_values });
  } else if (state.flow_step === 'AWAITING_INPUT' && state.discovered_fields?.length) {
    // Legacy fallback — keyed by field *name*, not id.
    const fields = await collectLegacyFromUser(state.discovered_fields);
    await kernel.auth.connections.submit(conn.id, { fields });
  }

  if (state.choices?.length) {
    // Choice: { id, label, type, mfa_type?, masked_destination?, description?, observed_selector? }
    // Use `id` — two options can share a `type` (e.g. two SMS destinations).
    const choice = await pickChoice(state.choices);
    await kernel.auth.connections.submit(conn.id, { selected_choice_id: choice.id });
  } else {
    // Legacy fallbacks, used only when `choices` is absent.
    if (state.pending_sso_buttons?.length) {
      const sso = await pickSSO(state.pending_sso_buttons);      // [{ provider, label, selector }]
      await kernel.auth.connections.submit(conn.id, { sso_provider: sso.provider });
    }
    if (state.mfa_options?.length) {
      // Each option is { type, label, description?, target? } — pick by `type`
      // and pass it as `mfa_option_id` (Kernel uses the type as the option id).
      const mfa = await pickMfa(state.mfa_options);
      await kernel.auth.connections.submit(conn.id, { mfa_option_id: mfa.type });
    }
    if (state.sign_in_options?.length) {
      const account = await pickSignIn(state.sign_in_options);
      await kernel.auth.connections.submit(conn.id, { sign_in_option_id: account.id });
    }
  }

  if (state.flow_step === 'AWAITING_EXTERNAL_ACTION') {
    showUser(state.external_action_message ?? 'Approve the push on your phone…');
  }
  await new Promise(r => setTimeout(r, 2000));
  state = await kernel.auth.connections.retrieve(conn.id);
}
```

Programmatic flow is more code but gives you per-step control over the UX.

## Stored credentials — re-auth without prompting

Pre-store credentials so subsequent re-auths don't need user input:

```ts
const credential = await kernel.credentials.create({
  name: 'netflix-user-123',
  domain: 'netflix.com',
  values: {
    email: 'user@example.com',
    password: '…',
  },
  totp_secret: 'JBSWY3DPEHPK3PXP', // optional Base32 TOTP for 2FA automation
  sso_provider: 'google',           // optional — google/github/microsoft/okta/auth0
});

// Link the credential when creating the connection
await kernel.auth.connections.create({
  domain: 'netflix.com',
  profile_name: 'netflix-user-123',
  credential: { name: credential.name },
});
```

Notes:

- Credential `values` is **never returned** by the API after creation — encrypted at rest with per-org keys. Treat write-once.
- Partial credentials are allowed: missing fields trigger user input during the flow (hybrid auto-fill + user-input).
- Provisioning paths: (1) auto-captured during the login flow when `save_credentials: true`, (2) pre-stored via `kernel.credentials.create`, (3) sourced from a credential provider (1Password) — see `references/patterns/profiles-pools-credentials.md`.

## Profile interop

Once a connection's `status === 'AUTHENTICATED'`, the saved session is attached to the **profile**, not the connection. Launch a browser with the same `profile.name` and it is already logged in:

```ts
await kernel.browsers.create({
  profile: { name: 'netflix-user-123' },
  stealth: true,
});
```

A single profile can carry multiple connections for different domains — log in once for each, and the browser is logged into all of them.

Most authenticated sessions stay valid for days; Kernel auto-refreshes when possible. When `status === 'NEEDS_AUTH'`, run the flow again.

Auto-refresh is driven by scheduled health checks, so both switches must be on: `health_checks` (default true) and `auto_reauth` (default true). `auto_reauth` is a **no-op when `health_checks: false`** — disabling health checks to save browser-seconds silently disables auto-refresh too. `health_check_interval` defaults to 3600s or your plan minimum, whichever is larger (Enterprise 300 / Startup 1200 / Hobbyist 3600 / Free 21600; max 86400).

Read `can_reauth` and `can_reauth_reason` on the connection to find out whether a human is actually required — e.g. `requires_totp_without_secret`, `requires_email_code`, `no_credential`, `no_viable_plans`. Use `kernel.auth.connections.timeline(id, { type: 'reauth' })` to see what the last attempts did.

## When to skip Managed Auth

- Fully public scraping (no login)
- You're willing to ask the user for their password and handle storage yourself (you should not be)
- The target site only supports OAuth and you already have OAuth tokens — drive the API directly without a browser

## Where to look next

- Embedded React component walk-through: `references/examples/managed-auth-flow.md`
- 1Password and other credential providers: `references/patterns/profiles-pools-credentials.md`
- Common auth errors (409, expired handoff, NEEDS_AUTH loops): `references/troubleshooting/auth-and-profile-errors.md`
