# Patterns

Proven TypeScript patterns for common problems.

## Result Type

Type-safe error handling without exceptions.

```typescript
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

function getUser(id: string): Result<User> {
  const user = users.find(u => u.id === id);
  if (!user) {
    return { success: false, error: new Error(`User ${id} not found`) };
  }
  return { success: true, data: user };
}

// Usage — TypeScript narrows based on success
const result = getUser('123');
if (result.success) {
  console.log(result.data.name); // User
} else {
  console.error(result.error.message); // Error
}
```

**When to use**: internal function failures where you want the caller to handle both paths explicitly. Use `throw` for truly unrecoverable errors.

---

## Discriminated Unions

Model state machines and exclusive variants.

```typescript
type LoadingState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

function render(state: LoadingState<User>): string {
  switch (state.status) {
    case 'idle':
      return 'Click to load';
    case 'loading':
      return 'Loading...';
    case 'success':
      return state.data.name;
    case 'error':
      return state.error.message;
  }
}
```

### Exhaustive switch with `never`

```typescript
function assertNever(value: never): never {
  throw new Error(`Unexpected value: ${value}`);
}

function render(state: LoadingState<User>): string {
  switch (state.status) {
    case 'idle': return 'Idle';
    case 'loading': return 'Loading';
    case 'success': return state.data.name;
    case 'error': return state.error.message;
    default: return assertNever(state);
    // Compile error if a case is missing
  }
}
```

---

## Const Assertions

Derive literal types from runtime values.

```typescript
const Status = {
  Pending: 'pending',
  Active: 'active',
  Done: 'done',
} as const;

type Status = typeof Status[keyof typeof Status];
// 'pending' | 'active' | 'done'

// Enum-like usage with both type and value
function isValidStatus(s: string): s is Status {
  return Object.values(Status).includes(s as Status);
}
```

### Config objects

```typescript
const config = {
  apiUrl: 'https://api.example.com',
  timeout: 5000,
  retries: 3,
} as const;

// config.apiUrl is 'https://api.example.com', not string
// config.timeout is 5000, not number
```

### Tuple inference

```typescript
function tuple<T extends readonly unknown[]>(...args: T): T {
  return args;
}

const pair = tuple(1, 'hello');     // readonly [1, 'hello']
const triple = tuple(1, 'hi', true); // readonly [1, 'hi', true]
```

---

## Builder Pattern

Type-safe fluent API that tracks what's been set.

```typescript
interface QueryBuilder<Selected extends string = never> {
  select<S extends string>(
    ...fields: S[]
  ): QueryBuilder<Selected | S>;

  where(condition: string): QueryBuilder<Selected>;

  execute(): Selected extends never ? never : Promise<Record<Selected, unknown>[]>;
}

function createQuery(): QueryBuilder {
  const state = { fields: [] as string[], conditions: [] as string[] };

  return {
    select(...fields) {
      state.fields.push(...fields);
      return this as any;
    },
    where(condition) {
      state.conditions.push(condition);
      return this;
    },
    execute() {
      // Implementation
      return Promise.resolve([]) as any;
    },
  };
}

// Usage
const result = createQuery()
  .select('name', 'email')
  .where('active = true')
  .execute(); // Promise<Record<'name' | 'email', unknown>[]>
```

---

## Type Guards for External Data

Validate data at system boundaries.

### Manual type guard

```typescript
interface ApiUser {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
}

function isApiUser(data: unknown): data is ApiUser {
  if (typeof data !== 'object' || data === null) return false;
  const obj = data as Record<string, unknown>;
  return (
    typeof obj.id === 'string' &&
    typeof obj.name === 'string' &&
    typeof obj.email === 'string' &&
    (obj.role === 'admin' || obj.role === 'user')
  );
}
```

### Schema validation (Zod)

```typescript
import { z } from 'zod';

const ApiUserSchema = z.object({
  id: z.string(),
  name: z.string().min(1),
  email: z.string().email(),
  role: z.enum(['admin', 'user']),
});

type ApiUser = z.infer<typeof ApiUserSchema>;

// At system boundary
function handleApiResponse(data: unknown): ApiUser {
  return ApiUserSchema.parse(data); // Throws if invalid
}

// Or safe version
function handleApiResponseSafe(data: unknown): Result<ApiUser> {
  const result = ApiUserSchema.safeParse(data);
  if (result.success) {
    return { success: true, data: result.data };
  }
  return { success: false, error: new Error(result.error.message) };
}
```

---

## Custom Error Classes

Typed error hierarchy for structured error handling.

```typescript
class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
  ) {
    super(message);
    this.name = this.constructor.name;
  }
}

class NotFoundError extends AppError {
  constructor(entity: string, id: string) {
    super(`${entity} not found: ${id}`, 'NOT_FOUND', 404);
  }
}

class ValidationError extends AppError {
  constructor(
    message: string,
    public readonly field: string,
  ) {
    super(message, 'VALIDATION_ERROR', 400);
  }
}

// Typed catch handling
try {
  await processRequest();
} catch (error) {
  if (error instanceof NotFoundError) {
    // error.statusCode is 404
    return respond(error.statusCode, error.message);
  }
  if (error instanceof ValidationError) {
    // error.field is available
    return respond(400, `Invalid ${error.field}: ${error.message}`);
  }
  if (error instanceof Error) {
    return respond(500, error.message);
  }
  return respond(500, 'Unknown error');
}
```

---

## Module Augmentation

Extend third-party types without modifying them.

```typescript
// Augment an existing module
declare module 'express' {
  interface Request {
    userId?: string;
    tenantId?: string;
  }
}

// Global augmentation
declare global {
  namespace NodeJS {
    interface ProcessEnv {
      DATABASE_URL: string;
      API_KEY: string;
      NODE_ENV: 'development' | 'production' | 'test';
    }
  }
}

// Usage — now type-safe
const dbUrl = process.env.DATABASE_URL; // string, not string | undefined
```

---

## Readonly and Immutability

### Shallow readonly

```typescript
interface Config {
  readonly apiUrl: string;
  readonly timeout: number;
}

// Or use Readonly<T>
type ImmutableConfig = Readonly<Config>;
```

### Readonly arrays and tuples

```typescript
function processItems(items: readonly string[]): string[] {
  // items.push('x'); // Error — readonly
  return [...items, 'processed']; // OK — creates new array
}

// Readonly tuple
type Point = readonly [number, number];
```

### Deep readonly

```typescript
type DeepReadonly<T> = {
  readonly [K in keyof T]: T[K] extends object ? DeepReadonly<T[K]> : T[K];
};

const config: DeepReadonly<AppConfig> = loadConfig();
// config.database.host = 'x'; // Error at any depth
```

---

## Function Overloads

Provide different call signatures with distinct return types.

```typescript
// Overload signatures — most specific first
function createElement(tag: 'input'): HTMLInputElement;
function createElement(tag: 'div'): HTMLDivElement;
function createElement(tag: string): HTMLElement;

// Implementation signature
function createElement(tag: string): HTMLElement {
  return document.createElement(tag);
}

const input = createElement('input'); // HTMLInputElement
const div = createElement('div');     // HTMLDivElement
const span = createElement('span');   // HTMLElement
```

**When to use**: when a function's return type depends on the specific input value. Prefer discriminated unions or generics when overloads would exceed 3-4 signatures.

---

## Type-Only Testing

Verify types behave correctly at compile time.

### With `@ts-expect-error`

```typescript
// Verify invalid usage is rejected
// @ts-expect-error — should not accept number
createUser(123);

// @ts-expect-error — should require email
createUser({ name: 'Alice' });
```

### With `expect-type`

```typescript
import { expectTypeOf } from 'expect-type';

expectTypeOf<User>().toHaveProperty('id');
expectTypeOf<User['id']>().toBeString();

type SuccessResult = Extract<Result<User>, { success: true }>;
expectTypeOf<SuccessResult>().toHaveProperty('data');
```
