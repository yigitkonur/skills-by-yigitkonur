---
title: Optimize TypeScript for LSP Performance
impact: MEDIUM-HIGH
impactDescription: prevents 2-10x slowdown in IDE responsiveness, avoids cascading inference across modules
tags: ts, lsp, performance, interfaces
---

## Optimize TypeScript for LSP Performance

The TypeScript Language Server performance directly impacts developer productivity. These five rules prevent common patterns that cause slowdowns — based on the official TypeScript Performance wiki and real-world findings.

**Incorrect (patterns that cause LSP slowdown):**

```typescript
// Rule 1 violation: intersection types recomputed on every use
type AdminUser = User & { permissions: Permission[] } & { auditLog: AuditEntry[] };

// Rule 2 violation: inferred return type cascades to all callers
export async function findById(id: OrderId) {
  return this.prisma.order.findUnique({ where: { id } });
  // Callers inherit Prisma.Order — infra leaks into domain
}

// Rule 3 violation: deep conditional type chain
type Resolve<T> = T extends Promise<infer R>
  ? R extends Result<infer V, infer E>
    ? V extends Array<infer I>
      ? I extends Entity<infer ID>
        ? ID  // 4 levels deep — exponential check
        : never : never : never : never;

// Rule 5 violation: anonymous mapped type recomputed everywhere
function update(entity: Partial<DeepNested<Entity>>): void {}
```

**Correct (five LSP speed rules):**

```typescript
// Rule 1: Prefer interface extends over & intersections (cached shapes)
interface AdminUser extends User {
  readonly permissions: Permission[];
  readonly auditLog: ReadonlyArray<AuditEntry>;
}

// Rule 2: Annotate return types on all exported functions
export async function findById(id: OrderId): Promise<Order | null> {
  const raw = await this.prisma.order.findUnique({ where: { id } });
  return raw ? OrderMapper.toDomain(raw) : null;
}

// Rule 3: Extract intermediate named types instead of deep chains
type ResolvedPromise<T> = T extends Promise<infer R> ? R : T;
type UnwrappedResult<T> = T extends Result<infer V, any> ? V : T;
type EntityId = ResolvedPromise<UnwrappedResult<ReturnType<typeof findById>>>;

// Rule 4: Use import type for type-only cross-layer imports
import type { Order } from '@domain/entities/Order';
import type { OrderRepository } from '@application/ports/OrderRepository';

// Rule 5: Name mapped types and reuse them (TS caches named types)
type PartialEntity = Partial<Entity>;
function update(entity: PartialEntity): void {}
```

**The Five Rules Summary:**

| Rule | Slow Pattern | Fast Pattern | Why |
|---|---|---|---|
| 1 | `type A = B & C & D` | `interface A extends B, C, D {}` | TS caches interface shapes; recomputes intersections |
| 2 | No return type annotation | `): Promise<Order \| null>` | Prevents cascading inference across modules |
| 3 | Deep conditional chains | Named intermediate types | Each extends check evaluated deeply |
| 4 | `import { Order }` | `import type { Order }` | Skips value resolution |
| 5 | Inline `Partial<Complex>` | Named `type X = Partial<Complex>` | Named types are cached |

**Benefits:**
- 2-10x improvement in IDE autocomplete and hover response time
- Explicit return types double as architectural boundary contracts
- `import type` enforces layer boundaries at syntax level via `verbatimModuleSyntax`
- Named types make error messages readable

Reference: [TypeScript Performance Wiki](https://github.com/microsoft/TypeScript/wiki/Performance) | [TypeScript tsconfig — verbatimModuleSyntax](https://www.typescriptlang.org/tsconfig#verbatimModuleSyntax)
