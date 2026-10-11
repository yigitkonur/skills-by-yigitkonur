# Profiles, browser pools, and credentials

Three persistence and reuse mechanisms. They compose:

- **Profiles**: per-user/per-flow Chromium state (cookies, localStorage, open tabs, preferences).
- **Browser pools**: pre-warmed browsers ready for instant acquire.
- **Credentials and credential providers**: encrypted credential storage for Managed Auth; native or 1Password-backed. (Vault credential items for `fill` are in [vaults-and-payments.md](vaults-and-payments.md).)

Source note: Verified against Kernel profiles, browser-pools, pricing and changelog docs and `@onkernel/sdk@0.123.0` / `@onkernel/cli@0.47.0` source in October 2026. Re-check live docs before changing billing or plan-gate claims.

## Profiles

Profile data is encrypted with a per-organization key. A profile `name` is unique within its project (1-255 characters: letters, numbers, `.`, `_`, `-`). `browsers.create({ profile: { name } })` requires the profile to exist: call `profiles.create` first, or take the Managed Auth path (`auth.connections.create` creates the profile if `profile_name` is new).

```ts
// 1. One-time setup (ConflictError means it already exists)
await kernel.profiles.create({ name: 'user-123' });

// 2. First session: log in and persist changes
await kernel.browsers.create({
  profile: { name: 'user-123', save_changes: true },
});
```

`save_changes: true` replaces the stored profile with the browser's complete state when the Kernel browser is **deleted or times out**. `browser.close()` only closes the local CDP connection and saves nothing. `browsers.create({ profile: { name: 'user-123' } })` without `save_changes` loads the snapshot and discards changes.

Concurrency rules (each browser loads its own snapshot; nothing syncs between running browsers):

| Need | Do |
|---|---|
| Concurrent tasks as the same end user | One profiled browser, one tab per task (named Playwright executors) |
| Many browsers, same starting state | Load one profile without `save_changes` |
| Persist from one browser | `save_changes: true` on that browser only |
| Independent durable writers | One profile per writer |

Only one browser should write a profile at a time; saving replaces the whole snapshot (no merge, last browser to end wins). Detect writers before starting one (guard with your own lock; check and create are separate requests):

```ts
async function activeWriters(profileId: string) {
  const writers = [];
  for await (const b of kernel.browsers.list({ status: 'active', query: profileId })) {
    if (b.profile?.id === profileId && b.profile_save_changes) writers.push(b.session_id);
  }
  return writers;
}
```

Load a profile into a running browser that was created **without** one:

```ts
const b = await kernel.browsers.create();
await kernel.browsers.update(b.session_id, {
  profile: { name: 'user-123' },
  start_url: 'https://example.com/dashboard',   // collapses the restored tabs onto one page
});
```

Loading **restarts Chromium and disconnects CDP clients** (reconnect afterwards); a browser that already has a profile cannot load another. `start_url` on `browsers.create` with a profile discards the restored tabs.

Direct profile API:

```ts
await kernel.profiles.list({ query: 'user' });
const p = await kernel.profiles.retrieve('user-123');             // by name or id
await kernel.profiles.update('user-123', { name: 'user-123-v2' }); // rename; avoid while a browser references it by name
const res = await kernel.profiles.download('user-123');           // Response: zstd tar by default, { format: 'tar' } to decompress
await kernel.profiles.delete('user-123');
```

Renaming a profile while a session references it by name can stop that session's changes from saving.

Use a profile for login state across sessions, saved preferences or fixtures, and stable returning-browser signals (pair with a consistent proxy). One profile can hold several Managed Auth connections (one per domain). A profile attached to a pool is read-only (below).

## Browser pools (Reserved Browsers)

A pool is a fixed set of identically configured browsers Kernel keeps running. Default to on-demand `browsers.create`; reach for a pool when demand is steady or bursty enough to keep it utilized, acquisition latency matters, or creation hits the `browsers.create` rate limit (acquire is exempt). Do not use a pool for per-session config, GPU browsers, or low-volume one-off work.

Limits and billing:
- Plan: the pools guide says Start-Up and Enterprise; the pricing page lists browser pools on every plan. Check `(await kernel.organization.entitlements.retrieve()).features.browser_pools.enabled` instead of hard-coding.
- No GPU browsers. Idle pooled browsers are not billed, but pool capacity counts against `max_concurrent_sessions` whether or not browsers are acquired (a pool of 40 holds 40 slots; standby still holds the slot). `max_pooled_sessions` is `@deprecated`.
- Creation takes minutes: declare pools at deploy/startup, not in the request path. The sum of pool sizes cannot exceed the org limit.
- `fill_rate_per_minute`: percentage of the pool filled per minute; default and normal cap 25. Raise `size` before a traffic peak.
- `timeout_seconds` (default 600, 10-259200) starts only after a browser is **acquired**; idle pooled browsers wait indefinitely. A leased browser idle past it is destroyed and replaced.
- `memory: '8GiB' | '16GiB'` (default `'8GiB'`) applies to headful pool browsers; updates affect newly created browsers only. Pools also take `region`, fixed at creation (see [browsers-lifecycle.md](../guides/browsers-lifecycle.md)).
- Sizing: if `available_count` is regularly 0, grow the pool; aim for 10-20% available; above 30-40% is waste.
- Vaults cannot be attached to pooled browsers (`BrowserPoolCreateParams` has no `vaults`; the CLI rejects `--vault` with `--pool-name`). Attach vaults with `browsers.create`.
- Idle pooled browsers suspend automatically; there is no `auto_standby` parameter.

```ts
const pool = await kernel.browserPools.create({
  name: 'my-pool',
  size: 10,
  fill_rate_per_minute: 25,
  stealth: true,
  headless: false,
  memory: '16GiB',
  timeout_seconds: 600,
  start_url: 'https://example.com',
  viewport: { width: 1280, height: 800 },
});

// Acquire is a long-poll. If no browser frees up within acquire_timeout_seconds,
// the response is empty (HTTP 204): retry until your own deadline.
async function acquireWithDeadline(name: string, deadlineMs: number, profileName?: string) {
  const end = Date.now() + deadlineMs;
  while (Date.now() < end) {
    const res = await kernel.browserPools.acquire(name, {
      acquire_timeout_seconds: 30,
      profile: profileName ? { name: profileName } : undefined,
    });
    if (res?.session_id) return res;
  }
  throw new Error(`pool ${name}: no browser available before deadline`);
}

const session = await acquireWithDeadline('my-pool', 5 * 60_000, 'user-123');
try {
  // use session.cdp_ws_url like any Kernel browser
} finally {
  await kernel.browserPools.release('my-pool', {
    session_id: session.session_id,
    reuse: true,   // default; a browser with an acquire-time profile is destroyed and replaced regardless
  });
}
```

Operations:

- `browserPools.create({ size, name?, memory?, fill_rate_per_minute?, profile?, refresh_on_profile_update?, proxy_id?, network?, region?, start_url?, ... })`
- `browserPools.retrieve(idOrName)` reports `available_count`, `acquired_count`, `region`, `profile_id`.
- `browserPools.acquire(name, { profile?, acquire_timeout_seconds?, start_url?, name?, tags?, telemetry? })`: `name`, `tags` (max 50) and `telemetry` apply to that lease only and clear on release. Acquire-time `start_url` overrides the pool's.
- `browserPools.release(name, { session_id, reuse })`: `reuse` defaults to **true** and returns the browser **without resetting it** (cookies, storage, tabs persist for the next acquirer). Use `reuse: false` after user-specific or sensitive work. A reused browser keeps the config it was created with, so it misses pool config changes made while it was leased.
- `browserPools.flush(name)`: destroys idle browsers only; leased browsers are untouched.
- `browserPools.update(name, { ..., discard_all_idle?: boolean })`: by default idle browsers keep the old config; `discard_all_idle: true` rebuilds them now. A leased browser is never touched; release it with `reuse: false` or run `flush()` / another `update` after release.
- `browserPools.delete(name, { force? })` (blocked while browsers are leased unless `force`) / `list({ name?, query?, region? })`.
- Pool `network` (`proxy_routes`, `private_hosts`, `allowed_hosts`): see [proxies.md](../guides/proxies.md) section 2.

### Pools and profiles

- `profile: { id } | { name }` on the pool attaches a baseline profile to every browser. It must exist first. **Pool profiles load read-only**: `save_changes` is not part of the shape and is silently ignored.
- `refresh_on_profile_update` flushes idle browsers when that profile is re-saved (for example after a Managed Auth login). It defaults to `true` when a profile is set and requires a profile on the pool; acquired browsers keep their data until released. Clear the pool profile with `update(name, { profile: { id: '' } })` (also disables the refresh).
- **Per-user durable state** (pool created without a profile). Option A (documented pattern): acquire, attach the profile to the running browser, release with `reuse: false`:

  ```ts
  const b = await kernel.browserPools.acquire('my-pool', {});
  await kernel.browsers.update(b.session_id, { profile: { name: 'user-8f21c3', save_changes: true } });
  // ... drive the browser as that user ...
  await kernel.browserPools.release('my-pool', { session_id: b.session_id, reuse: false });
  ```

  Option B (SDK/CLI): `acquire(name, { profile: { name, save_changes: true } })`; the browser is always destroyed and rebuilt on release, and the profile is saved to the persistent profile. `save_changes` defaults to false; without it, the user's session is not written back.
- A pool profile is one shared identity. For different users use per-user profiles as above, never the pool profile.

Cost guardrails: create pools outside request paths; release every acquired browser (an acquired browser stays out of the pool until release or timeout); report pool name/id, acquired `session_id`, release result, and whether `reuse` was true.

## Credentials

Per-project encrypted credential store for Managed Auth. **Values are never returned after creation** (responses expose `has_values`, `has_totp_secret`, `value_keys`).

```ts
const credential = await kernel.credentials.create({
  name: 'netflix-user-123',
  domain: 'netflix.com',
  values: { email: 'user@example.com', password: '…' },   // arbitrary form fields are accepted
  totp_secret: 'JBSWY3DPEHPK3PXP',   // base32 16-128 chars or otpauth:// URI; used automatically for 2FA
  sso_provider: 'google',            // open string (examples: google, github, microsoft)
});

// Use during a connection
await kernel.auth.connections.create({
  domain: 'netflix.com',
  profile_name: 'netflix-user-123',
  credential: { name: credential.name },
});

// Current code (length follows totp_digits; do not assume 6)
const { code, expires_at } = await kernel.credentials.totpCode('netflix-user-123');
```

TOTP algorithm/digits/period, `credentials.update` and `remove_value_keys` are covered in [managed-auth.md](../guides/managed-auth.md). Provisioning paths: auto-capture during login (`save_credentials: true`), pre-store with `credentials.create`, or an external provider (1Password). Partial credentials are allowed; missing fields prompt the user.

## Credential providers (1Password service account)

Drives Managed Auth from a 1Password vault via a service-account token (`ops_...`); values stay in 1Password and are fetched at login time. This is separate from 1Password Agentic Autofill (user-approved, vault items), which is in [vaults-and-payments.md](vaults-and-payments.md).

- **Dashboard (recommended in docs):** *Integrations -> Connect 1Password*, name the provider and paste the token. Multiple providers can be connected.
- **SDK:**

```ts
const provider = await kernel.credentialProviders.create({
  name: 'my-1p',
  provider_type: 'onepassword',
  token: process.env.OP_TOKEN!,
  // cache_ttl_seconds: 300,   // default 300
});

await kernel.credentialProviders.test(provider.id);   // { success, vaults, error? }

// Auto-match by domain
await kernel.auth.connections.create({
  domain: 'netflix.com',
  profile_name: 'netflix-user-123',
  credential: { provider: 'my-1p', auto: true },
});

// Or an exact item: 'VaultName/ItemName'
await kernel.auth.connections.create({
  domain: 'netflix.com',
  profile_name: 'netflix-user-123b',
  credential: { provider: 'my-1p', path: 'Vault/Netflix Login' },
});
```

- `credentialProviders.listItems(id)` returns `{ items }` (each with `id`, `path`, `title`, `vault_id`, `vault_name`, `urls?`) for picker UIs. `update(id, { token?, cache_ttl_seconds?, enabled?, name?, priority? })` rotates or reorders (lower `priority` is checked first).
- Matching uses each item's website/URL field (`github.com`, `https://github.com/login` and `*.example.com` all match); with several matches **the first is used**.
- Not supported: vault or item names containing `/`, and 1Password "sign in with" linked-item references (store a direct username/password login). TOTP comes from the item's `otpauth://` secret (SHA1/SHA256/SHA512, 6-9 digits, 15-300 s).
- Connections backed by 1Password cannot back a vault `managed_auth` item.

## Composition guide

| Need | Combine |
|---|---|
| Per-user login that survives sessions | Profile + Managed Auth (Hosted UI) |
| Bulk warm-start automation, no auth | Browser pool with `stealth: true` (only if steady/bursty demand; else on-demand) |
| Many users, same upstream SaaS | Profile-per-user + 1Password provider + auto-match |
| Pool of pre-authenticated browsers (read-only baseline) | Pool created with `profile: { name }` + `refresh_on_profile_update: true` |
| Durable per-user pool sessions | Profile-free pool + attach profile with `save_changes: true` + `release({ reuse: false })` |
| Headless re-auth without prompting | Pre-stored credential + `auth.connections.create({ credential: { name } })` |
| Credential and card autofill | `browsers.create({ vaults: [{ id }] })` + `vaults.items.performOperation(... 'fill')` |

## Where to look next

- Vaults, fill, payments: `references/patterns/vaults-and-payments.md`
- Hosted UI vs Programmatic flow: `references/guides/managed-auth.md`
- CLI reference for pools, profiles, credentials: `references/guides/cli-reference.md`
- Common 409 conflicts and `NEEDS_AUTH` loops: `references/troubleshooting/auth-and-profile-errors.md`
