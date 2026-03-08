# YAGNI -- You Ain't Gonna Need It

**Don't build features, abstractions, or infrastructure until you have a concrete, immediate need for them.**

---

## Origin

Coined by **Ron Jeffries** as a core practice of **Extreme Programming (XP)** in the late 1990s. The principle was formalized in Kent Beck's *Extreme Programming Explained* (1999). It emerged as a direct reaction against Big Design Up Front (BDUF) culture, where teams spent months building frameworks and abstractions for hypothetical future requirements -- most of which never materialized.

---

## The Problem It Solves

Developers are pattern-matchers and forward-thinkers. We see a requirement and immediately imagine ten future variations. So we build configuration systems, plugin architectures, and abstraction layers to handle those ten variations. The cost: we spend weeks building infrastructure instead of features. The code becomes harder to understand because it's solving problems that don't exist yet. And when the *actual* future requirement arrives, it almost never matches the shape we predicted -- so the premature abstraction becomes an obstacle rather than an accelerator.

---

## The Principle Explained

YAGNI is a discipline of restraint. It says: solve today's problem today. When you feel the urge to add "just in case" code, stop. When someone in a design meeting says "we might need to support X in the future," write it on a backlog and move on. The only code that belongs in the system is code that's needed *right now* to pass a test or fulfill a requirement.

This doesn't mean "don't think about the future" -- it means "don't *build* for the future." You should absolutely design your code to be easy to change (that's the Open-Closed Principle). But "easy to change" is different from "pre-built for every possible change." Good structure makes future changes cheap. Pre-built abstractions make the *wrong* future change cheap and the *right* one expensive.

The economic argument is devastating: studies consistently show that 60-80% of speculatively built features are never used. You're paying the full cost of building, testing, and maintaining code that delivers zero value. Worse, that code actively harms the codebase by adding complexity, increasing cognitive load, and creating maintenance burden.

---

## Code Examples

### BAD: Building for hypothetical future requirements

```typescript
// "We might need to support different notification channels someday"
interface NotificationChannel {
  send(message: string, recipient: string): Promise<void>;
}

interface NotificationConfig {
  channel: "email" | "sms" | "push" | "slack" | "webhook";
  retryPolicy: RetryPolicy;
  batchSize: number;
  rateLimitPerMinute: number;
  templateEngine: "handlebars" | "mustache" | "ejs";
}

class NotificationRouter {
  private channels: Map<string, NotificationChannel> = new Map();
  private middleware: NotificationMiddleware[] = [];

  registerChannel(name: string, channel: NotificationChannel): void {
    this.channels.set(name, channel);
  }

  addMiddleware(mw: NotificationMiddleware): void {
    this.middleware.push(mw);
  }

  async send(config: NotificationConfig, message: string, recipient: string): Promise<void> {
    let processed = message;
    for (const mw of this.middleware) {
      processed = await mw.process(processed);
    }
    const channel = this.channels.get(config.channel);
    if (!channel) throw new Error(`Unknown channel: ${config.channel}`);
    await channel.send(processed, recipient);
  }
}

// The actual requirement: send an email when a user signs up.
// All we needed was this:
```

### GOOD: Solve today's problem today

```typescript
// The requirement: send an email when a user signs up.
async function sendWelcomeEmail(user: User): Promise<void> {
  await emailClient.send({
    to: user.email,
    subject: "Welcome!",
    body: `Hi ${user.name}, welcome to our platform.`,
  });
}

// Clean, obvious, testable, done.
// When (IF) we need SMS support, we'll add it then.
// We'll know more about the actual requirements at that point.
```

### BAD: Premature generalization of a data access layer

```typescript
// "Let's build a generic repository so we can swap databases later"
interface Repository<T> {
  findById(id: string): Promise<T | null>;
  findAll(filter: Partial<T>): Promise<T[]>;
  create(entity: Omit<T, "id">): Promise<T>;
  update(id: string, changes: Partial<T>): Promise<T>;
  delete(id: string): Promise<void>;
  findWithPagination(filter: Partial<T>, page: number, size: number): Promise<PaginatedResult<T>>;
  executeRaw(query: string, params: unknown[]): Promise<unknown>;
}

// 200+ lines of generic implementation, type gymnastics,
// and an `executeRaw` escape hatch that defeats the entire purpose.
// You're never switching databases. You know this.
```

### GOOD: Direct, specific data access

```typescript
// Specific queries for specific needs
interface UserRepository {
  getById(id: string): Promise<User | null>;
  getByEmail(email: string): Promise<User | null>;
  create(input: CreateUserInput): Promise<User>;
  updateProfile(id: string, profile: ProfileUpdate): Promise<User>;
}

// Uses PostgreSQL directly. If we ever need to change databases
// (we won't), this interface is the seam where we'd do it.
// But we haven't built a generic abstraction layer we don't need.
```

### BAD: Configuration system for a single use case

```typescript
// "What if we need to configure this differently per environment?"
const config = {
  featureFlags: {
    enableNewDashboard: process.env.FEATURE_NEW_DASHBOARD === "true",
    enableBetaApi: process.env.FEATURE_BETA_API === "true",
    maxRetries: parseInt(process.env.MAX_RETRIES ?? "3"),
    retryBackoff: process.env.RETRY_BACKOFF as "linear" | "exponential",
    // 40 more flags for features that don't exist yet
  },
};
```

### GOOD: Add configuration when you need it

```typescript
// Today we have one configurable thing: the API base URL.
const API_BASE_URL = process.env.API_BASE_URL ?? "https://api.example.com";

// That's it. When we need another config value, we'll add it.
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|-----------|-------------|
| **BDUF (Big Design Up Front)** | The direct opposite. Design everything before writing code. Appropriate in safety-critical domains (aerospace, medical), over-applied everywhere else. |
| **Speculative Generality** | Martin Fowler's code smell for the same problem -- abstract base classes, unused parameters, and hook methods "just in case." |
| **Last Responsible Moment** | From Lean Software Development. Delay decisions until the cost of not deciding outweighs the cost of deciding. Complements YAGNI by providing a decision framework. |
| **Evolutionary Architecture** | Build systems that can evolve. Instead of predicting the future, make change cheap. YAGNI's architectural sibling. |

---

## When NOT to Apply

- **Security and data integrity.** "We don't need encryption yet" is never acceptable. Some things must be built in from the start because retrofitting is prohibitively expensive.
- **Core architectural decisions.** Choosing a database, a communication protocol, or a deployment model -- these are hard to change later. Think carefully up front.
- **Public APIs.** Once published, APIs are contracts. Plan for versioning and backward compatibility before your first release.
- **Compliance and audit requirements.** Logging, audit trails, and data retention rules should be designed in early, not bolted on.
- **Known upcoming requirements.** If the product team has committed to launching SMS notifications next sprint, it's reasonable to consider that in today's design. YAGNI targets *speculative* features, not *scheduled* ones.

---

## Tensions & Trade-offs

- **YAGNI vs. DRY**: YAGNI says "don't abstract yet." DRY says "don't duplicate." When you see the same pattern twice, DRY pushes you to extract; YAGNI asks whether the abstraction is truly needed yet.
- **YAGNI vs. Open-Closed Principle**: OCP wants code open for extension. YAGNI says don't build extension points until you need them. Resolution: write clean code with good seams, but don't add explicit plugin hooks or strategy patterns until there's a second strategy.
- **YAGNI vs. Performance**: Sometimes you need to design for scale before you have scale. A database schema that works for 1,000 rows might not work for 10 million. The key is distinguishing *architectural* decisions (worth thinking ahead) from *feature* decisions (don't build ahead).

---

## Real-World Consequences

A startup built a multi-tenant, multi-region, plugin-based architecture for their MVP. They spent 8 months on infrastructure. By the time they launched, their competitor (who'd shipped a simple monolith) had captured the market. The startup's sophisticated architecture supported requirements they never reached -- because they ran out of runway. The plugin system was never used by anyone. The multi-region deployment served traffic from one region. The multi-tenancy supported one tenant.

---

## Key Quotes

> "Always implement things when you actually need them, never when you just foresee that you need them."
> -- Ron Jeffries

> "The best code is no code at all."
> -- Jeff Atwood

> "Simplicity -- the art of maximizing the amount of work not done -- is essential."
> -- Agile Manifesto

> "Speculative generality can be spotted when the only users of a function or class are test cases."
> -- Martin Fowler

---

## Further Reading

- *Extreme Programming Explained* -- Kent Beck (1999, 2nd Edition 2004)
- *Refactoring* -- Martin Fowler (2018), especially the "Speculative Generality" smell
- ["YAGNI"](https://martinfowler.com/bliki/Yagni.html) -- Martin Fowler
- *Lean Software Development* -- Mary & Tom Poppendieck (2003)
- ["The Last Responsible Moment"](https://blog.codinghorror.com/the-last-responsible-moment/) -- Jeff Atwood
