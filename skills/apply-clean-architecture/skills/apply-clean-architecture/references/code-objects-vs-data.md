---
title: Distinguish Objects from Data Structures at Layer Boundaries
impact: HIGH
impactDescription: prevents encapsulation leaks, clarifies what crosses architectural boundaries
tags: code, objects, data-structures, boundaries, ddd
---

## Distinguish Objects from Data Structures at Layer Boundaries

Objects hide data and expose behavior — they live in the domain layer. Data structures expose data and have no behavior — they live at layer boundaries as DTOs, API responses, and DB records. Mixing these two leads to anemic models or leaky abstractions.

**Incorrect (one type used everywhere — leaks internals):**

```typescript
// Used in domain, application, API response, and DB layer
interface User {
  id: string;
  email: string;
  passwordHash: string;  // Exposed to API response!
  createdAt: Date;
}
```

**Correct (per-layer models with clear purposes):**

```typescript
// DOMAIN — Object: hides data, exposes behavior
class User {
  readonly #id: UserId;
  readonly #email: Email;
  #passwordHash: string;

  verifyPassword(raw: string): boolean { /* bcrypt compare */ }
  changeEmail(newEmail: Email): Result<void, 'InvalidEmail'> { /* ... */ }

  get id(): UserId { return this.#id; }
  get email(): Email { return this.#email; }
  // passwordHash is NEVER exposed
}

// APPLICATION — Command: what a use case accepts
interface RegisterUserCommand {
  readonly email: string;
  readonly rawPassword: string;
}

// INFRASTRUCTURE — DB record: matches persistence schema
interface UserRecord {
  id: string;
  email: string;
  password_hash: string;
  created_at: Date;
  updated_at: Date;
}

// ADAPTER — API response DTO: never exposes passwordHash
interface UserResponseDTO {
  readonly id: string;
  readonly email: string;
  readonly createdAt: string;  // ISO string for JSON
}

// QUERY — Read model: flat, optimized for read performance
interface UserListItemDTO {
  readonly id: string;
  readonly email: string;
  readonly orderCount: number;  // Joined data not in domain entity
}
```

**Why each model has a different reason to change:**
- Domain `User` changes when business rules change
- `UserRecord` changes when the database schema changes
- `UserResponseDTO` changes when the API contract changes
- `UserListItemDTO` changes when the read view requirements change

**When NOT to use this pattern:**
- Tiny applications where a single type is genuinely sufficient
- Internal helper types that never cross a layer boundary

**Benefits:**
- Domain entities cannot accidentally leak sensitive fields (passwordHash)
- Each layer evolves independently — DB schema changes don't break API contracts
- `#` private fields enforce runtime encapsulation — not bypassable with `as any`
- Clear ownership of each type — no ambiguity about who can change it

Reference: [Clean Code, Ch. 6 — Objects and Data Structures](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
