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
