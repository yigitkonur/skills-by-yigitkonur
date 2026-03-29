# Server-Side Testing with convex-test

## Use This When
- Testing Convex TypeScript backend functions locally before the Swift client touches them.
- Verifying query logic, mutation side-effects, and auth guards without a live deployment.
- Setting up fast backend test cycles in CI.

## Overview

`convex-test` runs your Convex functions against an in-memory instance using vitest. No deployment needed. Each `convexTest()` call gets a fresh database.

## Installation

```bash
npm install --save-dev convex-test vitest @edge-runtime/vm
```

## Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "edge-runtime",
    server: {
      deps: {
        inline: ["convex", "convex-test"],
      },
    },
  },
});
```

`environment: "edge-runtime"` is required because Convex functions run in an edge-like runtime, not Node.js.

## Basic Test Structure

```typescript
import { convexTest } from "convex-test";
import { expect, test, describe } from "vitest";
import schema from "../convex/schema";
import { api } from "../convex/_generated/api";

describe("messages", () => {
  test("send and list messages", async () => {
    const t = convexTest(schema);

    await t.mutation(api.messages.send, {
      channelId: "test-channel" as any,
      body: "Hello from test",
    });

    const messages = await t.query(api.messages.list, {
      channelId: "test-channel" as any,
    });

    expect(messages).toHaveLength(1);
    expect(messages[0].body).toBe("Hello from test");
  });
});
```

## Testing with Authentication

Simulate Clerk-issued identities with `t.withIdentity()`:

```typescript
test("authenticated mutation gets user identity", async () => {
  const t = convexTest(schema);

  const asUser = t.withIdentity({
    subject: "user-123",
    issuer: "https://clerk.example.com",
    name: "Test User",
    email: "test@example.com",
  });

  await asUser.mutation(api.users.store, {});

  const users = await t.query(api.users.list, {});
  expect(users).toHaveLength(1);
  expect(users[0].name).toBe("Test User");
});

test("unauthenticated mutation throws", async () => {
  const t = convexTest(schema);

  await expect(
    t.mutation(api.users.store, {})
  ).rejects.toThrow();
});
```

This validates that `convex-helpers` `userQuery`/`userMutation` wrappers (or manual `ctx.auth.getUserIdentity()` guards) correctly reject unauthenticated calls.

## Testing Internal Functions

```typescript
import { internal } from "../convex/_generated/api";

test("internal function can be called directly", async () => {
  const t = convexTest(schema);

  await t.mutation(internal.testHelpers.resetAll, {});

  const messages = await t.query(api.messages.list, {
    channelId: "any" as any,
  });
  expect(messages).toEqual([]);
});
```

## Testing Actions

```typescript
test("action orchestrates mutation and query", async () => {
  const t = convexTest(schema);

  const asUser = t.withIdentity({
    subject: "user-456",
    issuer: "https://clerk.example.com",
  });

  const result = await asUser.action(api.channels.createWithDefaults, {
    name: "new-channel",
  });

  expect(result).toBeDefined();
});
```

## Running Tests

```bash
npx vitest run                                # all tests
npx vitest                                    # watch mode
npx vitest run convex/tests/messages.test.ts  # specific file
```

## Project Structure

```
convex/
  schema.ts
  messages.ts
  users.ts
  tests/
    messages.test.ts
    users.test.ts
vitest.config.ts
```

## Key Points

| Concept | Detail |
|---|---|
| Schema enforcement | `convexTest(schema)` validates all args and returns |
| Auth simulation | `t.withIdentity({...})` fakes Clerk identity |
| Isolation | Each `convexTest()` call gets a fresh in-memory DB |
| Edge runtime | `environment: "edge-runtime"` in vitest config is required |
| No deployment | Tests run locally, no network calls |
| Internal functions | Use `internal` import to test non-public functions |

## Avoid
- Skipping `environment: "edge-runtime"` in vitest config -- tests will fail with runtime errors.
- Testing auth guards only from the Swift side -- `convex-test` catches backend auth bugs faster.
- Importing from `"./_generated/server"` in test files -- import `api` and `internal` from `"./_generated/api"` instead.
- Deploying `testHelpers.ts` mutations to production -- guard with environment checks or use `internalMutation`.

## Read Next
- [02-integration-testing-with-test-deployment.md](02-integration-testing-with-test-deployment.md)
- [../backend/03-queries-mutations-actions-scheduling.md](../backend/03-queries-mutations-actions-scheduling.md)
- [../backend/04-auth-rules-and-server-ownership.md](../backend/04-auth-rules-and-server-ownership.md)
