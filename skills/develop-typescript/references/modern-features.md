# Modern TypeScript Features (5.0–5.7)

New language features, type system additions, and configuration options from recent TypeScript releases.

## `satisfies` Operator (5.0+)

Validates that an expression matches a type without widening inference.

```typescript
// WITHOUT satisfies — type is widened
const palette = {
  red: [255, 0, 0],
  green: '#00ff00',
};
// palette.red is (string | number[])[]
// palette.green is string | number[]

// WITH satisfies — validates but preserves literal types
const palette = {
  red: [255, 0, 0],
  green: '#00ff00',
} satisfies Record<string, string | number[]>;
// palette.red is number[] (preserved)
// palette.green is string (preserved)

palette.green.toUpperCase(); // OK — TypeScript knows it's string
```

### Use cases

```typescript
// Validate config objects while keeping literal types
type Route = { path: string; exact?: boolean };

const routes = {
  home: { path: '/', exact: true },
  about: { path: '/about' },
  user: { path: '/user/:id' },
} satisfies Record<string, Route>;

// routes.home.path is '/' (literal), not string
type HomePath = typeof routes.home.path; // '/'

// Validate exhaustive mappings
type Color = 'red' | 'green' | 'blue';

const colorHex = {
  red: '#ff0000',
  green: '#00ff00',
  blue: '#0000ff',
} satisfies Record<Color, string>;
// Compile error if a color is missing
```

---

## Const Type Parameters (5.0+)

Infer literal types from generic arguments without requiring `as const` at the call site.

```typescript
// WITHOUT const — T is widened
function createRoutes<T extends Record<string, string>>(routes: T): T {
  return routes;
}
const r1 = createRoutes({ home: '/', about: '/about' });
// typeof r1 = { home: string; about: string }

// WITH const — T preserves literals
function createRoutes<const T extends Record<string, string>>(routes: T): T {
  return routes;
}
const r2 = createRoutes({ home: '/', about: '/about' });
// typeof r2 = { readonly home: '/'; readonly about: '/about' }
```

### Practical example — event system

```typescript
function defineEvents<const T extends readonly string[]>(events: T) {
  type EventName = T[number];
  return {
    on(event: EventName, handler: () => void) {},
    emit(event: EventName) {},
  };
}

const emitter = defineEvents(['click', 'hover', 'submit']);
emitter.on('click', () => {}); // OK
emitter.on('scroll', () => {}); // Error: 'scroll' not in union
```

---

## Decorators (5.0+, Stage 3)

TC39 standard decorators (not the experimental legacy ones).

```typescript
function logged<This, Args extends any[], Return>(
  target: (this: This, ...args: Args) => Return,
  context: ClassMethodDecoratorContext<This, (this: This, ...args: Args) => Return>,
) {
  return function (this: This, ...args: Args): Return {
    console.log(`Calling ${String(context.name)}`);
    return target.call(this, ...args);
  };
}

class UserService {
  @logged
  getUser(id: string) {
    return { id, name: 'Alice' };
  }
}

// Decorator factories
function validate(schema: unknown) {
  return function <This, Args extends any[], Return>(
    target: (this: This, ...args: Args) => Return,
    context: ClassMethodDecoratorContext,
  ) {
    return function (this: This, ...args: Args): Return {
      // validate args against schema
      return target.call(this, ...args);
    };
  };
}
```

**Key differences from legacy decorators**:
- No `reflect-metadata` required
- Works with `--experimentalDecorators: false` (default)
- Class field decorators have different semantics
- Cannot modify class shape (no adding properties via decorator)

---

## `NoInfer<T>` Utility Type (5.4+)

Prevents TypeScript from using a parameter position for type inference.

```typescript
// WITHOUT NoInfer — T inferred from both arguments
function createFSM<T extends string>(
  initial: T,
  transitions: Record<T, T[]>,
) {}

createFSM('idle', {
  idle: ['loading'],
  loading: ['success', 'error'],
  success: ['idle'],
  error: ['idle'],
});
// T is 'idle' | 'loading' | 'success' | 'error' — works!

// But this also "works" (wrong):
createFSM('idle', {
  idle: ['loading'],
  loading: ['typo_state'], // No error — 'typo_state' widens T
});

// WITH NoInfer — T inferred only from 'initial'
function createFSM<T extends string>(
  initial: T,
  transitions: Record<T, NoInfer<T>[]>,
) {}

createFSM('idle', {
  idle: ['loading'],
  loading: ['typo_state'], // Error: 'typo_state' not assignable
});
```

### Common use cases

```typescript
// Default values that shouldn't widen the type
function useState<T>(initial: T, defaultValue: NoInfer<T>): [T, (v: T) => void] {
  // defaultValue doesn't influence T inference
  return [initial, () => {}];
}

// Callback return types
function map<T, U>(
  arr: T[],
  fn: (item: T) => NoInfer<U>,
  fallback: U,
): U[] {
  // U inferred from fallback, not fn return
  return arr.map(fn);
}
```

**Before 5.4 workaround**: `T & {}` partially blocked inference but was less reliable.

---

## `using` Declarations and Explicit Resource Management (5.2+)

Automatic cleanup of resources when they leave scope — like `try/finally` without the boilerplate.

```typescript
// Define a disposable resource
class DatabaseConnection implements Disposable {
  constructor(private url: string) {
    console.log(`Connected to ${url}`);
  }

  query(sql: string) {
    return []; // query results
  }

  [Symbol.dispose]() {
    console.log(`Disconnected from ${this.url}`);
  }
}

// Automatic cleanup — [Symbol.dispose]() called at end of scope
function getUsers() {
  using db = new DatabaseConnection('postgres://localhost/mydb');
  return db.query('SELECT * FROM users');
  // db.[Symbol.dispose]() called here automatically
}
```

### Async disposable

```typescript
class TempFile implements AsyncDisposable {
  constructor(public path: string) {}

  async write(content: string) {
    await fs.writeFile(this.path, content);
  }

  async [Symbol.asyncDispose]() {
    await fs.unlink(this.path);
    console.log(`Cleaned up ${this.path}`);
  }
}

async function processData() {
  await using tmp = new TempFile('/tmp/data.json');
  await tmp.write(JSON.stringify(data));
  // tmp.[Symbol.asyncDispose]() called here
}
```

### DisposableStack for multiple resources

```typescript
function createServerResources() {
  const stack = new DisposableStack();

  const db = stack.use(new DatabaseConnection('postgres://...'));
  const cache = stack.use(new RedisConnection('redis://...'));
  const logger = stack.use(new FileLogger('/var/log/app.log'));

  return { db, cache, logger, [Symbol.dispose]: () => stack.dispose() };
}

function handleRequest() {
  using resources = createServerResources();
  // All three cleaned up when scope ends
}
```

**Requirements**: `"lib": ["ESNext"]` or `"lib": ["ES2022", "ESNext.Disposable"]` in tsconfig.

---

## Inferred Type Predicates (5.5+)

TypeScript can now infer type predicates from function bodies without explicit annotation.

```typescript
// Before 5.5 — required explicit predicate
function isString(x: unknown): x is string {
  return typeof x === 'string';
}

// 5.5+ — TypeScript infers the predicate automatically
const strings = ['a', null, 'b', undefined].filter(x => x != null);
// strings is string[] (not (string | null | undefined)[])

// Works with array methods
const numbers = [1, 'two', 3, 'four'].filter(x => typeof x === 'number');
// numbers is number[]
```

**Limitation**: Only works when the return expression is a simple type check. Complex logic still needs explicit predicates.

---

## Import Attributes (5.3+)

Stable syntax for specifying how modules should be loaded (replaces import assertions).

```typescript
// Import JSON with type assertion
import config from './config.json' with { type: 'json' };

// Dynamic import
const data = await import('./data.json', { with: { type: 'json' } });

// CSS modules (bundler-dependent)
import styles from './styles.css' with { type: 'css' };
```

**Requires**: `"module": "ESNext"` or `"module": "NodeNext"`. The `assert` keyword is deprecated in favor of `with`.

---

## `isolatedDeclarations` (5.5+)

Allows tools other than `tsc` to generate `.d.ts` files by requiring explicit return types on exported functions.

```typescript
// tsconfig.json
// "isolatedDeclarations": true

// ERROR — return type must be explicit for exported function
export function add(a: number, b: number) {
  return a + b;
}

// OK — explicit return type
export function add(a: number, b: number): number {
  return a + b;
}

// OK — non-exported functions can still use inference
function internal(x: number) {
  return x * 2;
}
```

**Why use it**: Enables faster `.d.ts` generation by tools like `tsup`, `oxc`, and `swc` without running the full type checker. Useful for large monorepos.

---

## `verbatimModuleSyntax` (5.0+)

Replaces `importsNotUsedAsValues` and `preserveValueImports`. Simple rule: what you write is what gets emitted.

```typescript
// With verbatimModuleSyntax: true

// This import is kept in output (value import)
import { readFile } from 'fs';

// This import is stripped (type-only import)
import type { Stats } from 'fs';

// Mixed — values kept, types stripped
import { readFile, type Stats } from 'fs';

// ERROR — type used as value without 'type' keyword
import { User } from './types'; // Error if User is only a type
```

**Why use it**: Eliminates ambiguity about which imports survive compilation. Required for correct ESM/CJS interop.

---

## Variance Annotations (5.0+)

Explicitly declare whether a type parameter is covariant (`out`), contravariant (`in`), or invariant (`in out`).

```typescript
// Covariant — T only appears in output positions
interface Producer<out T> {
  get(): T;
}

// Contravariant — T only appears in input positions
interface Consumer<in T> {
  accept(value: T): void;
}

// Invariant — T appears in both positions
interface Processor<in out T> {
  process(input: T): T;
}

// Practical example — read-only collection is covariant
interface ReadonlyRepo<out T> {
  findById(id: string): T | undefined;
  findAll(): readonly T[];
}

// A repo of Dog can be used where a repo of Animal is expected
declare const dogRepo: ReadonlyRepo<Dog>;
const animalRepo: ReadonlyRepo<Animal> = dogRepo; // OK
```

**Why use them**: Makes intent explicit, catches variance errors at declaration site instead of use site, and can improve type-checking performance.

---

## Narrowing Improvements Across Versions

### Narrowing in closures preserved across assignments (5.4+)

```typescript
function process(value: string | number) {
  if (typeof value === 'string') {
    // Before 5.4: value narrowed here but lost in callback
    // After 5.4: narrowing preserved if value isn't reassigned
    const callback = () => {
      console.log(value.toUpperCase()); // OK in 5.4+
    };
    callback();
  }
}
```

### Control flow narrowing for computed access (5.5+)

```typescript
const obj: Record<string, string | number> = getConfig();
const key = 'host';

if (typeof obj[key] === 'string') {
  obj[key].toUpperCase(); // Narrowed in 5.5+
}
```

---

## Regular Expression Syntax Checking (5.5+)

TypeScript now validates regex syntax at compile time.

```typescript
// Error in 5.5+ — invalid regex
const re1 = /[/; // Unterminated character class

// Error — invalid quantifier
const re2 = /a{}/; // Nothing to quantify

// OK — valid regex
const re3 = /^[a-z]+$/i;
```

---

## Quick Reference Table

| Feature | Version | Key Benefit |
|---------|---------|-------------|
| `satisfies` | 5.0 | Validate types without widening |
| `const` type params | 5.0 | Infer literals in generics |
| TC39 Decorators | 5.0 | Standard class decorators |
| Variance annotations | 5.0 | Explicit `in`/`out` on type params |
| `verbatimModuleSyntax` | 5.0 | Predictable import erasure |
| `using` declarations | 5.2 | Auto resource cleanup |
| Import attributes | 5.3 | `with { type: 'json' }` syntax |
| `NoInfer<T>` | 5.4 | Block inference from specific params |
| Closure narrowing | 5.4 | Narrowing preserved in callbacks |
| Inferred predicates | 5.5 | Auto type guards for `.filter()` |
| Regex checking | 5.5 | Compile-time regex validation |
| `isolatedDeclarations` | 5.5 | Fast `.d.ts` without full type check |
