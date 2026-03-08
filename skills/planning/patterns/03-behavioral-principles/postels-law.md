# Postel's Law (Robustness Principle)

**Be conservative in what you send, be liberal in what you accept.**

---

## Origin

Postel's Law was formulated by Jon Postel in RFC 761 (1980) and reaffirmed in RFC 793 (1981), the specification for TCP. The exact quote: *"Be conservative in what you do, be liberal in what you accept from others."* Postel was describing how TCP implementations should handle non-conforming packets to ensure interoperability across the early, heterogeneous Internet. The principle became one of the most debated maxims in software engineering, with strong advocates and vocal critics.

---

## The Problem It Solves

In a distributed world, you do not control every system that talks to yours. Clients send malformed JSON, APIs return extra fields you did not expect, and upstream services change their response format without warning. Without some tolerance for variation, systems become brittle — a single unexpected field in a JSON response crashes your parser, or a client sending `"true"` instead of `true` gets rejected despite the intent being clear.

---

## The Principle Explained

Postel's Law has two halves, and both matter equally. **Be conservative in what you send** means your outputs should strictly conform to the specification. If your API says it returns ISO 8601 dates, every response must use ISO 8601 — not sometimes Unix timestamps, not sometimes locale-formatted strings. This makes life easy for consumers.

**Be liberal in what you accept** means your inputs should tolerate reasonable variation. If a client sends `Content-Type: application/json; charset=utf-8` and your parser only checks for `application/json`, accept it. If an API returns an extra `_metadata` field you do not use, ignore it rather than crashing.

The principle is most valuable at **system boundaries** — between services, between your API and external clients, between your parser and user input. It is less applicable within a single codebase, where strict typing and fail-fast are usually more appropriate. The key tension is between interoperability (accept variation) and correctness (reject ambiguity). Modern practice often favors a middle path: accept known variations, reject truly invalid input, and always validate before trusting.

---

## Code Examples

### BAD: Being strict in what you accept — brittle parsing

```typescript
// Rejects valid input over trivial formatting differences
function parseWebhookPayload(raw: string): WebhookEvent {
  const parsed = JSON.parse(raw);

  // Rejects if extra fields are present
  const allowedKeys = ["event", "timestamp", "data"];
  const extraKeys = Object.keys(parsed).filter((k) => !allowedKeys.includes(k));
  if (extraKeys.length > 0) {
    throw new Error(`Unexpected fields: ${extraKeys.join(", ")}`);
  }

  // Rejects if timestamp format is slightly different
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(parsed.timestamp)) {
    throw new Error("Timestamp must be in exact ISO 8601 with milliseconds and Z");
  }
  // "2024-01-15T10:30:00Z" — rejected (missing milliseconds)
  // "2024-01-15T10:30:00.000+00:00" — rejected (uses offset instead of Z)

  return parsed as WebhookEvent;
}

// Being sloppy in what you send — inconsistent output
function formatApiResponse(data: unknown): string {
  return JSON.stringify({
    data,
    timestamp: Date.now(),        // Sometimes Unix ms
    // ...elsewhere in codebase:
    // timestamp: new Date().toISOString()  // Sometimes ISO string
  });
}
```

### GOOD: Applying Postel's Law — tolerant reader, strict writer

```typescript
import { z } from "zod";

// Liberal in accepting: use a schema that accepts reasonable variations
const webhookEventSchema = z.object({
  event: z.string().min(1),
  timestamp: z.union([
    z.string().datetime(),                          // ISO 8601 in any valid form
    z.number().transform((n) => new Date(n).toISOString()), // Unix ms
    z.string().regex(/^\d+$/).transform((s) => new Date(parseInt(s)).toISOString()),
  ]),
  data: z.record(z.unknown()),
}).passthrough(); // Accept and ignore unknown fields

function parseWebhookPayload(raw: string): WebhookEvent {
  const parsed = JSON.parse(raw);
  const result = webhookEventSchema.safeParse(parsed);

  if (!result.success) {
    throw new ValidationError("Invalid webhook payload", result.error.issues);
  }

  // We only use fields we understand; extras are ignored
  return {
    event: result.data.event,
    timestamp: result.data.timestamp as string,
    data: result.data.data,
  };
}

// Conservative in sending: strict, documented, consistent output
interface ApiResponse<T> {
  data: T;
  meta: {
    timestamp: string;   // Always ISO 8601 with timezone
    requestId: string;   // Always UUID v4
    version: string;     // Always semver
  };
}

function formatApiResponse<T>(data: T, requestId: string): ApiResponse<T> {
  return {
    data,
    meta: {
      timestamp: new Date().toISOString(), // Always ISO 8601
      requestId,                           // Always from request context
      version: "2.1.0",                    // Always current API version
    },
  };
}

// Tolerant reader pattern for consuming external APIs
interface ExternalUserResponse {
  id: string;
  name: string;
  email: string;
  // We only use these three fields, even if the API returns 50 more
}

async function fetchExternalUser(userId: string): Promise<ExternalUserResponse> {
  const response = await fetch(`https://api.external.com/users/${userId}`);
  const body = await response.json();

  // Extract only what we need — ignore the rest
  return {
    id: String(body.id ?? body.userId ?? body.user_id),
    name: String(body.name ?? body.displayName ?? "Unknown"),
    email: String(body.email ?? body.emailAddress ?? ""),
  };
}
```

---

## Alternatives & Related Principles

| Approach | Relationship |
|---|---|
| **Strict Parsing / Fail-Fast** | The counter-argument to Postel's Law. If you accept malformed input, you encourage senders to be sloppy, creating a "race to the bottom" where everyone depends on undocumented leniency. JSON's strict syntax is a deliberate rejection of Postel's Law. |
| **Schema Validation (JSON Schema, Zod, io-ts)** | A middle ground: define exactly what you accept, validate it, but be explicit about which variations are tolerated. |
| **Contract-First Design (OpenAPI, Protobuf)** | Explicit contracts reduce the need for liberal acceptance — both sides agree on the format upfront. |
| **Tolerant Reader Pattern** | Martin Fowler's pattern: read only the fields you need, ignore the rest. A specific implementation of the "liberal in what you accept" half. |
| **Consumer-Driven Contracts** | Consumers define what they need from a provider, allowing providers to evolve without breaking consumers. An alternative to liberal acceptance. |

---

## When NOT to Apply

- **Security-sensitive inputs**: Never be "liberal" with authentication tokens, SQL queries, or file paths. Strict validation is mandatory.
- **Within a single codebase**: Inside your own code, use strict types and fail-fast. Postel's Law is for system boundaries, not internal method calls.
- **When it masks bugs**: If your system silently accepts and "fixes" malformed input, the sender never discovers their bug. This is how HTML's permissive parsing led to decades of browser incompatibility.
- **Financial / compliance systems**: In banking and healthcare, accepting approximate input can have legal consequences. Strict validation is preferred.
- **When the sender is also you**: If you control both sides, strict contracts (Protobuf, GraphQL) are better than liberal acceptance.

---

## Tensions & Trade-offs

- **Interoperability vs. Correctness**: Being liberal helps interoperability but hides bugs. HTML's permissive parsing made the web accessible but created a nightmare for browser vendors.
- **Evolution vs. Stability**: Ignoring unknown fields allows APIs to evolve, but can mask breaking changes.
- **Postel's Law vs. Fail-Fast**: These principles directly conflict. The resolution: apply Postel's Law at system boundaries and fail-fast within your code.
- **The "liberal acceptance" ratchet**: Once you accept malformed input, you cannot stop — someone depends on it. This is why JSON's strict parser was a deliberate design choice.

---

## Real-World Consequences

**Adherence example**: HTTP header parsing is famously liberal. Servers accept headers with varying capitalization, extra whitespace, and different line endings. This has enabled the Web to function despite thousands of different HTTP client implementations.

**Over-application example**: HTML's permissive parsing allowed `<p><div></p></div>` to "work." Browser vendors spent decades reverse-engineering each other's error recovery heuristics. The HTML5 spec eventually formalized the error handling, but the technical debt was immense.

**Modern critique**: In 2015, Martin Thomson published RFC 9413 (originally an Internet-Draft) titled *"The Harmful Consequences of the Robustness Principle"*, arguing that Postel's Law has caused more harm than good in protocol design by encouraging sloppy implementations.

---

## Key Quotes

> "Be conservative in what you do, be liberal in what you accept from others." — Jon Postel, RFC 793 (1981)

> "Postel's Law is not a license to accept garbage. It is an instruction to handle reasonable variation gracefully." — common interpretation

> "The Robustness Principle, applied liberally, has been the single greatest cause of interoperability problems on the Internet." — Martin Thomson, draft-thomson-postel-was-wrong

---

## Further Reading

- Postel, J. — RFC 793: *Transmission Control Protocol* (1981)
- Thomson, M. — RFC 9413: *Maintaining Robust Protocols* (2023, originally "The Harmful Consequences of the Robustness Principle")
- Fowler, M. — [Tolerant Reader](https://martinfowler.com/bliki/TolerantReader.html)
- Bray, T. — *The JSON Data Interchange Format* (RFC 8259) — strict by design, rejecting Postel's Law
- Hickson, I. — HTML5 parsing specification (formalizing error recovery after decades of liberal acceptance)
