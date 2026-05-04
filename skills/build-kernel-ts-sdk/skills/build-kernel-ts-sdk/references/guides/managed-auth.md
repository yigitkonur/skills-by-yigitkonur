# Managed Auth

Kernel **Managed Auth** lets a Kernel browser log into a third-party SaaS on behalf of an end-user. Two flow shapes share the same `kernel.auth.connections.*` SDK surface; pick one early.

## Flow shapes

| | Hosted UI | Programmatic |
|---|---|---|
| Where credentials are entered | Kernel-hosted page (or `<KernelManagedAuth />` embed on your domain) | Your own UI |
| What you write | Backend `create` + `login`; frontend `redirect` (or embed) | Backend `create` + `login` + poll + `submit`; you build the input UI |
| MFA / SSO support | Built in | You handle: detect from `mfa_options` / `pending_sso_buttons`, route the user, submit |
| When to pick | Default — fastest to ship, covers SSO, 2FA, security keys | You need design control, headless flows, or you already have credentials and just want to drive submit |

## SDK surface

| Method | Purpose |
|---|---|
| `kernel.auth.connections.create({ domain, profile_name, login_url?, allowed_domains?, save_credentials?, credential? })` | Create a connection scoping a `domain` to a browser `profile_name`. |
| `kernel.auth.connections.login(id)` | Start a login session; returns `{ hosted_url }` for redirect/embed (Hosted UI) or starts the polling loop (Programmatic). |
| `kernel.auth.connections.retrieve(id)` | Returns current `flow_status`, `flow_step`, connection `status`, and (in programmatic mode) `discovered_fields`, `pending_sso_buttons`, `mfa_options`, `sign_in_options`. |
| `kernel.auth.connections.submit(id, { fields?, sso_provider?, mfa_option_id?, sign_in_option_id?, sso_button_selector? })` | Programmatic only: submit user-collected values. Pick the single field that matches the current `flow_step` — for `AWAITING_INPUT` it's `fields`; for SSO it's `sso_provider` or `sso_button_selector`; for MFA it's `mfa_option_id`; for sign-in pickers it's `sign_in_option_id`. |
| `kernel.auth.connections.update(id, …)` | Edit a connection (e.g. switch credential). |
| `kernel.auth.connections.list()` / `delete(id)` / `follow(id)` | Standard list/delete plus an SSE feed for state. |

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

const { hosted_url } = await kernel.auth.connections.login(conn.id);
// Return both id and hosted_url to your frontend.
return Response.json({ id: conn.id, hosted_url });
```

```ts
// 2. Frontend — redirect or embed
window.location.href = hosted_url;          // simplest: redirect away

// OR embed Kernel's hosted UI in your own page:
//   import { KernelManagedAuth } from '@onkernel/managed-auth-react';
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
  if (state.flow_step === 'AWAITING_INPUT' && state.discovered_fields?.length) {
    const fields = await collectFromUser(state.discovered_fields);
    // discovered_fields: [{ name: 'username', type: 'text' }, { name: 'password', type: 'password' }]
    await kernel.auth.connections.submit(conn.id, { fields });
  }
  if (state.flow_step === 'AWAITING_EXTERNAL_ACTION') {
    showUser('Approve the push on your phone…');
  }
  if (state.pending_sso_buttons?.length) {
    const choice = await pickSSO(state.pending_sso_buttons); // [{ provider, label, selector }]
    await kernel.auth.connections.submit(conn.id, { sso_provider: choice.provider });
  }
  if (state.mfa_options?.length) {
    // Each option is { type, label, description?, target? } — pick by `type`
    // and pass it as `mfa_option_id` (Kernel uses the type as the option id).
    const choice = await pickMfa(state.mfa_options);
    await kernel.auth.connections.submit(conn.id, { mfa_option_id: choice.type });
  }
  if (state.sign_in_options?.length) {
    const account = await pickSignIn(state.sign_in_options);
    await kernel.auth.connections.submit(conn.id, { sign_in_option_id: account.id });
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

## When to skip Managed Auth

- Fully public scraping (no login)
- You're willing to ask the user for their password and handle storage yourself (you should not be)
- The target site only supports OAuth and you already have OAuth tokens — drive the API directly without a browser

## Where to look next

- Embedded React component walk-through: `references/examples/managed-auth-flow.md`
- 1Password and other credential providers: `references/patterns/profiles-pools-credentials.md`
- Common auth errors (409, expired handoff, NEEDS_AUTH loops): `references/troubleshooting/auth-and-profile-errors.md`
