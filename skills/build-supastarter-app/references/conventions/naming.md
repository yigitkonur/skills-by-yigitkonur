# Naming Conventions

> Standard naming patterns used across the codebase. Follow these when creating new files, components, variables, or types.

## Files and Directories

| Type | Convention | Example |
|------|------------|---------|
| Directories | lowercase with dashes | `auth-wizard/`, `use-session/` |
| React components | PascalCase `.tsx` | `LoginForm.tsx`, `UserCard.tsx` |
| Hooks | camelCase with `use-` prefix | `use-session.ts`, `use-active-organization.ts` |
| Utilities/lib | camelCase or dashed | `orpc-client.ts`, `base-url.ts` |
| API procedures | dashed actions | `create-checkout-link.ts`, `submit-contact-form.ts` |
| Types files | `types.ts` in the module | `packages/payments/types.ts` |
| Config files | `config.ts` in the package | `packages/auth/config.ts` |
| Barrel exports | `index.ts` | `packages/auth/index.ts` |

## Variables and Functions

| Type | Convention | Example |
|------|------------|---------|
| Local variables | camelCase | `isLoading`, `currentUser` |
| Boolean variables | `is/has/can/should` prefix | `isActive`, `hasPermission`, `canSubmit` |
| Functions | camelCase, verb-first | `getSession()`, `createCheckoutLink()` |
| Event handlers | `handle` + event | `handleSubmit`, `handleClick` |
| React hooks | `use` prefix | `useSession()`, `useActiveOrganization()` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRIES`, `USER_ROLES` |

## Types and Interfaces

| Type | Convention | Example |
|------|------------|---------|
| Interfaces | PascalCase, descriptive | `UserProps`, `AuthConfig` |
| Type aliases | PascalCase | `PlanId`, `UserRole` |
| Generics | Single uppercase letter | `T`, `K`, `V` |
| Enums | Not used — use `as const` maps | See below |

### Use `as const` maps instead of enums

```typescript
// ✅ Correct
const USER_ROLES = {
  admin: "admin",
  user: "user",
} as const;

type UserRole = (typeof USER_ROLES)[keyof typeof USER_ROLES];

// ❌ Wrong — never use enums
enum UserRole { Admin, User }
```

## React Components

```typescript
// ✅ Named export, function keyword, PascalCase
export function UserCard({ user }: UserCardProps) {
  return <div>{user.name}</div>;
}

// ❌ Wrong — default export, arrow function, class
export default ({ user }) => <div>{user.name}</div>;
export default class UserCard extends Component {}
```

## API Procedures

Procedure variables use camelCase matching the action:

```typescript
// packages/api/modules/payments/procedures/create-checkout-link.ts
export const createCheckoutLink = protectedProcedure
  .route({ method: "POST", path: "/checkout" })
  .input(z.object({ ... }))
  .handler(async ({ input, context }) => { ... });
```

## Database Models

Prisma models use PascalCase singular nouns:

```prisma
model User { ... }
model Organization { ... }
model Purchase { ... }
```

Query functions use camelCase with the model name:

```typescript
export async function getUserById(id: string) { ... }
export async function createPurchase(data: PurchaseInput) { ... }
```

---

**Related references:**
- `references/conventions/typescript-patterns.md` — TypeScript patterns
- `references/conventions/component-patterns.md` — Component structure patterns
- `references/cheatsheets/file-locations.md` — File placement guide
- `references/conventions/code-review-checklist.md` — Pre-commit quality checks
