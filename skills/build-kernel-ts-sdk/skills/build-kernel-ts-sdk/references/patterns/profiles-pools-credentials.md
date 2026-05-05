# Profiles, browser pools, and credentials

Three persistence and reuse mechanisms. They compose:

- **Profiles** — per-user/per-flow Chromium state (cookies, localStorage, IndexedDB, login state).
- **Browser pools** — pre-warmed browsers ready for instant acquire.
- **Credentials and credential providers** — encrypted credential storage; native or 1Password-backed.

## Profiles

Direct `browsers.create({ profile: { name } })` requires the profile to already exist. Either call `profiles.create` first, or take the Managed Auth path (`auth.connections.create` auto-creates the profile if `profile_name` is new).

```ts
// 1. One-time setup
await kernel.profiles.create({ name: 'user-123' });

// 2. First session — log in and persist changes
await kernel.browsers.create({
  profile: { name: 'user-123', save_changes: true },
});
```

`save_changes: true` snapshots the profile's state on `deleteByID`. Subsequent `browsers.create({ profile: { name: 'user-123' } })` (without `save_changes`) loads that snapshot read-only.

Direct profile API:

```ts
await kernel.profiles.list();
const p = await kernel.profiles.retrieve('user-123');       // by name or id
const archive = await kernel.profiles.download('user-123'); // download archive for backup
await kernel.profiles.delete('user-123');
```

When to use a profile:

- Anything that needs login state across sessions.
- Loading saved preferences or test fixtures.
- Carrying anti-detection signals (browsing history, cookies) that build site trust.

A single profile can carry login state for **multiple domains** when paired with multiple Managed Auth connections.

## Browser pools (Reserved Browsers)

Pre-configure a fixed set of browsers ready for instant acquire. You are billed only when a browser is **acquired**, not while idle in the pool.

```ts
const pool = await kernel.browserPools.create({
  name: 'my-pool',
  size: 10,
  stealth: true,
  headless: false,
  timeout_seconds: 600,
  viewport: { width: 1280, height: 800 },
});

// Acquire is a long-poll. If no browser is free in the poll window,
// the response is empty (HTTP 204) and you must retry until your own deadline.
async function acquireWithDeadline(name: string, deadlineMs: number) {
  const end = Date.now() + deadlineMs;
  while (Date.now() < end) {
    const res = await kernel.browserPools.acquire(name, { acquire_timeout_seconds: 30 });
    if (res?.session_id) return res;
  }
  throw new Error(`pool ${name}: no browser available before deadline`);
}

const session = await acquireWithDeadline('my-pool', 5 * 60_000);
try {
  // … use session.cdp_ws_url like any Kernel browser …
} finally {
  await kernel.browserPools.release('my-pool', {
    session_id: session.session_id,
    reuse: true,                           // default; reuse the instance
    // reuse: false                        // destroy and rebuild — use after sensitive flows
  });
}
```

Operations:

- `kernel.browserPools.create({ name, size, … })` — define a pool with browser-create params baked in.
- `kernel.browserPools.retrieve(name)` — current `available_count`, `acquired_count`, etc.
- `kernel.browserPools.acquire(name, { acquire_timeout_seconds })` — long-poll for a browser. Returns `204 No Content` (an empty response, not a throw) when the poll window elapses; **the client must retry** until your own outer deadline.
- `kernel.browserPools.release(name, { session_id, reuse })` — return a browser to the pool. `reuse: false` destroys and rebuilds (useful after credential changes or sensitive flows).
- `kernel.browserPools.flush(name)` — destroy all idle browsers; the pool refills automatically.
- `kernel.browserPools.update / delete / list` — standard.

Acquired browsers are exempt from `flush`. Use `flush` to roll the pool after a config change or to invalidate session state across all idle instances.

## Credentials

Per-org encrypted credential store. **Values are never returned by the API after creation.**

```ts
const credential = await kernel.credentials.create({
  name: 'netflix-user-123',
  domain: 'netflix.com',
  values: {
    email: 'user@example.com',
    password: '…',
    // arbitrary form fields are accepted
  },
  totp_secret: 'JBSWY3DPEHPK3PXP',  // Base32; used automatically for 2FA prompts
  sso_provider: 'google',           // 'google' | 'github' | 'microsoft' | 'okta' | 'auth0'
});

// Use during a connection
await kernel.auth.connections.create({
  domain: 'netflix.com',
  profile_name: 'netflix-user-123',
  credential: { name: credential.name },
});

// Poll TOTP code if you ever need to display it
const { code } = await kernel.credentials.totpCode('netflix-user-123');
```

Provisioning paths:

1. **Auto-capture during login** — `auth.connections.create({ … save_credentials: true })` stores values entered through the flow.
2. **Pre-store** — `kernel.credentials.create({ … })` before any browser flow runs, then reference by name.
3. **External provider** — 1Password (below).

Partial credentials (some fields missing) are allowed; missing fields prompt the user during the flow.

## Credential providers (1Password)

Drive credentials from a 1Password vault via service-account token. Avoids storing user-managed credentials in Kernel directly.

**Two setup paths — pick one:**

- **Dashboard (recommended in docs):** Go to *Integrations → Connect 1Password* in the Kernel dashboard. Paste the service-account token there; the provider is registered with the name you choose. No SDK call needed for setup. Reference it later via `credential: { provider: '<name>' }`.
- **SDK:** `kernel.credentialProviders.create(...)` for fully programmatic provisioning (e.g. CI bootstrap):

```ts
const provider = await kernel.credentialProviders.create({
  name: 'my-1p',
  provider_type: 'onepassword',
  token: process.env.OP_TOKEN!,
  // cache_ttl_seconds: 300, // optional, defaults to 300
});

// Validate the connection
await kernel.credentialProviders.test(provider.id);

// Auto-match by domain — 1Password Login items with website URL matching `domain` are tried in order
await kernel.auth.connections.create({
  domain: 'netflix.com',
  profile_name: 'netflix-user-123',
  credential: { provider: 'my-1p', auto: true },
});

// Or reference an exact item by path
await kernel.auth.connections.create({
  domain: 'netflix.com',
  profile_name: 'netflix-user-123',
  credential: { provider: 'my-1p', path: 'Vault/Netflix Login' },
});
```

`kernel.credentialProviders.listItems(id)` enumerates available items for picker UIs. TOTP secrets stored in 1Password items are used automatically.

## Composition guide

| Need | Combine |
|---|---|
| Per-user login that survives sessions | Profile + Managed Auth (Hosted UI) |
| Bulk warm-start automation, no auth | Browser pool with `stealth: true` |
| Many users, same upstream SaaS | Profile-per-user + 1Password provider + auto-match |
| Pool of pre-authenticated browsers | Pool + per-browser profile (acquire, set profile, run, release with `reuse: false`) |
| Headless re-auth without prompting | Pre-stored credential + `auth.connections.create({ credential: { name } })` then submit |

## Where to look next

- Hosted UI vs Programmatic flow: `references/guides/managed-auth.md`
- Common 409 conflicts and `NEEDS_AUTH` loops: `references/troubleshooting/auth-and-profile-errors.md`
