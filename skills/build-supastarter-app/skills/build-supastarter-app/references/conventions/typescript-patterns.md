# TypeScript Patterns

> TypeScript conventions used throughout the Supastarter codebase. Follow these when writing new code to maintain consistency.

## Strict Mode

All TypeScript in the project uses strict mode. The base config is at `tooling/typescript/base.json` and extended by each package.

## Interfaces Over Type Aliases

Use `interface` for object shapes, `type` for unions, intersections, and utility types:

```typescript
// ✅ Interface for object shapes
interface UserProps {
  name: string;
  email: string;
  isActive: boolean;
}

// ✅ Type for unions and computed types
type PlanId = "free" | "pro" | "lifetime" | "enterprise";
type UserRole = (typeof USER_ROLES)[keyof typeof USER_ROLES];
```

## `as const` Instead of Enums

The codebase never uses TypeScript enums. Use `as const` objects with derived types:

```typescript
// ✅ as const pattern (used throughout the codebase)
export const config = {
  billingAttachedTo: "user" as "user" | "organization",
  plans: {
    free: { isFree: true },
    pro: { recommended: true, prices: [...] },
  },
} as const;

// Derive types from the constant
type PlanId = keyof typeof config.plans;

// ❌ Never use enums
enum PlanType { Free, Pro }
```

## Function Types

Use explicit function type signatures for exported callbacks:

```typescript
// packages/payments/types.ts — function type pattern
export type CreateCheckoutLink = (params: {
  type: "subscription" | "one-time";
  productId: string;
  email?: string;
  redirectUrl?: string;
  customerId?: string;
  organizationId?: string;
  userId?: string;
  trialPeriodDays?: number;
  seats?: number;
}) => Promise<string | null>;

// Implementing the type
export const createCheckoutLink: CreateCheckoutLink = async (params) => {
  // Implementation
};
```

## Zod for Runtime Validation

Use Zod schemas for API input validation, form validation, and runtime type checking:

```typescript
import { z } from "zod";

// Schema definition
const createItemSchema = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
  organizationId: z.string(),
});

// Derive TypeScript type from schema
type CreateItemInput = z.infer<typeof createItemSchema>;

// Use in oRPC procedure
export const createItem = protectedProcedure
  .input(createItemSchema)
  .handler(async ({ input }) => {
    // `input` is typed as CreateItemInput
  });
```

## Generic Patterns

```typescript
// Constrained generics with extends
export async function sendEmail<T extends TemplateId>(
  params: { to: string } & TemplateParams<T>
): Promise<boolean> { ... }

// Utility types
type Prettify<T> = { [K in keyof T]: T[K] } & {};
```

## Environment Variable Typing

Cast environment variables at the point of use:

```typescript
// ✅ Pattern used in the codebase
const s3Endpoint = process.env.S3_ENDPOINT as string;
if (!s3Endpoint) {
  throw new Error("Missing env variable S3_ENDPOINT");
}

// For NEXT_PUBLIC_ vars in config objects
productId: process.env.NEXT_PUBLIC_PRICE_ID_PRO_MONTHLY as string,
```

## Type Exports

Export types alongside implementations from barrel files:

```typescript
// packages/auth/index.ts
export {
  auth,
  type Session,
  type ActiveOrganization,
  type Organization,
  type OrganizationMemberRole,
} from "./auth";
```

## Avoid These Patterns

- **`any`** — allowed by Biome config but use sparingly; prefer `unknown` or proper types
- **Non-null assertions (`!`)** — allowed but prefer optional chaining or guards
- **Type assertions (`as`)** — only for environment variables and known safe casts
- **`@ts-ignore`** — never; use `@ts-expect-error` with an explanation if absolutely needed

---

**Related references:**
- `references/conventions/naming.md` — Naming conventions
- `references/conventions/component-patterns.md` — React component patterns
- `references/setup/tooling-biome.md` — Biome lint rules
- `references/conventions/code-review-checklist.md` — Pre-commit quality checks
- `references/cheatsheets/imports.md` — Common import patterns
