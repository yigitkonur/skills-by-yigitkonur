# Rate Limiting and Backpressure

## Origin

Rate limiting has roots in network traffic shaping (1990s) and became a standard API concern as public web APIs scaled. The token bucket algorithm was formalized in networking RFCs for traffic policing. Backpressure as a concept comes from reactive systems and fluid dynamics — when a downstream system cannot keep up, the upstream must slow down or shed load.

## Explanation

### Rate Limiting Algorithms

**Token Bucket**: A bucket holds tokens up to a maximum capacity. Each request consumes a token. Tokens are added at a fixed rate. Allows bursts up to the bucket size, then throttles. Most commonly used in production (AWS, Stripe, GitHub).

**Sliding Window Log**: Stores a timestamp for every request. Counts requests within the window by scanning the log. Precise but memory-intensive.

**Sliding Window Counter**: Hybrid approach. Divides time into fixed windows, then interpolates based on the current position within the window. Good balance of accuracy and efficiency.

**Leaky Bucket**: Requests enter a queue (bucket) and are processed at a fixed rate. Excess requests overflow and are rejected. Smooths out bursts entirely.

**Fixed Window**: Simplest approach. Count requests per fixed time window (e.g., per minute). Susceptible to burst at window boundaries.

### Backpressure

Backpressure is the broader concept of a system signaling that it is overloaded. Rate limiting is one form. Others include:

- Returning 503 with `Retry-After` header
- Queue depth limits
- Load shedding (dropping low-priority work)
- Circuit breakers (stopping calls to failing services)

## TypeScript Code Examples

### Bad: No Rate Limiting

```typescript
// BAD: Any client can hammer this endpoint without limit
app.post("/emails/send", async (req, res) => {
  await emailService.send(req.body);
  res.status(200).json({ sent: true });
  // A single client can exhaust your email quota in seconds
});
```

### Good: Token Bucket Implementation

```typescript
// GOOD: Token bucket rate limiter with per-client tracking
interface Bucket {
  tokens: number;
  lastRefill: number;
}

class TokenBucketLimiter {
  private buckets = new Map<string, Bucket>();

  constructor(
    private readonly maxTokens: number,
    private readonly refillRate: number, // tokens per second
  ) {}

  consume(clientId: string): { allowed: boolean; retryAfterMs: number } {
    const now = Date.now();
    let bucket = this.buckets.get(clientId);

    if (!bucket) {
      bucket = { tokens: this.maxTokens, lastRefill: now };
      this.buckets.set(clientId, bucket);
    }

    // Refill tokens based on elapsed time
    const elapsed = (now - bucket.lastRefill) / 1000;
    bucket.tokens = Math.min(
      this.maxTokens,
      bucket.tokens + elapsed * this.refillRate
    );
    bucket.lastRefill = now;

    if (bucket.tokens >= 1) {
      bucket.tokens -= 1;
      return { allowed: true, retryAfterMs: 0 };
    }

    const retryAfterMs = Math.ceil((1 - bucket.tokens) / this.refillRate * 1000);
    return { allowed: false, retryAfterMs };
  }
}

const limiter = new TokenBucketLimiter(100, 10); // 100 burst, 10/sec refill

function rateLimitMiddleware(req: Request, res: Response, next: NextFunction) {
  const clientId = req.headers["x-api-key"] as string ?? req.ip;
  const result = limiter.consume(clientId);

  res.setHeader("X-RateLimit-Limit", "100");
  res.setHeader("X-RateLimit-Remaining", Math.floor(limiter["buckets"].get(clientId)?.tokens ?? 0).toString());

  if (!result.allowed) {
    res.setHeader("Retry-After", Math.ceil(result.retryAfterMs / 1000).toString());
    return res.status(429).json({
      error: "Too Many Requests",
      retryAfterMs: result.retryAfterMs,
    });
  }

  next();
}
```

### Good: Sliding Window Counter with Redis

```typescript
// GOOD: Distributed sliding window using Redis
import Redis from "ioredis";

const redis = new Redis();

async function slidingWindowCheck(
  clientId: string,
  limit: number,
  windowSec: number
): Promise<{ allowed: boolean; remaining: number; resetAt: number }> {
  const now = Date.now();
  const windowMs = windowSec * 1000;
  const windowKey = `ratelimit:${clientId}`;

  const pipe = redis.pipeline();
  // Remove entries outside the window
  pipe.zremrangebyscore(windowKey, 0, now - windowMs);
  // Add current request
  pipe.zadd(windowKey, now.toString(), `${now}:${Math.random()}`);
  // Count requests in window
  pipe.zcard(windowKey);
  // Set expiry on the key
  pipe.expire(windowKey, windowSec);

  const results = await pipe.exec();
  const count = results![2][1] as number;

  return {
    allowed: count <= limit,
    remaining: Math.max(0, limit - count),
    resetAt: now + windowMs,
  };
}

app.use(async (req, res, next) => {
  const clientId = req.headers["x-api-key"] as string ?? req.ip;
  const result = await slidingWindowCheck(clientId, 1000, 3600); // 1000/hour

  res.setHeader("X-RateLimit-Limit", "1000");
  res.setHeader("X-RateLimit-Remaining", result.remaining.toString());
  res.setHeader("X-RateLimit-Reset", Math.ceil(result.resetAt / 1000).toString());

  if (!result.allowed) {
    return res.status(429).json({ error: "Rate limit exceeded" });
  }

  next();
});
```

### Good: Client-Side Backoff and Retry

```typescript
// GOOD: Client respects 429 and backs off exponentially
async function fetchWithRetry(
  url: string,
  options: RequestInit,
  maxRetries = 3
): Promise<Response> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, options);

    if (response.status !== 429) return response;

    if (attempt === maxRetries) return response; // Give up

    const retryAfter = response.headers.get("Retry-After");
    const delayMs = retryAfter
      ? parseInt(retryAfter, 10) * 1000
      : Math.min(1000 * Math.pow(2, attempt) + Math.random() * 1000, 30000);

    console.warn(`Rate limited. Retrying in ${delayMs}ms (attempt ${attempt + 1})`);
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }

  throw new Error("Unreachable");
}
```

## Alternatives

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **API Gateway rate limiting** (Kong, AWS API Gateway) | Managed infrastructure | Less application-level control |
| **WAF-level throttling** (Cloudflare) | DDoS protection | Coarse-grained, limited customization |
| **Queue-based admission control** | Smoothing bursty workloads | Adds latency, requires queue infrastructure |
| **Priority-based load shedding** | Protecting critical paths | Requires request classification |
| **Circuit breakers** | Protecting downstream services | Rejects all traffic, not just excess |

## When NOT to Apply

- **Internal services behind a service mesh**: If your infrastructure already handles traffic shaping (e.g., Istio, Linkerd), application-level rate limiting may be redundant.
- **Low-traffic internal tools**: The overhead of rate limiting infrastructure is not justified for a tool used by five people.
- **Read-heavy caching layers**: If responses are served from cache, the cost per request is negligible and aggressive rate limiting frustrates users.

## Trade-offs

- **Accuracy vs. memory**: Sliding window log is perfectly accurate but stores every timestamp. Token bucket is approximate but uses O(1) memory per client.
- **Distributed consistency**: In multi-instance deployments, local rate limiting allows each instance's full quota. Centralized (Redis-based) limiting is accurate but adds a network round-trip per request.
- **User experience**: Aggressive limits frustrate legitimate users. Communicate limits clearly via headers (`X-RateLimit-*`) and provide `Retry-After` on 429 responses.
- **Fairness**: Per-client limiting is fair but requires reliable client identification. IP-based limiting penalizes users behind shared NAT.

## Further Reading

- [Stripe — Rate Limiting](https://stripe.com/blog/rate-limiters)
- [Cloudflare — How Rate Limiting Works](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/)
- [Google Cloud — Rate Limiting Strategies](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
- [IETF — RateLimit Header Fields (draft)](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/)
