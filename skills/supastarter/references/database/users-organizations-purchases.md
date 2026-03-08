# Users, Organizations, and Purchases

> Focused reference for the model groups you will touch most often in Supastarter. Consult this when tracing auth state, organization membership, or active billing plans.

## Representative relationships

```prisma
model User {
  paymentsCustomerId String?
  purchases          Purchase[]
  members            Member[]
}

model Organization {
  paymentsCustomerId String?
  members            Member[]
  purchases          Purchase[]
}

model Member {
  organizationId String
  userId         String
  role           String

  @@unique([organizationId, userId])
}

model Purchase {
  organizationId String?
  userId         String?
  type           PurchaseType
  subscriptionId String? @unique
  productId      String
  status         String?
}
```

## How the app uses them

- **User** carries auth/profile state, onboarding completion, locale, and optional billing customer ID.
- **Organization** carries team identity plus optional billing customer ID for org-attached billing.
- **Purchase** is the canonical record used by plan resolution helpers and payment webhooks.
- **Member.role** drives org-level authorization in organization settings and selectors.

## Query implications

- If billing is organization-based, most purchase operations must start from the organization context.
- If billing is user-based, personal dashboard flows read purchases directly from `userId`.
- Purchase webhooks update rows by `subscriptionId`, which is why that field is unique.

---

**Related references:**
- `references/payments/checkout-and-portal-flow.md` — How purchase rows map to active plans
- `references/organizations/active-organization-context.md` — How org context reaches the UI
- `references/auth/server-session-helpers.md` — Server-side session and organization access
