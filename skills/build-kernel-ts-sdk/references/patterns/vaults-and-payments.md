# Vaults and Payments

Kernel Vaults provide project-scoped, encrypted storage and autofill for sensitive credentials, Stripe Link wallets, AgentCard payment instruments, and Machine Payments Protocol (MPP) browser purchases.

Vault secrets and payment cards are injected directly into the browser DOM at human typing speed and are **never exposed to agent LLM context, prompt traces, or plain logs**.

## Core Concepts

1. **Vaults:** Project-scoped encrypted containers (`kernel.vaults.*`).
2. **Credential Items:** Logins, passwords, API tokens, and arbitrary form fields stored within a vault. Each field has a stable `name` and an optional human-readable `label` (up to 128 bytes UTF-8).
3. **Paced Fill:** Character-by-character typing with randomized human delays into DOM selectors via `kernel.vaults.items.performOperation(key, { type: 'fill', ... })`.
4. **Payment Instruments:** Stripe Link wallets and AgentCard virtual cards for autonomous checkouts.
5. **1Password Agentic Autofill (Preview):** End users authorize an agent to access logins from their personal 1Password account without exporting secrets.
6. **MPP Browser Purchases:** Autonomous agents purchase stealth, headful browser sessions through the Machine Payments Protocol via HTTP 402 without a Kernel account or API key.

---

## 1. Vault Lifecycle & Browser Attachment

Vaults are bound to a browser session at creation and are **immutable** for the life of that session.

```ts
import Kernel from '@onkernel/sdk';
const kernel = new Kernel();

// 1. Create or retrieve a project-scoped vault
const vault = await kernel.vaults.upsert({ name: 'checkout-vault' });

// 2. Link vault to browser on creation
const session = await kernel.browsers.create({
  stealth: true,
  vaults: [{ id: vault.id }],
  timeout_seconds: 600,
});
```

---

## 2. General Credential Items & Paced Fill

### Storing Credential Items

Credential fields have stable identifiers (`name`) and optional human-readable UI labels (`label`):

```ts
await kernel.vaults.items.upsert('netflix-account', {
  id_or_name: 'checkout-vault',
  type: 'credential',
  spec: {
    provider: 'managed_auth', // or direct values
  },
});
```

### Performing Paced Autofill

When performing fill, Kernel types character-by-character into the targeted DOM selectors. The agent never sees the secret text.

```ts
const fillRes = await kernel.vaults.items.performOperation('netflix-account', {
  id_or_name: 'checkout-vault',
  type: 'fill',
  browser_id: session.session_id,
  page_url: 'https://www.netflix.com/login', // exact URL must match open tab
  timeout_ms: 15_000,
  fields: [
    { field: 'username', selector: 'input#id_userLoginId' },
    { field: 'password', selector: 'input#id_password' },
  ],
});

// Inspect fill status per field
for (const f of fillRes.fields) {
  // f.status: 'filled' | 'failed' | 'not_attempted' | 'unknown'
  // f.error_code: 'target_changed' | 'element_not_found' | 'ambiguous_selector' | 'element_not_editable' | 'timeout'
  console.log(`Field #${f.index}: ${f.status} (${f.error_code ?? 'ok'})`);
}
```

---

## 3. 1Password Agentic Autofill (Preview)

Allows end-users to approve logins located in their personal 1Password accounts. Once the organization has preview access, operations are executed through `kernel.vaults.items.performOperation`:

```ts
// 1. Create access request
const req = await kernel.vaults.items.performOperation('user-login-key', {
  id_or_name: 'checkout-vault',
  type: '1pw_create_access_request',
  // params: title, message, url
});

// 2. Poll access request status until approved
const status = await kernel.vaults.items.performOperation('user-login-key', {
  id_or_name: 'checkout-vault',
  type: '1pw_access_request_status',
});

// 3. Fill approved credentials into page
await kernel.vaults.items.performOperation('user-login-key', {
  id_or_name: 'checkout-vault',
  type: '1pw_fill',
  browser_id: session.session_id,
  fields: [
    { field: 'username', selector: 'input[name="email"]' },
    { field: 'password', selector: 'input[name="password"]' },
  ],
});
```

---

## 4. Payment Cards & Wallets (Link and AgentCard)

Complete autonomous purchases while isolating card data from the agent.

### Stripe Link

Vault provider configs include the Link publishable key. Agents inject saved cards directly into Link authentication flows.

### AgentCard

AgentCard provides virtual cards with autopilot authorization rules and spending limits:

- **Autopilot Rule Matching:** Uses `checkout_origin` in the card spec to match allowed merchant domains.
- **Preparing Checkout:**
  ```ts
  await kernel.vaults.items.performOperation('card-item-key', {
    id_or_name: 'checkout-vault',
    type: 'prepare_checkout',
    checkout: {
      amount_cents: 2999,
      currency: 'USD',
      merchant: 'Example Store',
    },
  });
  ```
- **Filling Card Elements:**
  ```ts
  await kernel.vaults.items.performOperation('card-item-key', {
    id_or_name: 'checkout-vault',
    type: 'fill',
    browser_id: session.session_id,
    fields: [
      { field: 'card_number', selector: 'input#card-number' },
      { field: 'expiration', selector: 'input#expiry', format: 'MM/YY' },
      { field: 'cvc', selector: 'input#cvc' },
    ],
  });
  ```
- **Authorizing Payment:**
  ```ts
  const authRes = await kernel.vaults.items.performOperation('card-item-key', {
    id_or_name: 'checkout-vault',
    type: 'authorize',
  });
  ```

---

## 5. Machine Payments Protocol (MPP) Browser Purchases

Autonomous external agents can purchase stealth, headful browser sessions directly via the Machine Payments Protocol (MPP) through an HTTP 402 challenge flow without possessing a Kernel account or API key:

```ts
// 1. Send purchase request to MPP endpoint
const buyRes = await fetch('https://api.onkernel.com/mpp/browsers', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    stealth: true,
    timeout_seconds: 300,
  }),
});

if (buyRes.status === 402) {
  // Extract payment challenge (lightning invoice or wallet address)
  const challenge = buyRes.headers.get('Payment-Required');
  // Complete payment via MPP wallet, then re-issue with payment proof
}
```

---

## 6. Client UI: `@onkernel/vault-react`

When building credential-collection UI in React apps, use `@onkernel/vault-react` (v0.2.0+):

```tsx
'use client';
import { VaultFieldCollector } from '@onkernel/vault-react';

export function CredentialInput() {
  return (
    <VaultFieldCollector
      vaultId="vlt_checkout_prod"
      showVisibilityToggle={true} // show/hide control for password fields
      onSuccess={(itemKey) => console.log('Stored item:', itemKey)}
    />
  );
}
```
