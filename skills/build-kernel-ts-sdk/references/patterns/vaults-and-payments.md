# Vaults and Payments: Credentials, Wallets & Agent Purchases

Kernel Vaults provide project-scoped, KMS-encrypted storage for sensitive credentials, Stripe Link wallets, and AgentCard payment instruments.

Vault secrets and payment cards are kept isolated from agent LLM contexts, prompt traces, session recordings, and plain logs while automating human-paced DOM autofill and egress payment authorization.

---

## 1. Core Architecture & Concepts

1. **Vaults:** Project-scoped encrypted containers (`kernel.vaults.*`). Bound to a browser session at creation time via `vaults: [{ id }]` and are **immutable** for the life of that session.
2. **Credential Items:** Logins, passwords, API tokens, and arbitrary form fields. Supports TOTP generation. Each field has a stable `name` and an optional human-readable `label` (up to 128 bytes UTF-8).
3. **Paced Fill:** Character-by-character typing with randomized human delays into DOM selectors via `kernel.vaults.items.performOperation(key, { type: 'fill', ... })`. Reserved for Link cards and general credentials.
4. **AgentCard Payment Instruments:** Virtual cards with autopilot authorization rules. Uses **alias-based egress interception**, NOT DOM fill.
5. **1Password Agentic Autofill (Preview):** End users authorize an agent to access logins from their personal 1Password account without exporting secrets. The 1Password extension detects fields autonomously (zero DOM selectors required) and locks the browser VM (`423 Locked`) during completion.
6. **Machine Payments Protocol (MPP):** Out-of-band HTTP 402 protocol allowing autonomous agents to purchase browser sessions with Stripe Link without a Kernel account. (Not a vault storage item).

---

## 2. Vault Lifecycle & Session Attachment

```ts
import Kernel from '@onkernel/sdk';
const kernel = new Kernel();

// 1. Create or retrieve a project-scoped vault
const vault = await kernel.vaults.upsert({ name: 'checkout-vault' });

// 2. Link vault to browser at creation (immutable after boot)
const session = await kernel.browsers.create({
  stealth: true,
  vaults: [{ id: vault.id }],
  timeout_seconds: 600,
});
```

---

## 3. General Credential Items & Paced DOM Fill

### Creating a Credential Item
```ts
await kernel.vaults.items.upsert('user-login', {
  id_or_name: 'checkout-vault',
  type: 'credential',
  spec: {
    provider: 'kernel',
    fields: [
      { name: 'username', type: 'email', value: 'agent@example.com' },
      { name: 'password', type: 'password', value: process.env.SERVICE_PASSWORD! },
      { name: 'totp', type: 'totp', value: 'JBSWY3DPEHPK3PXP' },
    ],
  },
});
```

### Performing Paced Autofill
Paced fill types secrets into targeted DOM selectors at human speed. The calling agent never sees the secret plaintext:

```ts
const fillRes = await kernel.vaults.items.performOperation('user-login', {
  id_or_name: 'checkout-vault',
  type: 'fill',
  browser_id: session.session_id,
  page_url: 'https://www.example.com/login', // exact URL must match active tab
  timeout_ms: 15_000,
  fields: [
    { field: 'username', selector: 'input#email' },
    { field: 'password', selector: 'input#password' },
    { field: 'totp', selector: 'input#two-factor-code' },
  ],
});

if (fillRes.type === 'fill') {
  for (const field of fillRes.fields) {
    // field.index is 0-based index into request fields array
    // field.status: 'filled' | 'failed' | 'not_attempted' | 'unknown'
    console.log(`Field index ${field.index}: ${field.status}`);
  }
}
```

---

## 4. Payment Cards & Wallets

### Stripe Link
Stripe Link wallets allow agents to inject saved payment methods during checkout. Provider configurations store the Link publishable key.

### AgentCard: Egress Interception Architecture
AgentCard provides virtual payment cards with automated rule matching and spend controls.

**Critical Architectural Difference**: AgentCard does **NOT** use DOM fill or `authorize` operations! Instead, it uses an **alias-based egress interception flow**:
1. When an AgentCard is provisioned, Kernel generates a Luhn-valid stand-in alias card (`card.state.aliases`).
2. The agent types the non-sensitive alias card details into the checkout form like standard text.
3. When the merchant processes the charge, Kernel's egress network intercepts the payment gateway request, matches the autopilot rules against `checkout_origin`, swaps the alias for the real card token, and authorizes the transaction.

```ts
// Provision an AgentCard in the vault
const card = await kernel.vaults.items.upsert('corp-procurement-card', {
  id_or_name: 'checkout-vault',
  type: 'card',
  spec: {
    provider: 'agentcard',
    wallet: 'wallet-1',
    merchant: 'Example Shop',
    amount: 5000,
    currency: 'USD',
    checkout_origin: 'https://store.example.com',
  },
});

// Access Luhn-valid stand-in aliases for typing
if (card.type === 'card' && card.state.provider === 'agentcard' && card.state.aliases) {
  const { number, exp_month, exp_year, cvc } = card.state.aliases;
  console.log('Alias Card to enter in DOM:', number, `${exp_month}/${exp_year}`, cvc);
}
```

---

## 5. 1Password Agentic Autofill (Preview)

Allows end-users to grant temporary access to specific logins in their 1Password vaults without exporting passwords:

1. **Create Access Request**:
   ```ts
   const req = await kernel.vaults.items.performOperation('user-1password-account', {
     id_or_name: 'checkout-vault',
     type: '1pw_create_access_request',
     goal: 'Log into supplier portal to download invoice',
     reason: 'Monthly procurement reconciliation',
   });
   ```
2. **Poll Status**: Wait until the user approves in their 1Password client.
3. **Trigger Fill**:
   ```ts
   await kernel.vaults.items.performOperation('user-1password-account', {
     id_or_name: 'checkout-vault',
     type: '1pw_fill',
     browser_id: session.session_id,
     page_url: 'https://portal.supplier.com/login',
   });
   ```
   *Note*: `1pw_fill` requires **zero DOM selectors**. The 1Password browser extension detects fields natively, submits the form, and locks the browser microVM (`423 Locked`) while autofill is in progress.

---

## 6. Machine Payments Protocol (MPP) Browser Purchases

The Machine Payments Protocol allows autonomous agents without a Kernel account or API key to acquire an isolated browser session:

- **Endpoint**: `POST https://api.onkernel.com/mpp/browsers`
- **Pricing**: Fixed \$0.50 per 30-minute browser session.
- **Protocol Flow**:
  1. Agent submits request without credentials.
  2. Kernel returns HTTP `402 Payment Required` with header `WWW-Authenticate: Payment`.
  3. Agent completes payment using Stripe Link shared payment token via `link-cli mpp pay`.
  4. Agent replays request with payment proof and receives browser connection URLs (`cdp_ws_url`, `browser_live_view_url`).

---

## 7. Client UI: `@onkernel/vault-react` (v0.2.0)

For secure credential capture in React web applications:

```tsx
'use client';
import { CredentialForm } from '@onkernel/vault-react';

export function AddCredentialModal({ vaultId }: { vaultId: string }) {
  return (
    <CredentialForm
      vaultId={vaultId}
      safeCredentialItem="user-login"
      onSuccess={(item) => console.log('Credential stored securely:', item.id)}
      onError={(err) => console.error('Storage error:', err)}
    />
  );
}
```
