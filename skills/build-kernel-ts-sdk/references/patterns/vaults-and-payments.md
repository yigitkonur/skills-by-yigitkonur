# Vaults and Payments: Credentials, Fill, Wallets & Agent Purchases

Kernel Vaults (preview) are project-scoped containers of typed items that an attached browser can use: `credential` (logins), `credential_account` (1Password link), `wallet` and `card` (payments). `fill` writes stored values into browser fields without the values passing through your code or the model; the API returns per-field outcomes, never values.

**`fill` is not secret isolation from the browser.** Page scripts, extensions, devtools and an agent with unrestricted browser/CDP access can read filled values. Authorize the destination in your controller before every fill (`page_url` and selectors proposed by a model authorize nothing). Never put collection/approval URLs, OAuth codes or API keys into model context.

Source note: Verified against Kernel vaults, auth, payments, wallets and MPP docs and `@onkernel/sdk@0.123.0` / `@onkernel/cli@0.47.0` source.

---

## 1. Resource model

| Concept | Behavior |
|---|---|
| Vault | Immutable `name` (1-255 of letters, numbers, `.`, `_`, `-`); `vaults.upsert({ name })` creates or retrieves; `vaults.list({ query })` is a case-insensitive name substring filter. Make one per end user or access boundary. |
| Item | Typed, addressed by an immutable `key` (same character rules). `upsert` on an existing key succeeds only if type/spec/provider match; otherwise 409. |
| Attachment | `vaults: [{ id }]` or `[{ name }]` on `browsers.create` (max 20, exactly one of `id`/`name` each). Immutable for the session; the browser and vault must be in the same project. It grants access to **every item in the vault, including items created later**. Pools cannot take vaults. |
| `available_operations` | What the item allows now: `collect`, `authorize`, `prepare_checkout`, `fill`, `webmcp_invoke`, `1pw_*`. Retrieve first and invoke only advertised operations. |
| `action` | A user step with a URL (`collect`, `link_oauth`, `spend_approval`, `card_enrollment`, `1password_oauth`, `1password_access_approval`) or without (`push_approval`, `mfa`, `embedded_ceremony`). Treat URLs as short-lived bearer links: show them only in the user's authenticated UI, never log them or give them to the agent. |
| Limits | Free orgs: 3 non-deleted vaults org-wide (`organization.limits.retrieve()` -> `vaults_used` / `max_vaults`; `null` = unlimited). Vault access is an entitlement (`features.vaults.enabled`). |

Deleting a vault or item stops further use; it does not undo values already filled or actions already performed. Project scope: set `projectID` on the client (or use a project-scoped key); without it the default project is used.

```ts
import Kernel from '@onkernel/sdk';

const kernel = new Kernel({ projectID: process.env.KERNEL_PROJECT_ID });
const vault = await kernel.vaults.upsert({ name: 'user-12345' });
const session = await kernel.browsers.create({
  stealth: true,
  vaults: [{ id: vault.id }],      // or { name: 'user-12345' }
  timeout_seconds: 600,
});
```

For payments, build the client with `maxRetries: 0` (docs do): `performOperation` is already sent with `maxRetries: 0`, but `upsert` creates are retried by default.

---

## 2. Credential items and `fill`

Two sources produce a ready `credential` item that `fill` can use: a Kernel-hosted collection form (or your backend writing values), or a Managed Auth connection that already holds a saved credential (section 2.4).

### 2.1 Define, collect, update

```ts
const item = await kernel.vaults.items.upsert('portal-login', {
  id_or_name: vault.id,
  type: 'credential',
  spec: {
    provider: 'kernel',
    description: 'Account Portal',          // form title: the site name only
    fields: [                                // top-to-bottom order of the site's form
      { name: 'username', label: 'Email address', type: 'email', required: true, sensitive: false },
      { name: 'password', label: 'Password', type: 'password', required: true, sensitive: true },
    ],
  },
});
if (item.type !== 'credential') throw new Error('expected a credential item');
const collectionUrl = item.action?.url;   // present only to the intended user; expires after 30 minutes
```

- Field rules: `type` is `text | email | password | totp`; 1-32 fields; `name` starts with an ASCII letter, ASCII letters/digits/underscore, max 64; `label` max 128 UTF-8 bytes; `required` defaults true; `sensitive` defaults **true** (password and totp must be true; `sensitive: false` values are returned in `state.fields`). Field definitions are immutable: use a new item key for a different shape. Initial `value` is non-empty, max 16 KiB; `email` must be a bare address.
- Without `value`s the item is `state.status: 'pending_collection'` with a `collect` action. Poll `items.retrieve(key, { id_or_name, wait: 60 })` (0-60 s long-poll) until `ready`. `ready` means values exist, not that a login worked. Retrieving renews an expired link; listing does not. To reopen the form for a ready item invoke `{ type: 'collect' }` (values are kept). `wait` does not observe edits to a ready item: compare `version`.
- Write values from trusted code by passing `value` on `upsert`, or update later:

```ts
const current = await kernel.vaults.items.retrieve('portal-login', { id_or_name: vault.id });
if (current.type !== 'credential') throw new Error('expected a credential item');
await kernel.vaults.items.update('portal-login', {
  id_or_name: vault.id,
  type: 'credential',
  version: current.version,          // 409 if stale; reload, do not blindly resubmit
  expected_item_id: current.id,      // 409 if the key now points at a different item
  spec: { fields: { password: { value: process.env.NEW_PASSWORD! } } },   // null or '' clears a value
});
```

  A successful update bumps `version` and invalidates open hosted forms. Clearing a required text/email/password returns the item to `pending_collection`; clearing a required totp seed is a 400.
- **TOTP**: supply the base32 seed as the field `value` (not a code or `otpauth://` URI). Vault `totp` fields always generate HMAC-SHA1, 6-digit, 30 s codes; there is no algorithm/digits/period option (use a Managed Auth credential for those, section 2.4). Fill writes a fresh code, never the seed.
- **Client-side encryption (`encrypted_value`)** is only for a custom credential collection web app that encrypts in the browser and forwards the ciphertext. Server code that holds plaintext should use `value`. Fetch `kernel.vaults.retrieveEncryptionKey(vaultName)` -> `{ alg: 'ECDH-ES', enc: 'A256GCM', jwk, kid }`; encrypt a compact JWE (no compression) to `jwk` with `kid` in the protected header and send it as the field's `encrypted_value` (instead of `value`); a wrong `kid` is `400 encryption_key_mismatch`; request body max 128 KiB.
- Credential items are for logins, never card numbers/CVC/expiry: use `wallet` + `card`.
- Building your own collection UI: use `@onkernel/vault-react` (section 7) with your authenticated backend calling `items.retrieve` / `items.update`.

### 2.2 Fill

```ts
const ready = await kernel.vaults.items.retrieve('portal-login', { id_or_name: vault.id, wait: 60 });
if (ready.type !== 'credential' || ready.state.status !== 'ready'
    || !ready.available_operations.some((op) => op.type === 'fill')) {
  throw new Error('credential is not ready to fill');
}

const fillRes = await kernel.vaults.items.performOperation('portal-login', {
  id_or_name: vault.id,
  type: 'fill',
  browser_id: session.session_id,                   // session id, not a browser name
  page_url: 'https://www.example.com/login',        // exact current top-level URL (path, query, fragment)
  timeout_ms: 15_000,                               // total deadline; default 10000, max 30000
  fields: [
    { field: 'username', selector: 'input#email' },
    { field: 'password', selector: 'input#password' },
    { field: 'totp', selector: 'input#two-factor-code' },
  ],
});

if (fillRes.type === 'fill') {
  console.log(fillRes.status);                     // 'completed' | 'failed' | 'unknown'
  for (const f of fillRes.fields) {
    // f.index: 0-based index into the request; f.status: 'filled' | 'failed' | 'not_attempted' | 'unknown'
    // f.error_code: 'target_changed' | 'element_not_found' | 'ambiguous_selector' |
    //               'element_not_editable' | 'option_not_found' | 'timeout' | 'execution_failed'
    console.log(`Field ${f.index}: ${f.status} (${f.error_code ?? 'ok'})`);
  }
}
```

Contract:
- `page_url` must exactly match one open top-level page (no prefix match, no navigation). Credentials may omit it only if the browser has exactly one open page; credential items have no destination allowlist, so **you** authorize the destination.
- Each selector must resolve to exactly one editable input/select across the main frame and all descendant frames (a container selector works if it contains exactly one editable element); two bindings may not target one element. `select` matches option **values**, not labels. 1-32 bindings, filled in request order, stopping at the first failure (earlier writes are not rolled back; later bindings are `not_attempted`). Values are typed character by character with a short randomized delay (paced fill).
- `fill` never clicks or submits (input/change handlers may still trigger site behavior). `completed` is not login success. Submit once yourself and verify the site's response.
- Known failures return **HTTP 200** with `failed`/`unknown`; always read the body. Validation errors before writing are 400/403/404/409 (nothing written).
- `fill` is safe to retry after `failed`, `unknown` or a lost response (a retry right after `unknown` can wait up to 15 s for the earlier attempt's browser lock). SDK retries are disabled on `performOperation`, so retry in your code.
- The CLI exits non-zero on `failed`/`unknown` but keeps the value-free result on stdout with `-o json`.

### 2.3 WebMCP invocation with vault values

Bind credential fields into a live WebMCP tool call (the tool may submit or have other side effects; its output is returned unredacted and may include the values):

```ts
await kernel.vaults.items.performOperation('portal-login', {
  id_or_name: vault.id,
  type: 'webmcp_invoke',
  browser_id: session.session_id,
  page_url: 'https://store.example.com',     // exact top-level URL from the discovered tool's source
  tool_ref: 'tool_ref_from_discovery',       // opaque ref from browsers.webmcp tool discovery
  input: { cart_id: 'cart_456', auth_token: null },   // an existing null slot per binding
  bindings: [{ field: 'password', input_path: '/auth_token' }],   // RFC 6901 pointer to that null
});
```

`input` is max 64 KiB; each `input_path` and each `field` may appear once; no root or array-append paths; a totp binding supplies a code. Statuses: `completed | canceled | error | awaiting_submission | unknown`. `unknown` is not retried automatically.

### 2.4 Managed-auth-backed items ("Fill from Managed Auth")

Reuse the credential Managed Auth saved for a user, without collecting it twice:

```ts
const maItem = await kernel.vaults.items.upsert('github-login', {
  id_or_name: vault.id,
  type: 'credential',
  spec: { provider: 'managed_auth', connection_id: auth.id, description: 'GitHub' },
});
if (maItem.type === 'credential' && maItem.state.provider === 'managed_auth') {
  console.log(Object.keys(maItem.state.fields ?? {}));   // bind fill fields by these names; list responses omit them
}
```

- Requires a connection that holds a saved **Kernel** credential (connection `status` may be `NEEDS_AUTH`), in the same project as the vault and browser. `404` unknown connection; `409` no saved values yet, other project, or an external provider (1Password).
- Created `ready` (no collection form, no `collect`, no `wait` needed); `update` returns 409; `description` is fixed at creation. The item reads the connection's credential on each read/fill, so Managed Auth changes apply immediately and `version` stays 1.
- `state.status` becomes `unavailable` (no operations) with `status_reason` `no_credential`, `connection_not_found` (create a new item) or `external_credential`; it returns to `ready` once the connection holds a saved Kernel credential again.
- `state.fields` entries are `text | email | password | totp`; a `totp` field exists only if the credential has a TOTP secret (a login does not save one), and fill uses the credential's own algorithm/digits/period.
- Fill does not restrict to the connection's domain: authorize the destination yourself. For a TOTP prompt on a later page, invoke `fill` again with only the `totp` binding.

---

## 3. Observe: `wait`, `expand`, events

- `items.retrieve(key, { id_or_name, wait?, expand? })`: `wait` (0-60 s) holds while the item is pending authorization, approval or collection; `expand: ['payment_methods']` only when `available_expansions` advertises it (live provider data, not persisted).
- `items.events(key, { id_or_name, after?, wait? })`: immutable event array (`id`, `name`, `browser_id?`, `data`, `created_at`); pass the last `id` as `after`; `wait` long-polls up to 60 s; an empty array is not a failure.
- Run an observer (retrieve with `wait: 5` plus events) **before** the agent submits a payment checkout, and keep it running until the merchant order is terminal. Correlate `browser_id` when a vault is attached to several sessions.

```ts
async function observePayment(vaultId: string, key: string, stop: AbortSignal): Promise<void> {
  let after: string | undefined;
  while (!stop.aborted) {
    const cur = await kernel.vaults.items.retrieve(key, { id_or_name: vaultId, wait: 5 });
    if (cur.action && 'url' in cur.action) { /* hand cur.action.url to your authenticated UI only */ }
    const events = await kernel.vaults.items.events(key, { id_or_name: vaultId, after, wait: 5 });
    for (const e of events) { console.log(e.id, e.name, e.browser_id); after = e.id; }
  }
}
```

---

## 4. Payments

Rules (both providers):
- Verify merchant, items, amount and currency from a trusted source (your order backend, or deterministic page data), show them to the user, freeze that object, and derive the card spec from it. Agent-proposed values are untrusted.
- Present wallet enrollment and approval actions in your own authenticated UI, never to the agent or its browser.
- Submit checkout **once**. Never retry a failed, timed-out or indeterminate payment, never fall back from `fill` to aliases. Success = the merchant's order record shows a matching paid order; fill `completed`, item `ready` or a success page is not proof.
- `recovery_required` (card) means an unresolved provider outcome: it blocks new authorization, checkout, and deletion of the card, its wallet and its vault. There is no reset; reconcile with the provider/support.
- At most one wallet per provider per vault (the API only enforces unique keys): list items first and reuse.

Wallet provider configs are optional: Kernel-managed OAuth clients are the default. Create your own only to bring your own Link/AgentCard OAuth client; this needs an **organization-scoped** key (project-scoped keys get 403), names are unique per org (409), delete is 409 while referenced:

```ts
const orgKernel = new Kernel({ apiKey: process.env.KERNEL_ORG_API_KEY! });
await orgKernel.vaultProviderConfigs.create({
  name: 'link-prod',
  provider: 'link',
  credentials: {
    client_id: process.env.LINK_CLIENT_ID!,
    client_secret: process.env.LINK_CLIENT_SECRET!,
    publishable_key: 'pk_live_...',    // Link only; used to refresh/revoke imported grants
  },
});
// AgentCard: credentials { client_id, client_secret }; response exposes test_mode (true = sandbox)
```

### 4.1 Link by Stripe (single-use card, `fill`)

Link supports only users with US phone numbers; card creation is live-only (no `spec.test`).

```ts
// app-owned: publishes an action URL to the end user's authenticated session
declare function presentProviderAction(item: unknown): Promise<void>;

const payKernel = new Kernel({ projectID: process.env.KERNEL_PROJECT_ID, maxRetries: 0 });

// 1. Wallet, then wait for `connected`
let wallet = await payKernel.vaults.items.upsert('link-wallet', {
  id_or_name: vault.id,
  type: 'wallet',
  spec: { provider: 'link', authorization: { method: 'oauth', client: { type: 'kernel_managed' } } },
});
if (wallet.action?.name === 'link_oauth') await presentProviderAction(wallet);
wallet = await payKernel.vaults.items.retrieve(wallet.key, { id_or_name: vault.id, wait: 60 });
if (wallet.type !== 'wallet' || wallet.state.status !== 'connected') throw new Error('wallet not connected');

// 2. Let the user choose a payment method (eligible=false is the only explicit negative)
const withMethods = await payKernel.vaults.items.retrieve(wallet.key, {
  id_or_name: vault.id,
  expand: ['payment_methods'],
});
const methods = withMethods.type === 'wallet' ? (withMethods.expanded?.payment_methods ?? []) : [];

// 3. Card item from the verified purchase (amount in minor units, 1-50000)
const cardSpec = {
  provider: 'link' as const,
  wallet: wallet.key,
  payment_method_id: methods[0].id,     // the user's pick
  amount: 2306,
  currency: 'usd',
  merchant_name: 'example shop',
  merchant_url: 'https://shop.example.com',
  context:                               // at least 100 characters
    'buy one notebook from example shop for a total of 23.06 usd, including tax and shipping. ' +
    'this request is for this purchase only and must not be repeated.',
};
const card = await payKernel.vaults.items.upsert('notebook-order', { id_or_name: vault.id, type: 'card', spec: cardSpec });

// 4. Authorize after explicit user approval, present the returned action, wait for `ready`
await payKernel.vaults.items.performOperation(card.key, { id_or_name: vault.id, type: 'authorize' });
let ready = await payKernel.vaults.items.retrieve(card.key, { id_or_name: vault.id });
if (ready.action && 'url' in ready.action) await presentProviderAction(ready);   // spend_approval / push_approval
ready = await payKernel.vaults.items.retrieve(card.key, { id_or_name: vault.id, wait: 60 });
if (ready.type !== 'card' || ready.state.status !== 'ready'
    || !ready.available_operations.some((op) => op.type === 'fill')) {
  throw new Error('card not ready to fill');
}

// 5. Fill the checkout
const fill = await payKernel.vaults.items.performOperation(card.key, {
  id_or_name: vault.id,
  type: 'fill',
  browser_id: session.session_id,
  page_url: 'https://shop.example.com/checkout',   // https, same origin as merchant_url; else 403 destination_denied
  fields: [
    { field: 'number', selector: '#card-number' },
    { field: 'expiration', selector: '#expiry', format: 'MM/YY' },
    { field: 'cvc', selector: '#security-code' },
  ],
  timeout_ms: 10_000,
});
if (fill.type !== 'fill' || fill.status !== 'completed') throw new Error('fill did not complete');
```

Card fill fields: `number`, `cvc`, `exp_month` (MM), `exp_year` (YYYY), combined `expiration` (**requires** `format: 'MM/YY' | 'MM/YYYY'`; `format` is forbidden on every other field), and `billing_name`, `billing_line1`, `billing_line2`, `billing_city`, `billing_state`, `billing_postal_code`, `billing_country`. Request only needed billing fields: an absent/empty one returns `400 field_unavailable` before any write. 1-32 ordered bindings. Card states: `requested, pending_authorization, ready, consumed, expired, declined, recovery_required`; wallet: `pending_authorization, connected, declined, reconnect_required, degraded`. Card updates replace the whole spec and are allowed only while `requested`. Never repeat `authorize` or create a replacement to retry an unknown purchase.

### 4.2 Kernel wallets (`provider: 'kernel'`; SDK/CLI only, not in public docs)

A user enrolls a card on a Kernel-hosted page (`card_enrollment` action); Kernel obtains an agentic network token and one-time code (VGS) and `fill` types them on `merchant_url`'s origin.

```ts
const kw = await payKernel.vaults.items.upsert('kernel-wallet', { id_or_name: vault.id, type: 'wallet', spec: { provider: 'kernel' } });
// present kw.action (card_enrollment) to the user, then wait for state.status === 'connected'
await payKernel.vaults.items.upsert('kernel-order', {
  id_or_name: vault.id,
  type: 'card',
  spec: {
    provider: 'kernel',
    wallet: 'kernel-wallet',
    amount: 4999,                       // minor units, at most 50000
    currency: 'usd',                    // aud brl cad chf czk dkk eur gbp hkd inr jpy krw mxn nok nzd pln sek sgd usd zar
    merchant_name: 'Acme Supplies',
    merchant_url: 'https://acme.example.com',
    merchant_country: 'US',             // required for Visa cards
  },
});
```

Then `authorize` and `fill` as for Link. Visa purchases need a `spend_approval` (Visa passkey) action before the code is issued; Mastercard needs none; the code is valid until the item's `expires_at`, so fill and submit before then. `authorize` returns 400 until the enrolled card's `capabilities.single_use_card.eligible` is true. Card updates are not supported (delete and recreate). Wallet states: `pending_authorization, connected, reconnect_required, degraded` (degraded: delete the wallet before adding another card).

### 4.3 AgentCard (alias egress interception, not `fill`)

The agent types Luhn-valid aliases from `card.state.aliases` (`number`, `cvc`, `exp_month`, `exp_year`) into the merchant form; when a recognized processor request containing the aliases is submitted, Kernel holds it, the user approves (Face ID), AgentCard executes it and Kernel replays the response. There is no `authorize` operation. Recognized processors need a native adapter (docs list Stripe, Shopify, Square, Recurly, Razorpay, Braintree, Worldpay, Bambora, Mercado Pago; the SDK also supports Adyen Sessions).

```ts
let acWallet = await payKernel.vaults.items.upsert('agentcard-wallet', {
  id_or_name: vault.id, type: 'wallet', spec: { provider: 'agentcard' },
});
if (acWallet.action?.name === 'card_enrollment') await presentProviderAction(acWallet);
acWallet = await payKernel.vaults.items.retrieve(acWallet.key, { id_or_name: vault.id, wait: 60 });
if (acWallet.type !== 'wallet' || acWallet.state.status !== 'connected') throw new Error('wallet not connected');

const ac = await payKernel.vaults.items.upsert('corp-procurement-card', {
  id_or_name: vault.id,
  type: 'card',
  spec: {
    provider: 'agentcard',
    wallet: acWallet.key,
    merchant: 'Example Shop',          // shown on the approval screen; not an enforced origin
    amount: 5000,
    currency: 'usd',
    checkout_origin: 'https://store.example.com',   // optional; https, lowercase host, no path; for autopilot rule matching
    // card_id?: pin an enrolled card; omitted = user picks at approval
  },
});
if (ac.type === 'card' && ac.state.provider === 'agentcard' && ac.state.status === 'ready' && ac.state.aliases) {
  const { number, exp_month, exp_year, cvc } = ac.state.aliases;   // give these to the agent
}
```

- Start the observer (section 3) before the browser submits; while a request is held, `retrieve` the card and hand `action.url` to the user. `state.authorization` has `status` (`awaiting_approval | approved | declined | expired`), expected/actual amounts, `charged_kind`, `replay_delivered`. After settling the card returns to `ready` (reusable, one authorization pending at a time); that does not prove the purchase.
- Card states: `requested, ready, preparing, ready_to_submit, pending_approval, consumed, stopped, outcome_unknown, degraded, recovery_required`. Updates replace the whole spec (re-include `checkout_origin`/`card_id`) and work only while `requested` or `ready`.
- **Prepared single-use checkout** (Square, Braintree, Worldpay, Bambora, Mercado Pago, Adyen; Square must use it in current deployments): invoke `prepare_checkout`, keep the returned approval page open, poll until `state.status === 'ready_to_submit'`, then submit the native pay request before `preparation.expires_at` (readiness lasts at most 30 s). Preparations are single-use even after failure or expiry; do not retry automatically.

```ts
await payKernel.vaults.items.performOperation('corp-procurement-card', {
  id_or_name: vault.id,
  type: 'prepare_checkout',
  checkout: {
    browser_id: session.session_id,
    environment: 'production',      // 'production' | 'sandbox' for Square/Braintree/Worldpay/Adyen; 'shared' for Bambora/Mercado Pago
    merchant_origin: 'https://store.example.com',   // top-level merchant page origin, not a processor iframe
    psp: 'square',                  // 'square' | 'braintree' | 'worldpay' | 'bambora' | 'mercado_pago' | 'adyen'; omit for Square
  },
});
```

  Adyen: fill public dummy card fields, not vault aliases. CLI: `kernel vaults items invoke <vault> <card> prepare_checkout --params '{"checkout":{...}}'` (or `--spec-file`).

---

## 5. 1Password Agentic Autofill (preview)

The end user approves, in the 1Password app, access to logins that stay in their private (non-shared) 1Password vault; passkeys are unsupported. Ask the user which path they want; fall back to a `provider: 'kernel'` credential (section 2) if they decline, the login is in a shared vault or is a passkey, linking fails, or the request ends `declined`/`failed`.

```ts
// 1. Link the account (Kernel-managed OAuth client); present action.url to the user, wait for connected
let acct = await kernel.vaults.items.upsert('1password-account', {
  id_or_name: vault.id,
  type: 'credential_account',
  spec: { provider: '1password', authorization: { method: 'oauth', client: { type: 'kernel_managed' } } },
});
if (acct.type === 'credential_account' && acct.action?.name === '1password_oauth') { /* present acct.action.url */ }
acct = await kernel.vaults.items.retrieve('1password-account', { id_or_name: vault.id, wait: 60 });
if (acct.type !== 'credential_account' || acct.state.status !== 'connected') throw new Error("1Password account isn't connected");

// 2. Describe the login (1-5 `login` entries, https `website`; goal max 140 chars, reason max 100)
await kernel.vaults.items.upsert('supplier-login', {
  id_or_name: vault.id,
  type: 'credential',
  spec: {
    provider: '1password',
    account: '1password-account',
    requests: {
      version: 2,
      goal: 'Log into supplier portal to download invoice',
      entries: [{ type: 'login', parameters: { website: 'https://supplier.example.com' }, reason: 'Supplier Portal login' }],
    },
  },
});

// 3. Request access (no browser needed); hand the onepassword:// approval link to the user (it grants nothing until they approve; 2-minute prompt)
const requested = await kernel.vaults.items.performOperation('supplier-login', {
  id_or_name: vault.id,
  type: '1pw_create_access_request',
});
if (requested.type === 'credential' && requested.action?.name === '1password_access_approval') { /* present requested.action.url */ }

// 4. Poll the decision (timeout_seconds 0-120, default 10); the decision is recorded only when you poll
let state: Kernel.Vaults.VaultItemOperationResponse = requested;
while (state.type === 'credential' && state.state.status === 'pending_authorization') {
  state = await kernel.vaults.items.performOperation('supplier-login', {
    id_or_name: vault.id,
    type: '1pw_access_request_status',
    timeout_seconds: 60,
  });
}
if (state.type !== 'credential' || state.state.status !== 'ready') throw new Error("1Password access wasn't granted");

// 5. Fill and submit: the page must be on the approved login's origin
const filled = await kernel.vaults.items.performOperation('supplier-login', {
  id_or_name: vault.id,
  type: '1pw_fill',
  browser_id: session.session_id,
  page_url: 'https://supplier.example.com/login',
  // entry_id: required when several approved entries share this origin; timeout_ms 1-30000 (default 30000)
});
if (filled.type === '1pw_fill') console.log(filled.status, filled.error_code);
```

- Statuses: item `pending_authorization -> ready | declined | failed` (`declined`/`failed` are final: create a new item key to ask again). A `ready` item does not expire when the 1Password grant does (30 days at launch; connection about 90 days), and it cannot be asked again; create a new item.
- `1pw_fill` outcomes: `fill_submitted` (extension submitted; login not verified), `fill_failed` (`error_code` `fillFailed | noExistingCredentials | authenticationFailed`), `fill_unknown` (inconclusive; `autosubmitFailed` means it filled and submitted but could not confirm; inspect the page before falling back). Errors: `400 page_not_found | ambiguous_page | invalid_request`, `403 destination_denied`, `409 agentic_mode_unavailable` or item not ready / token expired / `entry_id` mismatch.
- For multi-page sign-ins invoke `1pw_fill` again on each page (each must share the origin; each is a new 1Password request).
- **Exclusive control**: while `1pw_fill` runs, new CDP, WebDriver and browser API requests get `423 Locked` and existing control connections are interrupted; reconnect afterwards. Live view is **not** locked: anyone with it can watch and send input during the fill.
- Never retry an uncertain access request automatically (an item allows one open request). Recovery: `1pw_recover` when advertised (never delete the account to recover). Delete every credential item that references an account before deleting the `credential_account` (else 409).
- Bring-your-own OAuth client: omit `account`, send `access_token` + `integration_key` (+ `access_token_expires_at`) in the credential spec; refresh tokens on your backend and send `1pw_update_access_token` (via `--spec-file` in the CLI) before each task. Items stop advertising operations after `access_token_expires_at`.
- Distinct from the service-account integration for Managed Auth ([profiles-pools-credentials.md](profiles-pools-credentials.md)).

---

## 6. Machine Payments Protocol (MPP): buy a browser

An agent with no Kernel account or API key buys one stealth, headful browser for 30 minutes for $0.50 (read the 402 challenge for the current price and duration). Link through Stripe's `link-cli` is the only supported payment flow; plain `fetch` does not handle the 402 challenge, and card details or stablecoins are not accepted.

```bash
# Inspect the offer without paying
curl -i -X POST https://api.onkernel.com/mpp/browsers
# Pay (Link CLI shows an approval URL; --context must be at least 100 characters)
link-cli mpp pay https://api.onkernel.com/mpp/browsers --method POST \
  --context "Buying a 30 minute Kernel stealth browser session at the customer's request so the assistant can run a browser task for them." \
  --data '{"email":"agent@example.com"}'
```

Flow: unauthenticated `POST /mpp/browsers` -> `402` with `WWW-Authenticate: Payment`; `link-cli` retries with `Authorization: Payment <credential>` (a Stripe shared payment token); `200` returns `session_id`, `cdp_ws_url`, `webdriver_ws_url`, `browser_live_view_url` (when available) and `expires_at` (`payment.amount` is in US cents). `--data` is an optional receipt-email body. The challenge expires after 30 minutes (time to approve, not browser lifetime). If the paid request times out, retry with the **same credential** to get the same browser without a second charge; after `expires_at` a retry returns a new 402 (`session_expired`). A failed create after charging attempts a refund (`503` with `refund_id`). Treat the URLs as credentials. The purchase returns URLs only; it provisions no vault. Use account-based browsers for merchant checkout, vaults and project management.

---

## 7. Client UI: `@onkernel/vault-react` (v0.2.0)

Custom-branded credential collection for your own page. The page reads a one-time capability token from the **URL fragment** (`/credentials/collect#token=...`; never path/query/cookie/storage) and sends it as `Authorization: Bearer` to a same-origin endpoint; your backend hashes it, maps it to `{vaultId, itemKey, itemId, expiresAt}`, and calls `items.retrieve` / `items.update` (send `expected_item_id` and the rendered `version`). Do not expose the Kernel API key to the frontend. Server code can import safe types from `@onkernel/vault-react/data`. The package ships no stylesheet.

```tsx
'use client';
import { CredentialForm, CredentialFormError, safeCredentialItem } from '@onkernel/vault-react';

export function AddCredentialModal({ itemFromBackend, tokenFromHash }: { itemFromBackend: unknown; tokenFromHash: string }) {
  return (
    <CredentialForm
      className="my-credentials"
      item={safeCredentialItem(itemFromBackend)}
      onSubmit={async ({ version, fields }) => {
        const res = await fetch('/api/credential-requests/current', {
          method: 'PATCH',
          credentials: 'omit',
          cache: 'no-store',
          headers: { Authorization: `Bearer ${tokenFromHash}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ version, fields }),
        });
        if (res.status === 409) throw new CredentialFormError('stale');
        if (!res.ok) throw new CredentialFormError('invalid');
      }}
    />
  );
}
```

`CredentialFormError` codes: `stale | expired | consumed | unavailable | invalid | network`. `onSubmit` gets `{ version, fields: { [name]: { value: string | null } } }` with changed fields only (`{ fields: {} }` when unchanged); TOTP is never rendered. Sensitive inputs are blank with a show/hide control (`credential-visibility`); required fields need a visible non-empty value every submit.
