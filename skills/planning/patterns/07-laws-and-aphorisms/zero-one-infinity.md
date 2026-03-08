# Zero-One-Infinity Rule

## Origin

Willem van der Poel, early computer scientist, 1960s. Formalized as a design principle: "The only reasonable numbers in software design are zero, one, and infinity."

Any other arbitrary limit (2, 5, 10, 100, 255, 1024) will eventually be wrong and create problems.

## Explanation

When designing a system, allow either:
- **Zero** of something (the feature does not exist)
- **One** of something (exactly one, enforced)
- **Infinity** of something (unbounded, limited only by resources)

Never pick an arbitrary number in between. Every arbitrary limit becomes a bug report, a migration, or a scaling crisis. "Users can have up to 5 email addresses" will eventually be wrong. Either they have zero or one, or they have as many as they want.

## TypeScript Code Examples

### Bad: Arbitrary Limits

```typescript
// "Users can have up to 3 addresses"
interface User {
  address1: Address;
  address2?: Address;
  address3?: Address;
  // Someday: "A customer needs 4 addresses for their business."
  // Then: add address4? Change the schema? Migrate data?
}

// "Projects can have up to 10 tags"
interface Project {
  name: string;
  tag1?: string;
  tag2?: string;
  tag3?: string;
  tag4?: string;
  tag5?: string;
  tag6?: string;
  tag7?: string;
  tag8?: string;
  tag9?: string;
  tag10?: string;
  // Every query, validation, and UI must handle ten optional fields.
}

// "Retry up to 3 times" — but what is magical about 3?
async function fetchWithRetry(url: string): Promise<Response> {
  for (let i = 0; i < 3; i++) {  // Why 3? Why not 2? Why not 5?
    try {
      return await fetch(url);
    } catch {
      if (i === 2) throw new Error("Failed after 3 retries");
    }
  }
  throw new Error("Unreachable");
}
```

### Good: Zero, One, or Infinity

```typescript
// Zero or infinity addresses — use an array
interface User {
  readonly addresses: ReadonlyArray<Address>;  // 0 to N
}

// Zero or infinity tags — use an array
interface Project {
  readonly name: string;
  readonly tags: ReadonlyArray<string>;  // 0 to N
}

// Configurable retry with sensible defaults — the limit is a parameter, not magic
interface RetryConfig {
  readonly maxAttempts: number;  // Caller decides; no hardcoded limit
  readonly backoffMs: number;
  readonly backoffMultiplier: number;
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,           // Default is 3, but it is configurable
  backoffMs: 1000,
  backoffMultiplier: 2,
};

async function fetchWithRetry(
  url: string,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<Response> {
  let lastError: Error | undefined;

  for (let attempt = 0; attempt < config.maxAttempts; attempt++) {
    try {
      return await fetch(url);
    } catch (error) {
      lastError = error as Error;
      const delay = config.backoffMs * Math.pow(config.backoffMultiplier, attempt);
      await sleep(delay);
    }
  }

  throw new Error(
    `Failed after ${config.maxAttempts} attempts: ${lastError?.message}`
  );
}
```

### Database Schema: Columns vs. Rows

```typescript
// BAD: Arbitrary limit baked into schema (columns)
// CREATE TABLE users (
//   phone1 VARCHAR(20),
//   phone2 VARCHAR(20),
//   phone3 VARCHAR(20)
// );

// GOOD: Zero-to-infinity via separate table (rows)
// CREATE TABLE user_phones (
//   user_id UUID REFERENCES users(id),
//   phone VARCHAR(20),
//   label VARCHAR(50),   -- "home", "work", "mobile"
//   PRIMARY KEY (user_id, phone)
// );

// TypeScript model mirrors the infinite design:
interface User {
  readonly id: string;
  readonly phones: ReadonlyArray<{
    number: string;
    label: string;
  }>;
}
```

## Common Violations and Fixes

| Violation | Problem | Fix |
|---|---|---|
| `MAX_TAGS = 10` | Customer needs 11 | Use an array with no hardcoded max |
| `image1, image2, image3` columns | Product has 4 images | Use an images table/array |
| `MAX_TEAM_SIZE = 20` | Department has 25 | Remove the limit or make it configurable |
| 255-char VARCHAR | URL is 300 chars | Use TEXT type |
| `MAX_FILE_SIZE = 10MB` | Video upload is 11MB | Make configurable or use streaming |
| `maxRetries = 3` | Transient outage lasts 5 cycles | Make configurable with backoff |

## Alternatives and Related Concepts

- **Configuration over convention:** Make limits configurable rather than hardcoded.
- **Postel's Law:** Be liberal in what you accept — which means do not impose unnecessary limits.
- **Database normalization:** First normal form eliminates repeating groups, which is the relational version of this rule.
- **Elastic scaling:** Cloud infrastructure embodies zero-one-infinity for compute resources.

## When NOT to Apply

- **Resource protection:** `MAX_QUERY_RESULTS = 1000` prevents OOM and protects databases. This is not an arbitrary limit — it is a safety valve. But make it configurable and paginate instead.
- **Security limits:** `MAX_LOGIN_ATTEMPTS = 5` prevents brute force. Security limits are intentional constraints, not arbitrary design choices.
- **Physical constraints:** Hardware has real limits. A 32-bit integer can hold ~4 billion, not infinity.
- **Business rules:** "Each plan allows up to N projects" is a pricing decision, not a design limit.
- **UX design:** "Show top 5 results" is a display choice, not a data model limit. The data model should store infinity; the UI can display a subset.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Arbitrary limits | Simple to implement, predictable resource use | Migration pain when limits are hit |
| Zero-one-infinity | Future-proof, flexible | Must still handle resource limits (pagination, streaming) |
| Configurable limits | Best of both worlds | More configuration complexity |

## Real-World Consequences

- **Early email systems:** Limited to 5 attachments. When business workflows required 6, workarounds proliferated.
- **IPv4 (32-bit addresses):** 4.3 billion seemed like infinity in 1981. It was not. IPv6 (128-bit) aims for actual practical infinity.
- **Twitter's 140 characters:** An arbitrary limit (from SMS) that shaped an entire platform's culture. Expanding to 280 was a major migration.
- **SQL Server 2000:** 256 columns per table. Seemed like infinity; some data warehouse designs hit it.
- **Git's SHA-1 hashes:** 160-bit seemed infinite. Collision attacks proved otherwise, requiring SHA-256 migration.

## The Design Heuristic

When you type a number that is not 0, 1, or some resource-protection constant, pause and ask:

1. "Why this number and not one higher?"
2. "What happens when someone needs more?"
3. "Can I use an unbounded collection instead?"
4. "If I must limit, can I make it configurable?"

## Further Reading

- van der Poel, W. — original formulation (1960s)
- Hunt, A. & Thomas, D. (1999). *The Pragmatic Programmer*
- Bloch, J. (2008). *Effective Java* — "minimize mutability" and design for extension
- Raymond, E.S. (2003). *The Art of Unix Programming*
