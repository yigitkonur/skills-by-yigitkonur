# Enforce Environment Variable Safety with astro:env Server and Client Segregation

> **Context:** Architecture & Philosophy | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

Astro 5 introduces `astro:env`, providing schema-validated, type-safe environment variables. It enforces an architectural boundary between client and server variables. Declaring variables with `access: 'secret'` prevents runtime leaks: secrets cannot be imported into client modules, and missing required variables fail fast at server boot or build time.

## 2. How It Differs From Classic React / Next.js

Next.js relies solely on naming conventions (`NEXT_PUBLIC_`) to control variable exposure. A developer mistakenly prefixing a secret with `NEXT_PUBLIC_` exposes it publicly in client bundles without warning. Astro 5 enforces schema validation in `astro.config.mjs` and restricts imports to dedicated virtual modules (`astro:env/server` vs `astro:env/client`).

## 3. Common Mistakes & Anti-Patterns

Using untyped, raw `process.env` throughout components leads to silent runtime `undefined` bugs and accidental exposure of sensitive keys when passing props to islands.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/components/PaymentModal.astro
// Anti-pattern: Untyped, unchecked process.env usage
const apiKey = process.env.PUBLIC_GATEWAY_KEY; // Might be undefined at runtime!
const secretKey = process.env.GATEWAY_SECRET; // Vulnerable to accidental client passing
---
<payment-element data-key={apiKey} data-secret={secretKey} />
```

### ✅ Best Practice / Idiomatic

```javascript
// astro.config.mjs (Astro 5)
import { defineConfig, envField } from 'astro/config'

export default defineConfig({
  env: {
    schema: {
      PUBLIC_GATEWAY_KEY: envField.string({ context: 'client', access: 'public' }),
      GATEWAY_SECRET: envField.string({ context: 'server', access: 'secret' }),
    },
  },
})
```

```astro
---
// src/components/PaymentModal.astro
// Idiomatic: Strict compile-time and runtime validation
import { PUBLIC_GATEWAY_KEY } from 'astro:env/client';
import { GATEWAY_SECRET } from 'astro:env/server'; // Will throw if imported into a client module
---
<div class="checkout">
  <!-- Only public key is ever rendered to HTML -->
  <button data-public-key={PUBLIC_GATEWAY_KEY}>Pay Now</button>
</div>
```

## 4. Verification & Audit

Run Astro's sync and build commands to validate environment configuration:

```bash
npx astro sync
# Validates environment schema and generates TypeScript types in .astro/env.d.ts
npx astro check
# TypeScript compiler will immediately error if server secrets are imported into client islands
```
