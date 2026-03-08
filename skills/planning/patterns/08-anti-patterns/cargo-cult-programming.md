# Cargo Cult Programming

## Origin

The term "cargo cult" comes from anthropology: after World War II, Pacific islanders built wooden replicas of airstrips and control towers, hoping to attract the cargo planes that had brought supplies during the war. They replicated the form without understanding the mechanism.

Applied to programming by Steve McConnell in *Code Complete* (1993) and popularized broadly in software engineering discourse. Richard Feynman coined "cargo cult science" in his 1974 Caltech commencement address.

## Explanation

Cargo cult programming is copying code, patterns, or practices without understanding why they work. The programmer replicates the visible structure but misses the underlying principles, resulting in code that appears correct but is fragile, inefficient, or nonsensical.

This includes:
- Copying Stack Overflow answers without understanding them
- Applying design patterns where they do not fit
- Following "best practices" as rituals rather than reasoned decisions
- Using frameworks and libraries without understanding their purpose

## TypeScript Code Examples

### Bad: Cargo-Culted Design Pattern

```typescript
// Someone read that "you should use the Repository Pattern"
// so they wrap every database call in a repository — including one-off scripts.

// Abstract repository (cargo-culted from a tutorial)
interface IRepository<T> {
  findAll(): Promise<T[]>;
  findById(id: string): Promise<T | null>;
  create(entity: T): Promise<T>;
  update(id: string, entity: Partial<T>): Promise<T>;
  delete(id: string): Promise<void>;
}

// Concrete repository
class UserRepository implements IRepository<User> {
  async findAll(): Promise<User[]> { return db.query("SELECT * FROM users"); }
  async findById(id: string): Promise<User | null> { return db.query("..."); }
  async create(user: User): Promise<User> { return db.query("..."); }
  async update(id: string, data: Partial<User>): Promise<User> { return db.query("..."); }
  async delete(id: string): Promise<void> { await db.query("..."); }
}

// Used in a one-time migration script:
const repo = new UserRepository();
const users = await repo.findAll();  // The abstraction adds nothing here.
// A direct `db.query("SELECT * FROM users")` would be clearer and simpler.

// The developer also created IUserRepositoryFactory,
// UserRepositoryFactoryImpl, and IUserService
// for a script that runs once and is deleted.
```

### Good: Understanding Before Applying

```typescript
// Repository pattern applied where it makes sense:
// multiple consumers, testability requirement, data source may change.

// The pattern is justified because:
// 1. The service has unit tests that mock the repository
// 2. We are considering moving from PostgreSQL to DynamoDB
// 3. Multiple services use user data with different query patterns

interface UserRepository {
  findByEmail(email: string): Promise<User | null>;
  findActiveByOrganization(orgId: string): Promise<User[]>;
  save(user: User): Promise<void>;
}

// PostgreSQL implementation
class PgUserRepository implements UserRepository {
  async findByEmail(email: string): Promise<User | null> {
    const row = await this.pool.query(
      "SELECT * FROM users WHERE email = $1",
      [email]
    );
    return row ? mapToUser(row) : null;
  }
  // ... other methods
}

// In tests: use a simple in-memory implementation
class InMemoryUserRepository implements UserRepository {
  private users: User[] = [];
  async findByEmail(email: string): Promise<User | null> {
    return this.users.find((u) => u.email === email) ?? null;
  }
  // ... simpler, faster tests without database
}
```

### Bad: Cargo-Culted Error Handling

```typescript
// Developer saw "always use try-catch" so they wrap everything:

async function getUser(id: string): Promise<User> {
  try {
    try {
      const user = await db.users.findById(id);
      try {
        if (!user) {
          try {
            throw new Error("User not found");
          } catch (e) {
            throw e;  // Re-throw... what was the point of catching?
          }
        }
        return user;
      } catch (e) {
        throw e;  // Another pointless catch-and-rethrow
      }
    } catch (e) {
      console.log("Error:", e);  // Log it...
      throw e;                   // ...and throw it again anyway
    }
  } catch (e) {
    throw e;  // Outermost catch just rethrows. Entire try-catch is noise.
  }
}

// The developer does not understand what try-catch is for.
// They saw it in tutorials and applied it ritually.
```

### Good: Intentional Error Handling

```typescript
async function getUser(id: string): Promise<User> {
  const user = await db.users.findById(id);
  if (!user) {
    throw new UserNotFoundError(id);
  }
  return user;
}

// Error handling at the boundary, where it serves a purpose:
app.get("/users/:id", async (req, res) => {
  try {
    const user = await getUser(req.params.id);
    res.json(user);
  } catch (error) {
    if (error instanceof UserNotFoundError) {
      res.status(404).json({ error: "User not found" });
    } else {
      logger.error("Unexpected error in getUser", { error, userId: req.params.id });
      res.status(500).json({ error: "Internal server error" });
    }
  }
});
```

## Common Cargo Cult Patterns in Software

| Cargo Cult Behavior | What It Looks Like | What Is Missing |
|---|---|---|
| Microservices everywhere | Every feature is a separate service | Understanding of when monoliths are better |
| 100% code coverage | Tests with no assertions | Understanding that coverage measures execution, not correctness |
| Kubernetes for everything | Single-container app on K8s | Understanding of when a VPS or serverless is simpler |
| TypeScript `any` everywhere | "We use TypeScript" but every type is `any` | Understanding that types are the point of TypeScript |
| Agile rituals without values | Daily standups, sprints, retros — no actual agility | Understanding the Agile Manifesto principles |
| DDD vocabulary without DDD | Classes named "Aggregate" and "ValueObject" without bounded contexts | Understanding the strategic patterns |

## Alternatives and Countermeasures

- **Ask "why" before "how":** Before applying a pattern, articulate the problem it solves.
- **Start simple:** Apply patterns when complexity demands them, not preemptively.
- **Read the source material:** Read the original pattern description, not just a blog summary.
- **Prototype without patterns:** Build the simplest version first, then refactor if needed.
- **Pair with someone who understands:** Learning through collaboration, not imitation.

## When NOT to Apply (When Copying Is Fine)

- **Boilerplate and configuration:** Copying a webpack config or Dockerfile from a working project is practical, not cargo cult — as long as you understand the settings.
- **Established conventions:** Following your team's coding conventions without questioning each one is efficiency, not cargo cult.
- **Well-documented patterns:** Using a well-known pattern (like MVC) in its intended context is application, not imitation.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Copy-paste from tutorials | Fast to implement, feels productive | Fragile, misunderstood, hard to debug |
| Understand before implementing | Correct application, deep knowledge | Slower initial development |
| Skip patterns entirely | Simple code, no ceremony | May miss genuine benefits of patterns |
| Learn patterns through refactoring | Patterns emerge from real needs | Requires patience and experience |

## Real-World Consequences

- **Enterprise Java (2000s):** The "Architecture Astronaut" era produced applications with dozens of design patterns, XML configuration files, and abstraction layers — all cargo-culted from J2EE best practices — for applications that were simple CRUD systems.
- **"Microservices" that are a distributed monolith:** Teams that adopted microservices because Netflix uses them, without understanding Netflix's specific scale and organizational constraints.
- **Scrum without autonomy:** Organizations that adopted Scrum ceremonies (standups, sprints, retros) but kept waterfall management, top-down planning, and no team autonomy.

## The Litmus Test

Before applying any pattern, answer: "What specific problem does this solve in my context, and what is the cost of not using it?"

If you cannot answer clearly, you may be cargo-culting.

## Further Reading

- McConnell, S. (2004). *Code Complete* (2nd ed.)
- Feynman, R. (1974). "Cargo Cult Science" — Caltech commencement address
- Gamma, E. et al. (1994). *Design Patterns* — read the "Applicability" sections, not just "Structure"
- Fowler, M. (2003). "Is Design Dead?" — martinfowler.com
