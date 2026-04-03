# Prisma Schema Overview

> Maps the main Prisma models that back auth, organizations, invitations, passkeys, and purchases.

## Key files

- `packages/database/prisma/schema.prisma`

## Representative code

```ts
generator client {
  provider   = "prisma-client"
  output     = "./generated"
  engineType = "client"
}

generator zod {
  provider = "prisma-zod-generator"
  output   = "./zod"
}

model User {
  id                 String  @id @default(cuid())
  email              String
  onboardingComplete Boolean @default(false)
  paymentsCustomerId String?
  locale             String?
  sessions           Session[]
  purchases          Purchase[]
  members            Member[]
  @@unique([email])
}

model Organization {
  id                 String   @id @default(cuid())
  name               String
  slug               String?
  logo               String?
  paymentsCustomerId String?
  members            Member[]
  invitations        Invitation[]
  purchases          Purchase[]
  @@unique([slug])
}
```

## Implementation notes

- The schema is centered around Better Auth models plus organization and purchase records.
- User and organization entities both store `paymentsCustomerId` so billing can attach to either level.
- The repo also generates Zod schemas from Prisma, which other packages consume for typing and validation.

---

**Related references:**
- `references/database/prisma-client.md` — How the generated client is created and exported
- `references/database/query-patterns.md` — How code accesses models through query helpers
- `references/payments/customer-ids.md` — Fields that persist external payment customer IDs
