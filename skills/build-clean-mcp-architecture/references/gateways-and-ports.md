# Gateways and Ports

> SKILL.md's *Gateways and ports* section routes here. After reading the agent should be able to write a port interface in `domain/ports/`, an adapter that implements it in `gateways/`, and the decorator stack that wraps it; the agent should know exactly how upstream errors classify into `DomainError` subclasses, what must never leak past the port boundary, and why each decorator is its own class rather than a closure or a method.

## Vocabulary, locked

- **Port:** an interface in `domain/ports/`, named `I<Capability>`. Defines what the use case asks for, in domain terms.
- **Adapter:** a class in `gateways/<provider>/`, suffixed `Gateway` or `Store`. Implements one port. Knows the SDK or wire protocol.
- **Decorator:** a class in `gateways/` whose constructor takes the port it decorates as its first argument. Implements the same port. Adds a single concern (caching, retry, sanitisation, observability).

The use case sees a port. The bootstrap composes adapter + decorators. The use case never knows whether it is talking to Redis, to an in-memory fake, or to a cached SDK call.

## Port-naming convention

Name the port for what it **does**, not for what it stores or how it talks. `IDatasetStore`, not `IRedisRepository<Dataset>`. `IProviderGateway`, not `IDataForSeoApiClient`. `INotifier`, not `IWebhookSender`. The capability name survives storage swaps and provider rotations; the storage name does not.

Cite from `mcp-d4s: src/domain/ports/`:

```ts
// domain/ports/provider-gateway.ts
import type { ProviderRequest } from '../provider/provider-request.js';
import type { ProviderResponse } from '../provider/provider-response.js';
import type { TaskTicket } from '../provider/task-ticket.js';

export interface IProviderGateway {
  /** Execute a synchronous (live) request and return results immediately. */
  fetch(request: ProviderRequest): Promise<ProviderResponse>;
  /** Submit an asynchronous task and return a ticket for later retrieval. */
  fetchTask(request: ProviderRequest): Promise<TaskTicket>;
  /** Retrieve the results of a previously submitted async task. */
  getTaskResult(ticket: TaskTicket): Promise<ProviderResponse>;
}
```

```ts
// domain/ports/dataset-store-port.ts
import type { Dataset } from '../dataset/dataset.js';
import type { DatasetId } from '../dataset/dataset-id.js';

export interface IDatasetStore {
  save(dataset: Dataset): Promise<void>;
  get(id: DatasetId): Promise<Dataset | undefined>;
  delete(id: DatasetId): Promise<void>;
}
```

```ts
// domain/ports/cache-port.ts
export interface ICache<TValue> {
  get(key: string): Promise<TValue | undefined>;
  set(key: string, value: TValue, ttlSeconds: number): Promise<void>;
  delete(key: string): Promise<void>;
}
```

Ports stay small. Start with only the methods one use case needs. Resist defining a generic `Repository<T>` until three real consumers exist. A speculative wide port quickly turns into a second copy of the SDK inside the codebase — equivalent surface, equivalent churn, no real decoupling.

## Adapter shape

An adapter implements a port. It is `final` in spirit — no inheritance among gateway adapters, only composition through decorators.

```ts
// gateways/<provider>/<provider>-gateway.ts
import type { IProviderGateway } from '../../domain/ports/provider-gateway.js';
import type { ProviderRequest } from '../../domain/provider/provider-request.js';
import type { ProviderResponse } from '../../domain/provider/provider-response.js';
import {
  ProviderError,
  RateLimitError,
  AuthError,
  TransientError,
} from '../../domain/errors.js';

export class ConcreteProviderGateway implements IProviderGateway {
  readonly #baseUrl: string;
  readonly #credentials: { username: string; password: string };

  constructor(config: {
    baseUrl: string;
    credentials: { username: string; password: string };
  }) {
    this.#baseUrl = config.baseUrl;
    this.#credentials = config.credentials;
  }

  async fetch(request: ProviderRequest): Promise<ProviderResponse> {
    try {
      const response = await this.#callSdk(request);
      return this.#mapToDomain(response);
    } catch (err: unknown) {
      throw this.#classifyError(err, request);
    }
  }

  // …fetchTask, getTaskResult similarly.

  #callSdk(_request: ProviderRequest): Promise<unknown> {
    throw new Error('not implemented in skeleton');
  }

  #mapToDomain(_raw: unknown): ProviderResponse {
    throw new Error('not implemented in skeleton');
  }

  /**
   * Classify upstream errors into DomainError subclasses BEFORE crossing the port.
   * The use case must never see a provider-specific exception type.
   */
  #classifyError(err: unknown, request: ProviderRequest): Error {
    const status = this.#extractStatus(err);
    if (status === 401 || status === 403) {
      return new AuthError(
        'Provider rejected credentials.',
        'invalid',
        'Re-check the API key in runtime config and re-deploy.',
      );
    }
    if (status === 429) {
      const retryAfter = this.#extractRetryAfterMs(err);
      return new RateLimitError(
        'Provider rate-limit exceeded.',
        retryAfter,
      );
    }
    if (status !== undefined && status >= 500 && status < 600) {
      return new TransientError(
        'Provider returned a transient 5xx.',
      );
    }
    return new ProviderError(
      this.#redactProviderText(this.#extractMessage(err)),
      'data-provider',
      'Verify the request parameters; retry once if the issue persists.',
      { cause: err instanceof Error ? err : undefined },
    );
  }

  #extractStatus(_err: unknown): number | undefined { return undefined; }
  #extractMessage(err: unknown): string {
    return err instanceof Error ? err.message : String(err);
  }
  #extractRetryAfterMs(_err: unknown): number | undefined { return undefined; }

  /**
   * Remove provider names, internal hostnames, signed URLs, and SDK stack
   * fragments from any string that might cross the port. The presenter
   * sanitises a second time at the wire boundary; the gateway sanitises
   * here so the use case never sees a leaky message.
   */
  #redactProviderText(text: string): string {
    return text
      .replace(/\bdata-?provider[a-z0-9_-]*\b/gi, 'data provider')
      .replace(/https?:\/\/[^\s]+/g, '[redacted-url]');
  }
}
```

The shape is non-negotiable: `implements I<Capability>` declared explicitly, classification table inside the gateway, secret-leak prevention in the same file. The cite is `mcp-d4s: src/gateways/dataforseo/dataforseo-gateway.ts` for the full classification surface.

## Decorator composition — order is fixed

Decorators wrap the port. Each decorator implements the same port and takes the wrapped port as its first constructor argument. The composition is explicit in `bootstrap.ts`:

```ts
// In infrastructure/server/bootstrap.ts:
const concrete = new ConcreteProviderGateway({ baseUrl, credentials });
const sanitised = new SanitisingProviderGateway(concrete);
const retried = new RetryingProviderGateway(sanitised, { maxAttempts: 3 });
const cached = new CachingProviderGateway(retried, redis, {
  keyPrefix: 'mcp:cache:',
  ttlSeconds: 24 * 60 * 60,
});
// Use case is wired with `cached` as the IProviderGateway port.
```

Read inside-out: the use case calls `cached.fetch(...)`; the cache checks Redis; on miss, it calls `retried.fetch(...)`; retry calls `sanitised.fetch(...)`; sanitise calls `concrete.fetch(...)`. On the way back, each decorator handles its concern, then returns to the layer above.

**The order — cache → retry → sanitise → concrete (outer → inner) — is fixed.** Reversing it changes semantics. Sanitisation must happen before caching writes the entry; reversing means the first cache miss leaks pre-sanitised data, and every subsequent hit returns properly sanitised data — a bug only the first request sees. Retry must wrap sanitise rather than wrap cache; reversing means a retried call hits the cache twice and the retry budget is consumed against the local Redis, not the upstream.

### Why each decorator is its own class, not a closure

- **Each decorator implements the same port.** A closure cannot declare `implements`, so type-checking the wrapping is weaker.
- **Each decorator is unit-testable in isolation.** A test instantiates the decorator with a fake inner port and asserts only the decorator's behaviour. With closures, the only test is end-to-end through the chain.
- **Each decorator surfaces in stack traces and logs.** A class name in a stack frame identifies which layer raised the error; an anonymous closure does not.
- **Each decorator is reusable.** `CachingGateway`, `RetryingGateway`, and `SanitisingGateway` are written once and applied to every port that needs them. A closure embedded in `bootstrap.ts` is single-use by construction.
- **Decorator order is visible at the call site.** Reading the constructor chain in `bootstrap.ts`, the layering is visible the layering. Closures collapse the order into a single deeply-nested function, which is exactly the readability problem the decorator pattern fixes.

### Skeleton: `CachingProviderGateway`

```ts
// gateways/caching-provider-gateway.ts
import { createHash } from 'node:crypto';
import type { Redis } from 'ioredis';
import type { IProviderGateway } from '../domain/ports/provider-gateway.js';
import type { ProviderRequest } from '../domain/provider/provider-request.js';
import type { ProviderResponse } from '../domain/provider/provider-response.js';
import type { TaskTicket } from '../domain/provider/task-ticket.js';

export class CachingProviderGateway implements IProviderGateway {
  readonly #inner: IProviderGateway;
  readonly #redis: Redis;
  readonly #keyPrefix: string;
  readonly #ttlSeconds: number;

  constructor(
    inner: IProviderGateway,
    redis: Redis,
    config: { keyPrefix: string; ttlSeconds: number },
  ) {
    this.#inner = inner;
    this.#redis = redis;
    this.#keyPrefix = config.keyPrefix;
    this.#ttlSeconds = config.ttlSeconds;
  }

  async fetch(request: ProviderRequest): Promise<ProviderResponse> {
    const key = this.#buildKey(request);
    const cached = await this.#redis.get(key);
    if (cached !== null) {
      return JSON.parse(cached) as ProviderResponse;
    }
    const fresh = await this.#inner.fetch(request);
    await this.#redis.set(key, JSON.stringify(fresh), 'EX', this.#ttlSeconds);
    return fresh;
  }

  fetchTask(request: ProviderRequest): Promise<TaskTicket> {
    return this.#inner.fetchTask(request); // task endpoints never cache.
  }

  getTaskResult(ticket: TaskTicket): Promise<ProviderResponse> {
    return this.#inner.getTaskResult(ticket); // task results never cache.
  }

  #buildKey(request: ProviderRequest): string {
    const hash = createHash('sha256')
      .update(JSON.stringify(request))
      .digest('hex');
    return `${this.#keyPrefix}${hash}`;
  }
}
```

Cite: `mcp-d4s: src/gateways/caching-provider-gateway.ts` for the full implementation, including cache-shape validation and uncacheable-route allow-lists.

## Error classification at the gateway boundary

Every gateway must classify upstream errors into a `DomainError` subclass before the error crosses the port. Provider-specific exception types — `DataForSeoApiError`, `googleapis.GaxiosError`, `Stripe.errors.StripeAPIError`, anything from a third-party SDK — never escape the gateway. Use the table in `error-contracts.md` to pick the right subclass.

The classification rules are:

| Upstream signal | DomainError subclass | `isRetryable` |
|-----------------|----------------------|---------------|
| 400 / validation rejection | `ValidationError` | `false` |
| 401 / 403 | `AuthError` (or `PermissionError` for "user lacks permission") | `false` |
| 404 | `NotFoundError` | `false` |
| 429 | `RateLimitError` (extracts `retryAfterMs`) | `true` |
| 5xx transient | `TransientError` (or `ProviderError` if not clearly retriable) | `true` |
| 5xx persistent | `ProviderError` | `false` |
| Network / DNS / timeout | `TransientError` | `true` |
| Quota exhausted (provider-specific signal) | `QuotaExhaustedError` | `true` (but with retry-after) |

Always preserve the original error via `cause`:

```ts
throw new ProviderError(
  'Provider returned 502.',
  'data-provider',
  'Retry once; if the issue persists, check the provider status page.',
  { cause: err instanceof Error ? err : undefined },
);
```

Preserving the stack chain is what lets an operator trace a sanitised MCP envelope back to its upstream root cause in observability tooling. Never swallow.

## Secret-leak prevention at the gateway

The presenter sanitises a second time at the wire boundary, but the gateway sanitises *first*, before the use case ever sees the message. Things that must never leak past the port:

- **Provider names.** "DataForSEO", "Stripe", "Twilio" — all become "data provider" or "payment provider" or "messaging provider" in any error message that crosses the port.
- **Internal URLs and DSNs.** `https://internal.api.example.com/v3/...`, `redis://...`, `postgres://...`, S3 paths, signed URLs.
- **Credentials and tokens.** API keys, bearer tokens, OAuth refresh tokens, even truncated.
- **SDK error stack frames.** They name internal classes and module paths the model and its operator should not see.
- **Connection strings and workspace tokens.** DuckDB workspace identifiers, Supabase project IDs, anything that looks like a routing handle.

The redaction rules live next to the gateway, not in the use case. The use case is allowed to assume that the message it catches is already sanitised. (The presenter then sanitises again as a defence-in-depth pass — but that does not relieve the gateway of its primary responsibility.)

## Cross-layer DTO duplication is correct

The handler-input shape, the use-case command, the gateway request, the gateway response, the presenter row, and the MCP response shape are six distinct types. Do not collapse them. A type that crosses every layer is the single biggest decay path the codebase will experience and the most reliable way provenance fields slip onto the wire — cache-hit metadata leaking into tool responses, provider field renames cascading into the model's view. Map between the types explicitly. Compile-time mapping is cheap; the bug surface from a collapsed type is enormous.

## Verification checklist

- [ ] Every external system the server talks to (provider API, persistence, OAuth, sampling/elicitation, downstream MCP client capabilities) is reached through a port in `domain/ports/` and an adapter in `gateways/`. No use case calls an SDK directly.
- [ ] Every gateway class explicitly declares `implements I<Capability>`. `grep -rE "class [A-Z][A-Za-z]+ implements I" src/gateways/` shows one hit per gateway.
- [ ] Every adapter classifies upstream errors into a `DomainError` subclass before the error crosses the port. No use case `catch` block ever sees a provider-specific exception type.
- [ ] Decorator composition in `bootstrap.ts` reads `cache → retry → sanitise → concrete` (outer → inner). No closure-style decorator is used.
- [ ] No gateway file imports from `application/`, `handlers/`, or `presenters/`. `dependency-cruiser` enforces this.
- [ ] No gateway file imports `mcp-use`. The matrix forbids it.
- [ ] Provider names, DSNs, signed URLs, and SDK stack fragments are redacted at the gateway, not at the presenter alone. A gateway test asserts that an upstream error containing the provider name produces a `DomainError.message` that does not.
- [ ] Every `throw` in a gateway preserves the original error via `cause`. `grep -nE "throw new [A-Z][A-Za-z]*Error\\(" src/gateways/` and review each — the `{ cause: err }` option must be present when wrapping an upstream error.
- [ ] Ports stay small. Each port has only the methods at least one use case calls today; no speculative `Repository<T>` surface.
