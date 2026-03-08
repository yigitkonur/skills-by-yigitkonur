# Conway's Law

## Origin

Melvin Conway, 1967: "Any organization that designs a system will produce a design whose structure is a copy of the organization's communication structure."

Published in Datamation magazine. Later popularized by Fred Brooks in *The Mythical Man-Month*.

## Explanation

Software architecture inevitably mirrors the social boundaries of the teams that build it. If three teams build a compiler, you get a three-pass compiler. If the front-end and back-end teams never talk, you get a rigid API boundary that may not serve the product well. This is not a suggestion — it is an observation about organizational physics.

The implication cuts both ways: if you want a particular system architecture, you must first arrange your teams to match that architecture. This deliberate inversion is called the **Inverse Conway Maneuver**.

## TypeScript Code Examples

### Bad: Architecture Forced by Org Chart

```typescript
// Team A owns "UserService," Team B owns "OrderService"
// They never talk, so the boundary is a clumsy REST call
// that duplicates user validation logic on both sides.

// user-service/src/validateUser.ts (Team A)
export function validateUser(userId: string): boolean {
  const user = db.users.findById(userId);
  return user !== null && user.active && !user.suspended;
}

// order-service/src/createOrder.ts (Team B)
// Team B doesn't trust Team A's endpoint latency, so they
// duplicate the validation logic with their own DB read.
export async function createOrder(userId: string, items: Item[]): Promise<Order> {
  // Duplicated validation — diverges over time
  const user = await fetch(`${USER_DB_DIRECT_URL}/users/${userId}`);
  if (!user || !user.active || !user.suspended) {  // Bug: inverted check
    throw new Error("Invalid user");
  }
  return orderRepo.create({ userId, items });
}
```

### Good: Team Topology Aligned with Desired Architecture

```typescript
// Single "Commerce Domain" team owns both user eligibility
// and order creation, sharing a domain module.

// commerce-domain/src/user-eligibility.ts
export interface EligibilityCheck {
  eligible: boolean;
  reason?: string;
}

export function checkPurchaseEligibility(user: User): EligibilityCheck {
  if (!user.active) return { eligible: false, reason: "inactive_account" };
  if (user.suspended) return { eligible: false, reason: "suspended" };
  if (user.outstandingBalance > user.creditLimit) {
    return { eligible: false, reason: "credit_exceeded" };
  }
  return { eligible: true };
}

// commerce-domain/src/create-order.ts
import { checkPurchaseEligibility } from "./user-eligibility";

export async function createOrder(
  user: User,
  items: ReadonlyArray<OrderItem>
): Promise<Order> {
  const eligibility = checkPurchaseEligibility(user);
  if (!eligibility.eligible) {
    throw new IneligibleUserError(eligibility.reason);
  }
  return orderRepo.create({ userId: user.id, items });
}
```

## The Inverse Conway Maneuver

Instead of letting architecture follow org structure accidentally, deliberately restructure teams to produce the architecture you want:

1. Define the target architecture (e.g., microservices around business capabilities).
2. Create team boundaries that match those service boundaries.
3. Give each team full ownership: code, data, deployment, on-call.
4. Minimize cross-team dependencies to reduce coordination overhead.

**Team Topologies** (Skelton & Pais, 2019) formalize this into four team types:
- **Stream-aligned teams** — deliver value along a business stream
- **Enabling teams** — help stream-aligned teams adopt new capabilities
- **Complicated-subsystem teams** — own areas requiring deep specialist knowledge
- **Platform teams** — provide self-service internal capabilities

## Alternatives and Related Concepts

- **Domain-Driven Design (DDD):** Bounded contexts often become team boundaries.
- **Spotify Model:** Squads, tribes, chapters — an attempt to align teams with product areas.
- **Amazon's Two-Pizza Teams:** Small teams that own services end-to-end.

## When NOT to Apply

- **Tiny teams (< 5 people):** Reorganizing for architecture is overhead; just communicate.
- **Temporary projects:** Short-lived work does not justify organizational restructuring.
- **When the current org structure genuinely matches desired architecture:** Do not reorganize for its own sake.

## Trade-offs

| Benefit | Cost |
|---|---|
| Architecture reflects intentional design | Reorganization is disruptive and politically expensive |
| Clear ownership reduces coordination | Teams can become siloed and lose the big picture |
| Independent deployment and scaling | Duplication of infrastructure and shared concerns |
| Faster local decision-making | Cross-cutting changes become harder |

## Real-World Consequences

- **Microsoft (pre-2014):** The famous org chart cartoon showed Windows teams producing a system whose internal boundaries mirrored VP fiefdoms — not user needs.
- **Amazon:** Moved to service-oriented architecture by giving each team a service to own, proving the Inverse Conway Maneuver at scale.
- **Spotify (2012-2018):** Squads aligned to features produced a modular system — but later struggled when cross-squad dependencies grew and the model was applied too rigidly.

## Further Reading

- Conway, M. (1968). "How Do Committees Invent?" — the original paper
- Brooks, F. (1975). *The Mythical Man-Month*
- Skelton, M. & Pais, M. (2019). *Team Topologies*
- Forsgren, N., Humble, J., & Kim, G. (2018). *Accelerate*
- ThoughtWorks Technology Radar — "Inverse Conway Maneuver" (2017)
