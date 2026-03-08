# Hexagonal Architecture (Ports and Adapters)

**Isolate your core business logic from external concerns by defining explicit boundaries through ports and adapters.**

---

## Origin

Hexagonal Architecture was conceived by Alistair Cockburn in 2005, published on his wiki under the name *"Ports and Adapters."* The hexagonal shape is arbitrary — Cockburn chose it because it was visually distinct and had enough "sides" to illustrate multiple ports. The pattern was a direct response to the problems of layered architecture, where business logic became entangled with database access and UI frameworks. It was later reinforced by Jeffrey Palermo's Onion Architecture (2008) and Robert C. Martin's Clean Architecture (2012), both of which share the same core insight: **dependencies point inward, toward the domain.**

---

## The Problem It Solves

In traditional layered architectures, business logic depends on the database layer. When you want to change from PostgreSQL to MongoDB, swap an email provider, or add a CLI interface alongside the web UI, you must modify the business logic. Worse, business rules become tangled with framework concerns — testing requires spinning up databases, changing a library version breaks domain code, and the "layers" become leaky abstractions where a UI concern drips down into the data layer.

---

## The Principle Explained

Hexagonal Architecture divides the application into three zones. The **core domain** sits at the center, containing business rules, entities, and domain services. It has zero dependencies on external technologies — no imports from Express, Prisma, AWS SDK, or any other infrastructure library.

The core communicates with the outside world through **ports** — interfaces that define what the domain needs (driven ports) or what the domain offers (driving ports). A `UserRepository` interface is a port. A `PaymentGateway` interface is a port. The domain depends only on these abstractions.

**Adapters** sit outside the core and implement the ports. A `PostgresUserRepository` adapter implements the `UserRepository` port using PostgreSQL. A `StripePaymentAdapter` implements the `PaymentGateway` port using Stripe's API. An `ExpressHttpAdapter` adapts HTTP requests into domain commands. Adapters depend on the domain (they implement domain interfaces), but the domain never depends on adapters. This inversion of dependency is the key insight.

---

## Code Examples

### BAD: Business logic coupled to infrastructure

```typescript
import { PrismaClient } from "@prisma/client";
import Stripe from "stripe";
import { sendEmail } from "./utils/email";

const prisma = new PrismaClient();
const stripe = new Stripe("sk_live_xxx");

// Business logic is tangled with Prisma, Stripe, and email infrastructure
async function createSubscription(userId: string, planId: string) {
  // Direct Prisma dependency — cannot test without a database
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) throw new Error("User not found");

  const plan = await prisma.plan.findUnique({ where: { id: planId } });
  if (!plan) throw new Error("Plan not found");

  // Business rule buried alongside Stripe-specific code
  if (user.subscriptionCount >= plan.maxSubscriptions) {
    throw new Error("Subscription limit reached");
  }

  // Direct Stripe dependency — cannot test without network
  const stripeCustomer = await stripe.customers.create({
    email: user.email,
    metadata: { userId: user.id },
  });

  const stripeSubscription = await stripe.subscriptions.create({
    customer: stripeCustomer.id,
    items: [{ price: plan.stripePriceId }],
  });

  // Direct database dependency again
  const subscription = await prisma.subscription.create({
    data: {
      userId: user.id,
      planId: plan.id,
      stripeSubscriptionId: stripeSubscription.id,
      status: "active",
    },
  });

  // Direct email dependency
  await sendEmail(user.email, "Welcome!", `You're subscribed to ${plan.name}`);

  return subscription;
}
```

### GOOD: Hexagonal Architecture — domain isolated from infrastructure

```typescript
// ============================================
// DOMAIN CORE — zero infrastructure dependencies
// ============================================

// Domain entities
class User {
  constructor(
    readonly id: string,
    readonly email: string,
    private subscriptionCount: number
  ) {}

  canSubscribeTo(plan: Plan): boolean {
    return this.subscriptionCount < plan.maxSubscriptions;
  }

  incrementSubscriptionCount(): void {
    this.subscriptionCount++;
  }
}

class Plan {
  constructor(
    readonly id: string,
    readonly name: string,
    readonly maxSubscriptions: number
  ) {}
}

class Subscription {
  constructor(
    readonly id: string,
    readonly userId: string,
    readonly planId: string,
    readonly status: "active" | "cancelled" | "expired"
  ) {}
}

// PORTS — interfaces that define what the domain needs
interface UserRepository {
  findById(id: string): Promise<User | null>;
  save(user: User): Promise<void>;
}

interface PlanRepository {
  findById(id: string): Promise<Plan | null>;
}

interface SubscriptionRepository {
  save(subscription: Subscription): Promise<Subscription>;
}

interface PaymentProvider {
  createCustomer(email: string, metadata: Record<string, string>): Promise<string>;
  createSubscription(customerId: string, planExternalId: string): Promise<string>;
}

interface NotificationService {
  sendWelcome(email: string, planName: string): Promise<void>;
}

// Domain errors
class UserNotFoundError extends Error {
  constructor(userId: string) { super(`User not found: ${userId}`); }
}

class SubscriptionLimitError extends Error {
  constructor(userId: string) { super(`Subscription limit reached for user: ${userId}`); }
}

// DOMAIN SERVICE — pure business logic, depends only on ports
class SubscriptionService {
  constructor(
    private readonly users: UserRepository,
    private readonly plans: PlanRepository,
    private readonly subscriptions: SubscriptionRepository,
    private readonly payments: PaymentProvider,
    private readonly notifications: NotificationService
  ) {}

  async createSubscription(userId: string, planId: string): Promise<Subscription> {
    const user = await this.users.findById(userId);
    if (!user) throw new UserNotFoundError(userId);

    const plan = await this.plans.findById(planId);
    if (!plan) throw new Error(`Plan not found: ${planId}`);

    // Business rule — clean, testable, no infrastructure
    if (!user.canSubscribeTo(plan)) {
      throw new SubscriptionLimitError(userId);
    }

    const customerId = await this.payments.createCustomer(
      user.email,
      { userId: user.id }
    );
    const externalSubId = await this.payments.createSubscription(customerId, planId);

    const subscription = new Subscription(
      generateId(),
      user.id,
      plan.id,
      "active"
    );

    user.incrementSubscriptionCount();
    await this.users.save(user);
    await this.subscriptions.save(subscription);
    await this.notifications.sendWelcome(user.email, plan.name);

    return subscription;
  }
}

// ============================================
// ADAPTERS — implement ports with real infrastructure
// ============================================

// Driven adapter: PostgreSQL implementation of UserRepository
class PostgresUserRepository implements UserRepository {
  constructor(private readonly prisma: PrismaClient) {}

  async findById(id: string): Promise<User | null> {
    const row = await this.prisma.user.findUnique({ where: { id } });
    if (!row) return null;
    return new User(row.id, row.email, row.subscriptionCount);
  }

  async save(user: User): Promise<void> {
    await this.prisma.user.update({
      where: { id: user.id },
      data: { subscriptionCount: user["subscriptionCount"] },
    });
  }
}

// Driven adapter: Stripe implementation of PaymentProvider
class StripePaymentAdapter implements PaymentProvider {
  constructor(private readonly stripe: Stripe) {}

  async createCustomer(email: string, metadata: Record<string, string>): Promise<string> {
    const customer = await this.stripe.customers.create({ email, metadata });
    return customer.id;
  }

  async createSubscription(customerId: string, priceId: string): Promise<string> {
    const sub = await this.stripe.subscriptions.create({
      customer: customerId,
      items: [{ price: priceId }],
    });
    return sub.id;
  }
}

// Driving adapter: Express HTTP handler
class SubscriptionHttpAdapter {
  constructor(private readonly service: SubscriptionService) {}

  async handleCreateSubscription(req: Request, res: Response): Promise<void> {
    try {
      const { userId, planId } = req.body;
      const subscription = await this.service.createSubscription(userId, planId);
      res.status(201).json(subscription);
    } catch (error) {
      if (error instanceof UserNotFoundError) {
        res.status(404).json({ error: error.message });
      } else if (error instanceof SubscriptionLimitError) {
        res.status(422).json({ error: error.message });
      } else {
        res.status(500).json({ error: "Internal server error" });
      }
    }
  }
}

// ============================================
// COMPOSITION ROOT — wiring adapters to ports
// ============================================
function bootstrap(): SubscriptionHttpAdapter {
  const prisma = new PrismaClient();
  const stripe = new Stripe(process.env.STRIPE_KEY!);

  const userRepo = new PostgresUserRepository(prisma);
  const planRepo = new PostgresPlanRepository(prisma);
  const subRepo = new PostgresSubscriptionRepository(prisma);
  const payments = new StripePaymentAdapter(stripe);
  const notifications = new EmailNotificationAdapter(/* smtp config */);

  const service = new SubscriptionService(
    userRepo, planRepo, subRepo, payments, notifications
  );

  return new SubscriptionHttpAdapter(service);
}
```

---

## Alternatives & Related Principles

| Pattern | Relationship |
|---|---|
| **Onion Architecture** | Jeffrey Palermo (2008). Nearly identical to Hexagonal — concentric rings instead of hexagon. Domain at center, application services next, infrastructure at the edge. |
| **Clean Architecture** | Robert C. Martin (2012). Same dependency rule (point inward) with more explicit ring definitions: Entities, Use Cases, Interface Adapters, Frameworks & Drivers. |
| **Vertical Slice Architecture** | Jimmy Bogard. Organizes by feature instead of by layer. Each feature has its own "mini hexagon." Trades reusability for cohesion. |
| **Layered Architecture** | The predecessor. Hexagonal fixes layered architecture's core flaw: business logic depending on infrastructure. |

---

## When NOT to Apply

- **Simple CRUD applications**: If the app has no business logic beyond "save to database and return," hexagonal architecture adds ceremony without benefit. A direct controller-to-repository path is simpler.
- **Prototypes and spikes**: When exploring feasibility, the indirection of ports and adapters slows down experimentation.
- **Single infrastructure target**: If you will never swap PostgreSQL for anything else, the `UserRepository` interface is speculative abstraction. Consider starting without the interface and introducing it when the second adapter arrives.
- **Very small teams**: The organizational overhead of maintaining domain/adapter boundaries may not pay off when one person writes everything.

---

## Tensions & Trade-offs

- **Purity vs. Pragmatism**: The purest hexagonal architecture has zero framework annotations in the domain. In practice, ORM decorators (`@Entity`, `@Column`) creep into domain classes for convenience.
- **Indirection vs. Navigability**: Jumping from HTTP handler to port interface to adapter implementation requires IDE support. `Ctrl+Click` on an interface method shows N implementations.
- **Testing benefit vs. Mocking cost**: Hexagonal makes unit testing trivial (inject mock adapters), but writing and maintaining mocks has its own cost.
- **Upfront design vs. Emergent architecture**: Hexagonal requires deciding on ports upfront. If the boundaries are wrong, refactoring ports affects the entire system.

---

## Real-World Consequences

**Adherence example**: A fintech company structured their payment processing domain using hexagonal architecture. When regulators required switching from Stripe to Adyen in the EU market, only the payment adapter was replaced. The domain service, business rules, and test suite remained unchanged. The migration took two weeks instead of the estimated two months.

**Over-application example**: A team applied full hexagonal architecture to a simple CRUD API with five endpoints and no business logic. The result was 47 files for what could have been 12. Onboarding new developers took three days instead of three hours because they had to understand the port/adapter indirection for trivially simple operations.

---

## Key Quotes

> "Allow an application to equally be driven by users, programs, automated tests, or batch scripts, and to be developed and tested in isolation from its eventual run-time devices and databases." — Alistair Cockburn

> "The overriding rule that makes this architecture work is the Dependency Rule: source code dependencies must point only inward." — Robert C. Martin, *Clean Architecture*

---

## Further Reading

- Cockburn, A. — [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) (2005)
- Palermo, J. — [The Onion Architecture](https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/) (2008)
- Martin, R.C. — *Clean Architecture* (2017)
- Bogard, J. — [Vertical Slice Architecture](https://jimmybogard.com/vertical-slice-architecture/) (2018)
- Netflix Engineering — [Hexagonal Architecture at Netflix](https://netflixtechblog.com/) (various posts on domain isolation)
