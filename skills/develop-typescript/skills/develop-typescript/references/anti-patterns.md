# Anti-Patterns

Every anti-pattern follows the same format: what's wrong, why it's wrong, and what to do instead.

## Type System

### Using `any` as an escape hatch

```typescript
// BAD — defeats TypeScript entirely
function processData(data: any): any {
  return data.value * 2;
}

// GOOD — use unknown and narrow
function processData(data: unknown): number {
  if (isValidData(data)) {
    return data.value * 2;
  }
  throw new Error('Invalid data');
}

function isValidData(data: unknown): data is { value: number } {
  return (
    typeof data === 'object' &&
    data !== null &&
    'value' in data &&
    typeof (data as { value: unknown }).value === 'number'
  );
}
```

**Why**: `any` disables all type checking. Every `any` is a potential runtime crash that TypeScript cannot catch.

---

### Type assertions (`as`) without runtime validation

```typescript
// BAD — no runtime check, crashes silently
const user = data as User;
console.log(user.email); // Runtime error if data isn't User

// GOOD — type guard with runtime check
function isUser(data: unknown): data is User {
  return (
    typeof data === 'object' &&
    data !== null &&
    'id' in data &&
    'email' in data &&
    typeof (data as User).id === 'string' &&
    typeof (data as User).email === 'string'
  );
}

if (isUser(data)) {
  console.log(data.email); // Safe
}
```

**Why**: `as` tells TypeScript to trust you. If you're wrong, you get runtime errors with zero warning.

---

### Numeric enums

```typescript
// BAD — reverse-mapped, unexpected in Object.values/keys
enum Status {
  Pending,   // 0
  Active,    // 1
  Done,      // 2
}
Object.values(Status); // ['Pending', 'Active', 'Done', 0, 1, 2]
const status: Status = 999; // No error — accepts any number

// GOOD — const object with as const
const Status = {
  Pending: 'pending',
  Active: 'active',
  Done: 'done',
} as const;

type Status = typeof Status[keyof typeof Status];
// 'pending' | 'active' | 'done'
```

**Why**: Numeric enums generate reverse mappings, accept arbitrary numbers, and break with tree-shaking and module systems.

---

### Discriminated unions without a discriminator

```typescript
// BAD — no discriminator, narrowing unreliable
type Result =
  | { data: string }
  | { error: string };

// GOOD — explicit discriminator field
type Result =
  | { type: 'success'; data: string }
  | { type: 'error'; error: string };

function handle(result: Result) {
  switch (result.type) {
    case 'success':
      return result.data;
    case 'error':
      throw new Error(result.error);
  }
}
```

**Why**: Without a discriminator, TypeScript cannot reliably narrow the type in all control flow scenarios.

---

### Over-specifying types that TypeScript can infer

```typescript
// BAD — noisy, redundant
const name: string = 'Alice';
const age: number = 30;
const isActive: boolean = true;
const users: Array<User> = [];

// GOOD — let inference work
const name = 'Alice';
const age = 30;
const isActive = true;
const users: User[] = [];
```

**Why**: TypeScript infers these correctly. Extra annotations add noise without safety. **Exception**: always annotate function parameters and return types.

---

### Using `@ts-ignore` instead of `@ts-expect-error`

```typescript
// BAD — silently hides errors, even if the error is later fixed
// @ts-ignore
const x: number = 'hello';

// GOOD — fails if the error is fixed (catches stale suppressions)
// @ts-expect-error — intentional type mismatch for legacy compat
const x: number = 'hello';
```

**Why**: `@ts-ignore` suppresses all errors on the next line forever. `@ts-expect-error` fails when the error disappears, so stale suppressions don't accumulate.

---

## Functions

### Optional parameters before required ones

```typescript
// BAD
function createUser(name?: string, id: string) {}

// GOOD
function createUser(id: string, name?: string) {}
```

**Why**: JavaScript requires optional parameters after required ones. The bad version is a compile error with strict settings.

---

### Too many parameters

```typescript
// BAD — hard to read, easy to mix up argument order
function createUser(id: string, name: string, email: string, age: number, role: string) {}

// GOOD — named parameters via object
interface CreateUserParams {
  id: string;
  name: string;
  email: string;
  age: number;
  role: string;
}

function createUser(params: CreateUserParams) {}
```

**Why**: More than 3 parameters are hard to remember and prone to ordering mistakes. Object parameters are self-documenting.

---

### Boolean flags that change behavior

```typescript
// BAD — caller must read implementation to understand
function getUsers(includeInactive: boolean) {
  if (includeInactive) return allUsers;
  return activeUsers;
}

// GOOD — separate functions with clear names
function getAllUsers() { return allUsers; }
function getActiveUsers() { return activeUsers; }

// OR — discriminated filter for complex cases
type UserFilter =
  | { type: 'all' }
  | { type: 'active' }
  | { type: 'byRole'; role: string };

function getUsers(filter: UserFilter) {
  switch (filter.type) {
    case 'all': return allUsers;
    case 'active': return activeUsers;
    case 'byRole': return allUsers.filter(u => u.role === filter.role);
  }
}
```

**Why**: Boolean flags hide behavior behind a truthy/falsy value. Named functions or discriminated unions make intent explicit.

---

## Async

### Sequential awaits when parallel is possible

```typescript
// BAD — waits for each to finish before starting the next
async function getData() {
  const users = await fetchUsers();
  const posts = await fetchPosts();
  const comments = await fetchComments();
  return { users, posts, comments };
}

// GOOD — runs all three concurrently
async function getData() {
  const [users, posts, comments] = await Promise.all([
    fetchUsers(),
    fetchPosts(),
    fetchComments(),
  ]);
  return { users, posts, comments };
}
```

**Why**: Independent operations should run concurrently. Sequential awaits waste time.

---

### Mixing callbacks and promises

```typescript
// BAD
function fetchData(callback: (data: Data) => void): Promise<void> {
  return fetch('/api/data')
    .then(response => response.json())
    .then(data => callback(data));
}

// GOOD — consistent async style
async function fetchData(): Promise<Data> {
  const response = await fetch('/api/data');
  return response.json();
}
```

**Why**: Mixing async patterns makes control flow unpredictable and error handling inconsistent.

---

## Objects and Arrays

### Mutating arguments

```typescript
// BAD — modifies the original array
function addUser(users: User[], newUser: User) {
  users.push(newUser);
  return users;
}

// GOOD — returns a new array
function addUser(users: readonly User[], newUser: User): User[] {
  return [...users, newUser];
}
```

**Why**: Mutations cause unexpected side effects. The caller doesn't expect their data to change. Use `readonly` to enforce at the type level.

---

### Using `delete` to remove properties

```typescript
// BAD — slow, mutable, confuses type inference
function removePassword(user: User): PublicUser {
  const result = { ...user };
  delete result.password;
  return result;
}

// GOOD — destructure and rest
function removePassword(user: User): PublicUser {
  const { password, ...publicUser } = user;
  return publicUser;
}
```

**Why**: `delete` is slow and mutable. Destructuring is immutable and TypeScript understands the resulting type.

---

### forEach when map/filter/reduce is clearer

```typescript
// BAD — imperative mutation
const names: string[] = [];
users.forEach(user => { names.push(user.name); });

// GOOD — declarative
const names = users.map(user => user.name);
```

```typescript
// BAD
const active: User[] = [];
users.forEach(user => { if (user.isActive) active.push(user); });

// GOOD
const active = users.filter(user => user.isActive);
```

**Why**: `map`, `filter`, and `reduce` express intent directly. `forEach` with mutation is harder to reason about.

---

## Error Handling

### Throwing non-Error objects

```typescript
// BAD — no stack trace, breaks error monitoring
if (!user) throw 'User not found';
if (!user) throw { message: 'Not found', code: 404 };

// GOOD — always throw Error or subclass
if (!user) throw new Error('User not found');

// BETTER — custom error class
class NotFoundError extends Error {
  constructor(
    public readonly entity: string,
    public readonly entityId: string,
  ) {
    super(`${entity} not found: ${entityId}`);
    this.name = 'NotFoundError';
  }
}

if (!user) throw new NotFoundError('User', userId);
```

**Why**: Non-Error objects have no stack trace, no `.name`, and break `instanceof` checks in catch blocks.

---

### Untyped catch blocks

```typescript
// BAD — error is unknown, accessing .message fails
try {
  await fetchData();
} catch (error) {
  console.log(error.message); // Error: 'error' is of type 'unknown'
}

// GOOD — check type before using
try {
  await fetchData();
} catch (error) {
  if (error instanceof Error) {
    console.error(error.message);
  } else {
    console.error('Unknown error:', String(error));
  }
}
```

**Why**: Since TypeScript 4.4, catch clause variables are `unknown` by default. Always narrow before accessing properties.

---

## Imports and Modules

### Not using `import type`

```typescript
// BAD — may be included in JS bundle
import { User } from './types';

// GOOD — stripped at compile time
import type { User } from './types';
```

**Why**: Without `import type`, bundlers may include the import in the output even though it's only used as a type.

---

### Barrel exports in performance-sensitive code

```typescript
// BAD — importing one thing loads everything
// index.ts
export * from './module1';
export * from './module2';
// ... 100+ modules

import { oneFunction } from './modules'; // Loads all

// GOOD — import directly
import { oneFunction } from './modules/module1';
```

**Why**: Barrel exports prevent tree-shaking and force unnecessary code to load.

---

### Circular dependencies

```typescript
// BAD — file1.ts imports file2.ts, file2.ts imports file1.ts
// This causes initialization order issues and subtle bugs

// GOOD — extract shared code to a third module
// shared.ts — contains what both files need
// file1.ts — imports from shared.ts
// file2.ts — imports from shared.ts
```

**Why**: Circular dependencies cause unpredictable initialization order and can produce `undefined` at runtime.

---

## Classes

### Using classes for plain data

```typescript
// BAD — unnecessary ceremony for a data structure
class User {
  constructor(
    public id: string,
    public name: string,
    public email: string,
  ) {}
}

// GOOD — interface + factory function
interface User {
  id: string;
  name: string;
  email: string;
}

function createUser(id: string, name: string, email: string): User {
  return { id, name, email };
}
```

**Why**: Interfaces are erased at compile time. Classes generate runtime code, break structural typing expectations, and add complexity for simple data shapes.

---

## Sharp Edges

### `noUncheckedIndexedAccess` changes array access

```typescript
// With noUncheckedIndexedAccess: true
const arr = [1, 2, 3];

// BAD — type error: arr[0] is number | undefined
const first: number = arr[0];

// GOOD — check for undefined
const first = arr[0];
if (first !== undefined) {
  console.log(first); // number
}
```

**Why**: Arrays can have holes and indices can be out of bounds. This flag makes TypeScript honest about it.

---

### Optional property vs `undefined` property

```typescript
// With exactOptionalPropertyTypes: true
interface WithOptional { x?: string }
interface WithUndefined { x: string | undefined }

const a: WithOptional = {};                // OK — x can be omitted
const b: WithOptional = { x: undefined };  // ERROR — can't assign undefined
const c: WithUndefined = {};               // ERROR — x is required
const d: WithUndefined = { x: undefined }; // OK — x present but undefined

// If you want both behaviors:
interface WithBoth { x?: string | undefined }
```

**Why**: `x?: string` means "may be absent." `x: string | undefined` means "must be present, may be undefined." These are semantically different.

---

### Function overload order matters

```typescript
// BAD — general overload first, specific one never matches
function parse(input: unknown): unknown;
function parse(input: string): object; // Never used!

// GOOD — specific overloads first
function parse(input: string): object;
function parse(input: unknown): unknown;
function parse(input: unknown): unknown {
  if (typeof input === 'string') return JSON.parse(input);
  return input;
}
```

**Why**: TypeScript checks overloads top-to-bottom and uses the first match. Put specific signatures before general ones.

---

### Structural typing allows accidental compatibility

```typescript
// These are compatible — same shape, different intent
interface UserId { id: string }
interface PostId { id: string }

function getUser(id: UserId) {}
getUser({ id: 'post-123' }); // No error!

// Fix: use branded types
type UserId = string & { readonly __brand: 'UserId' };
type PostId = string & { readonly __brand: 'PostId' };

function createUserId(id: string): UserId { return id as UserId; }
function getUser(id: UserId) {}

getUser(createUserId('user-123')); // OK
getUser('post-123' as PostId);     // Error!
```

**Why**: TypeScript is structurally typed. Two types with the same shape are interchangeable. Use branded types when you need nominal distinction.

---

## Configuration

### Using `moduleResolution: "node"` with modern bundlers

```typescript
// BAD — tsconfig.json
{
  "compilerOptions": {
    "moduleResolution": "node"  // Legacy Node.js CJS resolution
  }
}

// GOOD — for Vite, webpack, esbuild, Bun
{
  "compilerOptions": {
    "moduleResolution": "bundler",
    "module": "ESNext"
  }
}

// GOOD — for Node.js ESM
{
  "compilerOptions": {
    "moduleResolution": "node16",
    "module": "node16"
  }
}
```

**Why**: `"node"` is the legacy CJS-only resolution. It doesn't understand `package.json` `"exports"`, `import` conditions, or ESM features. Use `"bundler"` for bundled apps or `"node16"` for Node.js.

---

### Targeting ES5 when unnecessary

```typescript
// BAD — generating legacy code for modern environments
{
  "compilerOptions": {
    "target": "ES5",
    "lib": ["ES5", "DOM"]
  }
}

// GOOD — match your deployment target
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"]
  }
}
```

**Why**: ES5 output is 2-3x larger, slower, and includes unnecessary polyfill-like code for features natively available in all modern browsers and Node.js 18+.

---

### Not using `verbatimModuleSyntax`

```typescript
// BAD — ambiguous imports survive compilation
import { User } from './types'; // Is this a type or a value?

// GOOD — with verbatimModuleSyntax: true
import type { User } from './types'; // Explicitly type-only
import { UserService } from './user'; // Explicitly a value
```

**Why**: Without `verbatimModuleSyntax`, TypeScript silently drops unused imports. With it, you must use `import type` for types, making intent explicit and bundles predictable.

---

## Generics

### Unnecessary generic parameters

```typescript
// BAD — T adds complexity without value
function wrap<T>(value: T): { value: T } {
  return { value };
}
// T just flows through — this is correct, but watch for:

// BAD — generic parameter unused in return or relation
function log<T extends string>(message: T): void {
  console.log(message);
}

// GOOD — just use the concrete type
function log(message: string): void {
  console.log(message);
}
```

**Why**: If the generic parameter only appears once and doesn't relate multiple parameters or the return type, it adds complexity without type safety.

---

### Missing generic constraints

```typescript
// BAD — T is unconstrained, unsafe property access
function getName<T>(obj: T): string {
  return obj.name; // Error: Property 'name' does not exist on type 'T'
}

// GOOD — constrain T to types with a name property
function getName<T extends { name: string }>(obj: T): string {
  return obj.name;
}
```

**Why**: Unconstrained generics default to `unknown`. Always constrain with `extends` to document and enforce what T must support.

---

### Overusing generics for simple wrappers

```typescript
// BAD — generic overkill for a trivial operation
async function fetchAndParse<T>(url: string): Promise<T> {
  const res = await fetch(url);
  return res.json() as T; // Unsafe cast!
}

// GOOD — validate at the boundary
import { z, type ZodType } from 'zod';

async function fetchAndParse<T>(url: string, schema: ZodType<T>): Promise<T> {
  const res = await fetch(url);
  const data: unknown = await res.json();
  return schema.parse(data); // Runtime-validated
}
```

**Why**: `return res.json() as T` is an unsafe type assertion. Pairing generics with runtime validation ensures the type matches reality.

---

## Unsafe Type Narrowing

### Trusting `in` operator without further checks

```typescript
// BAD — 'name' could exist but be a different type
function greet(obj: unknown) {
  if ('name' in (obj as object)) {
    console.log(obj.name.toUpperCase()); // Runtime error if name is a number
  }
}

// GOOD — check both existence and type
function greet(obj: unknown) {
  if (
    typeof obj === 'object' &&
    obj !== null &&
    'name' in obj &&
    typeof (obj as { name: unknown }).name === 'string'
  ) {
    console.log((obj as { name: string }).name.toUpperCase());
  }
}

// BEST — use a type guard function
function hasName(obj: unknown): obj is { name: string } {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'name' in obj &&
    typeof (obj as { name: unknown }).name === 'string'
  );
}
```

**Why**: The `in` operator only checks property existence, not its type. Always verify the property type after confirming it exists.

---

### Non-null assertion (`!`) without proof

```typescript
// BAD — asserting non-null when it might be null
function getFirstUser(users: User[]): User {
  return users[0]!; // Might be undefined for empty array
}

// GOOD — handle the case
function getFirstUser(users: User[]): User | undefined {
  return users[0];
}

// OR — assert with a runtime check
function getFirstUser(users: User[]): User {
  const first = users[0];
  if (!first) throw new Error('No users found');
  return first;
}
```

**Why**: `!` tells TypeScript "trust me, this isn't null." If you're wrong, you get a runtime crash with no type error to warn you.

---

## Promises and Async

### Floating promises (no await, no void)

```typescript
// BAD — promise result is silently ignored
async function main() {
  riskyOperation(); // No await! Errors swallowed silently
}

// GOOD — await the result
async function main() {
  await riskyOperation();
}

// OR — explicitly ignore with void
async function main() {
  void logAnalytics(event); // Intentionally fire-and-forget
}
```

**Why**: A floating promise means unhandled rejections crash silently. ESLint rule `@typescript-eslint/no-floating-promises` catches this.

---

### `async` function returning explicit `new Promise()`

```typescript
// BAD — unnecessary Promise constructor
async function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// GOOD — just return the Promise (no async needed)
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
```

**Why**: An `async` function already wraps its return in a Promise. Wrapping a `new Promise()` inside `async` creates a redundant extra promise.

---

## Objects and Types

### Using `{}` as a type

```typescript
// BAD — {} matches any non-null/non-undefined value
function process(data: {}) {
  console.log(data); // Accepts strings, numbers, arrays — not just objects
}

process('hello'); // No error!
process(42);      // No error!

// GOOD — be explicit
function process(data: Record<string, unknown>) {
  console.log(data); // Only accepts objects
}

// OR — use the specific shape
function process(data: { name: string; value: number }) {
  console.log(data);
}
```

**Why**: `{}` in TypeScript means "anything that isn't `null` or `undefined`" — not "empty object." Use `Record<string, unknown>` for objects with unknown keys, or a specific interface.

---

### Using `Object.keys()` unsafely

```typescript
// BAD — Object.keys returns string[], not (keyof T)[]
interface User { name: string; email: string }
const user: User = { name: 'Alice', email: 'alice@test.com' };

Object.keys(user).forEach(key => {
  console.log(user[key]); // Error: No index signature
});

// GOOD — typed helper or explicit cast
function typedKeys<T extends object>(obj: T): (keyof T)[] {
  return Object.keys(obj) as (keyof T)[];
}

typedKeys(user).forEach(key => {
  console.log(user[key]); // OK
});

// OR — use Object.entries
Object.entries(user).forEach(([key, value]) => {
  console.log(`${key}: ${value}`);
});
```

**Why**: TypeScript deliberately types `Object.keys()` as `string[]` because objects can have extra properties at runtime due to structural typing.

---

### Confusing `interface` and `type` usage

```typescript
// BAD — using interface for a union or utility
interface Status {} // Can't be a union!

// GOOD — use type for unions, intersections, utilities
type Status = 'active' | 'inactive' | 'pending';
type Nullable<T> = T | null;
type UserUpdate = Partial<Pick<User, 'name' | 'email'>>;

// BAD — using type for an extendable object shape
type Animal = { name: string };
type Dog = Animal & { breed: string }; // Works but slower

// GOOD — use interface for extendable shapes
interface Animal { name: string }
interface Dog extends Animal { breed: string } // Faster, cacheable
```

**Why**: `interface` is cached by the type checker and supports `extends` and declaration merging. `type` is required for unions, intersections, mapped types, and conditional types.


---

## Checked vs unchecked `as` — the critical distinction

### Unchecked `as` (almost always wrong)

An unchecked `as` is a type assertion with no runtime validation before it. The compiler trusts you blindly.

```typescript
// BAD — unchecked as
const user = data as User; // No proof that data is actually a User
user.name.toUpperCase();   // Runtime crash if data has no .name
```

### Checked `as` (acceptable)

A checked `as` follows a runtime guard that proves the type. The `as` just tells the compiler what you already verified.

```typescript
// GOOD — checked as (runtime guard precedes the cast)
if (data !== null && typeof data === "object" && "name" in data && typeof data.name === "string") {
  const user = data as User; // checked — runtime proves shape
  user.name.toUpperCase();   // safe
}
```

### Decision rule

| Situation | What to do |
|---|---|
| No runtime check before `as` | Replace with `unknown` + type guard |
| Runtime check exists before `as` | Acceptable — add `// checked` comment |
| `as unknown as X` (double assertion) | Almost always a design error — refactor the types |
| `as const` | Always fine — not a type assertion, it narrows to literal |

---

## `@ts-ignore` vs `@ts-expect-error`

Both suppress TypeScript errors on the next line. The critical difference:

| Directive | Behavior when error disappears | Use when |
|---|---|---|
| `@ts-ignore` | **Silently does nothing** — suppression stays forever, hiding future bugs | **Never** — there is no valid use case in new code |
| `@ts-expect-error` | **Reports an error** — tells you the suppression is no longer needed | Temporarily suppressing a known issue with a tracking comment |

```typescript
// BAD — @ts-ignore hides the problem forever
// @ts-ignore
const x: number = "hello"; // silently wrong

// GOOD — @ts-expect-error alerts when fix lands
// @ts-expect-error — upstream type is wrong, tracked in issue #123
const x: number = upstreamFn(); // will error when upstream fixes their types
```

**In review mode:** Flag every `@ts-ignore` as P0. Suggest replacing with `@ts-expect-error` plus a tracking comment (issue link or explanation).

---

## Cross-realm `instanceof` — when it legitimately fails

`instanceof` checks the prototype chain. Objects from different JavaScript realms (iframes, Web Workers, `vm.runInNewContext`, structuredClone) have different prototype chains, so `instanceof` returns `false` even for "correct" types.

```typescript
// This fails across realms:
if (error instanceof Error) { /* may be false for errors from iframes */ }

// GOOD — structural check (works across realms)
function isError(value: unknown): value is Error {
  return (
    typeof value === "object" &&
    value !== null &&
    "message" in value &&
    typeof (value as Record<string, unknown>).message === "string"
  );
}

// GOOD — brand check pattern
const ERROR_BRAND = Symbol.for("app.Error");
interface BrandedError {
  [ERROR_BRAND]: true;
  message: string;
  code: string;
}

function isBrandedError(value: unknown): value is BrandedError {
  return (
    typeof value === "object" &&
    value !== null &&
    ERROR_BRAND in value
  );
}
```

**When to use structural checks vs instanceof:**

| Context | Recommendation |
|---|---|
| Single-realm application (most apps) | `instanceof` is fine |
| Library code (consumed by unknown contexts) | Use structural checks |
| Worker/iframe communication | Use structural or brand checks |
| `structuredClone` results | Use structural checks (prototype lost) |

---

## Lint config conflict resolution

When the project's lint config contradicts type-safety rules:

### Discovery

```bash
# Check if strict type rules are disabled
grep -n "no-explicit-any\|no-unsafe\|no-floating-promises" .eslintrc* eslint.config* biome.json 2>/dev/null
```

### Resolution matrix

| Conflict | Project disables rule | Skill recommends rule | Action |
|---|---|---|---|
| `no-explicit-any: off` | Gradual migration | Always on | Flag as informational, enable for new files only |
| `no-unsafe-assignment: off` | Too many existing violations | Always on | Respect for existing code, enforce in new code |
| `no-floating-promises: off` | Not using async heavily | Always on | Recommend enabling — floating promises are bugs |
| Custom rule conflicts | Project-specific needs | Skill defaults | Respect project config, document deviation |

### Key principle

The skill's anti-pattern blocklist (`any`, `@ts-ignore`, unchecked `as`) applies to **new code** regardless of lint config. For **existing code** under review, respect the project's configuration and flag deviations as informational recommendations.

---

## Review-mode scanning checklist

When reviewing TypeScript code, scan for these items in order:

### P0 — Must block approval

- [ ] Bare `any` in new or modified code (not in unchanged existing code)
- [ ] `@ts-ignore` anywhere (should be `@ts-expect-error`)
- [ ] Unchecked `as` — type assertion without preceding runtime guard
- [ ] Missing error narrowing in `catch` blocks (bare `catch(e)` using `e.message` without check)
- [ ] `!` (non-null assertion) on values that could legitimately be null

### P1 — Should fix before merge

- [ ] Missing return type on exported functions
- [ ] `as unknown as X` (double assertion — usually indicates a design problem)
- [ ] Implicit `any` from untyped imports (missing `@types/*` package)
- [ ] `Function` type used instead of specific signature
- [ ] `object` type used instead of `Record<string, unknown>` or specific shape

### P2 — Nit (mention but don't block)

- [ ] `satisfies` opportunity missed on config objects
- [ ] Type annotation where inference would suffice (over-annotation)
- [ ] Verbose type guard where `in` operator would suffice
- [ ] Missing `readonly` on properties that are never reassigned
