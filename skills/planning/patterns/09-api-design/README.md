# 09 — API Design

A collection of patterns, strategies, and trade-offs for designing HTTP APIs that are consistent, evolvable, and production-ready.

## Contents

| # | Pattern | Summary | Key Decision |
|---|---------|---------|--------------|
| 1 | [REST Principles](./rest-principles.md) | Richardson Maturity Model (L0-L3), resource-oriented design, HATEOAS, statelessness | How RESTful does your API need to be? |
| 2 | [API Versioning](./api-versioning.md) | URI vs header vs query param vs date-based versioning | How will you evolve without breaking consumers? |
| 3 | [Idempotency](./idempotency.md) | Idempotency keys, safe methods, retry safety with payment examples | How do you make retries safe? |
| 4 | [Rate Limiting & Backpressure](./rate-limiting-and-backpressure.md) | Token bucket, sliding window, leaky bucket, 429 responses | How do you protect your service from overload? |
| 5 | [Pagination](./pagination.md) | Offset vs cursor vs keyset pagination, deep pagination problems | How will clients traverse large collections? |
| 6 | [Error Responses](./error-responses.md) | RFC 9457, error codes, machine vs human-readable errors | How will clients understand and react to failures? |
| 7 | [Contract-First Design](./contract-first-design.md) | OpenAPI first, consumer-driven contracts, Pact testing | Who defines the API shape, and when? |
| 8 | [GraphQL vs REST](./graphql-vs-rest.md) | N+1 problem, over-fetching, federation, honest trade-offs | Which paradigm fits your situation? |

## Decision Matrix

Use this matrix to navigate to the right pattern based on what you are deciding.

### "What API style should I use?"

```
Is it service-to-service with high throughput?
  YES --> Consider gRPC (see rest-principles.md for alternatives)
  NO  --> Do you have multiple clients with different data needs?
            YES --> Consider GraphQL (see graphql-vs-rest.md)
            NO  --> REST at Level 2 is almost certainly the right choice
                    (see rest-principles.md)
```

### "How should I version my API?"

```
Is this a public API with third-party consumers?
  YES --> Date-based (Stripe model) or URI versioning
          (see api-versioning.md)
  NO  --> Is it internal with coordinated deployments?
            YES --> Prefer additive-only changes, no explicit versioning
            NO  --> URI path versioning (/v1/) is the safest default
```

### "How should I paginate?"

```
Is the dataset small (< 1000 items)?
  YES --> Return everything, no pagination needed
  NO  --> Does the UI need "jump to page N"?
            YES --> Offset pagination (accept the deep-page cost)
            NO  --> Cursor-based pagination
                    (see pagination.md)
```

### "Do I need idempotency keys?"

```
Does the endpoint create resources or trigger side effects?
  YES --> Is it a payment or financial transaction?
            YES --> Mandatory idempotency keys (see idempotency.md)
            NO  --> Strongly recommended for any POST with side effects
  NO  --> GET/PUT/DELETE are idempotent by design — no keys needed
```

### "How should I handle errors?"

```
Is this a public or widely consumed API?
  YES --> RFC 9457 (Problem Details) with documented error codes
          (see error-responses.md)
  NO  --> Consistent envelope with machine-readable codes at minimum
```

### "Should I design the contract first?"

```
Do you have multiple consumers or cross-team dependencies?
  YES --> Contract-first with OpenAPI + consumer-driven contracts
          (see contract-first-design.md)
  NO  --> Is the API shape still evolving rapidly?
            YES --> Code-first is fine; formalize later
            NO  --> Contract-first prevents regret
```

## Cross-References

- **Authentication & Authorization**: Not covered here. See your security patterns section for OAuth 2.0, API keys, JWT, and RBAC.
- **API Gateway Patterns**: Rate limiting and versioning can be handled at the gateway level (Kong, AWS API Gateway) rather than in application code.
- **Observability**: Every pattern here benefits from request tracing (correlation IDs), structured logging, and metrics. See your observability patterns section.
- **Event-Driven APIs**: For webhooks, server-sent events, and WebSocket APIs, different design principles apply beyond what is covered in this REST/GraphQL-focused section.

## Recommended Reading Order

For someone new to API design, read in this order:

1. **REST Principles** — foundational vocabulary
2. **Error Responses** — applicable to every API you build
3. **Pagination** — you will need this on day one
4. **Idempotency** — critical before you handle money
5. **Rate Limiting** — critical before you go public
6. **API Versioning** — critical before your second consumer
7. **Contract-First Design** — critical before your second team
8. **GraphQL vs REST** — only when you are evaluating the switch
