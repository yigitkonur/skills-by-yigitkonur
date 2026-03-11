# Testing

Type-level testing, runtime testing patterns, and mock typing for TypeScript.

## Type-Level Testing

### Using `expect-type`

Verify that types behave correctly at compile time.

```bash
npm install -D expect-type
```

```typescript
import { expectTypeOf } from 'expect-type';

// Basic type assertions
expectTypeOf<string>().toBeString();
expectTypeOf<number>().toBeNumber();
expectTypeOf<boolean>().toBeBoolean();
expectTypeOf<null>().toBeNull();

// Object shape
interface User {
  id: string;
  name: string;
  email: string;
  age?: number;
}

expectTypeOf<User>().toHaveProperty('id');
expectTypeOf<User>().toHaveProperty('name');
expectTypeOf<User['id']>().toBeString();
expectTypeOf<User['age']>().toEqualTypeOf<number | undefined>();

// Function signatures
function createUser(name: string, email: string): User {
  return { id: '1', name, email };
}

expectTypeOf(createUser).parameter(0).toBeString();
expectTypeOf(createUser).returns.toEqualTypeOf<User>();
expectTypeOf(createUser).toBeCallableWith('Alice', 'alice@example.com');
```

### Testing generic types

```typescript
import { expectTypeOf } from 'expect-type';

type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

// Verify success case
type SuccessResult = Extract<Result<User>, { success: true }>;
expectTypeOf<SuccessResult>().toHaveProperty('data');
expectTypeOf<SuccessResult['data']>().toEqualTypeOf<User>();

// Verify error case
type ErrorResult = Extract<Result<User>, { success: false }>;
expectTypeOf<ErrorResult>().toHaveProperty('error');
expectTypeOf<ErrorResult['error']>().toEqualTypeOf<Error>();

// Verify custom error type
type CustomResult = Result<User, string>;
type CustomError = Extract<CustomResult, { success: false }>;
expectTypeOf<CustomError['error']>().toBeString();
```

### Testing utility types

```typescript
import { expectTypeOf } from 'expect-type';

// Test a custom utility type
type RequireKeys<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>;

interface Config {
  host?: string;
  port?: number;
  debug?: boolean;
}

type RequiredHostConfig = RequireKeys<Config, 'host'>;

expectTypeOf<RequiredHostConfig>().toEqualTypeOf<{
  host: string;
  port?: number;
  debug?: boolean;
}>();
```

---

## Using `@ts-expect-error` for Type Tests

Verify that invalid usage produces type errors.

```typescript
// Verify that function rejects wrong argument types
function greet(name: string): string {
  return `Hello, ${name}`;
}

// @ts-expect-error — should not accept number
greet(42);

// @ts-expect-error — should not accept undefined
greet(undefined);

// @ts-expect-error — should require an argument
greet();
```

### Testing discriminated unions

```typescript
type Shape =
  | { kind: 'circle'; radius: number }
  | { kind: 'rect'; width: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case 'circle': return Math.PI * shape.radius ** 2;
    case 'rect': return shape.width * shape.height;
  }
}

// @ts-expect-error — invalid kind value
area({ kind: 'triangle', sides: 3 });

// @ts-expect-error — missing required fields
area({ kind: 'circle' });

// @ts-expect-error — wrong field for the kind
area({ kind: 'circle', width: 10 });
```

---

## Vitest Type Testing

Vitest has built-in support for type testing via `expectTypeOf`.

```typescript
// user.test-d.ts (naming convention for type-only test files)
import { expectTypeOf, test } from 'vitest';
import { createUser, type User, type AdminUser } from './user';

test('createUser returns User type', () => {
  expectTypeOf(createUser).returns.toEqualTypeOf<User>();
});

test('AdminUser extends User', () => {
  expectTypeOf<AdminUser>().toMatchTypeOf<User>();
});

test('User id is string', () => {
  expectTypeOf<User['id']>().toBeString();
});
```

```bash
# Run type tests
vitest typecheck

# In vitest.config.ts
export default defineConfig({
  test: {
    typecheck: {
      enabled: true,
      tsconfig: './tsconfig.json',
    },
  },
});
```

---

## Mock Typing Patterns

### Typed mocks with Vitest

```typescript
import { vi, type Mock } from 'vitest';

interface UserRepository {
  findById(id: string): Promise<User | null>;
  save(user: User): Promise<User>;
  delete(id: string): Promise<void>;
}

// Full mock — all methods are vi.fn()
const mockRepo: { [K in keyof UserRepository]: Mock } = {
  findById: vi.fn(),
  save: vi.fn(),
  delete: vi.fn(),
};

// With return values
mockRepo.findById.mockResolvedValue({ id: '1', name: 'Alice', email: 'a@b.com' });
mockRepo.save.mockImplementation(async (user) => user);
mockRepo.delete.mockResolvedValue(undefined);
```

### Partial mocks

```typescript
// Only mock what you need
function createMockRepo(overrides: Partial<UserRepository> = {}): UserRepository {
  return {
    findById: vi.fn().mockResolvedValue(null),
    save: vi.fn().mockImplementation(async (user) => user),
    delete: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  };
}

// Usage
const repo = createMockRepo({
  findById: vi.fn().mockResolvedValue({ id: '1', name: 'Alice', email: 'a@b.com' }),
});
```

### Type-safe spies

```typescript
import { vi } from 'vitest';

class EmailService {
  async send(to: string, subject: string, body: string): Promise<boolean> {
    // real implementation
    return true;
  }
}

const service = new EmailService();
const sendSpy = vi.spyOn(service, 'send');

// Type-safe: only accepts valid arguments
sendSpy.mockResolvedValue(true);

await service.send('user@test.com', 'Welcome', 'Hello!');

expect(sendSpy).toHaveBeenCalledWith('user@test.com', 'Welcome', 'Hello!');
```

---

## Testing Async Code

```typescript
import { describe, it, expect, vi } from 'vitest';

describe('fetchUser', () => {
  it('returns user on success', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: '1', name: 'Alice' }),
    });

    globalThis.fetch = mockFetch;

    const user = await fetchUser('1');
    expect(user).toEqual({ id: '1', name: 'Alice' });
  });

  it('throws on HTTP error', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    });

    globalThis.fetch = mockFetch;

    await expect(fetchUser('999')).rejects.toThrow('Not Found');
  });
});
```

### Testing Result types

```typescript
import { describe, it, expect } from 'vitest';

describe('parseConfig', () => {
  it('returns success for valid config', () => {
    const result = parseConfig('{"port": 3000}');

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.port).toBe(3000);
    }
  });

  it('returns error for invalid JSON', () => {
    const result = parseConfig('not json');

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toBeInstanceOf(Error);
    }
  });
});
```

---

## Testing with Dependency Injection

```typescript
// Define interfaces for dependencies
interface Logger {
  info(message: string): void;
  error(message: string, error?: Error): void;
}

interface UserRepository {
  findById(id: string): Promise<User | null>;
}

// Service uses interfaces, not implementations
class UserService {
  constructor(
    private readonly repo: UserRepository,
    private readonly logger: Logger,
  ) {}

  async getUser(id: string): Promise<User> {
    this.logger.info(`Fetching user ${id}`);
    const user = await this.repo.findById(id);
    if (!user) throw new NotFoundError('User', id);
    return user;
  }
}

// Test with mocks
describe('UserService', () => {
  it('returns user when found', async () => {
    const mockUser: User = { id: '1', name: 'Alice', email: 'a@b.com' };

    const service = new UserService(
      { findById: vi.fn().mockResolvedValue(mockUser) },
      { info: vi.fn(), error: vi.fn() },
    );

    const user = await service.getUser('1');
    expect(user).toEqual(mockUser);
  });
});
```

---

## Snapshot Testing for Types

Use `tsd` for type assertion snapshots.

```bash
npm install -D tsd
```

```typescript
// index.test-d.ts
import { expectType, expectError } from 'tsd';
import { createClient } from './index';

const client = createClient({ apiKey: 'test' });

expectType<Promise<User>>(client.getUser('1'));
expectType<Promise<User[]>>(client.listUsers());

expectError(client.getUser(123)); // Should require string
expectError(createClient({})); // Should require apiKey
```

```json
// package.json
{
  "scripts": {
    "test:types": "tsd"
  }
}
```

---

## Test Configuration

### Vitest with TypeScript

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.ts', 'src/**/*.spec.ts'],
    coverage: {
      provider: 'v8',
      include: ['src/**/*.ts'],
      exclude: ['src/**/*.test.ts', 'src/**/*.d.ts', 'src/types/**'],
    },
    typecheck: {
      enabled: true,
    },
  },
});
```

### Separate test tsconfig

```json
// tsconfig.test.json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "types": ["vitest/globals"],
    "noEmit": true
  },
  "include": ["src/**/*.ts", "test/**/*.ts"]
}
```


---

## Testing generic constraints

When testing that a generic function correctly constrains its type parameter, use both positive and negative test cases:

```typescript
// Function under test
function merge<T extends Record<string, unknown>>(a: T, b: Partial<T>): T {
  return { ...a, ...b };
}

// Positive — should compile
const result = merge({ a: 1, b: "hello" }, { a: 2 });

// Negative — should NOT compile
// @ts-expect-error: number does not extend Record<string, unknown>
merge(42, {});

// @ts-expect-error: string does not extend Record<string, unknown>
merge("hello", {});

// Verify the constraint propagates
const merged = merge({ x: 1 }, { x: 2 });
//    ^? const merged: { x: number }
```

### Testing conditional types

```typescript
type IsString<T> = T extends string ? true : false;

// Positive cases — use satisfies for inline assertions
const _t1: IsString<"hello"> = true satisfies true;
const _t2: IsString<42> = false satisfies false;

// Distribution behavior
type Distributed = IsString<string | number>; // true | false (distributes)
const _t3: Distributed = true;  // OK
const _t4: Distributed = false; // OK
```

---

## Edge case testing checklist

When testing types, always include these edge cases:

| Category | Test cases |
|---|---|
| **Falsy values** | `null`, `undefined`, `""`, `0`, `false`, `NaN` |
| **Empty containers** | `[]`, `{}`, `new Map()`, `new Set()` |
| **Union boundaries** | Each member individually, all members together |
| **Optional properties** | Present, missing, explicitly `undefined` |
| **Generic limits** | `never`, `unknown`, `any` as type arguments |
| **Recursive types** | Shallow (1 level), medium (3-5), at recursion limit |
| **Branded types** | Base type without brand, correct brand, wrong brand |

```typescript
// Example: testing a type guard with edge cases
function isNonEmpty(value: unknown): value is string {
  return typeof value === "string" && value.length > 0;
}

// Edge cases to test at runtime AND type level:
expect(isNonEmpty("hello")).toBe(true);
expect(isNonEmpty("")).toBe(false);        // falsy string
expect(isNonEmpty(null)).toBe(false);      // null
expect(isNonEmpty(undefined)).toBe(false); // undefined
expect(isNonEmpty(0)).toBe(false);         // wrong type
expect(isNonEmpty([])).toBe(false);        // wrong type
```

---

## Type testing strategy selection guide

| Strategy | Best for | Drawbacks | Example |
|---|---|---|---|
| `@ts-expect-error` | Quick negative tests in source | Only tests "has error", not *which* error | See above |
| `// ^?` (twoslash) | Hover-type verification in docs/tests | Requires tooling support (e.g., Vitest) | `const x = fn(); //  ^? const x: string` |
| `expectTypeOf` (vitest) | Full type assertion API | Requires vitest | `expectTypeOf(fn).returns.toEqualTypeOf<string>()` |
| `expect-type` (package) | Standalone type testing | Separate dependency | `expectTypeOf<Actual>().toEqualTypeOf<Expected>()` |
| `tsd` | Testing `.d.ts` files of published packages | Separate test runner | `expectType<string>(fn())` |
| `satisfies` | Inline constraint checking | TS 4.9+ only | `const x = value satisfies Schema` |
| `as const satisfies` | Inline constraint + literal preservation | TS 4.9+ only | `const x = [1, 2] as const satisfies number[]` |

**Decision flow:**
1. Testing a published package's types? -> **tsd**
2. Using Vitest? -> **expectTypeOf** (built-in)
3. Quick negative test? -> **@ts-expect-error**
4. Inline constraint in production code? -> **satisfies**
5. Type tests in a test file? -> **expect-type** package
