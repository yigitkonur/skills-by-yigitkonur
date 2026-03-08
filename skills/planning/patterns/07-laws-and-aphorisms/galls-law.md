# Gall's Law

## Origin

John Gall, 1975, *Systemantics: How Systems Really Work and How They Fail*: "A complex system that works is invariably found to have evolved from a simple system that worked. A complex system designed from scratch never works and cannot be patched up to make it work. You have to start over with a working simple system."

## Explanation

You cannot design a working complex system from scratch. Every successful complex system — biological, social, or technological — started as a simple system that worked, then incrementally grew in complexity while remaining functional at each step.

In software, this means: build the simplest thing that works, ship it, get feedback, and evolve it. The "big bang rewrite" that tries to build the perfect complex system from day one almost always fails.

This is the theoretical foundation for MVP (Minimum Viable Product), iterative development, and evolutionary architecture.

## TypeScript Code Examples

### Bad: Designing the Perfect System From Scratch

```typescript
// Day 1: "Let's build the ultimate notification system"
// Before any user has requested notifications.

interface NotificationConfig {
  channels: ("email" | "sms" | "push" | "slack" | "webhook" | "carrier_pigeon")[];
  scheduling: {
    immediate: boolean;
    delayed: { delayMs: number };
    recurring: { cron: string; timezone: string };
    batched: { windowMs: number; maxBatch: number };
  };
  routing: {
    rules: RoutingRule[];
    fallbacks: FallbackChain[];
    circuitBreaker: CircuitBreakerConfig;
  };
  templating: {
    engine: "handlebars" | "mjml" | "custom";
    i18n: { locales: string[]; fallbackLocale: string };
    abTesting: { variants: Variant[]; trafficSplit: number[] };
  };
  delivery: {
    retry: { maxAttempts: number; backoff: "linear" | "exponential" };
    deduplication: { windowMs: number; strategy: "content" | "id" };
    rateLimiting: { perUser: number; perChannel: number; windowMs: number };
  };
}

// Six months later: still not shipped. Requirements changed.
// The scheduling system nobody uses conflicts with the routing
// system nobody tested. The whole thing is scrapped.
```

### Good: Start Simple, Evolve From Working System

```typescript
// Week 1: Simple notification that works
export async function sendNotification(
  userId: string,
  message: string
): Promise<void> {
  const user = await userRepo.findById(userId);
  if (!user?.email) return;
  await emailClient.send({ to: user.email, subject: "Notification", body: message });
}

// Week 4: Users want different channels — add SMS (simple extension)
export async function sendNotification(
  userId: string,
  message: string,
  channel: "email" | "sms" = "email"
): Promise<void> {
  const user = await userRepo.findById(userId);
  if (channel === "sms" && user?.phone) {
    await smsClient.send({ to: user.phone, body: message });
  } else if (user?.email) {
    await emailClient.send({ to: user.email, subject: "Notification", body: message });
  }
}

// Month 3: Need templates — extract a thin templating layer
// Month 6: Need retries — wrap with retry logic
// Month 9: Need rate limiting — add a rate limiter middleware
// Each step: system works, users get value, feedback drives design
```

## The MVP Connection

Gall's Law provides the theoretical basis for why MVPs work:

```
Gall's Law:     Simple working system → evolve → complex working system
MVP approach:   Minimal feature set → ship → iterate → full product
Big bang:       Complex design → build for months → ship → usually fails
```

The key insight is that each intermediate state must work. You cannot have a phase where the system is broken "but will work once we add the remaining pieces."

## Alternatives and Related Concepts

- **Evolutionary Architecture** (Ford, Parsons, Kua): Architecture that supports incremental change.
- **Strangler Fig Pattern:** Incrementally replace a legacy system by wrapping it with new functionality.
- **Walking Skeleton:** Build the thinnest possible end-to-end system first, then flesh it out.
- **YAGNI (You Ain't Gonna Need It):** Do not build what you do not yet need — closely related to starting simple.

## When NOT to Apply

- **Safety-critical systems:** Medical devices, aircraft software, and nuclear systems require upfront design. You cannot "iterate" on a pacemaker in production.
- **Protocol design:** Network protocols and file formats must be designed carefully because backward compatibility constraints make iteration expensive.
- **Cryptographic systems:** Security cannot be bolted on incrementally. Cryptographic protocols require formal analysis before deployment.
- **Hard real-time systems:** Timing guarantees require upfront architectural commitment.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Start simple, evolve | Working system at every stage, fast feedback | May accumulate technical debt, local optima |
| Big upfront design | Theoretically optimal architecture | High risk of failure, slow to deliver value |
| Walking skeleton | End-to-end proof of concept early | Initial version may mislead about final quality |
| Strangler fig migration | Low risk, incremental | Requires maintaining two systems during transition |

## Real-World Consequences

- **Amazon:** Started as an online bookstore. Not an "everything store" on day one. The infrastructure that became AWS evolved from internal tools — not from a grand cloud platform design.
- **Linux:** Started as a simple terminal emulator. Linus Torvalds did not design a full OS kernel upfront.
- **The Second System Effect (Brooks):** The follow-up system is over-designed because designers try to include everything they learned — violating Gall's Law by building complex from scratch.
- **Healthcare.gov (2013):** Attempted to build a complex, multi-state, multi-insurer marketplace from scratch. Failed spectacularly on launch.

## The Corollary

If a complex system is not working, you cannot fix it. You must go back to a simpler version that does work and evolve forward from there. This is why "big bang rewrites" of legacy systems fail — and why the Strangler Fig pattern succeeds.

## Further Reading

- Gall, J. (1975). *Systemantics: How Systems Really Work and How They Fail*
- Gall, J. (2002). *The Systems Bible* (updated edition)
- Ford, N., Parsons, R., & Kua, P. (2017). *Building Evolutionary Architectures*
- Ries, E. (2011). *The Lean Startup* — MVP as Gall's Law applied to business
- Fowler, M. (2004). "StranglerFigApplication" — martinfowler.com
