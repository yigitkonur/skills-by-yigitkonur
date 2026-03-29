# Integration Testing with Test Deployment

## Use This When
- Verifying the full round-trip: Swift client -> WebSocket -> Convex backend -> database -> subscription push.
- Setting up a CI-safe integration test suite that avoids polluting production data.
- Writing end-to-end tests that exercise real Convex functions.

## Why a Dedicated Test Deployment

Unit tests mock the FFI layer. Integration tests verify the real stack. Use a separate deployment so tests never touch production data.

## Setup

### 1. Create the Test Deployment

```bash
npx convex deploy --project your-project --team your-team \
  --preview test-integration
```

Or use a persistent dev deployment for CI:

```bash
npx convex dev --once --url https://test-slug.convex.cloud
```

### 2. Set the Environment Variable

In Xcode: Edit Scheme -> Test -> Environment Variables:

```
CONVEX_TEST_URL = https://test-slug.convex.cloud
```

In CI (GitHub Actions):

```yaml
env:
  CONVEX_TEST_URL: ${{ secrets.CONVEX_TEST_URL }}
```

### 3. Create a Test Helper

```swift
import ConvexMobile

enum TestConvex {
  static let client: ConvexClient = {
    guard let url = ProcessInfo.processInfo
      .environment["CONVEX_TEST_URL"] else {
      fatalError("CONVEX_TEST_URL not set")
    }
    return ConvexClient(deploymentUrl: url)
  }()
}
```

## Backend Reset Mutation

Create `convex/testHelpers.ts` -- deploy only to the test environment:

```typescript
import { internalMutation } from "./_generated/server";

export const resetAll = internalMutation({
  args: {},
  handler: async (ctx) => {
    const tables = ["messages", "channels", "users"];
    for (const table of tables) {
      const docs = await ctx.db.query(table).collect();
      for (const doc of docs) {
        await ctx.db.delete(doc._id);
      }
    }
  },
});
```

Expose via a test-only action guarded by deployment URL:

```typescript
import { action } from "./_generated/server";
import { internal } from "./_generated/api";

export const resetForTesting = action({
  args: {},
  handler: async (ctx) => {
    if (process.env.CONVEX_CLOUD_URL?.includes("test-slug")) {
      await ctx.runMutation(internal.testHelpers.resetAll);
    }
  },
});
```

## Swift Integration Test

Integration tests share a database, so they must run serially:

```swift
import Testing
import Combine
import ConvexMobile

@Suite(.serialized)
struct MessageIntegrationTests {
  let client = TestConvex.client

  struct Message: Decodable, Equatable {
    let id: String
    let body: String
    enum CodingKeys: String, CodingKey {
      case id = "_id"
      case body
    }
  }

  @Test func roundTripMessage() async throws {
    // 1. Reset
    try await client.action(
      "testHelpers:resetForTesting",
      with: [:]
    ) as Void

    // 2. Write
    try await client.mutation(
      "messages:send",
      with: [
        "channelId": "test-channel",
        "body": "integration test"
      ]
    ) as Void

    // 3. Read via subscription
    let messages: [Message] = try await firstValue(
      client.subscribe(
        to: "messages:list",
        with: ["channelId": "test-channel"],
        yielding: [Message].self
      )
      .receive(on: DispatchQueue.main)
    )

    #expect(messages.count == 1)
    #expect(messages[0].body == "integration test")
  }
}
```

> **Auth Note:** If `messages:send` uses `userMutation`, this test will throw "Unauthenticated". For server-side tests, use `convex-test`'s `withIdentity` helper to simulate an authenticated user. For Swift integration tests, either create a test-only unauthenticated mutation or set up `ConvexClientWithAuth` with test credentials.

## Helper: First Value from Publisher

```swift
import Combine
import ConvexMobile

func firstValue<T>(
  _ publisher: AnyPublisher<T, ClientError>,
  timeout: TimeInterval = 5.0
) async throws -> T {
  try await withCheckedThrowingContinuation { continuation in
    var cancellable: AnyCancellable?
    cancellable = publisher
      .receive(on: DispatchQueue.main)
      .first()
      .sink(
        receiveCompletion: { completion in
          if case .failure(let error) = completion {
            continuation.resume(throwing: error)
          }
          cancellable?.cancel()
        },
        receiveValue: { value in
          continuation.resume(returning: value)
          cancellable?.cancel()
        }
      )

    DispatchQueue.main.asyncAfter(deadline: .now() + timeout) {
      cancellable?.cancel()
      continuation.resume(
        throwing: ClientError.InternalError(msg: "Timeout")
      )
    }
  }
}
```

## Auth-Protected Functions

If your backend functions use `userMutation` or `userQuery` (which require an authenticated user), the Swift integration test client must provide a valid auth token. For server-side testing without a real auth provider, use `convex-test`'s `withIdentity` helper in your TypeScript test files to provide a test auth context. From the Swift side, you can create a test-only unprotected wrapper mutation for integration tests, or configure your test deployment's auth to accept test tokens.

## CI Considerations

| Concern | Solution |
|---|---|
| Parallel test targets | Use `@Suite(.serialized)` |
| Flaky WebSocket | Retry with backoff in `firstValue` |
| Leftover data | Always call `resetForTesting` before assertions |
| Secret management | Store `CONVEX_TEST_URL` in CI secrets, never in code |
| Deployment drift | Run `npx convex deploy` in CI before tests |

## Avoid
- Running `resetAll` against a production deployment -- guard with a URL check.
- Using `.replaceError(with:)` anywhere in integration test pipelines -- it terminates the publisher after the first error.
- Skipping `CodingKeys` with `case id = "_id"` on Decodable models.
- Running integration tests in parallel without `@Suite(.serialized)` -- they share a database.

## Read Next
- [01-mock-ffi-client-unit-testing.md](01-mock-ffi-client-unit-testing.md)
- [05-server-side-testing-with-convex-test.md](05-server-side-testing-with-convex-test.md)
- [../operations/01-verified-corrections-and-trust-boundaries.md](../operations/01-verified-corrections-and-trust-boundaries.md)
