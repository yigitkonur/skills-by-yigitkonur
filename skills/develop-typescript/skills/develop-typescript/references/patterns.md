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

---

## `satisfies` Patterns

### Exhaustive config validation

```typescript
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const logColors = {
  debug: '\x1b[36m',
  info: '\x1b[32m',
  warn: '\x1b[33m',
  error: '\x1b[31m',
} satisfies Record<LogLevel, string>;
// Compile error if a log level is missing
// Each value is typed as its literal string, not just 'string'
```

### Preserving literal types in maps

```typescript
const apiEndpoints = {
  getUser: { method: 'GET', path: '/users/:id' },
  createUser: { method: 'POST', path: '/users' },
  deleteUser: { method: 'DELETE', path: '/users/:id' },
} satisfies Record<string, { method: string; path: string }>;

// apiEndpoints.getUser.method is 'GET' (literal), not string
type GetUserMethod = typeof apiEndpoints.getUser.method; // 'GET'
```

---

## Pipe and Compose

Type-safe function composition.

```typescript
// Type-safe pipe — each function's input must match the previous output
function pipe<A, B>(fn1: (a: A) => B): (a: A) => B;
function pipe<A, B, C>(fn1: (a: A) => B, fn2: (b: B) => C): (a: A) => C;
function pipe<A, B, C, D>(
  fn1: (a: A) => B,
  fn2: (b: B) => C,
  fn3: (c: C) => D,
): (a: A) => D;
function pipe(...fns: Function[]) {
  return (input: unknown) => fns.reduce((acc, fn) => fn(acc), input);
}

// Usage
const processUser = pipe(
  (id: string) => ({ id, name: 'Unknown' }),
  (user) => ({ ...user, name: user.name.toUpperCase() }),
  (user) => `User: ${user.name} (${user.id})`,
);

const result = processUser('123'); // string
```

### Async pipe

```typescript
type AsyncFn<A, B> = (a: A) => Promise<B>;

async function asyncPipe<A, B, C>(
  input: A,
  fn1: AsyncFn<A, B>,
  fn2: AsyncFn<B, C>,
): Promise<C> {
  const b = await fn1(input);
  return fn2(b);
}

const result = await asyncPipe(
  'user-123',
  async (id) => fetchUser(id),
  async (user) => enrichWithPermissions(user),
);
```

---

## State Machine Pattern

Model valid state transitions at the type level.

```typescript
type OrderState =
  | { status: 'draft'; items: Item[] }
  | { status: 'submitted'; items: Item[]; submittedAt: Date }
  | { status: 'paid'; items: Item[]; submittedAt: Date; paidAt: Date; amount: number }
  | { status: 'shipped'; items: Item[]; trackingNumber: string }
  | { status: 'cancelled'; reason: string };

// Only valid transitions
function submitOrder(order: Extract<OrderState, { status: 'draft' }>):
  Extract<OrderState, { status: 'submitted' }> {
  return {
    status: 'submitted',
    items: order.items,
    submittedAt: new Date(),
  };
}

function payOrder(
  order: Extract<OrderState, { status: 'submitted' }>,
  amount: number,
): Extract<OrderState, { status: 'paid' }> {
  return {
    status: 'paid',
    items: order.items,
    submittedAt: order.submittedAt,
    paidAt: new Date(),
    amount,
  };
}

// Invalid transitions are compile errors
// payOrder(draftOrder, 100); // Error: 'draft' not assignable to 'submitted'
```

---

## Type-Safe API Client

Build type-safe HTTP clients from route definitions.

```typescript
interface ApiRoutes {
  'GET /users': { response: User[]; query: { page?: number; limit?: number } };
  'GET /users/:id': { response: User; params: { id: string } };
  'POST /users': { response: User; body: { name: string; email: string } };
  'PUT /users/:id': { response: User; params: { id: string }; body: Partial<User> };
  'DELETE /users/:id': { response: void; params: { id: string } };
}

type RouteConfig<R extends keyof ApiRoutes> = ApiRoutes[R];

type ExtractMethod<R extends string> = R extends `${infer M} ${string}` ? M : never;
type ExtractPath<R extends string> = R extends `${string} ${infer P}` ? P : never;

async function apiCall<R extends keyof ApiRoutes>(
  route: R,
  ...args: 'params' extends keyof RouteConfig<R>
    ? ['body' extends keyof RouteConfig<R>
        ? { params: RouteConfig<R>['params']; body: RouteConfig<R>['body'] }
        : { params: RouteConfig<R>['params'] }]
    : 'body' extends keyof RouteConfig<R>
      ? [{ body: RouteConfig<R>['body'] }]
      : []
): Promise<RouteConfig<R>['response']> {
  // implementation
  return {} as any;
}

// Usage — fully typed
const users = await apiCall('GET /users');                    // User[]
const user = await apiCall('GET /users/:id', { params: { id: '1' } }); // User
const newUser = await apiCall('POST /users', { body: { name: 'A', email: 'a@b.com' } });
```

---

## Type-Safe Event Emitter

```typescript
type EventMap = Record<string, unknown>;

class Emitter<Events extends EventMap> {
  private listeners = new Map<string, Set<Function>>();

  on<K extends keyof Events & string>(
    event: K,
    listener: (data: Events[K]) => void,
  ): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(listener);
    return () => { this.listeners.get(event)?.delete(listener); };
  }

  emit<K extends keyof Events & string>(event: K, data: Events[K]): void {
    this.listeners.get(event)?.forEach(fn => fn(data));
  }
}

// Usage
interface AppEvents {
  login: { userId: string; timestamp: Date };
  logout: { userId: string };
  error: { code: number; message: string };
}

const bus = new Emitter<AppEvents>();
bus.on('login', (data) => console.log(data.userId)); // Typed
bus.emit('error', { code: 500, message: 'Server error' }); // Typed
```

---

## Branded Types for Domain Modeling

```typescript
declare const __brand: unique symbol;
type Brand<T, B extends string> = T & { readonly [__brand]: B };

// Domain types
type UserId = Brand<string, 'UserId'>;
type OrderId = Brand<string, 'OrderId'>;
type Email = Brand<string, 'Email'>;
type PositiveInt = Brand<number, 'PositiveInt'>;

// Smart constructors with validation
function UserId(raw: string): UserId {
  if (!raw.startsWith('usr_')) throw new Error('Invalid UserId format');
  return raw as UserId;
}

function Email(raw: string): Email {
  if (!raw.includes('@')) throw new Error('Invalid email');
  return raw as Email;
}

function PositiveInt(raw: number): PositiveInt {
  if (!Number.isInteger(raw) || raw <= 0) throw new Error('Must be positive integer');
  return raw as PositiveInt;
}

// Can't accidentally swap branded types
function sendEmail(to: Email, userId: UserId): void {}
sendEmail(Email('a@b.com'), UserId('usr_123')); // OK
// sendEmail(UserId('usr_123'), Email('a@b.com')); // Error!
```

---

## Mapped Type Transformations

### Make all methods async

```typescript
type Asyncify<T> = {
  [K in keyof T]: T[K] extends (...args: infer A) => infer R
    ? (...args: A) => Promise<Awaited<R>>
    : T[K];
};

interface SyncService {
  getUser(id: string): User;
  deleteUser(id: string): void;
  name: string;
}

type AsyncService = Asyncify<SyncService>;
// {
//   getUser(id: string): Promise<User>;
//   deleteUser(id: string): Promise<void>;
//   name: string;
// }
```

### Get only methods from an interface

```typescript
type MethodKeys<T> = {
  [K in keyof T]: T[K] extends Function ? K : never;
}[keyof T];

type Methods<T> = Pick<T, MethodKeys<T>>;

type UserMethods = Methods<UserService>;
// Only the method signatures, no properties
```


---

> **Cross-reference:** For retry/timeout patterns with error handling, see also [error-handling.md](error-handling.md) → "Retry and timeout patterns" section.

## Pattern 18 — Typed middleware/interceptor chain

Use when building HTTP clients, API routers, or plugin systems with typed middleware.

```typescript
type Middleware<TContext> = (
  context: TContext,
  next: () => Promise<TContext>,
) => Promise<TContext>;

function compose<TContext>(...middlewares: Middleware<TContext>[]): Middleware<TContext> {
  return async (context, next) => {
    let index = -1;

    async function dispatch(i: number): Promise<TContext> {
      if (i <= index) throw new Error("next() called multiple times");
      index = i;

      const fn = i === middlewares.length ? next : middlewares[i];
      return fn(context, () => dispatch(i + 1));
    }

    return dispatch(0);
  };
}

// Usage
interface RequestContext {
  url: string;
  headers: Record<string, string>;
  startTime?: number;
}

const timing: Middleware<RequestContext> = async (ctx, next) => {
  ctx.startTime = Date.now();
  const result = await next();
  console.log(`${ctx.url} took ${Date.now() - ctx.startTime}ms`);
  return result;
};

const auth: Middleware<RequestContext> = async (ctx, next) => {
  ctx.headers["Authorization"] = `Bearer ${getToken()}`;
  return next();
};

const pipeline = compose(timing, auth);
```

---

## Pattern 19 — Type-safe factory function

Use when creating instances of related types based on a discriminant, with full type narrowing.

```typescript
interface Circle {
  kind: "circle";
  radius: number;
}

interface Rectangle {
  kind: "rectangle";
  width: number;
  height: number;
}

interface Triangle {
  kind: "triangle";
  base: number;
  height: number;
}

type Shape = Circle | Rectangle | Triangle;

type ShapeConfig = {
  circle: { radius: number };
  rectangle: { width: number; height: number };
  triangle: { base: number; height: number };
};

function createShape<K extends keyof ShapeConfig>(
  kind: K,
  config: ShapeConfig[K],
): Extract<Shape, { kind: K }> {
  return { kind, ...config } as Extract<Shape, { kind: K }>;
}

// Fully typed — autocomplete works for config based on kind
const circle = createShape("circle", { radius: 5 });
//    ^? const circle: Circle
const rect = createShape("rectangle", { width: 10, height: 20 });
//    ^? const rect: Rectangle
```

---

## Pattern 20 — Retry with exponential backoff

Use for network requests, database operations, or any operation that may transiently fail.

```typescript
interface RetryOptions {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  shouldRetry?: (error: unknown) => boolean;
}

const DEFAULT_RETRY: RetryOptions = {
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 30_000,
  shouldRetry: () => true,
};

async function withRetry<T>(
  fn: () => Promise<T>,
  options: Partial<RetryOptions> = {},
): Promise<T> {
  const opts = { ...DEFAULT_RETRY, ...options };
  let lastError: unknown;

  for (let attempt = 1; attempt <= opts.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (attempt === opts.maxAttempts) break;
      if (!opts.shouldRetry!(error)) break;

      const delay = Math.min(
        opts.baseDelay * Math.pow(2, attempt - 1),
        opts.maxDelay,
      );
      const jitter = delay * (0.5 + Math.random() * 0.5);
      await new Promise((resolve) => setTimeout(resolve, jitter));
    }
  }

  throw lastError;
}

// Usage
const data = await withRetry(
  () => fetch("https://api.example.com/data").then((r) => r.json()),
  {
    maxAttempts: 3,
    baseDelay: 1000,
    shouldRetry: (error) => {
      if (error instanceof Response) return error.status >= 500;
      return true;
    },
  },
);
```
