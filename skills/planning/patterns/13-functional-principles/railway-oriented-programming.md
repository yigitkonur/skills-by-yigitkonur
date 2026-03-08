# Railway-Oriented Programming

**Model computations as a two-track railway: the happy path and the error path. Functions compose along the tracks without explicit error checking at every step.**

---

## Origin / History

Railway-Oriented Programming (ROP) was coined by Scott Wlaschin in his 2014 talk and blog series "Railway Oriented Programming" for the F# community. The underlying concept — monadic error handling via Either/Result types — originates from Haskell's `Either` monad and ML's `Result` type, dating back to the 1990s. The Rust language (2010+) adopted `Result<T, E>` as its primary error handling mechanism, proving the pattern's viability in systems programming.

In TypeScript, the pattern gained traction through libraries like fp-ts (Giulio Canti, 2017), neverthrow (George Briggs, 2019), and Effect (Effect-TS team, 2022+). These brought monadic error handling to a language that traditionally relied on try/catch.

Wlaschin's contribution was not the invention of the technique but the visualization: two parallel railway tracks, where functions either continue on the "success" track or divert to the "failure" track, and composition connects track segments seamlessly.

---

## The Problem It Solves

Traditional error handling in TypeScript has two problematic patterns. First, try/catch creates invisible control flow: any function might throw, and the caller has no way to know from the type signature. Second, error checks at every step create deeply nested or early-return-heavy code that obscures the happy path.

Consider validating a user registration: check email format, verify uniqueness, hash password, create record, send welcome email. With try/catch, each step might throw different errors that get caught in a single catch block, losing context. With explicit checks, you get a cascade of `if (error) return error` statements. Both approaches make the happy path hard to see and composition impossible.

ROP solves this by encoding success and failure in the type system. Each function returns `Result<Success, Failure>`, and a `chain`/`flatMap` operation connects them. If any step fails, subsequent steps are automatically skipped — the computation slides to the error track.

---

## The Principle Explained

The core abstraction is the `Result<T, E>` type (also called `Either<L, R>`): a value that is either a success containing `T` or a failure containing `E`. Functions that can fail return this type instead of throwing. The type system forces the caller to handle both cases.

Composition works through `map` (transform the success value, pass through failures) and `chain`/`flatMap` (apply a function that itself returns a Result, flattening the nesting). A pipeline of `chain` calls reads as a sequence of steps where each step can fail, but the error handling is implicit in the plumbing.

The "railway" metaphor makes this concrete: imagine two parallel tracks. A `map` function is a piece of track that transforms cargo on the success track and does nothing on the failure track. A `chain` function is a switch that might divert from the success track to the failure track. The beauty is that once on the failure track, the cargo (error) rides through all subsequent stations untouched until the end, where you handle it once.

---

## Code Examples

### BAD: Nested try/catch with lost context and invisible control flow

```typescript
async function registerUser(input: {
  email: string;
  password: string;
  name: string;
}): Promise<User> {
  try {
    // Any of these can throw — but which one did?
    const validatedEmail = validateEmail(input.email);
    const existingUser = await findUserByEmail(validatedEmail);
    if (existingUser) throw new Error("Email already in use");
    const hashedPassword = await hashPassword(input.password);
    const user = await createUser({
      email: validatedEmail,
      password: hashedPassword,
      name: input.name,
    });
    await sendWelcomeEmail(user.email);
    return user;
  } catch (error) {
    // All errors land here — validation, DB, email service
    // Lost context: was it a user error or a system failure?
    console.error("Registration failed:", error);
    throw error; // Re-throw with no additional context
  }
}
```

### GOOD: Railway-oriented pipeline with Result types (using neverthrow)

```typescript
import { ok, err, Result, ResultAsync } from "neverthrow";

// Each function returns a Result — errors are in the type signature
type RegistrationError =
  | { kind: "INVALID_EMAIL"; detail: string }
  | { kind: "EMAIL_TAKEN"; email: string }
  | { kind: "WEAK_PASSWORD"; detail: string }
  | { kind: "DB_ERROR"; cause: unknown }
  | { kind: "EMAIL_SERVICE_ERROR"; cause: unknown };

function validateEmail(email: string): Result<string, RegistrationError> {
  const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return pattern.test(email)
    ? ok(email.toLowerCase().trim())
    : err({ kind: "INVALID_EMAIL", detail: `Invalid format: ${email}` });
}

function validatePassword(password: string): Result<string, RegistrationError> {
  return password.length >= 8
    ? ok(password)
    : err({ kind: "WEAK_PASSWORD", detail: "Password must be at least 8 characters" });
}

function checkEmailAvailability(
  email: string,
): ResultAsync<string, RegistrationError> {
  return ResultAsync.fromPromise(
    findUserByEmail(email).then((existing) => {
      if (existing) throw new Error("taken");
      return email;
    }),
    () => ({ kind: "EMAIL_TAKEN" as const, email }),
  );
}

// The railway pipeline — reads as a clear sequence of steps
function registerUser(input: {
  email: string;
  password: string;
  name: string;
}): ResultAsync<User, RegistrationError> {
  return ok(input)
    .andThen(({ email }) => validateEmail(email))
    .asyncAndThen((validEmail) => checkEmailAvailability(validEmail))
    .andThen((email) =>
      validatePassword(input.password).map((password) => ({ email, password })),
    )
    .andThen(({ email, password }) =>
      ResultAsync.fromPromise(
        hashPassword(password).then((hashed) => ({ email, hashed })),
        (cause) => ({ kind: "DB_ERROR" as const, cause }),
      ),
    )
    .andThen(({ email, hashed }) =>
      ResultAsync.fromPromise(
        createUser({ email, password: hashed, name: input.name }),
        (cause) => ({ kind: "DB_ERROR" as const, cause }),
      ),
    );
}

// At the boundary: handle both tracks
const result = await registerUser(formData);
result.match(
  (user) => res.status(201).json(user),
  (error) => {
    switch (error.kind) {
      case "INVALID_EMAIL":
      case "WEAK_PASSWORD":
        return res.status(400).json({ error: error.detail });
      case "EMAIL_TAKEN":
        return res.status(409).json({ error: `${error.email} is taken` });
      case "DB_ERROR":
      case "EMAIL_SERVICE_ERROR":
        return res.status(500).json({ error: "Internal server error" });
    }
  },
);
```

### Minimal Result type implementation

```typescript
type Result<T, E> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

function succeed<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

function fail<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

function map<T, U, E>(
  result: Result<T, E>,
  fn: (value: T) => U,
): Result<U, E> {
  return result.ok ? succeed(fn(result.value)) : result;
}

function chain<T, U, E>(
  result: Result<T, E>,
  fn: (value: T) => Result<U, E>,
): Result<U, E> {
  return result.ok ? fn(result.value) : result;
}
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **try/catch** | Native to JavaScript. No library needed. But errors are invisible in types, composition breaks at every throw, and catch blocks mix error types. |
| **Error codes / sentinel values** | `null` or `-1` as error indicators. Simple but easy to ignore, no type safety, loses error context. |
| **Go-style multiple returns** | `const [result, error] = await doThing()`. Explicit, but requires checking `error` at every call site. Cannot compose. |
| **Option/Maybe type** | Like Result but without error information — just "present" or "absent". Good for optional values, insufficient for error handling. |
| **Effect-TS** | A full effect system that tracks errors, async, dependencies, and more in the type system. More powerful than Result alone but significantly more complex. |

---

## When NOT to Apply

- **Simple scripts and prototypes**: The overhead of Result types in a 50-line script is not justified. Use try/catch.
- **When the team does not know the pattern**: ROP requires understanding monadic composition. Introducing it without training creates confusion, not clarity.
- **Truly exceptional conditions**: Out-of-memory errors, stack overflows, and assertion failures should still throw. They are not business logic errors.
- **Thin API layers**: If your controller just calls a service and maps the result to HTTP, explicit try/catch may be clearer than importing a Result library.

---

## Tensions & Trade-offs

- **Type safety vs. Verbosity**: Result types make errors explicit at the cost of more verbose function signatures and return type annotations.
- **Composition vs. Debugging**: A long `.andThen().map().andThen()` chain is elegant but harder to step through in a debugger than sequential try/catch blocks.
- **Library dependency vs. DIY**: Using fp-ts or neverthrow adds a dependency. Rolling your own Result type is simple but lacks ecosystem utilities.
- **Interop with throwing code**: The JavaScript ecosystem is built on throwing. Wrapping every library call in `ResultAsync.fromPromise` adds friction.

---

## Real-World Consequences

**Rust's Result type**: Rust adopted Result as its primary error handling mechanism. The `?` operator (early return on error) makes ROP ergonomic. The result: Rust programs have some of the clearest error handling of any systems language, and "exception safety" is a non-issue.

**fp-ts in production**: Several fintech companies use fp-ts to model financial transaction pipelines. Each step (validate, authorize, execute, reconcile) returns an `Either`, and the pipeline composes without any step needing to know about errors from other steps. Error reports are structured and complete because the error type is a discriminated union.

**Validation pipelines**: E-commerce platforms that switched from try/catch to Result-based validation reported that they could now return all validation errors at once (by collecting results) instead of stopping at the first error — improving user experience without complicating the code.

---

## Further Reading

- [Scott Wlaschin — Railway Oriented Programming (F# for Fun and Profit)](https://fsharpforfunandprofit.com/rop/)
- [neverthrow — Type-safe error handling for TypeScript](https://github.com/supermacro/neverthrow)
- [fp-ts — Functional programming in TypeScript](https://gcanti.github.io/fp-ts/)
- [Effect-TS — Next-generation TypeScript effect system](https://effect.website/)
- [Rust Book — Error Handling with Result](https://doc.rust-lang.org/book/ch09-02-recoverable-errors-with-result.html)
