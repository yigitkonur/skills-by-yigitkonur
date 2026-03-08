# Contract-First API Design

## Origin

Contract-first design originates from the SOA (Service-Oriented Architecture) era when WSDL files defined web service interfaces before implementation. The concept was reborn in the REST world with OpenAPI (formerly Swagger) and gained further traction through consumer-driven contract testing, popularized by Pact (ThoughtWorks, 2013). The core idea: define the interface before writing code, and verify it continuously.

## Explanation

### Contract-First vs. Code-First

**Code-first**: Write your Express routes, then generate an OpenAPI spec from annotations or code. The spec is a byproduct. Risk: the spec drifts from reality, endpoints are designed ad hoc, and consumers discover the API shape after it is built.

**Contract-first**: Write the OpenAPI spec (or GraphQL schema) first. Review it with consumers. Generate server stubs and client SDKs from the spec. The spec is the source of truth. Benefit: parallel frontend/backend development, early feedback, automatic validation.

### Consumer-Driven Contracts

Instead of the provider defining the contract alone, each consumer declares what it needs from the provider (a "contract"). The provider runs all consumer contracts as part of its test suite. If a change breaks any consumer's contract, the build fails before deployment.

### Pact Testing Flow

1. **Consumer** writes a test defining the expected request/response (the "pact").
2. The pact file is published to a Pact Broker.
3. **Provider** pulls consumer pacts and replays them against its real implementation.
4. If all pacts pass, the provider can deploy safely.

## TypeScript Code Examples

### Bad: Code-First with No Contract

```typescript
// BAD: API shape discovered only after implementation
// No spec, no contract, no validation — consumers learn the shape by trial and error

app.get("/users/:id", async (req, res) => {
  const user = await db.users.findById(req.params.id);
  // What does this return? What fields? What types?
  // Nobody knows until they call it.
  res.json(user);
});

// Six months later, someone renames "name" to "fullName"
// Three consumers break in production
```

### Good: OpenAPI-First with Validation

```yaml
# openapi.yaml — written and reviewed BEFORE implementation
openapi: 3.1.0
info:
  title: User Service
  version: 1.0.0
paths:
  /users/{id}:
    get:
      operationId: getUserById
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        "200":
          description: User found
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
        "404":
          description: User not found
          content:
            application/problem+json:
              schema:
                $ref: "#/components/schemas/ProblemDetail"
components:
  schemas:
    User:
      type: object
      required: [id, email, createdAt]
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        displayName:
          type: string
        createdAt:
          type: string
          format: date-time
```

```typescript
// GOOD: Request/response validation enforced by the spec
import { OpenApiValidator } from "express-openapi-validator";

app.use(
  OpenApiValidator.middleware({
    apiSpec: "./openapi.yaml",
    validateRequests: true,
    validateResponses: true, // Catches implementation drift
  })
);

// Implementation must match the spec or requests/responses are rejected
app.get("/users/:id", async (req, res) => {
  const user = await userService.findById(req.params.id);
  if (!user) {
    return res.status(404).json({
      type: "https://api.example.com/errors/not-found",
      title: "Not Found",
      status: 404,
      detail: `User ${req.params.id} not found`,
    });
  }
  // If this response doesn't match the User schema, the validator rejects it
  res.status(200).json(user);
});
```

### Good: Type Generation from OpenAPI

```typescript
// GOOD: Generate TypeScript types from the OpenAPI spec
// Run: npx openapi-typescript openapi.yaml -o src/api-types.ts

// Generated types (src/api-types.ts):
export interface paths {
  "/users/{id}": {
    get: {
      parameters: { path: { id: string } };
      responses: {
        200: { content: { "application/json": components["schemas"]["User"] } };
        404: { content: { "application/problem+json": components["schemas"]["ProblemDetail"] } };
      };
    };
  };
}

export interface components {
  schemas: {
    User: {
      id: string;
      email: string;
      displayName?: string;
      createdAt: string;
    };
  };
}

// Both frontend and backend use the same generated types
// The spec is the single source of truth
```

### Good: Consumer-Driven Contract with Pact

```typescript
// GOOD: Consumer test defines exactly what it needs
// consumer.pact.test.ts
import { PactV3, MatchersV3 } from "@pact-foundation/pact";

const provider = new PactV3({
  consumer: "OrderService",
  provider: "UserService",
});

describe("UserService contract", () => {
  it("returns user profile for a valid user ID", async () => {
    await provider
      .given("user abc-123 exists")
      .uponReceiving("a request for user abc-123")
      .withRequest({
        method: "GET",
        path: "/users/abc-123",
      })
      .willRespondWith({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: {
          id: MatchersV3.string("abc-123"),
          email: MatchersV3.email(),
          displayName: MatchersV3.string("Alice"),
        },
      })
      .executeTest(async (mockServer) => {
        const response = await fetch(`${mockServer.url}/users/abc-123`);
        const user = await response.json();

        expect(user.id).toBe("abc-123");
        expect(user.email).toBeDefined();
        expect(user.displayName).toBeDefined();
      });
  });
});

// Provider verification (provider side):
// The provider runs all consumer pacts against its real implementation
import { Verifier } from "@pact-foundation/pact";

new Verifier({
  providerBaseUrl: "http://localhost:3000",
  pactBrokerUrl: "https://pact-broker.example.com",
  provider: "UserService",
  providerVersion: process.env.GIT_SHA,
  stateHandlers: {
    "user abc-123 exists": async () => {
      await seedUser({ id: "abc-123", email: "alice@test.com", displayName: "Alice" });
    },
  },
}).verifyProvider();
```

## Alternatives

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **OpenAPI + codegen** | REST APIs with broad consumer base | Spec can feel bureaucratic for fast iteration |
| **GraphQL schema-first** | APIs with complex querying needs | Schema is the contract; introspection replaces docs |
| **Protobuf/gRPC** | Service-to-service with strong typing | Not browser-native, requires tooling |
| **tRPC** | Full-stack TypeScript monorepos | No explicit contract file — types are the contract |
| **JSON Schema** | Validating payloads without full API spec | Schema only, no endpoint/method definition |

## When NOT to Apply

- **Rapid prototyping**: When the API shape is changing daily, maintaining a formal spec creates friction. Start code-first, formalize the contract once the design stabilizes.
- **Single consumer, same team**: If one frontend team owns both client and server, tRPC or shared TypeScript types may give you contract safety with less ceremony.
- **Internal event-driven systems**: For Kafka topics or message queues, schema registries (Avro, Protobuf) are more appropriate than OpenAPI.

## Trade-offs

- **Upfront investment**: Writing the spec first feels slower initially but prevents expensive rework when consumers discover problems late.
- **Tooling dependency**: Contract-first requires good tooling (code generators, validators, Pact broker). The ecosystem is mature for OpenAPI but uneven for other formats.
- **Spec drift**: Even with contract-first, the spec can drift if response validation is not enforced at runtime. Always enable response validation in development and staging.
- **Organizational coordination**: Consumer-driven contracts require cross-team cooperation. The Pact Broker becomes a shared dependency. This is a cultural investment, not just a technical one.

## Further Reading

- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
- [Pact Documentation](https://docs.pact.io/)
- [Contract Testing vs. Integration Testing — Martin Fowler](https://martinfowler.com/bliki/ContractTest.html)
- [openapi-typescript — Type generation from OpenAPI](https://github.com/drwpow/openapi-typescript)
