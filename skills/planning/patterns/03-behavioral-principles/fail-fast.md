# Fail Fast

**Detect and report errors at the earliest possible moment rather than allowing them to propagate.**

---

## Origin

The Fail Fast principle has roots in engineering and systems thinking, long predating software. In software, it was popularized by Jim Shore in his 2004 IEEE Software article *"Fail Fast"* and is a core tenet of the Erlang/OTP philosophy developed by Joe Armstrong at Ericsson in the late 1980s. Martin Fowler and others have written extensively about it in the context of Continuous Integration and agile development. The phrase appears in hardware engineering as far back as the 1970s.

---

## The Problem It Solves

When errors are not detected early, they propagate through the system, mutating state and crossing boundaries until they surface far from their origin. A null value introduced in step 1 of a pipeline causes a crash in step 47 — and the stack trace points to step 47, not step 1. Developers spend hours tracing backward through the system. In production, silent corruption is worse than a crash: the system appears to work while producing subtly wrong results (incorrect billing, corrupted data, security vulnerabilities).

---

## The Principle Explained

Fail Fast means validating inputs, preconditions, and invariants as early as possible, and raising errors immediately rather than continuing with invalid state. If a function receives a null argument it cannot handle, it should throw immediately — not proceed until the null dereferences somewhere deep in call stack.

The principle applies at every level. At the code level, use assertions and guard clauses. At the API level, validate requests before processing. At the build level, catch type errors at compile time rather than runtime. At the deployment level, fail a health check rather than serving partial responses.

Critically, Fail Fast does not mean "crash and lose data." It means "detect the problem now, report it clearly, and stop the current operation before it can cause further damage." The system should fail in a controlled, observable way — with clear error messages, proper logging, and graceful cleanup — not silently continue in a corrupt state.

---

## Code Examples

### BAD: Failing slowly — errors propagate and obscure root cause

```typescript
interface UserInput {
  name?: string;
  email?: string;
  age?: number;
}

// This function silently continues with bad data
async function createUser(input: UserInput): Promise<User> {
  // No validation — nulls and invalid values propagate
  const user = {
    name: input.name?.trim(),          // could be undefined
    email: input.email?.toLowerCase(), // could be undefined
    age: input.age,                    // could be negative, NaN, etc.
    createdAt: new Date(),
  };

  // Undefined name silently becomes the string "undefined" in DB
  const result = await db.query(
    `INSERT INTO users (name, email, age) VALUES ($1, $2, $3)`,
    [user.name, user.email, user.age]
  );

  // Sending email to undefined@... fails silently or crashes later
  await emailService.sendWelcome(user.email!);

  return { id: result.rows[0].id, ...user } as User;
}

// Called elsewhere — the error surfaces far from the cause
async function handleRegistration(req: Request): Promise<Response> {
  try {
    const user = await createUser(req.body);
    // Crash happens HERE when trying to format the response
    // because user.name is undefined — but the bug is in the input
    return { status: 200, body: `Welcome, ${user.name.toUpperCase()}!` };
  } catch (error) {
    // Stack trace points here, not at the missing input validation
    return { status: 500, body: "Internal server error" };
  }
}
```

### GOOD: Failing fast — errors caught at the boundary

```typescript
class ValidationError extends Error {
  constructor(
    public readonly field: string,
    public readonly reason: string
  ) {
    super(`Validation failed for '${field}': ${reason}`);
    this.name = "ValidationError";
  }
}

interface CreateUserInput {
  name: string;
  email: string;
  age: number;
}

function validateCreateUserInput(input: unknown): CreateUserInput {
  if (input === null || typeof input !== "object") {
    throw new ValidationError("input", "must be an object");
  }

  const { name, email, age } = input as Record<string, unknown>;

  if (typeof name !== "string" || name.trim().length === 0) {
    throw new ValidationError("name", "must be a non-empty string");
  }

  if (typeof email !== "string" || !email.includes("@")) {
    throw new ValidationError("email", "must be a valid email address");
  }

  if (typeof age !== "number" || !Number.isInteger(age) || age < 0 || age > 150) {
    throw new ValidationError("age", "must be an integer between 0 and 150");
  }

  return { name: name.trim(), email: email.toLowerCase(), age };
}

async function createUser(input: CreateUserInput): Promise<User> {
  // Precondition: input is already validated — we can trust the types
  const result = await db.query(
    `INSERT INTO users (name, email, age) VALUES ($1, $2, $3) RETURNING id`,
    [input.name, input.email, input.age]
  );

  if (result.rows.length === 0) {
    throw new Error("Database INSERT did not return an ID — invariant violation");
  }

  return { id: result.rows[0].id, ...input, createdAt: new Date() };
}

async function handleRegistration(req: Request): Promise<Response> {
  try {
    // Fail fast: validate at the boundary
    const validatedInput = validateCreateUserInput(req.body);
    const user = await createUser(validatedInput);
    return { status: 201, body: `Welcome, ${user.name}!` };
  } catch (error) {
    if (error instanceof ValidationError) {
      // Clear, actionable error for the caller
      return { status: 400, body: `Invalid input: ${error.message}` };
    }
    throw error; // Unexpected errors propagate to global handler
  }
}
```

---

## Alternatives & Related Principles

| Approach | Relationship |
|---|---|
| **Fail-Safe** | The opposite strategy: when something goes wrong, default to a safe state rather than stopping. Circuit breakers and fallback values are fail-safe. Use fail-safe for runtime resilience; use fail-fast for development-time correctness. |
| **Graceful Degradation** | The system continues operating with reduced functionality rather than failing entirely. Complementary to fail-fast: fail fast on programmer errors, degrade gracefully on external failures. |
| **Let It Crash (Erlang/OTP)** | Processes fail fast and a supervisor restarts them. The innovation is not preventing crashes but recovering from them cheaply. This combines fail-fast detection with fail-safe recovery. |
| **Defensive Programming** | Check everything, trust nothing. Can lead to excessive null checks and silent fallbacks — the opposite of fail-fast if taken to mean "never let an error surface." |
| **Design by Contract** | Preconditions, postconditions, and invariants are checked at method boundaries. A formal version of fail-fast. |

---

## When NOT to Apply

- **User-facing input**: Users make typos. A form should highlight errors, not crash. Fail-fast applies to the validation layer, but the UI should be forgiving.
- **External service calls**: A downstream service being unavailable should trigger retries, circuit breakers, or fallbacks — not an immediate crash.
- **Batch processing**: If processing 10,000 records, failing fast on record #3 and stopping all processing may not be appropriate. Collect errors, skip bad records, and report at the end.
- **Observability in production**: In production, a fail-fast crash with no telemetry is worse than a degraded response with logging. Ensure fail-fast is paired with proper error reporting.

---

## Tensions & Trade-offs

- **Fail-Fast vs. Availability**: Failing fast reduces availability. A 500 error is worse for the user than a partially correct response — sometimes.
- **Fail-Fast vs. Resilience**: Distributed systems need both. Fail fast on logic errors (bad inputs, invariant violations). Fail safe on infrastructure errors (network timeouts, disk full).
- **Validation cost**: Exhaustive upfront validation can be expensive. Validating a 100MB file upload at the boundary requires buffering the entire file before processing begins.
- **Error message quality**: Fail-fast is only useful if the error message clearly indicates the problem. `AssertionError: assertion failed` is fail-fast but useless.

---

## Real-World Consequences

**Violation example**: The Ariane 5 rocket explosion (1996) occurred because a 64-bit floating-point number was converted to a 16-bit signed integer without range checking. The overflow was caught but the handler shut down the inertial reference system — a fail-fast response at the wrong layer. The software should have validated the conversion at the boundary, or the system design should have handled the failure differently.

**Adherence example**: TypeScript's strict mode is a fail-fast mechanism. By catching type errors at compile time rather than runtime, entire categories of bugs are eliminated before code ever runs. Teams adopting `strict: true` typically see a significant reduction in production type-related errors.

---

## Key Quotes

> "It is better to fail fast and visibly than to produce incorrect results silently." — Jim Shore, IEEE Software, 2004

> "Let it crash." — Joe Armstrong, Erlang philosophy

> "Assertions are not error handling. Assertions catch programmer mistakes; error handling catches user mistakes and environmental failures." — common paraphrase

> "The earlier you catch defects, the cheaper they are to fix." — Barry Boehm, on the cost of defect curves

---

## Further Reading

- Shore, J. — *Fail Fast* (IEEE Software, 2004)
- Armstrong, J. — *Making Reliable Distributed Systems in the Presence of Software Errors* (PhD thesis, 2003)
- Nygard, M. — *Release It!* (2018), Chapter on stability patterns
- Bloch, J. — *Effective Java* (2018), Item 49: "Check parameters for validity"
- Meyer, B. — *Object-Oriented Software Construction* (1997), Design by Contract chapters
