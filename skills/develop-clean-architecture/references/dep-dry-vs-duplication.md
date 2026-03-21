---
title: Accept Cross-Layer Duplication — DRY Ends at the Layer Boundary
impact: HIGH
impactDescription: prevents the most common architectural erosion — sharing types across layers destroys isolation
tags: dep, dry, duplication, boundaries, dtos
---

## Accept Cross-Layer Duplication — DRY Ends at the Layer Boundary

DRY (Don't Repeat Yourself) is correct within a single layer but destructive across layers. Each layer needs its own models because each serves a different master and changes for different reasons. Sharing one type across all layers creates hidden coupling.

**Incorrect (one type shared everywhere — DRY applied naively):**

```typescript
// One User type used in domain, application, API, and DB layers
type User = Prisma.User;  // Leaks DB schema into ALL layers

// Domain entity changes when DB schema changes — violated dependency rule
// API response exposes passwordHash — security bug
// Query joins can't add computed fields — stuck to entity shape
```

**Correct (intentional per-layer models):**

```typescript
// 1. DOMAIN entity — behavior-rich, encapsulated
class User {
  #id: UserId;
  #email: Email;
  #passwordHash: string;  // Never leaves this layer
  verifyPassword(raw: string): boolean { /* ... */ }
  changeEmail(newEmail: Email): Result<void, 'InvalidEmail'> { /* ... */ }
}

// 2. APPLICATION command — what a use case accepts
interface RegisterUserCommand {
  readonly email: string;
  readonly rawPassword: string;
}

// 3. INFRASTRUCTURE DB record — matches persistence schema
interface UserRecord {
  id: string;
  email: string;
  password_hash: string;  // snake_case — DB convention
  created_at: Date;
}

// 4. ADAPTER API response — never exposes internal fields
interface UserResponseDTO {
  readonly id: string;
  readonly email: string;
  readonly createdAt: string;  // ISO string for JSON
}

// 5. QUERY read model — flat, optimized for reads
interface UserListItemDTO {
  readonly id: string;
  readonly email: string;
  readonly orderCount: number;  // Joined data not in domain entity
}
```

**Why each model has a different reason to change:**
- Domain `User` → business rules change
- `UserRecord` → database schema changes
- `UserResponseDTO` → API contract changes
- `UserListItemDTO` → read view requirements change

**The mapper bridges the gap:**

```typescript
class UserMapper {
  static toDomain(record: UserRecord): User {
    return User.reconstitute(
      record.id as UserId,
      parseEmail(record.email) as Email,
      record.password_hash,
    );
  }
  static toRecord(user: User): UserRecord { /* ... */ }
  static toResponse(user: User): UserResponseDTO { /* ... */ }
}
```

**When NOT to use this pattern:**
- Tiny apps where domain, DB, and API shapes are genuinely identical
- Value objects that are the same across all layers (e.g., Money)

**Benefits:**
- Each layer evolves independently — DB changes don't break API contracts
- Security: sensitive fields never accidentally appear in API responses
- Query models can include computed/joined fields not in the domain entity
- Mapper layer is the only place that knows both shapes — single translation point

Reference: [Clean Architecture — Robert C. Martin, Ch. 22](https://www.oreilly.com/library/view/clean-architecture-a/9780134494272/)
