# Vaults and Payments: Credentials, Wallets & Agent Purchases

Kernel Vaults provide project-scoped, KMS-encrypted storage for sensitive credentials, Stripe Link wallets, AgentCard payment instruments, and native payment cards.

Vault secrets and payment cards are kept isolated from agent LLM contexts, prompt traces, session recordings, and plain logs while automating human-paced DOM autofill and egress payment authorization.

---

## 1. Core Architecture & Concepts

1. **Vaults:** Project-scoped encrypted containers (`kernel.vaults.*`). Bound to a browser session at creation time via `vaults: [{ id }]` or `vaults: [{ name }]` (up to 20 references) and are **immutable** for the life of that session. Free-tier organizations can store up to 3 non-deleted vaults across all projects (`limits.max_vaults: 3`).
2. **Credential Items:** Logins, passwords, API tokens, and arbitrary form fields (`kernel.vaults.items.*`). Supports TOTP generation. Each field has a stable `name`, an optional human-readable `label` (up to 128 bytes UTF-8), and optional client-side JWE ECDH-ES encryption (`encrypted_value` via `retrieveEncryptionKey`).
3. **Brokered Providers:** Native integrations for `provider: 'managed_auth'` (linking Managed Auth connections directly into vaults) and `provider: '1password'` (1Password Agentic Autofill).
4. **Paced Fill:** Character-by-character typing with randomized human delays into DOM selectors via `kernel.vaults.items.performOperation(key, { type: 'fill', ... })`. Supported for general credential items (`provider: 'kernel'`), Link cards (`provider: 'link'`), and native Kernel cards (`provider: 'kernel'`, backed by VGS network tokens). Returns structured per-field error codes (`target_changed`, `element_not_found`, etc.).
5. **WebMCP Invocation with Vault Secrets:** Invoke WebMCP tools in-browser using vault secrets (`type: 'webmcp_invoke'`) without exposing sensitive tokens to LLM prompt context.
6. **AgentCard Payment Instruments:** Virtual cards with autopilot authorization rules. Uses **alias-based egress interception**, NOT DOM fill. For payment gateways requiring prepared single-use checkout (Square, Braintree, Worldpay, Bambora, Mercado Pago, and Adyen), the card must execute `prepare_checkout` (`type: 'prepare_checkout'`).
7. **1Password Agentic Autofill (Preview):** End users authorize an agent to access logins from their personal 1Password account without exporting secrets. The 1Password extension detects fields autonomously (zero DOM selectors required), locks the browser for exclusive automation (`423 Locked`), while Live View continues streaming, and auto-submits upon completion.
8. **Machine Payments Protocol (MPP):** Out-of-band HTTP 402 protocol allowing autonomous agents to purchase browser sessions with Stripe Link via `link-cli mpp pay` without a Kernel account. (Not a vault storage item).

---

## 2. Vault Lifecycle & Session Attachment

```ts
import Kernel from '@onkernel/sdk';
const kernel = new Kernel();

// 1. Create or retrieve a project-scoped vault (max 3 on free tier)
const vault = await kernel.vaults.upsert({ name: 'checkout-vault' });

// 2. Link vault to browser at creation (supports up to 20 vaults by id or name; immutable after boot)
const session = await kernel.browsers.create({
  stealth: true,
  vaults: [{ id: vault.id }], // or { name: 'checkout-vault' }
  timeout_seconds: 600,
});
```

---

## 3. General Credential Items & Paced DOM Fill

### Creating a Credential Item with Field Labels
```ts
await kernel.vaults.items.upsert('user-login', {
  id_or_name: 'checkout-vault',
  type: 'credential',
  spec: {
    provider: 'kernel',
    fields: [
      { name: 'username', label: 'Work Email', type: 'email', value: 'agent@example.com' },
      { name: 'password', label: 'Account Password', type: 'password', value: process.env.SERVICE_PASSWORD! },
      { name: 'totp', label: 'Two-Factor Seed', type: 'totp', value: 'JBSWY3DPEHPK3PXP' },
    ],
  },
});
```

### Client-Side Encryption for Sensitive Values (ECDH-ES / A256GCM)
For zero-knowledge secrets, encrypt values client-side using the vault's public key before calling `upsert`:
```ts
// 1. Fetch vault public key
const key = await kernel.vaults.retrieveEncryptionKey('checkout-vault');
// key: { alg: 'ECDH-ES', enc: 'A256GCM', jwk: {...}, kid: '...' }

// 2. Encrypt value into JWE string using vault JWK (e.g. jose library)
const encryptedSecret = await encryptWithJwk(key.jwk, process.env.SERVICE_PASSWORD!);

// 3. Upsert using encrypted_value instead of plain value
await kernel.vaults.items.upsert('zero-knowledge-secret', {
  id_or_name: 'checkout-vault',
  type: 'credential',
  spec: {
    provider: 'kernel',
    fields: [
      { name: 'apiKey', type: 'password', encrypted_value: encryptedSecret },
    ],
  },
});
```

### Managed Auth Credential Provider in Vaults
Link an active Managed Auth connection directly into a vault item:
```ts
await kernel.vaults.items.upsert('managed-login', {
  id_or_name: 'checkout-vault',
  type: 'credential',
  spec: {
    provider: 'managed_auth',
    connection_id: 'conn_12345',
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
    // field.error_code: 'target_changed' | 'element_not_found' | 'ambiguous_selector' |
    //                   'element_not_editable' | 'option_not_found' | 'timeout' | 'execution_failed'
    console.log(`Field index ${field.index}: ${field.status} (${field.error_code ?? 'ok'})`);
  }
}
```

### WebMCP Tool Invocation with Vault Credentials
Invoke tools registered in the browser (or via polyfill) using vault credentials without injecting secrets into LLM prompts:
```ts
await kernel.vaults.items.performOperation('user-login', {
  id_or_name: 'checkout-vault',
  type: 'webmcp_invoke',
  browser_id: session.session_id,
  page_url: 'https://store.example.com',
  tool_ref: 'checkout_cart',
  input: { cart_id: 'cart_456' },
  bindings: [
    { field: 'password', input_path: 'auth_token' },
  ],
});
```

---

## 4. Payment Cards & Wallets

### Vault Provider Configurations CRUD
Configure third-party payment providers at the organization level:
```ts
// Configure Stripe Link or AgentCard provider credentials
await kernel.vaultProviderConfigs.create({
  name: 'link-prod',
  provider: 'link',
  credentials: {
    publishable_key: 'pk_live_...',
    client_id: process.env.STRIPE_CLIENT_ID!,
    client_secret: process.env.STRIPE_CLIENT_SECRET!,
  },
});
```

### Stripe Link & Native Kernel Cards (DOM Fill)
Stripe Link and native Kernel cards (`provider: 'kernel'`, backed by VGS network tokens) use DOM fill to inject payment details:
```ts
// 1. Create Link Wallet
const wallet = await kernel.vaults.items.upsert('link-wallet', {
  id_or_name: 'checkout-vault',
  type: 'wallet',
  spec: {
    provider: 'link',
    authorization: { method: 'oauth', client: { type: 'kernel_managed' } },
  },
});

// 2. Create payment card item
const card = await kernel.vaults.items.upsert('order-card', {
  id_or_name: 'checkout-vault',
  type: 'card',
  spec: {
    provider: 'link',
    wallet: 'link-wallet',
    payment_method_id: 'pm_card_123',
    context: 'Order checkout context',
    amount: 4999, // in cents
    currency: 'USD',
    merchant_name: 'Acme Supplies',
    merchant_url: 'https://acme.example.com',
  },
});

// 3. Fill card into DOM
await kernel.vaults.items.performOperation('order-card', {
  id_or_name: 'checkout-vault',
  type: 'fill',
  browser_id: session.session_id,
  page_url: 'https://acme.example.com/checkout',
  fields: [
    { field: 'card_number', selector: 'input#card-nr' },
    { field: 'exp_date', selector: 'input#exp' },
    { field: 'cvc', selector: 'input#cvc' },
  ],
});
```

### AgentCard: Egress Interception & Prepared Single-Use Checkout
AgentCard provides virtual payment cards with automated rule matching and spend controls:

1. **Autopilot Matching & Alias Typing**:
   Kernel generates a Luhn-valid stand-in alias card (`card.state.aliases`). The agent types the non-sensitive alias card into the DOM. When the merchant charges the card, Kernel's egress network intercepts the payment gateway request, matches autopilot rules against `checkout_origin`, and authorizes the transaction.

2. **Prepared Checkout Requirement (`prepare_checkout`)**:
   Processors like Square, Braintree, Worldpay, Bambora, Mercado Pago, and Adyen require the card item to execute `prepare_checkout` (`type: 'prepare_checkout'`) before native submission. In current Kernel deployments, prepared checkout is enabled; Square checkouts **must** call `prepare_checkout`:

```ts
// Provision an AgentCard with checkout_origin
const agentCard = await kernel.vaults.items.upsert('corp-procurement-card', {
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

// For Square, Braintree, Adyen, etc.: Prepare checkout prior to submission
await kernel.vaults.items.performOperation('corp-procurement-card', {
  id_or_name: 'checkout-vault',
  type: 'prepare_checkout',
  checkout: {
    browser_id: session.session_id,
    environment: 'production',
    merchant_origin: 'https://store.example.com',
    psp: 'square',
  },
});

// Access Luhn-valid stand-in aliases for typing
if (agentCard.type === 'card' && agentCard.state.provider === 'agentcard' && agentCard.state.aliases) {
  const { number, exp_month, exp_year, cvc } = agentCard.state.aliases;
  console.log('Alias Card to enter in DOM:', number, `${exp_month}/${exp_year}`, cvc);
}
```

---

## 5. 1Password Agentic Autofill (Preview)

Allows end-users to grant temporary access to specific logins in their 1Password vaults without exporting passwords:

1. **Connect 1Password Account Item** (`type: 'credential_account'`):
   ```ts
   await kernel.vaults.items.upsert('user-1password-account', {
     id_or_name: 'checkout-vault',
     type: 'credential_account',
     spec: {
       provider: '1password',
       authorization: { method: 'oauth', client: { type: 'kernel_managed' } },
     },
   });
   ```

2. **Define Credential Item referencing the Account** (`type: 'credential'`):
   ```ts
   await kernel.vaults.items.upsert('supplier-login', {
     id_or_name: 'checkout-vault',
     type: 'credential',
     spec: {
       provider: '1password',
       account: 'user-1password-account',
       requests: {
         version: 2,
         goal: 'Log into supplier portal to download invoice',
         entries: [
           {
             type: 'login',
             parameters: { website: 'https://supplier.example.com' },
             reason: 'Supplier Portal login',
           },
         ],
       },
     },
   });
   ```

3. **Request Access & Poll Approval on the Credential Item**:
   ```ts
   // Create access request on the credential item (NOT the account item)
   await kernel.vaults.items.performOperation('supplier-login', {
     id_or_name: 'checkout-vault',
     type: '1pw_create_access_request',
   });

   // Poll approval status
   const status = await kernel.vaults.items.performOperation('supplier-login', {
     id_or_name: 'checkout-vault',
     type: '1pw_access_request_status',
     timeout_seconds: 60,
   });
   ```

4. **Trigger Autofill**:
   ```ts
   await kernel.vaults.items.performOperation('supplier-login', {
     id_or_name: 'checkout-vault',
     type: '1pw_fill',
     browser_id: session.session_id,
     page_url: 'https://portal.supplier.com/login',
   });
   ```

   *Exclusive Control Invariant*: While `1pw_fill` executes, Kernel gives exclusive control to the 1Password extension. Any new CDP, WebDriver, or browser API automation requests are rejected with HTTP `423 Locked`. **Live View is NOT locked**; human operators can continue watching the session stream. Unlike general `fill`, the 1Password extension automatically detects fields, types credentials, and submits the form without manual DOM selectors.

---

## 6. Machine Payments Protocol (MPP) Browser Purchases

The Machine Payments Protocol allows autonomous agents without a Kernel account or API key to acquire an isolated browser session:

- **Endpoint**: `POST https://api.onkernel.com/mpp/browsers`
- **Pricing**: Fixed $0.50 per 30-minute browser session.
- **Protocol Flow**:
  1. Agent submits request without credentials.
  2. Kernel returns HTTP `402 Payment Required` with header `WWW-Authenticate: Payment`.
  3. Agent completes payment using Stripe Link shared payment token via `link-cli mpp pay`.
  4. Agent replays request with payment proof and receives browser connection URLs (`cdp_ws_url`, `browser_live_view_url`).

```bash
# Purchase a 30-minute stealth session via Stripe Link CLI
link-cli mpp pay https://api.onkernel.com/mpp/browsers --method POST --data '{"email":"user@example.com"}'
```

---

## 7. Client UI: `@onkernel/vault-react` (v0.2.0)

For secure credential capture in React web applications:

```tsx
'use client';
import { CredentialForm, CredentialFormError, safeCredentialItem } from '@onkernel/vault-react';

export function AddCredentialModal({ itemFromBackend, tokenFromHash }: { itemFromBackend: any; tokenFromHash: string }) {
  return (
    <CredentialForm
      className="my-credentials"
      item={safeCredentialItem(itemFromBackend)}
      onSubmit={async ({ version, fields }) => {
        const res = await fetch('/api/credentials/submit', {
          method: 'PATCH',
          headers: {
            Authorization: `Bearer ${tokenFromHash}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ version, fields }),
        });
        if (res.status === 409) throw new CredentialFormError('stale');
        if (!res.ok) throw new CredentialFormError('invalid');
      }}
    />
  );
}
```

The component renders show/hide password toggles (`credential-visibility` button), validates fields natively, and transforms submitted fields into a typed payload. Rejections in `onSubmit` throw `new CredentialFormError('stale')` or `new CredentialFormError('invalid')`.
