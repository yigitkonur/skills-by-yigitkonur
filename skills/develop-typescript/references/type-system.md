# Type System

Advanced TypeScript type system patterns for real-world use.

## Generics

### Constrained generics

```typescript
interface Entity {
  id: string;
  createdAt: Date;
}

function findById<T extends Entity>(items: T[], id: string): T | undefined {
  return items.find(item => item.id === id);
}

// Multiple constraints via intersection
function merge<T extends object, U extends object>(a: T, b: U): T & U {
  return { ...a, ...b };
}
```

### When NOT to use generics

```typescript
// BAD — unnecessary generic, T is never meaningfully constrained
function add<T extends number, U extends number>(a: T, b: U): number {
  return a + b;
}

// GOOD — just use concrete types
function add(a: number, b: number): number {
  return a + b;
}
```

Rule: if the generic parameter doesn't appear in the return type or isn't used to relate multiple parameters, remove it.

---

## Conditional Types

### Distributive behavior

```typescript
// Distributive — T is distributed over the union
type ExtractStrings<T> = T extends string ? T : never;
type Result = ExtractStrings<string | number | boolean>; // string

// Non-distributive — wrap in tuple to prevent distribution
type IsString<T> = [T] extends [string] ? true : false;
type A = IsString<string | number>; // false (entire union checked)
```

### Extracting types with `infer`

```typescript
type ExtractPromise<T> = T extends Promise<infer U> ? U : T;
type A = ExtractPromise<Promise<string>>; // string
type B = ExtractPromise<number>;          // number

// Extract function return type
type AsyncReturn<T extends (...args: any) => any> =
  T extends (...args: any) => Promise<infer R> ? R : never;
```

---

## Mapped Types

### Basic transformations

```typescript
// Make all properties optional
type Optional<T> = { [K in keyof T]?: T[K] };

// Make all properties readonly
type Immutable<T> = { readonly [K in keyof T]: T[K] };

// Make specific keys required
type RequireKeys<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>;

interface User {
  id?: string;
  name?: string;
  email?: string;
}

type UserWithId = RequireKeys<User, 'id'>;
// { id: string; name?: string; email?: string }
```

### Key remapping

```typescript
type Prefixed<T, P extends string> = {
  [K in keyof T as `${P}${string & K}`]: T[K];
};

type Events = { click: MouseEvent; focus: FocusEvent };
type Handlers = Prefixed<Events, 'on'>;
// { onclick: MouseEvent; onfocus: FocusEvent }
```

### Filtering keys by value type

```typescript
type KeysOfType<T, V> = {
  [K in keyof T]: T[K] extends V ? K : never;
}[keyof T];

interface Example {
  name: string;
  age: number;
  active: boolean;
  count: number;
}

type NumberKeys = KeysOfType<Example, number>; // 'age' | 'count'
```

---

## Template Literal Types

### String manipulation at compile time

```typescript
type EventName = 'click' | 'focus' | 'blur';
type EventHandler = `on${Capitalize<EventName>}`;
// 'onClick' | 'onFocus' | 'onBlur'

type HTTPMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';
type Endpoint = `/api/${'users' | 'posts'}`;
type Route = `${HTTPMethod} ${Endpoint}`;
// 'GET /api/users' | 'POST /api/users' | ...
```

### CamelCase conversion

```typescript
type CamelCase<S extends string> =
  S extends `${infer First}_${infer Rest}`
    ? `${First}${Capitalize<CamelCase<Rest>>}`
    : S;

type Result = CamelCase<'user_first_name'>; // 'userFirstName'
```

### Deep key paths

```typescript
type DeepKey<T> = T extends object
  ? {
      [K in keyof T & string]: K | `${K}.${DeepKey<T[K]>}`;
    }[keyof T & string]
  : never;

interface Config {
  database: {
    host: string;
    port: number;
    credentials: { username: string; password: string };
  };
}

type ConfigKeys = DeepKey<Config>;
// 'database' | 'database.host' | 'database.port' | 'database.credentials' | ...
```

---

## Branded Types

Nominal typing for TypeScript's structural type system.

```typescript
declare const __brand: unique symbol;
type Brand<T, B extends string> = T & { readonly [__brand]: B };

type UserId = Brand<string, 'UserId'>;
type OrderId = Brand<string, 'OrderId'>;
type PositiveNumber = Brand<number, 'PositiveNumber'>;

// Constructors with validation
function createUserId(id: string): UserId {
  if (!id.startsWith('usr_')) throw new Error('Invalid user ID format');
  return id as UserId;
}

function createPositiveNumber(n: number): PositiveNumber {
  if (n <= 0) throw new Error('Must be positive');
  return n as PositiveNumber;
}

// Type-safe — cannot swap parameters
function processOrder(orderId: OrderId, userId: UserId) {}
```

**When to use branded types**:
- IDs that should not be mixed (UserId vs OrderId)
- Validated values (EmailAddress, PositiveNumber, NonEmptyString)
- Domain types that share a primitive base (currency amounts, coordinates)

---

## Recursive Types

### Safe recursion with depth limiting

```typescript
// BAD — infinite recursion
type BadDeep<T> = T extends object ? BadDeep<T[keyof T]> : T;

// GOOD — depth-limited with tuple counter
type DeepPartial<T, D extends number[] = [0, 0, 0, 0, 0]> =
  D['length'] extends 0
    ? T
    : T extends object
      ? { [K in keyof T]?: DeepPartial<T[K], Tail<D>> }
      : T;

type Tail<T extends unknown[]> = T extends [unknown, ...infer R] ? R : [];
```

### Circular references — use interfaces

```typescript
// BAD — type alias may not reference itself directly in older TS
type Node = { value: string; children: Node[] };

// GOOD — interfaces handle self-reference
interface TreeNode {
  value: string;
  children: TreeNode[];
  parent?: TreeNode;
}

// JSON type — mutual recursion
type Json = string | number | boolean | null | JsonObject | JsonArray;
interface JsonObject { [key: string]: Json }
interface JsonArray extends Array<Json> {}
```

---

## Utility Types

### Built-in utilities — prefer these over custom implementations

```typescript
Partial<T>           // All properties optional
Required<T>          // All properties required
Readonly<T>          // All properties readonly
Pick<T, K>           // Select specific properties
Omit<T, K>           // Exclude specific properties
Record<K, V>         // Object with key type K and value type V
Extract<T, U>        // Members of T assignable to U
Exclude<T, U>        // Members of T not assignable to U
NonNullable<T>       // Remove null and undefined
ReturnType<T>        // Return type of a function
Parameters<T>        // Parameter types of a function as tuple
Awaited<T>           // Unwrap Promise type
```

### Custom utilities for common needs

```typescript
// Deep readonly
type DeepReadonly<T> = {
  readonly [K in keyof T]: T[K] extends object ? DeepReadonly<T[K]> : T[K];
};

// Deep partial
type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K];
};

// Make readonly properties mutable
type Mutable<T> = { -readonly [K in keyof T]: T[K] };

// Extract keys whose values match a type
type KeysOfType<T, V> = {
  [K in keyof T]: T[K] extends V ? K : never;
}[keyof T];

// Safe property access
type SafeGet<T, K extends PropertyKey> = K extends keyof T ? T[K] : never;
```

---

## Type Guards

### Custom type guards

```typescript
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function isDefined<T>(value: T | null | undefined): value is T {
  return value !== null && value !== undefined;
}

// Use with array methods
const values: (string | null)[] = ['a', null, 'b'];
const strings = values.filter(isDefined); // string[]
```

### Assertion functions

```typescript
function assertIsDefined<T>(value: T | null | undefined): asserts value is T {
  if (value === null || value === undefined) {
    throw new Error('Expected defined value');
  }
}

const input: string | null = getValue();
assertIsDefined(input);
input.toUpperCase(); // TypeScript knows input is string
```

### Generic type guard for objects

```typescript
function isArrayOf<T>(
  value: unknown,
  guard: (item: unknown) => item is T,
): value is T[] {
  return Array.isArray(value) && value.every(guard);
}

const data: unknown = [1, 2, 3];
if (isArrayOf(data, (x): x is number => typeof x === 'number')) {
  data.forEach(n => n.toFixed(2)); // number[]
}
```

---

## Type Performance

### Prefer interfaces over intersections

```typescript
// BAD — intersection creates a new type on every use
type Heavy = TypeA & TypeB & TypeC & TypeD;

// GOOD — interface extends is cheaper
interface Light extends TypeA, TypeB, TypeC, TypeD {}
```

### Break large unions into discriminated groups

```typescript
// BAD — 50+ member union, slow to check
type Status = 'a' | 'b' | 'c' | /* ... */;

// GOOD — grouped discriminated union
type Status =
  | { phase: 'initial'; value: 'pending' | 'loading' }
  | { phase: 'active'; value: 'running' | 'paused' }
  | { phase: 'complete'; value: 'success' | 'error' | 'cancelled' };
```

### Diagnostics

```bash
# Measure type-checking time
tsc --extendedDiagnostics --incremental false

# Generate type trace for analysis
tsc --generateTrace trace --incremental false
npx @typescript/analyze-trace trace

# Check type coverage
npx type-coverage --detail --strict
```

---

## Variance Annotations (5.0+)

Explicitly declare whether a type parameter is covariant, contravariant, or invariant.

```typescript
// Covariant — T only in output positions (return types, readonly properties)
interface Producer<out T> {
  get(): T;
  readonly value: T;
}

// Contravariant — T only in input positions (parameters)
interface Consumer<in T> {
  accept(value: T): void;
}

// Invariant — T in both positions
interface Processor<in out T> {
  process(input: T): T;
}
```

### Why variance matters

```typescript
interface Animal { name: string }
interface Dog extends Animal { breed: string }

// Covariant: Producer<Dog> assignable to Producer<Animal> ✓
declare const dogProducer: Producer<Dog>;
const animalProducer: Producer<Animal> = dogProducer; // OK

// Contravariant: Consumer<Animal> assignable to Consumer<Dog> ✓
declare const animalConsumer: Consumer<Animal>;
const dogConsumer: Consumer<Dog> = animalConsumer; // OK

// Invariant: neither direction works
declare const dogProcessor: Processor<Dog>;
// const animalProcessor: Processor<Animal> = dogProcessor; // Error
```

**Benefits**: Catches errors at declaration site, documents intent, and can improve type-checking performance.

---

## `satisfies` Operator (5.0+)

Validates an expression against a type without widening its inferred type.

```typescript
type ColorMap = Record<string, string | number[]>;

// WITHOUT satisfies — widened to string | number[]
const colors: ColorMap = {
  red: [255, 0, 0],
  green: '#00ff00',
};
colors.green.toUpperCase(); // Error: string | number[] has no toUpperCase

// WITH satisfies — preserves narrow literal types
const colors = {
  red: [255, 0, 0],
  green: '#00ff00',
} satisfies ColorMap;
colors.green.toUpperCase(); // OK — TypeScript knows it's string
colors.red.map(x => x);    // OK — TypeScript knows it's number[]
```

### Exhaustive record validation

```typescript
type Theme = 'light' | 'dark' | 'system';

const themeLabels = {
  light: 'Light Mode',
  dark: 'Dark Mode',
  system: 'System Default',
} satisfies Record<Theme, string>;
// Compile error if a theme is missing

type ThemeKey = keyof typeof themeLabels; // 'light' | 'dark' | 'system'
```

---

## Const Type Parameters (5.0+)

Infer literal types in generic functions without `as const` at the call site.

```typescript
// WITHOUT const — infers wide types
function createConfig<T extends Record<string, unknown>>(config: T): T {
  return config;
}
const c1 = createConfig({ mode: 'production', port: 3000 });
// typeof c1 = { mode: string; port: number }

// WITH const — infers literal types
function createConfig<const T extends Record<string, unknown>>(config: T): T {
  return config;
}
const c2 = createConfig({ mode: 'production', port: 3000 });
// typeof c2 = { readonly mode: 'production'; readonly port: 3000 }
```

---

## `NoInfer<T>` Utility (5.4+)

Prevents a type parameter from being inferred from a specific argument.

```typescript
function createSignal<T>(value: T, fallback: NoInfer<T>): T {
  return value ?? fallback;
}

// T inferred from 'value' only, not 'fallback'
createSignal('hello', 42);
// Error: Argument of type 'number' is not assignable to parameter of type 'string'
```

**Use case**: When multiple parameters share a generic type but you want inference to come from only one of them.

---

## `using` and Disposable Types (5.2+)

Automatic resource cleanup via `Symbol.dispose`.

```typescript
class TempFile implements Disposable {
  constructor(public path: string) {}

  [Symbol.dispose]() {
    fs.unlinkSync(this.path);
  }
}

function processData() {
  using file = new TempFile('/tmp/data.json');
  // file automatically cleaned up at scope end
}

// Async version
class DbConnection implements AsyncDisposable {
  async [Symbol.asyncDispose]() {
    await this.close();
  }
}

async function query() {
  await using db = new DbConnection();
  return db.execute('SELECT 1');
}
```

---

## Advanced Template Literal Patterns

### Type-safe event emitter

```typescript
type EventMap = {
  userCreated: { userId: string; name: string };
  orderPlaced: { orderId: string; total: number };
  error: { code: string; message: string };
};

type EventHandler<T> = (data: T) => void;

class TypedEmitter<Events extends Record<string, unknown>> {
  private handlers = new Map<string, Set<Function>>();

  on<K extends keyof Events & string>(
    event: K,
    handler: EventHandler<Events[K]>,
  ): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);
    return () => this.handlers.get(event)?.delete(handler);
  }

  emit<K extends keyof Events & string>(event: K, data: Events[K]): void {
    this.handlers.get(event)?.forEach(fn => fn(data));
  }
}

const emitter = new TypedEmitter<EventMap>();
emitter.on('userCreated', (data) => {
  console.log(data.userId); // Typed: { userId: string; name: string }
});
```

### Path-based type access

```typescript
type DeepValue<T, P extends string> =
  P extends `${infer Head}.${infer Tail}`
    ? Head extends keyof T
      ? DeepValue<T[Head], Tail>
      : never
    : P extends keyof T
      ? T[P]
      : never;

interface AppConfig {
  server: { host: string; port: number };
  database: { url: string; pool: { min: number; max: number } };
}

type DbUrl = DeepValue<AppConfig, 'database.url'>; // string
type PoolMax = DeepValue<AppConfig, 'database.pool.max'>; // number
```

---

## Discriminated Union Patterns

### State machines with exhaustive checking

```typescript
type AuthState =
  | { status: 'anonymous' }
  | { status: 'authenticating'; provider: string }
  | { status: 'authenticated'; user: User; token: string }
  | { status: 'error'; error: Error; retryCount: number };

function getAuthMessage(state: AuthState): string {
  switch (state.status) {
    case 'anonymous':
      return 'Please log in';
    case 'authenticating':
      return `Signing in with ${state.provider}...`;
    case 'authenticated':
      return `Welcome, ${state.user.name}`;
    case 'error':
      return `Error: ${state.error.message} (attempt ${state.retryCount})`;
    default: {
      const _exhaustive: never = state;
      throw new Error(`Unhandled state: ${JSON.stringify(_exhaustive)}`);
    }
  }
}
```

### Tagged API responses

```typescript
type ApiResponse<T> =
  | { status: 'success'; data: T; meta: { total: number; page: number } }
  | { status: 'error'; code: number; message: string }
  | { status: 'loading' };

function renderResponse<T>(response: ApiResponse<T>): string {
  switch (response.status) {
    case 'success':
      return `Got ${response.meta.total} results`;
    case 'error':
      return `Error ${response.code}: ${response.message}`;
    case 'loading':
      return 'Loading...';
  }
}
```


---

## Type guard quality rubric

Not all type guards are equal. Use this rubric to evaluate whether a type guard is production-quality:

| Criterion | Good | Bad |
|---|---|---|
| **Checks all discriminating properties** | Checks `type`, `code`, and `message` | Only checks `type` |
| **Handles `null`/`undefined`** | Starts with `!= null` check | Assumes non-null |
| **Uses `in` operator for property existence** | `"name" in value` | `value.name !== undefined` (crashes if no `.name`) |
| **Returns `value is T`** (not `boolean`) | `function isUser(v: unknown): v is User` | `function isUser(v: unknown): boolean` |
| **Narrows to specific type** | `v is User` | `v is object` (too broad) |
| **Works across realms** | Structural check | `instanceof` (fails across realms) |

### Template for a production-quality type guard

```typescript
function isUser(value: unknown): value is User {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof (value as Record<string, unknown>).id === "string" &&
    "name" in value &&
    typeof (value as Record<string, unknown>).name === "string"
  );
}
```

---

## Cross-realm `instanceof` safety

See also: anti-patterns.md → "Cross-realm instanceof" section.

When writing type guards for library code or code that handles messages from workers/iframes, never rely solely on `instanceof`. Use structural checks:

```typescript
// BAD — fails across realms
function isDate(value: unknown): value is Date {
  return value instanceof Date;
}

// GOOD — works across realms
function isDate(value: unknown): value is Date {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as Record<string, unknown>).getTime === "function" &&
    !isNaN((value as Date).getTime())
  );
}
```

---

## Narrowing strategy decision tree

Use this decision tree to choose the right narrowing approach:

```
Is the value `unknown`?
├── Yes → Use type guard function (`value is T`)
│   ├── Is it from an external source (API, message, file)?
│   │   └── Yes → Use Zod/Valibot schema validation
│   └── Is it from internal code?
│       └── Yes → Use structural type guard (typeof/in checks)
└── No → Is it a union type?
    ├── Yes → Is it a discriminated union (common property)?
    │   ├── Yes → Use switch/if on the discriminant property
    │   └── No → Use `in` operator or type guard function
    └── No → Is it `T | null | undefined`?
        ├── Yes → Use `!= null` (covers both null and undefined)
        └── No → Value is already narrowed; no action needed
```

### Common narrowing mistakes

| Mistake | Why it fails | Fix |
|---|---|---|
| `typeof x === "object"` without null check | `typeof null === "object"` in JS | Add `x !== null` |
| `if (x)` to narrow string | Empty string `""` is falsy | Use `typeof x === "string"` |
| `in` operator on primitive | Runtime error | Guard with `typeof x === "object"` first |
| Narrowing in callback loses narrowing | Control flow analysis resets in closures | Assign to local variable before callback |

---

## Variance — practical example

Variance determines whether a generic type `G<A>` is assignable to `G<B>` when `A` is assignable to `B`.

```typescript
// Covariant (out) — read-only positions
interface Reader<out T> {
  read(): T;
}
// Reader<Dog> is assignable to Reader<Animal> ✓ (Dog extends Animal)

// Contravariant (in) — write-only positions
interface Writer<in T> {
  write(value: T): void;
}
// Writer<Animal> is assignable to Writer<Dog> ✓ (reversed!)

// Invariant (in out) — both read and write
interface Container<in out T> {
  get(): T;
  set(value: T): void;
}
// Container<Dog> is NOT assignable to Container<Animal>
// Container<Animal> is NOT assignable to Container<Dog>
```

### When to add explicit variance annotations

- **Performance:** TS 5.0+ uses variance annotations to skip expensive structural comparisons
- **Correctness:** Makes the intended variance explicit and catches violations
- **Add `out`** when the type parameter only appears in return positions (read)
- **Add `in`** when the type parameter only appears in parameter positions (write)
- **Add `in out`** when it appears in both (or when you want to explicitly mark invariance)

---

## Finding `satisfies` opportunities

`satisfies` (TS 4.9+) validates that an expression matches a type without widening it. This preserves literal types and enables better autocomplete.

### Where to look

```bash
# Config objects with type annotations — candidates for satisfies
grep -rn "^const .* : Record<" --include="*.ts" | head -10
grep -rn "^const .* : {" --include="*.ts" | head -10

# Enum-like objects — strong candidates
grep -rn "^const .* = {" --include="*.ts" | grep -l "as const" | head -10
```

### Before/after

```typescript
// BEFORE — annotation widens literal types
const routes: Record<string, string> = {
  home: "/",
  about: "/about",
};
// typeof routes.home is `string`

// AFTER — satisfies preserves literals
const routes = {
  home: "/",
  about: "/about",
} satisfies Record<string, string>;
// typeof routes.home is `"/"`

// BEST — as const satisfies for full immutability + validation
const routes = {
  home: "/",
  about: "/about",
} as const satisfies Record<string, string>;
// typeof routes.home is `"/"`; object is deeply readonly
```
