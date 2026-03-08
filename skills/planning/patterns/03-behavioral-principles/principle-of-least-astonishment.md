# Principle of Least Astonishment (POLA)

**Software should behave the way its users and developers expect it to.**

---

## Origin

The Principle of Least Astonishment (also called the Principle of Least Surprise) dates back to the early 1970s in the context of programming language design. It was popularized in the paper *"The Design of Everyday Things"* by Don Norman (1988) in the broader UX context, and explicitly referenced in Geoffrey James' *"The Tao of Programming"* (1987). In software engineering, it became a core tenet through the Unix philosophy and was formalized in various IEEE and ISO usability standards. The Ruby community is notably vocal about it, with Yukihiro Matsumoto citing POLA as a Ruby design goal.

---

## The Problem It Solves

When software surprises its users — whether those users are end-users or fellow developers — errors multiply. A function named `getUser()` that modifies a database, a `sort()` method that mutates the original array while also returning it, or a configuration file where `timeout: 30` means 30 milliseconds instead of 30 seconds — these all violate POLA. The result is bugs born from false assumptions, longer onboarding times, and defensive programming where developers stop trusting the API and inspect every method before calling it.

---

## The Principle Explained

POLA states that a component of a system should behave in a way that most users will expect it to behave. The behavior should not astonish or surprise. This applies at every level: API naming, function signatures, return types, error handling, configuration defaults, and side effects.

The critical insight is that "least astonishing" is relative to the **audience**. For a JavaScript developer, arrays being zero-indexed is not surprising. For a Lua developer, one-indexed arrays are expected. POLA requires knowing your audience and their mental model. In a TypeScript codebase, following established conventions (camelCase, Promises for async operations, `null`/`undefined` semantics) is applying POLA.

At the API level, POLA demands **consistency** and **honesty**. If nine methods in a class are pure queries that return values, the tenth should not secretly write to a database. If your error handling uses exceptions throughout the codebase, one module should not switch to error codes without clear justification. Names should describe what happens, return types should match expectations, and defaults should be safe.

---

## Code Examples

### BAD: Violating POLA — surprising behavior

```typescript
class UserService {
  // Surprise: "get" suggests a read-only query, but this has side effects
  async getUser(id: string): Promise<User> {
    const user = await this.db.findOne({ id });
    // Hidden side effect: updates last accessed timestamp
    await this.db.update({ id }, { lastAccessed: new Date() });
    // Hidden side effect: increments a global counter
    this.analytics.trackUserAccess(id);
    return user;
  }

  // Surprise: returns undefined instead of throwing when user not found
  // but other methods in this class throw on missing resources
  async getUserByEmail(email: string): Promise<User | undefined> {
    return this.db.findOne({ email });
  }

  // Surprise: "delete" actually soft-deletes, unlike other delete methods
  async deleteUser(id: string): Promise<void> {
    await this.db.update({ id }, { isDeleted: true });
  }
}

// Surprise: timeout unit is inconsistent
const config = {
  connectionTimeout: 5000, // milliseconds
  readTimeout: 30,         // SECONDS — different unit, no indication
  retryDelay: 2,           // seconds again? milliseconds? who knows
};

// Surprise: sort mutates AND returns — which is the primary behavior?
function sortUsers(users: User[]): User[] {
  return users.sort((a, b) => a.name.localeCompare(b.name));
  // Caller might not realize `users` is now also sorted in place
}
```

### GOOD: Applying POLA — predictable behavior

```typescript
class UserService {
  // Read-only: name clearly says "find", no side effects
  async findUser(id: string): Promise<User> {
    const user = await this.db.findOne({ id });
    if (!user) {
      throw new UserNotFoundError(id);
    }
    return user;
  }

  // Consistent: also throws on not found, same pattern as findUser
  async findUserByEmail(email: string): Promise<User> {
    const user = await this.db.findOne({ email });
    if (!user) {
      throw new UserNotFoundError(`email: ${email}`);
    }
    return user;
  }

  // Side effects are in clearly-named methods
  async recordUserAccess(id: string): Promise<void> {
    await this.db.update({ id }, { lastAccessed: new Date() });
    this.analytics.trackUserAccess(id);
  }

  // Name makes behavior explicit
  async softDeleteUser(id: string): Promise<void> {
    await this.db.update({ id }, { isDeleted: true, deletedAt: new Date() });
  }

  async permanentlyDeleteUser(id: string): Promise<void> {
    await this.db.delete({ id });
  }
}

// Consistent units with explicit naming
interface TimeoutConfig {
  connectionTimeoutMs: number;
  readTimeoutMs: number;
  retryDelayMs: number;
}

const config: TimeoutConfig = {
  connectionTimeoutMs: 5000,
  readTimeoutMs: 30_000,
  retryDelayMs: 2000,
};

// Pure function: returns a new array, original untouched
function sortedUsers(users: readonly User[]): User[] {
  return [...users].sort((a, b) => a.name.localeCompare(b.name));
}
```

---

## Alternatives & Related Principles

| Principle | Relationship |
|---|---|
| **Principle of Least Privilege** | Related but different axis: POLA is about expectation, PoLP is about access. Both reduce surprise — PoLP ensures code cannot do unexpected things. |
| **Convention over Configuration** | Implements POLA by making defaults match what most developers expect, reducing the need to read documentation. |
| **Uniform Access Principle** | Properties and methods should be accessed the same way, reducing surprise about how to interact with objects. |
| **Principle of Least Effort** | From information science — users choose the path of least resistance. POLA ensures that path leads to correct behavior. |

---

## When NOT to Apply

- **When conventions conflict**: If two well-known conventions disagree (e.g., Ruby one-indexed vs. Python zero-indexed), you must pick one and document the choice rather than trying to satisfy both audiences.
- **When performance demands it**: Sometimes the unsurprising approach is slow. A `copy()` method that deep-clones a massive object is expected but might not be viable. Document the shallow copy behavior prominently.
- **When breaking from a bad convention**: If the existing codebase has established a bad pattern, introducing a better but inconsistent pattern may temporarily violate POLA. Use migration strategies and clear documentation.
- **Security contexts**: Sometimes surprising behavior is intentional — timing-safe comparison functions behave "surprisingly" (constant time regardless of input) for security reasons.

---

## Tensions & Trade-offs

- **POLA vs. Innovation**: Truly novel APIs necessarily surprise users. The first time someone sees `async/await` it is astonishing compared to callback conventions.
- **POLA vs. Correctness**: Sometimes the "expected" behavior is wrong. JavaScript's `==` operator behaves as many expect (`"1" == 1` is `true`) but `===` is more correct.
- **POLA vs. Backward Compatibility**: Fixing surprising behavior in a public API is itself surprising to existing users who have adapted to the old behavior.
- **Whose astonishment**: Junior and senior developers have different expectations. Library authors target a different audience than application developers.

---

## Real-World Consequences

**Violation example**: MySQL's `GROUP BY` historically allowed selecting non-aggregated columns not in the GROUP BY clause, returning an arbitrary row's value. This "worked" and surprised developers coming from PostgreSQL or SQL Server, leading to subtle data bugs that went undetected for years.

**Adherence example**: Go's standard library is famously consistent — `io.Reader` and `io.Writer` interfaces are used everywhere with the same semantics. Developers can predict how any I/O function works based on its signature alone, leading to high composability.

---

## Key Quotes

> "If a necessary feature has a high astonishment factor, it may be necessary to redesign the feature." — ANSI C Rationale (1988)

> "People are part of the system. The design should match the user's experience, expectations, and mental models." — Don Norman, *The Design of Everyday Things*

> "Programs must be written for people to read, and only incidentally for machines to execute." — Abelson & Sussman, *Structure and Interpretation of Computer Programs*

---

## Further Reading

- Norman, D. — *The Design of Everyday Things* (1988, revised 2013)
- James, G. — *The Tao of Programming* (1987)
- Bloch, J. — *Effective Java* (2008), Item 40: "Design method signatures carefully"
- Pike, R. — *Notes on Programming in C* (1989)
- Python Enhancement Proposal (PEP) 20 — *The Zen of Python* ("There should be one — and preferably only one — obvious way to do it")
