# Error Contracts

> SKILL.md's *Error handling* section routes here. After reading you should be able to write `domain/errors.ts` from scratch with the full hierarchy, build the lookup table in `infrastructure/errors/error-contracts.ts` that maps `code` → MCP JSON-RPC envelope, and explain why this codebase throws/catches instead of returning Result types. Every guardrail in the SKILL.md error section should land here, on observable code.

## Two-error model

- **Expected errors** — validation rejections, missing-resource cases, exhausted quota, provider 4xx responses — are typed `DomainError` subclasses carrying a stable `code`, an LLM-readable `recoveryHint`, and an `isRetryable` flag. Throw inside; map at the handler boundary.
- **Unexpected errors** (defects, OOM, programmer-error throws, anything not deriving from `DomainError`) are caught by a single boundary middleware that maps them to a generic, redacted MCP envelope.

Separating expected from unexpected is what lets the boundary mapper give the model an actionable hint without leaking internal stack frames or provider names. The mapper is one symmetric table; new error subclasses extend it via a single entry, not via scattered `if (error instanceof X) ...` blocks throughout the handler layer.

## Throw / catch, not Result types

This codebase uses throw / catch with structured `cause` chains — composition through thrown errors, not through monadic chaining. Combining throw-style with a return-typed-result discipline inside one codebase produces twice the bug surface (forgotten handling on one side, double-wrapping on the other). Pick one, apply uniformly. The pick is locked here as throw / catch.

Every `catch` block uses `catch (err: unknown)` and narrows explicitly. With `useUnknownInCatchVariables` enabled (part of `strict`), the compiler forces a narrowing step — and that narrowing is exactly what catches the case where you assumed `.message` on a value that was never an `Error`. Wrapping always preserves the original via `cause`:

```ts
try {
  await sdkCall();
} catch (err: unknown) {
  throw new ProviderError(
    'Provider returned an error.',
    'data-provider',
    'Verify the request and retry once.',
    { cause: err instanceof Error ? err : undefined },
  );
}
```

Preserving the stack chain is what lets an operator trace a sanitised MCP envelope back to its upstream root cause in observability tooling. Never swallow.

## `DomainError` base + subclasses

The cite is `mcp-d4s: src/domain/errors.ts`. The base carries `code` (machine-readable), `recoveryHint` (LLM-actionable, optional), and `isRetryable` (boolean). The `name` property is set to the class name so `instanceof`-free identification still works after structured cloning across worker boundaries.

```ts
// domain/errors.ts

/**
 * Base class for every expected error in this server. Every subclass
 * sets `code` to a stable string literal and either provides or
 * inherits a default `recoveryHint`. `isRetryable` defaults to false;
 * subclasses that represent transient failures override it via
 * RetryableError or by passing `{ isRetryable: true }` through options.
 */
export class DomainError extends Error {
  readonly code: string;
  readonly recoveryHint: string | undefined;
  readonly isRetryable: boolean;

  constructor(
    message: string,
    code: string,
    recoveryHint?: string,
    options?: ErrorOptions & { isRetryable?: boolean },
  ) {
    super(message, options);
    this.name = 'DomainError';
    this.code = code;
    this.recoveryHint = recoveryHint;
    this.isRetryable = options?.isRetryable ?? false;
  }
}

// ── Validation ─────────────────────────────────────────────────────

export interface ValidationIssue {
  readonly path: string;
  readonly message: string;
}

export class ValidationError extends DomainError {
  readonly field: string;
  readonly issues?: readonly ValidationIssue[];

  constructor(opts: {
    field: string;
    reason: string;
    issues?: readonly ValidationIssue[];
    recoveryHint?: string;
  }) {
    super(
      `Validation failed for "${opts.field}": ${opts.reason}`,
      'VALIDATION_ERROR',
      opts.recoveryHint
        ?? `Check the value provided for "${opts.field}" and ensure it meets the documented constraints.`,
    );
    this.name = 'ValidationError';
    this.field = opts.field;
    if (opts.issues !== undefined) this.issues = opts.issues;
  }
}

// ── Not found ──────────────────────────────────────────────────────

export class NotFoundError extends DomainError {
  readonly resourceType: string | undefined;

  constructor(message: string, resourceType?: string, recoveryHint?: string) {
    super(
      message,
      'NOT_FOUND',
      recoveryHint
        ?? 'Verify the target exists. Check for typos in identifiers.',
    );
    this.name = 'NotFoundError';
    this.resourceType = resourceType;
  }
}

// ── Provider ───────────────────────────────────────────────────────

export class ProviderError extends DomainError {
  readonly provider: string;

  constructor(
    message: string,
    provider: string,
    recoveryHint?: string,
    options?: ErrorOptions,
  ) {
    super(
      message,
      'PROVIDER_ERROR',
      recoveryHint
        ?? 'The upstream provider returned an error. Check parameters and retry once.',
      options,
    );
    this.name = 'ProviderError';
    this.provider = provider;
  }
}

// ── Auth ───────────────────────────────────────────────────────────

export class AuthError extends DomainError {
  readonly reason: 'expired' | 'invalid' | 'revoked';

  constructor(
    message: string,
    reason: 'expired' | 'invalid' | 'revoked' = 'invalid',
    recoveryHint?: string,
  ) {
    super(
      message,
      'AUTH_ERROR',
      recoveryHint ?? 'Re-authenticate to obtain a fresh token.',
    );
    this.name = 'AuthError';
    this.reason = reason;
  }
}

// ── Permission ─────────────────────────────────────────────────────

export class PermissionError extends DomainError {
  readonly resourceId: string | undefined;

  constructor(message: string, resourceId?: string, recoveryHint?: string) {
    super(
      message,
      'PERMISSION_DENIED',
      recoveryHint ?? 'Check your account permissions for this resource.',
    );
    this.name = 'PermissionError';
    this.resourceId = resourceId;
  }
}

// ── Retryable base ─────────────────────────────────────────────────

export class RetryableError extends DomainError {
  readonly retryAfterMs: number | undefined;

  constructor(
    message: string,
    code: string,
    retryAfterMs?: number,
    recoveryHint?: string,
  ) {
    super(message, code, recoveryHint, { isRetryable: true });
    this.name = 'RetryableError';
    this.retryAfterMs = retryAfterMs;
  }
}

// ── Rate limit ─────────────────────────────────────────────────────

export class RateLimitError extends RetryableError {
  constructor(message: string, retryAfterMs?: number, recoveryHint?: string) {
    const hint = recoveryHint
      ?? (retryAfterMs
        ? `Rate limit exceeded. Wait ${Math.ceil(retryAfterMs / 1000)}s before retrying.`
        : 'Rate limit exceeded. Wait before retrying.');
    super(message, 'RATE_LIMITED', retryAfterMs, hint);
    this.name = 'RateLimitError';
  }
}

// ── Quota ──────────────────────────────────────────────────────────

export class QuotaExhaustedError extends RetryableError {
  readonly quotaType: string | undefined;

  constructor(
    message: string,
    quotaType?: string,
    retryAfterMs?: number,
    recoveryHint?: string,
  ) {
    super(
      message,
      'QUOTA_EXHAUSTED',
      retryAfterMs,
      recoveryHint
        ?? 'API quota exhausted. Wait for quota reset or reduce query complexity.',
    );
    this.name = 'QuotaExhaustedError';
    this.quotaType = quotaType;
  }
}

// ── Conflict ───────────────────────────────────────────────────────

export class ConflictError extends DomainError {
  readonly conflictReason: string | undefined;

  constructor(message: string, conflictReason?: string, recoveryHint?: string) {
    super(
      message,
      'CONFLICT',
      recoveryHint
        ?? 'A conflicting operation is in progress. Retry after it completes.',
    );
    this.name = 'ConflictError';
    this.conflictReason = conflictReason;
  }
}
```

Subclasses can extend further as the domain demands (e.g. a `CapabilityError` for "the MCP client cannot do sampling and this tool needs it"), but every new subclass must:

1. Set a unique stable `code` string literal.
2. Either accept or default a `recoveryHint`.
3. Either inherit `isRetryable: true` from `RetryableError` or stay at `false`.
4. Set `this.name` to the class name.
5. Get an entry in the lookup table below.

## The lookup table — `infrastructure/errors/error-contracts.ts`

The mapper is symmetric, table-driven, and easy to extend. One entry per `code`. The cite is `mcp-d4s: src/infrastructure/errors/error-contracts.ts` (in d4s the table additionally enriches the payload with `how_to_fix` / `try_instead` / `next_steps`; the new-skill version below is the simpler structural shape — extend it as your server grows).

```ts
// infrastructure/errors/error-contracts.ts
import {
  DomainError,
  ValidationError,
  NotFoundError,
  ProviderError,
  AuthError,
  PermissionError,
  RateLimitError,
  QuotaExhaustedError,
  ConflictError,
  RetryableError,
} from '../../domain/errors.js';
import type { McpToolResult } from '../../shared/types/mcp-types.js';

/**
 * MCP JSON-RPC code per domain code. The numbers track MCP-protocol
 * conventions; do not invent new ones without coordinating across
 * clients that depend on the value.
 */
export type ToolErrorCode =
  | 'VALIDATION_FAILED'
  | 'NOT_FOUND'
  | 'AUTH_REQUIRED'
  | 'ACCESS_DENIED'
  | 'RATE_LIMITED'
  | 'QUOTA_EXHAUSTED'
  | 'UPSTREAM_UNAVAILABLE'
  | 'CONFLICT'
  | 'INTERNAL_ERROR';

const JSON_RPC_CODES: Record<ToolErrorCode, number> = {
  VALIDATION_FAILED:    -32602,
  NOT_FOUND:            -32001,
  AUTH_REQUIRED:        -32002,
  ACCESS_DENIED:        -32002,
  RATE_LIMITED:         -32003,
  UPSTREAM_UNAVAILABLE: -32004,
  CONFLICT:             -32006,
  QUOTA_EXHAUSTED:      -32007,
  INTERNAL_ERROR:       -32000,
};

/** Stable map: domain `code` → wire `ToolErrorCode`. */
const DOMAIN_CODE_MAP: Record<string, ToolErrorCode> = {
  VALIDATION_ERROR:   'VALIDATION_FAILED',
  NOT_FOUND:          'NOT_FOUND',
  PROVIDER_ERROR:     'UPSTREAM_UNAVAILABLE',
  AUTH_ERROR:         'AUTH_REQUIRED',
  PERMISSION_DENIED:  'ACCESS_DENIED',
  RATE_LIMITED:       'RATE_LIMITED',
  QUOTA_EXHAUSTED:    'QUOTA_EXHAUSTED',
  CONFLICT:           'CONFLICT',
};

interface ToolErrorPayload {
  readonly code: ToolErrorCode;
  readonly jsonRpcCode: number;
  readonly message: string;
  readonly recoveryHint: string | undefined;
  readonly retryable: boolean;
  readonly retryAfterMs: number | null;
  readonly requestId: string;
}

interface MapOptions {
  readonly requestId: string;
}

const URL_PATTERN = /\b(?:https?|file|ftp):\/\/[^\s<>"'`]+/gi;
const DSN_PATTERN = /\b(?:postgres(?:ql)?|redis|rediss):\/\/[^\s<>"'`]+/gi;
const PROVIDER_NAME_PATTERN = /\bdata-?provider[a-z0-9_-]*\b/gi;

function sanitise(text: string): string {
  return text
    .replace(DSN_PATTERN, '[redacted-dsn]')
    .replace(URL_PATTERN, '[redacted-url]')
    .replace(PROVIDER_NAME_PATTERN, 'data provider');
}

function retryAfterFor(error: unknown): number | null {
  if (error instanceof RetryableError && typeof error.retryAfterMs === 'number') {
    return error.retryAfterMs;
  }
  return null;
}

export function mapErrorToPayload(
  error: unknown,
  options: MapOptions,
): ToolErrorPayload {
  if (error instanceof DomainError) {
    const wireCode = DOMAIN_CODE_MAP[error.code] ?? 'INTERNAL_ERROR';
    return {
      code: wireCode,
      jsonRpcCode: JSON_RPC_CODES[wireCode],
      message: sanitise(error.message),
      recoveryHint: error.recoveryHint
        ? sanitise(error.recoveryHint)
        : undefined,
      retryable: error.isRetryable,
      retryAfterMs: retryAfterFor(error),
      requestId: options.requestId,
    };
  }

  // Unknown error — never expose the raw message.
  return {
    code: 'INTERNAL_ERROR',
    jsonRpcCode: JSON_RPC_CODES.INTERNAL_ERROR,
    message: 'An internal error occurred. If the issue persists, contact support with the request_id.',
    recoveryHint: 'Retry the request; if the issue persists, inspect server logs with the request_id.',
    retryable: false,
    retryAfterMs: null,
    requestId: options.requestId,
  };
}

/**
 * Build the MCP `CallToolResult` envelope for an error. The boundary
 * middleware calls this once per failed tool call.
 */
export function buildErrorResult(
  error: unknown,
  options: MapOptions,
): McpToolResult {
  const payload = mapErrorToPayload(error, options);

  const sections = [`## Error\n${payload.message}`];
  if (payload.recoveryHint) {
    sections.push(`## Recovery\n- ${payload.recoveryHint}`);
  }
  sections.push(`## Request ID\n\`${payload.requestId}\``);

  return {
    content: [{ type: 'text', text: sections.join('\n\n') }],
    structuredContent: {
      isError: true,
      error: payload,
    },
    _meta: {
      errorCode: payload.code,
      requestId: payload.requestId,
      ...(payload.retryAfterMs !== null
        ? { retryAfterMs: payload.retryAfterMs }
        : {}),
    },
    isError: true,
  };
}
```

The mapper has three guarantees:

1. **Every known `DomainError.code` resolves through `DOMAIN_CODE_MAP`.** A new subclass without a map entry falls through to `INTERNAL_ERROR`, which generates a generic redacted envelope rather than leaking the raw message. That is safe-by-default; the lint-time fix is to add the entry.
2. **Unknown errors never leak `Error.message`.** The `else` branch produces the same generic envelope regardless of input. Stack frames stay in logs, never on the wire.
3. **Sanitisation runs at the wire boundary.** Even if a gateway forgot to strip a DSN, the mapper strips it again. Defence in depth.

## Wiring into the boundary middleware

The `errorBoundary` middleware (see the pipeline in `composition-root.md`) catches everything and delegates to `buildErrorResult`:

```ts
// infrastructure/middleware/error-boundary.ts
import type { Middleware, ToolHandler, ToolContext } from './types.js';
import { buildErrorResult } from '../errors/error-contracts.js';
import { getActiveRequestContext } from '../../shared/request-context.js';
import { logger } from '../observability/logger.js';

export function errorBoundary(): Middleware {
  return (next: ToolHandler): ToolHandler => {
    return async (ctx: ToolContext) => {
      try {
        return await next(ctx);
      } catch (err: unknown) {
        const requestId = getActiveRequestContext()?.requestId ?? 'req_unknown';
        logger.warn('tool_call_failed', {
          requestId,
          error: err instanceof Error ? err.name : 'unknown',
          message: err instanceof Error ? err.message : String(err),
        });
        return buildErrorResult(err, { requestId });
      }
    };
  };
}
```

The handler does not catch. The use case does not catch (except to wrap an upstream into a `DomainError`). The boundary middleware catches. One catch site, one mapping table, one envelope shape.

## Domain-event ordering — never dispatch before durable commit

A `ToolResponse` may carry next-step hints that the LLM acts on. Those hints, like any domain event, must be emitted only **after** the use case's main side effect has succeeded:

- The provider call returned without throwing.
- The persistence write committed.
- The materialisation succeeded.

Pre-commit dispatch is the canonical "two systems disagree" failure: the agent is told the export is staged, and seconds later the storage write fails or is rolled back. The use case constructs the `ToolResponse` (with `nextSteps`) only after the durable side effect commits.

## What you must verify before finishing

- [ ] `domain/errors.ts` defines the `DomainError` base with `code`, `recoveryHint`, and `isRetryable`. The `name` property is set to the class name on every subclass.
- [ ] At least these subclasses exist: `ValidationError`, `NotFoundError`, `ProviderError`, `AuthError`, `PermissionError`, `RateLimitError`, `QuotaExhaustedError`, `ConflictError`, `RetryableError`. Every one has a stable `code` literal and a default `recoveryHint`.
- [ ] `infrastructure/errors/error-contracts.ts` ships a `DOMAIN_CODE_MAP` lookup table covering every `DomainError` `code` produced anywhere in `src/`. A grep for `new [A-Z][A-Za-z]+Error\(` produces no codes that are missing from the map.
- [ ] `mapErrorToPayload` falls back to `INTERNAL_ERROR` for unknown errors and never copies `error.message` into the envelope on that path.
- [ ] The `errorBoundary` middleware is the only place in `src/` that calls `buildErrorResult`. `grep -rn "buildErrorResult" src/` returns one definition and one call site.
- [ ] Every `catch` block uses `catch (err: unknown)`. `grep -nE "catch \\(err\\)" src/ src/__tests__/` returns no hits.
- [ ] Every wrapped throw uses `{ cause: err instanceof Error ? err : undefined }` (or equivalent). Stack-trace continuity is preserved.
- [ ] The mapper sanitises URLs, DSNs, and provider names before writing the envelope. A test asserts that an upstream error containing `redis://...` produces an envelope where the substring is replaced by `[redacted-dsn]`.
- [ ] Domain events / next-step hints attached to a `ToolResponse` are constructed only after the use case's durable side effect commits. A reviewer can trace the construction site and confirm it is below the awaited write.
- [ ] No monadic-result return type appears in business-logic code. Throw / catch is the convention; mixed disciplines are forbidden.
