# Narrowing and Generics

> SKILL.md's *TypeScript quality bar — locked, no opt-out* section, and rules 7 and 9 in its non-negotiable list, route here. This reference covers the narrowing patterns and generic-signature rules an MCP server needs end to end: `unknown` narrowing via Zod or structural type guards, `satisfies` for typed config records, discriminated unions with `never` exhaustiveness, generic ports named for capability, branded constructors, `as const` literal lookup tables, `import type` boundary discipline, type predicates with `is`, and the narrow case where phantom types pay back. After reading, an agent should be able to write or audit any narrowing or generic signature in `domain/`, `application/`, `gateways/`, `handlers/`, or `presenters/` without consulting other documents.

## `unknown` narrowing — never `any`

Every value whose shape is not yet proven is typed `unknown`. The two legitimate ways to narrow `unknown` to `T`:

1. **Zod schema** — for any value that arrived from an external surface (provider response, cache rehydrate, persisted blob). The schema is the proof, and a parse failure is reclassified by the gateway to `ProviderError` (or by the handler-boundary mapper to `ValidationError`).
2. **Structural type guard** with `is` — for ad-hoc shape checks where a Zod schema would be overkill (a single-field probe, a discriminator check on an in-memory union value).

Bare `as` casts are not a narrowing tool. An `as` is acceptable only when an immediately-preceding runtime guard has already proven the shape; mark the site with a `// checked` comment so the reviewer can match guard to cast. `as unknown as X` is forbidden — its presence indicates a missing brand constructor or a missing port.

### Pattern A — Zod-backed `unknown` narrowing inside a gateway

```typescript
// src/gateways/cache/redis-dataset-cache-gateway.ts
import { z } from 'zod';
import { ProviderError } from '../../domain/errors.js';

// The cached payload shape. Stored Redis values are always treated as `unknown`
// until parsed; cache poisoning and version drift make blind casts unsafe.
const CachedDatasetEnvelope = z.object({
  v: z.literal(1),
  rows: z.array(z.record(z.string(), z.unknown())),
  storedAt: z.string().datetime(),
}).strict();

export type CachedDataset = z.infer<typeof CachedDatasetEnvelope>;

export async function readCachedDataset(redis: Redis, key: string): Promise<CachedDataset | null> {
  const raw: unknown = await redis.get(key).then((s) => (s == null ? null : JSON.parse(s)));
  if (raw === null) return null;
  const parsed = CachedDatasetEnvelope.safeParse(raw);
  if (!parsed.success) {
    // Drop the poisoned entry; treat as a miss. Never throw `unknown` shapes at the model.
    throw new ProviderError('Cached dataset envelope failed schema validation; treating as miss.', 'redis', undefined, { cause: parsed.error });
  }
  return parsed.data;
}
```

The use case sees `CachedDataset | null` — a typed, post-narrowing value. The provider name and the structured cause stay inside the gateway.

### Pattern B — structural guard with `is`

A type predicate (`x is T`) is the only correct way to write a guard. Returning bare `boolean` does not narrow; subsequent code re-runs the same checks or, worse, casts blindly.

```typescript
// src/shared/utils/type-guards.ts

export function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

export function hasStringField<K extends string>(
  value: unknown,
  key: K,
): value is Record<K, string> {
  return isRecord(value) && key in value && typeof (value as Record<string, unknown>)[key] === 'string';
}
```

Three rules every guard obeys:

- Check `value !== null && typeof value === 'object'` before anything else (`in` on a primitive throws).
- Use `in` to assert the discriminating property exists; do not rely on `value.kind` directly until you have proven `kind in value`.
- The return type is `value is T`, not `boolean`. The reviewer's grep for `: boolean` followed by an `if (...)` narrowing block surfaces broken guards.

Always prefer narrowing with a guard or a Zod parse over a non-null assertion (`!`). The non-null assertion collapses to a runtime crash, which the MCP error mapper turns into a generic `internal_error`; an explicit throw lets the gateway emit a typed `DomainError` with a `recoveryHint`.

## `satisfies` for typed config records

`satisfies T` validates a literal expression against `T` **without widening** the literal types. Annotation widens; `satisfies` does not. This matters for capability catalogs, alias maps, prompt registries, route tables, and any const-shaped record where downstream code keys off literal values via `keyof typeof MAP`.

```typescript
// src/shared/capability-catalog.ts

interface CapabilityDescriptor {
  readonly title: string;
  readonly destructive: boolean;
  readonly recoveryHint: string;
}

// `as const satisfies …` gives all three properties at once:
//   - deeply readonly (the `as const`)
//   - shape-checked against CapabilityDescriptor (the `satisfies`)
//   - literal-typed keys and values (consumers can use `keyof typeof CAPABILITIES`)
export const CAPABILITIES = {
  'analyze-backlinks': {
    title: 'Analyze Backlinks',
    destructive: false,
    recoveryHint: 'Verify the target domain and retry.',
  },
  'export-dataset': {
    title: 'Export Dataset',
    destructive: false,
    recoveryHint: 'Confirm the dataset id has not expired and retry.',
  },
} as const satisfies Record<string, CapabilityDescriptor>;

// `keyof typeof CAPABILITIES` is now `'analyze-backlinks' | 'export-dataset'` —
// a literal union that drives downstream switches with `never` exhaustiveness.
export type CapabilityName = keyof typeof CAPABILITIES;
```

Annotation pitfall to avoid:

```typescript
// wrong — the Record<string, …> annotation widens keys to `string`,
// so downstream `keyof typeof` lookup gives `string`, not the literal union.
const CAPABILITIES: Record<string, CapabilityDescriptor> = { /* … */ };
```

Use `satisfies` for static config; use a generic constraint (`extends`) when the type is computed from a function argument.

## Discriminated unions with `never` exhaustiveness

Every multi-state value uses a literal discriminant — `kind`, `_tag`, `code`, `mode` — and every switch over the discriminant ends in a `default` branch that assigns to a `never`. Adding a new variant becomes a compile error at every consumer.

```typescript
// src/application/datasets/dataset-status.ts

export type DatasetStatus =
  | { readonly kind: 'pending'; readonly handlerId: string }
  | { readonly kind: 'ready'; readonly handlerId: string; readonly rowCount: number }
  | { readonly kind: 'expired'; readonly handlerId: string; readonly expiredAt: string }
  | { readonly kind: 'failed'; readonly handlerId: string; readonly reason: string };

export function describeStatus(status: DatasetStatus): string {
  switch (status.kind) {
    case 'pending':
      return `Dataset ${status.handlerId} is still materialising.`;
    case 'ready':
      return `Dataset ${status.handlerId} is ready (${status.rowCount} rows).`;
    case 'expired':
      return `Dataset ${status.handlerId} expired at ${status.expiredAt}.`;
    case 'failed':
      return `Dataset ${status.handlerId} failed: ${status.reason}.`;
    default: {
      // Adding a 5th variant without updating this switch is a compile error.
      const _exhaustive: never = status;
      throw new Error(`Unhandled dataset status: ${JSON.stringify(_exhaustive)}`);
    }
  }
}
```

Three properties:

- The discriminant is **a string literal**. Numeric discriminants accept arbitrary numbers; structural-only variants (no discriminant, narrow on field presence) do not survive serialisation through the JSON-RPC wire.
- Every variant has the **same shape of discriminant** (here, `kind`). Mixing `kind` and `_tag` across variants of the same union breaks narrowing.
- The `default` branch **must throw**. Without the throw, control reaches a state the type system has already proven cannot happen, and the next refactor reintroduces the original silent-`undefined` bug.

Discriminated unions are the standard shape for `DomainError` subclasses (`code` is the discriminant), tool-output kinds, workspace lifecycle states, and provider-result variants.

## Generic ports — name for capability, never for storage

Generic parameters earn their place by relating two parameter types or relating a parameter to the return. A single-occurrence `<T>` on a port or a use-case helper is a wrapper smell — the helper should depend on a concrete domain type instead.

The port-naming rule that travels with this:

- A port is named for the **capability** it expresses, not for what it stores. `IDatasetStore`, `IBacklinksGateway`, `INotifier` — concrete domain semantics in the name.
- A generic-parameterised port (`IRepository<T>`, `IStore<T>`) is an anti-pattern: it leaks the storage idiom into domain code, and every consumer has to translate.
- If a port genuinely benefits from generics, the parameter constrains via `extends` to a domain type, never to `unknown` or a primitive.

```typescript
// anti-pattern — generic-parameterised, capability-stripped port.
// The use case ends up importing `IRepository<Dataset>` and the storage idiom
// (Mongo, Redis, in-memory) leaks through the type into domain code.
export interface IRepository<T> {
  save(value: T): Promise<void>;
  load(id: string): Promise<T | null>;
}

// correct — capability-named, domain-aware port.
export interface IDatasetStore {
  save(dataset: Dataset, options?: { ttlMs?: number; requesterScope?: RequesterScope }): Promise<void>;
  load(id: DatasetId, requesterScope?: RequesterScope): Promise<Dataset | null>;
  describe(id: DatasetId, requesterScope?: RequesterScope): StoredDatasetInfo | null;
}
```

When generics are genuinely necessary — for example a typed-middleware composer that threads a context type — the parameter is constrained, the parameter is used in more than one position, and the call site supplies a literal so `const T` preserves the literal type:

```typescript
export function compose<TContext extends object>(
  layers: ReadonlyArray<(next: (ctx: TContext) => Promise<void>) => (ctx: TContext) => Promise<void>>,
): (ctx: TContext) => Promise<void> {
  return layers.reduceRight<(ctx: TContext) => Promise<void>>(
    (next, layer) => layer(next),
    async () => {},
  );
}
```

The same rule covers factories that build literal-shaped registries: the factory takes a `const T extends …` parameter so call-site object literals retain their string-literal types into the inferred handler type.

## Branded constructors — narrow before you brand

Brands are how the type system catches "wrong-id-in-the-right-slot" mistakes. The brand is only as strong as the constructor that mints it: a brand without a validating constructor is a comment, not a guarantee.

```typescript
// src/domain/identity/requester-user-id.ts

const REQUESTER_USER_ID = /^usr_[a-z0-9]{20,32}$/;

export type RequesterUserId = string & { readonly __brand: 'RequesterUserId' };

export function parseRequesterUserId(raw: string): RequesterUserId {
  if (!REQUESTER_USER_ID.test(raw)) {
    throw new ValidationError({
      field: 'requester_user_id',
      reason: 'Requester id is malformed; expected `usr_` followed by 20-32 lowercase alphanumerics.',
    });
  }
  return raw as RequesterUserId;
}

export function isRequesterUserId(value: unknown): value is RequesterUserId {
  return typeof value === 'string' && REQUESTER_USER_ID.test(value);
}
```

Rules:

- The bare `as RequesterUserId` cast is private to the constructor file.
- Every external surface that produces an `unknown` candidate goes through `parseRequesterUserId` (throws) or `isRequesterUserId` (predicate). Cache rehydrate, Redis read, OAuth subject claim — all three pass through the constructor before the value enters the domain.
- The constructor throws a `DomainError` subclass, not a bare `Error`. The handler-boundary mapper turns it into the MCP envelope.

See `typescript-quality-bar.md` for the full branded-ID pattern, including the `createId()` mint helper for fresh values.

## `as const` literal lookup tables

For closed sets — data types, modes, sort directions, internal status codes — the codebase uses an `as const` literal array plus a `typeof X[number]` union. Numeric `enum` is forbidden; string `enum` is dispreferred (use `as const` and brand it via `satisfies` if you want shape validation).

```typescript
const BACKLINKS_DATA_TYPES = [
  'backlinks',
  'referring_domains',
  'anchors',
  'domain_pages',
  'pages_summary',
  'competitors',
  'referring_networks',
  'ranks',
  'spam_scores',
  'new_lost_backlinks',
  'new_lost_referring_domains',
] as const;

export type BacklinksDataType = typeof BACKLINKS_DATA_TYPES[number];
```

Why this beats `enum`:

- Tree-shakes. `enum` emits a runtime object even when the only use is the type.
- Plays with `satisfies`. A registry keyed by `BacklinksDataType` typechecks at write time.
- Plays with discriminated unions. The literal members are available as discriminants without further lifting.

For a registry that needs both shape validation and immutability, combine `as const satisfies T` (see the `satisfies` section above).

## `import type` and boundary discipline

`verbatimModuleSyntax: true` makes `import type` mandatory for type-only imports across layers. The deeper rationale lives in `typescript-quality-bar.md`; the narrowing-and-generics rule that depends on it:

- Cross-layer port imports use `import type { IDatasetStore } from '…'`. Importing the port as a value drags the file into the runtime graph and changes which module gets loaded on cold start.
- Inside a single layer, value imports are fine — a `domain/` value is allowed to import another `domain/` value at runtime.
- Generic constraints reference imported types via `import type`; the constraint resolves at compile time and never participates in runtime resolution.

## Type predicates with `is`

A function whose body checks shape and whose return type is `value is T` is a *type predicate*. Predicates are how custom narrowing functions plug into the compiler; without the `is`, the function returns a `boolean` and the compiler does not narrow.

```typescript
function isToolResponse(value: unknown): value is ToolResponse {
  return value !== null
    && typeof value === 'object'
    && 'kind' in value
    && (value as { kind: unknown }).kind === 'tool_response';
}
```

Rules:

- Predicate functions live in `shared/utils/` or in the same file as the type they check.
- A predicate must check the discriminating field, not just the type's shape — otherwise the predicate "narrows" two different values that share fields (a frequent source of provenance-leak bugs).
- A predicate is preferable to a Zod schema only for **shape checks of values that are already typed somewhere in the system**. For untyped, externally-sourced values, prefer Zod.

## Phantom types — only for genuinely strict state machines

A phantom type is a type-level tag that has no runtime presence (`type Acquired<T> = T & { readonly [_state]: 'Acquired' }`). It costs cognitive load at every site that reads it; it pays back only when the state machine is genuinely strict and a wrong transition is a real production bug.

The two cases where phantom types earn their keep in this pack:

- Analytics-workspace lease lifecycle (`Acquired → Committed → Released`): a `Committed` lease must not be re-acquired, a `Released` lease must not be queried. The compiler enforces the transitions.
- Capability-token issuance: a token that has been minted but not yet stamped with a `requester_user_id` cannot be used to authenticate.

Skip phantom types for everything else. A `pending → ready → expired` dataset status is fine as a discriminated union; pushing it into phantom types makes the test code unreadable for no extra safety.

When you do use a phantom type, hide the brand symbol behind a `unique symbol` in the same module, and only expose state-changing functions that produce the next phantom variant — never expose the cast.

## What you must verify before finishing

- [ ] Every guard that narrows `unknown` returns `value is T`, never bare `boolean`; `grep -rn ": boolean " src/shared/utils/type-guards.ts` finds zero non-`is` predicates.
- [ ] Every config catalog inside `src/shared/` is built with `as const` (and, where shape validation is needed, `as const satisfies T`); no `: Record<string, X>` annotation widens a literal lookup table.
- [ ] Every `switch` over a discriminated union ends with a `default` branch that assigns the value to `const _exhaustive: never` and throws; new variants surface as compile errors at every switch site.
- [ ] Every port interface name expresses a capability (`I<Capability>Gateway` / `I<Capability>Store`); no `IRepository<T>` or `IStore<T>` ports survive in `domain/ports/`.
- [ ] Every branded type has a `parse*` constructor that throws `ValidationError` on a malformed input; the bare `as Brand` cast is private to the constructor's file.
