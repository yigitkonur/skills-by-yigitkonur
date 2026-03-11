# Error Handling

Type-safe error handling patterns for TypeScript applications.

## Result Type

Discriminated union for explicit error handling without exceptions.

```typescript
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };
```

### Basic usage

```typescript
function parseJSON<T>(raw: string): Result<T> {
  try {
    return { success: true, data: JSON.parse(raw) as T };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err : new Error(String(err)),
    };
  }
}

const result = parseJSON<Config>('{"port": 3000}');
if (result.success) {
  console.log(result.data.port); // Config
} else {
  console.error(result.error.message); // Error
}
```

### Result helpers

```typescript
function ok<T>(data: T): Result<T, never> {
  return { success: true, data };
}

function err<E = Error>(error: E): Result<never, E> {
  return { success: false, error };
}

// Usage
function divide(a: number, b: number): Result<number, string> {
  if (b === 0) return err('Division by zero');
  return ok(a / b);
}
```

### Chaining results

```typescript
function mapResult<T, U, E>(
  result: Result<T, E>,
  fn: (data: T) => U,
): Result<U, E> {
  if (result.success) {
    return { success: true, data: fn(result.data) };
  }
  return result;
}

function flatMapResult<T, U, E>(
  result: Result<T, E>,
  fn: (data: T) => Result<U, E>,
): Result<U, E> {
  if (result.success) {
    return fn(result.data);
  }
  return result;
}

// Pipeline
const result = flatMapResult(
  parseJSON<{ userId: string }>(raw),
  (data) => findUser(data.userId),
);
```

### Async results

```typescript
type AsyncResult<T, E = Error> = Promise<Result<T, E>>;

async function fetchUser(id: string): AsyncResult<User> {
  try {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) {
      return err(new Error(`HTTP ${response.status}: ${response.statusText}`));
    }
    const data = await response.json();
    return ok(data as User);
  } catch (error) {
    return err(error instanceof Error ? error : new Error(String(error)));
  }
}
```

---

## Custom Error Hierarchy

Structured error classes with metadata for different failure modes.

```typescript
abstract class AppError extends Error {
  abstract readonly code: string;
  abstract readonly statusCode: number;
  readonly timestamp = new Date();

  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
  }

  toJSON() {
    return {
      name: this.name,
      code: this.code,
      message: this.message,
      statusCode: this.statusCode,
      timestamp: this.timestamp,
    };
  }
}

class NotFoundError extends AppError {
  readonly code = 'NOT_FOUND';
  readonly statusCode = 404;

  constructor(
    public readonly entity: string,
    public readonly entityId: string,
  ) {
    super(`${entity} not found: ${entityId}`);
  }
}

class ValidationError extends AppError {
  readonly code = 'VALIDATION_ERROR';
  readonly statusCode = 400;

  constructor(
    message: string,
    public readonly field: string,
    public readonly value: unknown,
  ) {
    super(message);
  }
}

class AuthorizationError extends AppError {
  readonly code = 'UNAUTHORIZED';
  readonly statusCode = 403;

  constructor(
    public readonly action: string,
    public readonly resource: string,
  ) {
    super(`Not authorized to ${action} on ${resource}`);
  }
}

class ConflictError extends AppError {
  readonly code = 'CONFLICT';
  readonly statusCode = 409;

  constructor(message: string) {
    super(message);
  }
}
```

### Using the hierarchy

```typescript
function handleError(error: unknown): { status: number; body: object } {
  if (error instanceof AppError) {
    return { status: error.statusCode, body: error.toJSON() };
  }

  if (error instanceof Error) {
    return {
      status: 500,
      body: { code: 'INTERNAL_ERROR', message: error.message },
    };
  }

  return {
    status: 500,
    body: { code: 'UNKNOWN_ERROR', message: String(error) },
  };
}
```

---

## Safe Catch Blocks

Since TypeScript 4.4+, catch variables are `unknown` by default with `strict: true`.

```typescript
// BAD — accessing properties on unknown
try {
  await riskyOperation();
} catch (error) {
  console.log(error.message); // Error: 'error' is of type 'unknown'
}

// GOOD — narrow before accessing
try {
  await riskyOperation();
} catch (error) {
  if (error instanceof AppError) {
    console.error(`[${error.code}] ${error.message}`);
  } else if (error instanceof Error) {
    console.error(error.message);
  } else {
    console.error('Unexpected error:', String(error));
  }
}
```

### Helper for catch blocks

```typescript
function ensureError(value: unknown): Error {
  if (value instanceof Error) return value;
  if (typeof value === 'string') return new Error(value);
  if (typeof value === 'object' && value !== null && 'message' in value) {
    return new Error(String((value as { message: unknown }).message));
  }
  return new Error(`Non-error thrown: ${JSON.stringify(value)}`);
}

// Clean catch blocks
try {
  await operation();
} catch (thrown) {
  const error = ensureError(thrown);
  logger.error(error.message, { stack: error.stack });
}
```

---

## Exhaustive Error Handling with `never`

Ensure all error cases are handled at compile time.

```typescript
type ApiError =
  | { type: 'not_found'; entity: string; id: string }
  | { type: 'validation'; field: string; message: string }
  | { type: 'unauthorized'; reason: string }
  | { type: 'rate_limited'; retryAfter: number };

function handleApiError(error: ApiError): string {
  switch (error.type) {
    case 'not_found':
      return `${error.entity} ${error.id} not found`;
    case 'validation':
      return `Invalid ${error.field}: ${error.message}`;
    case 'unauthorized':
      return `Access denied: ${error.reason}`;
    case 'rate_limited':
      return `Rate limited. Retry after ${error.retryAfter}s`;
    default: {
      const _exhaustive: never = error;
      throw new Error(`Unhandled error type: ${JSON.stringify(_exhaustive)}`);
    }
  }
}
// Adding a new error type without handling it → compile error
```

---

## Boundary Validation with Zod

Validate external data at system boundaries and derive types from schemas.

```typescript
import { z } from 'zod';

// Define schema — single source of truth
const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string().min(1).max(100),
  role: z.enum(['admin', 'user', 'viewer']),
  createdAt: z.coerce.date(),
});

// Derive type from schema
type User = z.infer<typeof UserSchema>;

// Validate at boundary
function parseApiResponse(data: unknown): Result<User> {
  const result = UserSchema.safeParse(data);
  if (result.success) {
    return ok(result.data);
  }
  const messages = result.error.issues
    .map(i => `${i.path.join('.')}: ${i.message}`)
    .join('; ');
  return err(new ValidationError(messages, 'body', data));
}
```

### Composing schemas

```typescript
const PaginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

const UserQuerySchema = PaginationSchema.extend({
  role: z.enum(['admin', 'user', 'viewer']).optional(),
  search: z.string().optional(),
  sortBy: z.enum(['name', 'createdAt', 'email']).default('createdAt'),
});

type UserQuery = z.infer<typeof UserQuerySchema>;

// Validate query parameters
function parseQuery(params: Record<string, string>): Result<UserQuery> {
  const result = UserQuerySchema.safeParse(params);
  if (!result.success) return err(new Error(result.error.message));
  return ok(result.data);
}
```

---

## Error Boundaries Pattern

Centralized error handling for different layers of an application.

```typescript
// Wrap async handlers with error boundary
function withErrorBoundary<Args extends unknown[], R>(
  fn: (...args: Args) => Promise<R>,
  errorHandler: (error: unknown) => R,
): (...args: Args) => Promise<R> {
  return async (...args) => {
    try {
      return await fn(...args);
    } catch (error) {
      return errorHandler(error);
    }
  };
}

// Usage with Express-like handler
const getUser = withErrorBoundary(
  async (req: Request, res: Response) => {
    const user = await userService.findById(req.params.id);
    if (!user) throw new NotFoundError('User', req.params.id);
    res.json(user);
  },
  (error) => {
    const { status, body } = handleError(error);
    res.status(status).json(body);
  },
);
```

---

## When to Use Each Pattern

```
Error handling decision:
│
├── External input (API, user, file system)?
│   └── Validate at boundary with Zod schema
│       └── Return Result<T> from validation
│
├── Expected failure (not found, conflict, auth)?
│   └── Return Result<T, AppError>
│       └── Caller handles both paths
│
├── Unexpected failure (runtime crash, OOM)?
│   └── throw new AppError(...)
│       └── Caught by error boundary
│
├── Async operation with multiple failure modes?
│   └── Return AsyncResult<T, AppError>
│       └── Chain with flatMapResult
│
└── Must guarantee all cases handled?
    └── Discriminated union + never default
```

---

## Anti-Patterns to Avoid

| Anti-Pattern | Fix |
|---|---|
| `throw 'string'` | Always `throw new Error()` or subclass |
| `catch (e) { e.message }` | Check `instanceof Error` first |
| `.catch(() => {})` | Always log or propagate errors |
| `Promise<void>` without `await` | Use `void` operator or ESLint `no-floating-promises` |
| Returning `null` for errors | Return `Result<T>` discriminated union |
| Generic `Error` for everything | Use typed error hierarchy with codes |
| `try/catch` around every function | Use error boundaries at layer boundaries |
