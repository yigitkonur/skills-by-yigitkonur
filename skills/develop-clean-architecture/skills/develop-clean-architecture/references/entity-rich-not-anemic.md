---
title: Build Rich Domain Models Not Anemic Data Structures
impact: CRITICAL
impactDescription: centralizes business logic, prevents scattered rules, makes entity self-documenting
tags: entity, domain-model, anemic, behavior, ddd
---

## Build Rich Domain Models Not Anemic Data Structures

Entities should contain behavior, not just data. Anemic domain models push business logic into services, scattering rules and duplicating validation. Use `#` private fields for runtime-enforced encapsulation, Result types for domain operations, and factory methods for controlled construction.

**Incorrect (anemic domain model — entity is a data bag):**

```typescript
// domain/entities/Subscription.ts
interface Subscription {
  id: string;
  planId: string;
  startDate: Date;
  endDate: Date;
  status: string;  // Not even a union type
}

// All logic shunted into a "service"
class SubscriptionService {
  validate(sub: Subscription): boolean { /* ... */ }
  calculateCost(sub: Subscription): number { /* ... */ }
  cancel(sub: Subscription): void {
    if (sub.status !== 'active') throw new Error('Cannot cancel');
    sub.status = 'cancelled';  // Direct mutation — no invariant check
    sub.endDate = new Date();
  }
  renew(sub: Subscription, months: number): void {
    if (sub.status !== 'active') throw new Error('Cannot renew');
    sub.endDate = new Date(sub.endDate.getTime() + months * 30 * 86400000);
  }
}
// Problems: logic scattered, no encapsulation, easy to bypass validation
```

**Correct (rich domain model with behavior, encapsulation, events):**

```typescript
type SubscriptionStatus = 'active' | 'cancelled' | 'expired';

class Subscription {
  readonly #id: SubscriptionId;
  readonly #planId: PlanId;
  #endDate: Date;
  #status: SubscriptionStatus;
  #domainEvents: DomainEvent[] = [];

  private constructor(
    id: SubscriptionId,
    planId: PlanId,
    endDate: Date,
    status: SubscriptionStatus,
  ) {
    this.#id = id;
    this.#planId = planId;
    this.#endDate = endDate;
    this.#status = status;
  }

  static create(planId: PlanId, months: number): Result<Subscription, 'InvalidPeriod'> {
    if (months < 1) return { ok: false, error: 'InvalidPeriod' };
    const end = new Date();
    end.setMonth(end.getMonth() + months);
    const sub = new Subscription(generateId() as SubscriptionId, planId, end, 'active');
    sub.#domainEvents.push(new SubscriptionCreated(sub.#id, planId));
    return { ok: true, value: sub };
  }

  static reconstitute(id: SubscriptionId, planId: PlanId, endDate: Date, status: SubscriptionStatus): Subscription {
    return new Subscription(id, planId, endDate, status);
  }

  cancel(): Result<void, 'NotActive'> {
    if (this.#status !== 'active') return { ok: false, error: 'NotActive' };
    this.#status = 'cancelled';
    this.#domainEvents.push(new SubscriptionCancelled(this.#id));
    return { ok: true, value: undefined };
  }

  renew(months: number): Result<void, 'NotActive' | 'InvalidPeriod'> {
    if (this.#status !== 'active') return { ok: false, error: 'NotActive' };
    if (months < 1) return { ok: false, error: 'InvalidPeriod' };
    this.#endDate = new Date(this.#endDate.getTime());
    this.#endDate.setMonth(this.#endDate.getMonth() + months);
    return { ok: true, value: undefined };
  }

  get isExpired(): boolean { return new Date() > this.#endDate; }
  get id(): SubscriptionId { return this.#id; }
  get status(): SubscriptionStatus { return this.#status; }

  pullDomainEvents(): ReadonlyArray<DomainEvent> {
    const events = [...this.#domainEvents];
    this.#domainEvents = [];
    return events;
  }
}

// Application service is a thin orchestrator — no business logic
class CancelSubscriptionUseCase {
  constructor(private readonly subs: SubscriptionRepository) {}

  async execute(id: SubscriptionId): Promise<Result<void, 'NotFound' | 'NotActive'>> {
    const sub = await this.subs.findById(id);
    if (!sub) return { ok: false, error: 'NotFound' };
    const result = sub.cancel();  // Business logic IN the entity
    if (!result.ok) return result;
    await this.subs.save(sub);
    return { ok: true, value: undefined };
  }
}
```

**Why `#` private fields over `private` keyword:** `#` fields are runtime-private — not accessible even via `as any` casting. For domain entities whose invariants must never be broken, this provides true encapsulation.

**When NOT to use this pattern:**
- Simple lookup/reference entities with no business rules (e.g., Country, Currency)
- DTOs and read models — these are data structures, not objects

**Benefits:**
- Business rules live with the data they operate on — impossible to forget validation
- Entity documents its own capabilities via public methods
- `#` private fields enforce encapsulation at runtime, not just compile time
- Application services become thin orchestrators — easy to test, easy to read

Reference: [Anemic Domain Model Anti-pattern — Martin Fowler](https://martinfowler.com/bliki/AnemicDomainModel.html)
