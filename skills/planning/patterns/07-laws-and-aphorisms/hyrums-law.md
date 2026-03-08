# Hyrum's Law

## Origin

Hyrum Wright, software engineer at Google, circa 2012. Formalized as: "With a sufficient number of users of an API, it does not matter what you promise in the contract: all observable behaviors of your system will be depended upon by somebody."

Sometimes called the "Law of Implicit Interfaces."

## Explanation

Your API contract says one thing. Your implementation does ten other things that are technically observable — ordering of JSON keys, timing of responses, whitespace in error messages, the specific wording of exceptions. Given enough consumers, someone will depend on every single one of those incidental behaviors. This means any change you make — even to "undefined" behavior — will break someone.

This is not hypothetical. It is an empirical observation from maintaining APIs used by thousands of internal teams at Google.

## TypeScript Code Examples

### Bad: Depending on Undocumented Behavior

```typescript
// The API returns users sorted by ID as an implementation detail.
// No documentation promises this ordering.

// api/users.ts
export async function getActiveUsers(): Promise<User[]> {
  // PostgreSQL happens to return rows in insertion order for small tables
  return db.query("SELECT * FROM users WHERE active = true");
}

// consumer/dashboard.ts — depends on implicit ordering
export async function renderDashboard(): Promise<void> {
  const users = await apiClient.getActiveUsers();
  // Assumes first user is the oldest account (earliest ID)
  // This breaks when the DB switches to parallel scans or
  // the API adds a cache layer that returns different ordering.
  const foundingMember = users[0];
  showFounderBadge(foundingMember);
}
```

### Good: Make Contracts Explicit, Hide Implementation Details

```typescript
// api/users.ts — explicit contract, implementation hidden
interface GetUsersOptions {
  readonly sortBy: "id" | "name" | "createdAt";
  readonly order: "asc" | "desc";
}

export async function getActiveUsers(
  options: GetUsersOptions = { sortBy: "id", order: "asc" }
): Promise<User[]> {
  return db.query(
    `SELECT * FROM users WHERE active = true ORDER BY ${options.sortBy} ${options.order}`
  );
}

// consumer/dashboard.ts — uses explicit ordering
export async function renderDashboard(): Promise<void> {
  const users = await apiClient.getActiveUsers({
    sortBy: "createdAt",
    order: "asc",
  });
  const foundingMember = users[0]; // Contract guarantees this is correct
  showFounderBadge(foundingMember);
}
```

### Bad: Leaking Error Message Format

```typescript
// Consumers parse error messages instead of error codes
export function validateAge(age: number): void {
  if (age < 0) {
    throw new Error("Age must be non-negative"); // Consumers regex this string
  }
}

// consumer code:
try {
  validateAge(input);
} catch (e) {
  if (e.message.includes("non-negative")) {  // Hyrum's Law in action
    showAgeError();
  }
}
```

### Good: Use Structured Error Types

```typescript
export class ValidationError extends Error {
  constructor(
    public readonly code: "NEGATIVE_AGE" | "AGE_TOO_HIGH" | "INVALID_FORMAT",
    message: string
  ) {
    super(message);
  }
}

export function validateAge(age: number): void {
  if (age < 0) {
    throw new ValidationError("NEGATIVE_AGE", "Age must be non-negative");
  }
}

// consumer code:
try {
  validateAge(input);
} catch (e) {
  if (e instanceof ValidationError && e.code === "NEGATIVE_AGE") {
    showAgeError(); // Depends on stable code, not fragile string
  }
}
```

## API Design Implications

1. **Minimize observable surface area.** Every behavior consumers can see, they will depend on.
2. **Randomize what should not be depended upon.** Google's protobuf serialization deliberately randomizes field ordering so no one depends on it.
3. **Version aggressively.** If you cannot hide a behavior, version it so you can change it later.
4. **Use opaque types.** Return IDs as opaque strings, not sequential integers — consumers will infer meaning from patterns.
5. **Document what is NOT guaranteed.** Explicitly state: "ordering is undefined," "timing may vary," "error messages may change."

## Alternatives and Related Concepts

- **Postel's Law (Robustness Principle):** "Be conservative in what you send, liberal in what you accept." Hyrum's Law shows why being liberal in what you accept creates long-term maintenance burden.
- **Semantic Versioning:** A contract mechanism, but Hyrum's Law means even minor versions break someone.
- **Consumer-Driven Contract Testing (Pact):** Explicitly captures what consumers actually depend on.

## When NOT to Apply

- **Internal-only code with few consumers:** If your function has two callers you control, just change both.
- **Early prototypes:** Over-engineering against Hyrum's Law in a prototype is premature.
- **Strongly typed, compiler-enforced interfaces:** The type system prevents depending on most incidental behavior (but not all — timing, ordering, and performance characteristics leak through).

## Trade-offs

| Defense | Benefit | Cost |
|---|---|---|
| Opaque types and encapsulation | Limits observable surface | More boilerplate, less convenient for consumers |
| Randomizing undefined behavior | Prevents implicit dependencies | Harder to debug, may confuse users |
| Strict versioning | Clean migration path | Version explosion, maintenance burden |
| Consumer-driven contract tests | Catches real dependencies | Test infrastructure overhead |

## Real-World Consequences

- **Python 2 dict ordering:** CPython 3.6 made dict ordering an implementation detail; 3.7 made it a language guarantee — because everyone already depended on it.
- **Google's protobuf map iteration:** Deliberately randomized to prevent ordering dependencies. Broke internal code that assumed deterministic ordering.
- **npm left-pad incident (2016):** Thousands of projects depended on an 11-line package's exact behavior, including its whitespace handling.
- **Java HashMap ordering:** Changed between Java 7 and 8. Broke code that assumed insertion-order iteration.

## Further Reading

- Hyrum's Law website: https://www.hyrumslaw.com/
- Wright, H. — talks at Google on large-scale API maintenance
- Winters, T., Manshreck, T., & Wright, H. (2020). *Software Engineering at Google*
- Fowler, M. (2011). "Consumer-Driven Contracts" — martinfowler.com
