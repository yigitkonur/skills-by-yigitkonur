# KISS -- Keep It Simple, Stupid

**Most systems work best if they are kept simple rather than made complicated; simplicity should be a key design goal and unnecessary complexity should be avoided.**

---

## Origin

Attributed to **Kelly Johnson**, lead engineer at Lockheed Martin's Skunk Works, around 1960. Johnson's requirement was that jet aircraft should be repairable by an average mechanic in field conditions with basic tools. If the design was too complex for that, it was too complex. The principle has roots even earlier -- in Occam's Razor (14th century), Einstein's "as simple as possible, but not simpler," and Antoine de Saint-Exupery's "perfection is achieved not when there is nothing more to add, but when there is nothing left to take away."

---

## The Problem It Solves

Complexity is the primary killer of software projects. Not requirements changes, not technical debt, not management -- complexity. When code is complex, developers can't hold it in their heads. They make changes in one place and break things in another. Bug fixes introduce new bugs. New features take exponentially longer. Onboarding takes months instead of days. Eventually, the team proposes a rewrite -- which will also become complex, because the *habit* of building complex solutions wasn't addressed.

---

## The Principle Explained

KISS demands that you prefer the simplest solution that adequately solves the problem. "Simple" doesn't mean "easy" -- simple means having fewer moving parts, fewer abstractions, fewer indirections, and more directness. A linked list is simpler than a red-black tree, but a red-black tree is the right choice when you need O(log n) operations. KISS doesn't say "use the dumbest tool." It says "don't use a more sophisticated tool than the problem demands."

The deeper insight is that simplicity is *hard*. It takes more effort to write simple code than complex code. Complex code is what comes out naturally when you start typing. Simple code requires you to think, refactor, and remove until only the essential remains. Juniors write complex code because they don't know better. Intermediates write complex code because they know too many patterns. Seniors write simple code because they've learned what actually matters.

There's a critical distinction between **essential complexity** (inherent in the problem domain) and **accidental complexity** (introduced by our solution). KISS targets accidental complexity. If the domain is genuinely complex -- tax law, medical protocols, financial regulation -- the code will reflect that. The goal is to not add complexity beyond what the domain requires.

---

## Code Examples

### BAD: Over-engineered solution to a simple problem

```typescript
// Task: check if a user is an admin
// "Let's use the Strategy pattern with a factory!"

interface AuthorizationStrategy {
  isAuthorized(user: User, resource: string, action: string): boolean;
}

class RoleBasedAuthStrategy implements AuthorizationStrategy {
  constructor(private roleHierarchy: Map<string, string[]>) {}

  isAuthorized(user: User, resource: string, action: string): boolean {
    const effectiveRoles = this.resolveRoleHierarchy(user.role);
    return effectiveRoles.some((role) =>
      this.getPermissions(role).some(
        (p) => p.resource === resource && p.actions.includes(action)
      )
    );
  }

  private resolveRoleHierarchy(role: string): string[] {
    const roles = [role];
    const children = this.roleHierarchy.get(role) ?? [];
    for (const child of children) {
      roles.push(...this.resolveRoleHierarchy(child));
    }
    return roles;
  }

  private getPermissions(role: string): Permission[] {
    // ...50 more lines
    return [];
  }
}

class AuthorizationStrategyFactory {
  static create(config: AuthConfig): AuthorizationStrategy {
    switch (config.type) {
      case "role-based": return new RoleBasedAuthStrategy(config.hierarchy);
      case "attribute-based": return new AbacStrategy(config.policies);
      case "acl": return new AclStrategy(config.acls);
      default: throw new Error(`Unknown auth type: ${config.type}`);
    }
  }
}
```

### GOOD: Direct solution

```typescript
// Task: check if a user is an admin
function isAdmin(user: User): boolean {
  return user.role === "admin";
}

// When the requirements *actually* get more complex, evolve the solution.
// Right now, this is all we need. It's obvious, testable, and fast.
```

### BAD: Abstraction astronautics in data transformation

```typescript
// "Let's build a pipeline framework for data transformations"
type TransformStep<TIn, TOut> = (input: TIn) => TOut;

class Pipeline<TStart> {
  private steps: TransformStep<unknown, unknown>[] = [];

  pipe<TOut>(step: TransformStep<TStart, TOut>): Pipeline<TOut> {
    this.steps.push(step as TransformStep<unknown, unknown>);
    return this as unknown as Pipeline<TOut>;
  }

  execute(input: TStart): unknown {
    return this.steps.reduce(
      (value, step) => step(value),
      input as unknown
    );
  }
}

// Usage:
const result = new Pipeline<RawApiResponse>()
  .pipe(extractData)
  .pipe(normalizeFields)
  .pipe(validateSchema)
  .pipe(mapToViewModel)
  .execute(apiResponse);

// Looks clever. But: type safety is lost at boundaries, debugging is
// opaque, stack traces are useless, and a new developer has to understand
// the Pipeline class before they can understand the business logic.
```

### GOOD: Just call the functions

```typescript
function processApiResponse(raw: RawApiResponse): ViewModel {
  const data = extractData(raw);
  const normalized = normalizeFields(data);
  const validated = validateSchema(normalized);
  return mapToViewModel(validated);
}

// Every step is visible. Types flow naturally. Debugging is trivial.
// Stack traces point to the exact line. A junior developer understands
// this on day one. No framework to learn, no abstraction to maintain.
```

### BAD: Unnecessary abstraction layers

```typescript
// Three layers of indirection for a simple database call
class UserController {
  constructor(private userService: UserService) {}
  async getUser(id: string) { return this.userService.getUser(id); }
}

class UserService {
  constructor(private userRepository: UserRepository) {}
  async getUser(id: string) { return this.userRepository.findById(id); }
}

class UserRepository {
  constructor(private db: Database) {}
  async findById(id: string) { return this.db.query("SELECT * FROM users WHERE id = $1", [id]); }
}

// Three files, three classes, zero added value. Each layer just
// delegates to the next with no transformation or business logic.
```

### GOOD: Only add layers that earn their keep

```typescript
class UserController {
  constructor(private db: Database) {}

  async getUser(id: string): Promise<User | null> {
    const row = await this.db.query("SELECT * FROM users WHERE id = $1", [id]);
    return row ? mapRowToUser(row) : null;
  }
}

// Add a service layer WHEN there's business logic that doesn't
// belong in the controller. Not before. Not "just in case."
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|-----------|-------------|
| **Worse Is Better** | Richard Gabriel's (1989) argument that simpler, "worse" systems with fewer features beat "better" systems with more features, because they're easier to adopt, port, and maintain. Unix vs. Lisp as the canonical example. |
| **MIT Approach (The Right Thing)** | The counterpoint to Worse Is Better. Build it correctly and completely the first time. Favored in academia and safety-critical systems. Higher up-front cost, potentially lower long-term cost in certain domains. |
| **New Jersey Approach** | Gabriel's name for Worse Is Better. Simplicity of implementation is prioritized over simplicity of interface. If it's hard to implement fully, simplify the interface. |
| **Gall's Law** | "A complex system that works is invariably found to have evolved from a simple system that worked." Start simple. Evolve. |
| **Essential vs. Accidental Complexity** | Fred Brooks' distinction (1986). KISS targets accidental complexity -- the stuff we introduce ourselves. |

---

## When NOT to Apply

- **When the domain is genuinely complex.** Oversimplifying a tax calculation engine or a medical records system leads to incorrect behavior. Don't confuse "simple code" with "simple model."
- **When you're building a library or framework.** Library code serves many consumers and rightly contains abstractions that would be overkill in application code.
- **When performance demands it.** Sometimes the simple O(n^2) solution isn't good enough and you need the complex O(n log n) one. That complexity is *essential*, not accidental.
- **When regulatory or safety requirements exist.** Audit logging, access control, and input validation add complexity. They're non-negotiable.

---

## Tensions & Trade-offs

- **KISS vs. DRY**: Making code DRY often adds abstraction layers. KISS says those layers are complexity. The resolution: only abstract when the duplication actually causes maintenance pain, not just because it offends your aesthetics.
- **KISS vs. Open-Closed Principle**: OCP encourages extension points and abstractions. KISS says keep it direct. Build the abstraction when you need the second implementation, not before.
- **KISS vs. Flexibility**: Flexible designs are complex designs. A system that handles every possible configuration is harder to understand than one that handles the three configurations you actually use.
- **KISS vs. Best Practices**: Blindly applying every "best practice" (dependency injection, repository pattern, CQRS, event sourcing) to every project creates accidental complexity. Best practices are context-dependent.

---

## Real-World Consequences

A team replaced a working 200-line Express endpoint with a "clean architecture" rewrite: controllers, use cases, repositories, domain entities, DTOs, mappers, and validators -- 2,000 lines across 15 files. The behavior was identical. The original developer could trace a request in 30 seconds. The new version required opening 8 files to understand the same flow. Bug fixes that took minutes now took hours. A junior developer spent their entire first week just understanding the folder structure. The "clean" architecture was abandoned six months later when the team couldn't maintain it.

---

## Key Quotes

> "Simplicity is the ultimate sophistication."
> -- Leonardo da Vinci (attributed)

> "Perfection is achieved, not when there is nothing more to add, but when there is nothing left to take away."
> -- Antoine de Saint-Exupery

> "There are two ways of constructing a software design: One way is to make it so simple that there are obviously no deficiencies, and the other way is to make it so complicated that there are no obvious deficiencies."
> -- C.A.R. Hoare

> "Controlling complexity is the essence of computer programming."
> -- Brian Kernighan

---

## Further Reading

- ["Worse Is Better"](https://dreamsongs.com/WorseIsBetter.html) -- Richard Gabriel (1989)
- *A Philosophy of Software Design* -- John Ousterhout (2018)
- ["No Silver Bullet"](http://worrydream.com/refs/Brooks-NoSilverBullet.pdf) -- Fred Brooks (1986) -- essential vs. accidental complexity
- *Systemantics: How Systems Really Work and How They Fail* -- John Gall (1975)
- *The Art of Unix Programming* -- Eric S. Raymond (2003)
