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
