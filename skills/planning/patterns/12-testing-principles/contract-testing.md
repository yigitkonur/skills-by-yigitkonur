# Contract Testing

**Verify that services agree on their API contracts without running the entire system together.**

---

## Origin / History

Contract testing emerged from the pain of microservice integration testing. As organizations decomposed monoliths into dozens or hundreds of services, the question "does service A still work with service B after this deployment?" became increasingly expensive to answer. End-to-end testing required standing up every service simultaneously — slow, flaky, and impractical at scale. Ian Robinson introduced consumer-driven contracts in 2006. Pact, the most popular contract testing framework, was created by Ron Holshausen and Beth Skurrie at REA Group (Australia) in 2013. The Spring Cloud Contract project brought contract testing to the Java/Spring ecosystem. Today, contract testing is considered essential for microservice architectures by ThoughtWorks, Netflix, and Atlassian.

## The Problem It Solves

In a microservice architecture, service A (the consumer) depends on service B (the provider). Service B's team deploys a change that renames a field from `userName` to `username`. Service B's own tests pass. Service A's own tests pass (they mock service B). In production, service A breaks because it expects `userName`. Neither team's tests caught the incompatibility. This is the integration testing gap: each service passes its own tests but fails when composed.

## The Principle Explained

Contract testing bridges this gap by making the API contract explicit and testing both sides against it independently.

**Consumer-driven contracts (CDC)** start from the consumer's perspective. Service A (consumer) writes a contract that says: "I send a GET to /users/123 and expect a response with `{ id: number, userName: string, email: string }`." This contract is shared with service B (provider). Service B runs the contract against its real implementation. If service B renames `userName` to `username`, the contract test fails on service B's side — before deployment.

The workflow has three steps:

1. **Consumer generates a contract.** During consumer tests, the consumer defines its expectations (request shape, expected response) and records them as a contract file (a "pact" in Pact terminology).

2. **Contract is shared.** Via a Pact Broker, a Git repository, or an artifact store.

3. **Provider verifies the contract.** The provider runs the contract against its actual implementation (not a mock). If verification fails, the provider knows it will break a consumer.

This inverts the traditional integration test: instead of testing the system end-to-end, you test each side against a shared contract. Tests run fast (seconds), in isolation, and can be parallelized across services.

## Code Examples

### GOOD: Consumer-driven contract with Pact

```typescript
// === CONSUMER SIDE (service A) ===
import { PactV3, MatchersV3 } from "@pact-foundation/pact";

const { like, eachLike, string, integer } = MatchersV3;

const provider = new PactV3({
  consumer: "OrderService",
  provider: "UserService",
});

describe("UserService contract", () => {
  it("returns user profile by ID", async () => {
    // Define the expected interaction
    await provider
      .given("user 123 exists")
      .uponReceiving("a request for user 123")
      .withRequest({
        method: "GET",
        path: "/api/users/123",
        headers: { Accept: "application/json" },
      })
      .willRespondWith({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: {
          id: integer(123),
          userName: string("janedoe"),
          email: string("jane@example.com"),
          tier: string("gold"),
        },
      })
      .executeTest(async (mockServer) => {
        // Test the consumer's HTTP client against the mock
        const client = new UserServiceClient(mockServer.url);
        const user = await client.getUserById(123);

        expect(user.id).toBe(123);
        expect(user.userName).toBeDefined();
        expect(user.email).toBeDefined();
      });
    // Pact writes the contract to a JSON file automatically
  });

  it("returns 404 for non-existent user", async () => {
    await provider
      .given("user 999 does not exist")
      .uponReceiving("a request for non-existent user")
      .withRequest({
        method: "GET",
        path: "/api/users/999",
      })
      .willRespondWith({
        status: 404,
        body: {
          error: string("User not found"),
        },
      })
      .executeTest(async (mockServer) => {
        const client = new UserServiceClient(mockServer.url);
        await expect(client.getUserById(999)).rejects.toThrow(UserNotFoundError);
      });
  });
});

// === PROVIDER SIDE (service B) ===
import { Verifier } from "@pact-foundation/pact";

describe("UserService provider verification", () => {
  let server: Server;

  beforeAll(async () => {
    server = await startUserService({ port: 0 }); // start real service
  });

  afterAll(() => server.close());

  it("satisfies all consumer contracts", async () => {
    const verifier = new Verifier({
      providerBaseUrl: `http://localhost:${server.port}`,
      pactUrls: ["./pacts/OrderService-UserService.json"],
      // State handlers set up test data for "given" clauses
      stateHandlers: {
        "user 123 exists": async () => {
          await testDb.seed({
            users: [{ id: 123, userName: "janedoe", email: "jane@example.com", tier: "gold" }],
          });
        },
        "user 999 does not exist": async () => {
          await testDb.clear("users");
        },
      },
    });

    await verifier.verifyProvider();
    // If the provider renamed "userName" to "username",
    // this test FAILS — catching the breaking change before deployment
  });
});
```

### BAD: E2E tests as the only integration verification

```typescript
// This test requires BOTH services to be running simultaneously.
// It uses a shared test database. It takes 30 seconds. It fails
// when the UserService is being deployed. It flakes on slow CI.
describe("order creation with user lookup", () => {
  it("creates order for existing user", async () => {
    // Assumes UserService is running at this URL and has this data
    const response = await fetch("http://localhost:3001/api/orders", {
      method: "POST",
      body: JSON.stringify({
        userId: 123,
        items: [{ productId: "P1", quantity: 1 }],
      }),
    });

    // If this fails, is it the OrderService? The UserService?
    // The database? The network? Who knows.
    expect(response.status).toBe(201);
    const order = await response.json();
    expect(order.user.userName).toBe("janedoe");
  });
});
```

## Alternatives & Related Approaches

| Approach | When to prefer it |
|---|---|
| **E2E tests** | When you need to verify the entire user journey, not just API compatibility |
| **Schema validation (OpenAPI/JSON Schema)** | When you want lightweight structural checks without behavioral verification |
| **Integration environments** | When you have few services and can afford to run everything together |
| **API versioning** | When breaking changes are managed through explicit version numbers, not contract tests |
| **GraphQL schema checks** | For GraphQL APIs where the schema IS the contract |

Contract testing does not replace E2E tests. It replaces the "does this API still return what I expect?" portion of integration testing, which is the most common source of microservice integration failures.

## When NOT to Apply

- **Monolithic applications.** If all code is in one deployable unit, contract testing adds overhead with no benefit. Use integration tests.
- **Stable, versioned public APIs.** If the API is versioned (v1, v2) and changes go through deprecation cycles, schema validation may be sufficient.
- **Fewer than 3 services.** The overhead of contract testing infrastructure (Pact Broker, CI pipelines) is hard to justify for very small systems.
- **Event-driven architectures with schema registries.** If you use Kafka with Avro/Protobuf and a schema registry, the registry already enforces contract compatibility. Contract testing adds less value here.

## Tensions & Trade-offs

- **Contract maintenance:** Every consumer interaction becomes a contract that the provider must satisfy. With 10 consumers, the provider has 10 contracts to verify. Adding a new field is easy (additive); removing or renaming a field requires coordinating with all consumers.
- **State setup complexity:** Provider verification requires setting up test data for each "given" state. For complex domains, this state setup can become as complex as the test itself.
- **Pact Broker as infrastructure:** A contract testing workflow typically requires a Pact Broker (or similar) to share contracts between teams. This is another piece of infrastructure to maintain.
- **Not a substitute for integration tests:** Contract tests verify the shape of requests and responses. They do not verify business logic correctness, performance characteristics, or end-to-end data flow.
- **Consumer tests use mocks:** The consumer side tests against a mock server, not the real provider. If the consumer's mock does not accurately reflect its real usage patterns, the contract may be incomplete.

## Real-World Consequences

Atlassian adopted Pact across their microservice platform. Before contract testing, they discovered API incompatibilities in staging — days into the deployment pipeline. After adopting Pact, they caught incompatibilities in the consumer's CI pipeline (minutes), before the code was even merged.

A large e-commerce company with 200+ microservices tried to maintain a shared integration environment. It was broken more often than it worked (each service deployed independently, and any breaking change broke the environment for everyone). They replaced the shared environment with contract tests and reduced their integration test failures by 80%.

## Further Reading

- [Pact Documentation](https://docs.pact.io/)
- [Ian Robinson: Consumer-Driven Contracts](https://martinfowler.com/articles/consumerDrivenContracts.html)
- [Martin Fowler: Contract Test](https://martinfowler.com/bliki/ContractTest.html)
- [Spring Cloud Contract](https://spring.io/projects/spring-cloud-contract)
- *Building Microservices* by Sam Newman — Chapter 7: Testing
