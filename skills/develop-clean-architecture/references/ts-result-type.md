---
title: Return Result Types Instead of Throwing in Domain Operations
impact: HIGH
impactDescription: makes error paths explicit and composable, eliminates uncaught exception crashes
tags: ts, result, error-handling, functional
---

## Return Result Types Instead of Throwing in Domain Operations

Replace thrown exceptions in domain and application layers with explicit `Result<T, E>` return types. This makes error paths visible in the type signature, forces callers to handle failures, and enables composable error propagation without try/catch pyramids.

**Incorrect (thrown exceptions hide error paths):**

```typescript
// domain/entities/User.ts
class User {
  constructor(
    public readonly id: string,
    public readonly email: string,
    public readonly age: number
  ) {
    if (!email.includes('@')) {
      throw new Error('Invalid email')  // Caller might not catch this
    }
    if (age < 18) {
      throw new Error('Must be 18 or older')  // Different error, same throw
    }
  }
}

// application/use-cases/RegisterUser.ts
class RegisterUserUseCase {
  async execute(input: RegisterInput): Promise<void> {
    try {
      const user = new User(generateId(), input.email, input.age)  // Might throw
      try {
        await this.userRepo.save(user)  // Might throw
        try {
          await this.emailService.sendWelcome(user.email)  // Might throw
        } catch (e) {
          // Nested try/catch pyramid — which error are we handling?
          console.error('Email failed', e)
        }
      } catch (e) {
        throw new Error('Registration failed')  // Original error lost
      }
    } catch (e) {
      throw e  // Re-thrown — caller has no idea what went wrong
    }
  }
}
```

**Correct (Result type makes errors explicit and composable):**

```typescript
// domain/types/Result.ts
type Result<T, E = Error> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E }

function ok<T>(value: T): Result<T, never> {
  return { ok: true, value }
}

function err<E>(error: E): Result<never, E> {
  return { ok: false, error }
}

function map<T, U, E>(result: Result<T, E>, fn: (v: T) => U): Result<U, E> {
  return result.ok ? ok(fn(result.value)) : result
}

function flatMap<T, U, E>(result: Result<T, E>, fn: (v: T) => Result<U, E>): Result<U, E> {
  return result.ok ? fn(result.value) : result
}

// domain/entities/User.ts
type UserError = 'INVALID_EMAIL' | 'UNDERAGE' | 'EMAIL_TAKEN'

class User {
  private constructor(
    public readonly id: string,
    public readonly email: string,
    public readonly age: number
  ) {}

  static create(id: string, email: string, age: number): Result<User, UserError> {
    if (!email.includes('@')) return err('INVALID_EMAIL')
    if (age < 18) return err('UNDERAGE')
    return ok(new User(id, email, age))
  }
}

// application/use-cases/RegisterUser.ts
class RegisterUserUseCase {
  async execute(input: RegisterInput): Promise<Result<User, UserError | 'SAVE_FAILED'>> {
    const userResult = User.create(generateId(), input.email, input.age)
    if (!userResult.ok) return userResult  // Propagate typed error

    const saveResult = await this.userRepo.save(userResult.value)
    if (!saveResult.ok) return err('SAVE_FAILED')

    // Fire-and-forget: email failure doesn't fail registration
    await this.emailService.sendWelcome(userResult.value.email)

    return ok(userResult.value)
  }
}

// Caller — every error path is visible and handled
const result = await registerUser.execute(input)
if (!result.ok) {
  switch (result.error) {
    case 'INVALID_EMAIL': return res.status(400).json({ message: 'Bad email' })
    case 'UNDERAGE': return res.status(400).json({ message: 'Must be 18+' })
    case 'EMAIL_TAKEN': return res.status(409).json({ message: 'Already registered' })
    case 'SAVE_FAILED': return res.status(500).json({ message: 'Try again later' })
  }
}
```

**When NOT to use this pattern:**
- Truly exceptional situations (out of memory, assertion violations) — throw is appropriate
- Infrastructure adapters wrapping external SDKs that throw — catch at the boundary, return Result
- Simple scripts or CLI tools where a top-level try/catch is sufficient
- When the team has adopted a library like `neverthrow` — use its API instead of rolling your own

**Benefits:**
- Error paths are part of the function signature — impossible to ignore
- No try/catch pyramids — results compose with map/flatMap
- Discriminated error types enable exhaustive handling in the caller
- Domain layer stays pure — no side-effectful throw statements
- Testing is straightforward — assert on `result.ok` and `result.error`

Reference: [neverthrow](https://github.com/supermacro/neverthrow) | [ts-results](https://github.com/vultix/ts-results)
