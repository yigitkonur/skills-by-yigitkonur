# TypeScript Quality Bar

> SKILL.md's *TypeScript quality bar — locked, no opt-out* section routes here. This reference fixes the locked `tsconfig.json` flag list with a one-line rationale per flag, the `import type` and `verbatimModuleSyntax` discipline, branded IDs with validating constructors, local structural types in `shared/types/` that mirror MCP SDK shapes, the explicit-return-types rule, the `pickDefined()` helper for `exactOptionalPropertyTypes`, and the ESM / NodeNext / TS-version constraints. After reading it, an agent should be able to write or audit any `.ts` file in the codebase against the bar without consulting other documents.

The baseline is **TypeScript 5.4+** on **Node 20 / 22**, ESM only. Where a rule needs a higher version, the rule names the version. Nothing in this file is optional for an MCP server in this pack.

## Locked `tsconfig.json` flag list

Every TypeScript MCP server in this pack ships this exact set in `compilerOptions`. Reorder freely; remove nothing.

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "incremental": true,
    "tsBuildInfoFile": ".tsbuildinfo",
    "outDir": "dist",
    "declaration": true,
    "sourceMap": true
  }
}
```

| Flag | Why this flag is on the locked list |
|---|---|
| `target: "ES2022"` | Lowest target that gives `Error.cause`, `at()`, top-level `await`, and class field syntax — all used by the error hierarchy and the composition root. Higher targets emit features Node 20 cannot run. |
| `lib: ["ES2022"]` | Excludes `DOM`. A DOM lib lets a stray `window.fetch` or `document` reference compile in server code and crash on first request. |
| `module: "NodeNext"` | Selects the only emitter that honours Node ESM `package.json` `"exports"` and conditional imports. `mcp-use/server` resolution depends on this. |
| `moduleResolution: "NodeNext"` | Same reason as `module`. The non-NodeNext value `"node"` does not understand `"exports"`; the value forbidden for an MCP server in this pack is the one suited for browser-bundling toolchains, which mishandles ESM resolution and breaks the server at start. |
| `strict: true` | Single switch that activates `strictNullChecks`, `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `noImplicitAny`, `noImplicitThis`, `alwaysStrict`, and `useUnknownInCatchVariables`. Disabling any sub-flag silently weakens the type system across layers. |
| `noUncheckedIndexedAccess: true` | Every array index and arbitrary-key object access becomes `T \| undefined`. MCP tools index into provider response arrays and alias maps constantly; without this flag, missing-key bugs reach the wire as malformed envelopes. |
| `exactOptionalPropertyTypes: true` | Distinguishes "absent property" from "property explicitly `undefined`". A stray `{ key: undefined }` survives `JSON.stringify` and changes the JSON-RPC envelope shape; this flag makes the difference a compile error. |
| `noImplicitOverride: true` | Subclasses of `DomainError` must mark overrides with `override`. Renaming a base method silently orphans subclass overrides without it; in the error hierarchy, that means lost `recoveryHint` reaching the model. |
| `noImplicitReturns: true` | Every branch of a handler / use case / presenter must return. Discriminant switches that miss a branch otherwise emit `undefined` and the client sees a malformed response. |
| `noFallthroughCasesInSwitch: true` | Pairs with the `never`-exhaustiveness pattern (see `narrowing-and-generics.md`); blocks accidental fallthrough on tool-discriminant switches. |
| `verbatimModuleSyntax: true` | Forces `import type` for type-only imports. This is the compile-time proof that runtime dependency direction is preserved across layers. |
| `isolatedModules: true` | Each file must be transpilable in isolation. The build pipeline (`mcp-use build`, esbuild, tsx) processes files one at a time; cross-file features (`const enum`, value re-exports of types) silently break in production builds otherwise. |
| `skipLibCheck: true` | Trims seconds off typecheck against the `mcp-use` + Zod + Vitest type graph. Disable only when investigating an `@types/*` regression. |
| `forceConsistentCasingInFileNames: true` | Linux production deploys are case-sensitive; macOS dev hosts are not. A file imported as `Dataset.ts` and saved as `dataset.ts` builds locally and crashes on Railway without this. |
| `resolveJsonModule: true` | Lets the composition root import `package.json` for the server's `version` field at startup; no other layer should use this. |
| `incremental` + `tsBuildInfoFile` | Sub-second `tsc --noEmit` on warm cache. The local merge gate runs typecheck on every PR — slow gates get skipped. The `.tsbuildinfo` artefact is a build cache; do not commit it. |
| `declaration: true`, `sourceMap: true` | Stack traces must point at source positions in production logs; declarations let the test runner type-check fixtures against the real exports. |

**Banned tsconfig values** for an MCP server: any non-NodeNext-aware module resolution mode that targets browser bundling toolchains; `target` below `ES2020`; `module: "CommonJS"`; `lib` containing `"DOM"` or `"DOM.Iterable"`; `paths` aliases (NodeNext + relative `.js` imports replace them); `noEmit: true` at the root tsconfig (use a separate `tsconfig.typecheck.json` if needed).

`tsc --noEmit` runs as a separate, blocking gate. Transpile-only tools (esbuild, swc, tsx, the `mcp-use` build) strip types without checking them; without an explicit typecheck step, type errors land in production tool responses.

## `import type` and `verbatimModuleSyntax`

With `verbatimModuleSyntax: true`, every type-only import must use `import type` (or the inline `type` qualifier on a named binding). A value import that is only used in a type position is a compile error, and the rule survives every refactor.

Use a separate `import type` statement rather than mixing value and type bindings in one import. ESLint's `@typescript-eslint/consistent-type-imports` is configured with `fixStyle: 'separate-type-imports'`. Prefer:

```typescript
import { z } from 'zod';
import type { CallToolResult } from '../shared/types/mcp-types.js';
import type { IDatasetStore } from '../domain/dataset/dataset-store-port.js';
```

Why it matters in MCP context: the dependency-cruiser merge gate enforces inward-only dependencies. A type-only import that accidentally becomes a value import drags the outer-layer module into the runtime graph; on a serverless or Railway cold start, that adds latency and may pull in `mcp-use` from a domain file. `verbatimModuleSyntax` is what makes that drift a compile error rather than a review nit.

ESM has one further rule that is not enforced by tsconfig: relative imports must include the `.js` extension even though the source file ends in `.ts`. The `.ts → .js` rewrite is a build concern, not a source concern.

```typescript
import { defineTool } from './define-tool.js';            // correct
import { defineTool } from './define-tool';                // ESM resolution failure at runtime
```

There are no barrel re-export files inside `src/`. Direct file imports only — barrels inflate cold-start and cause cycles.

## Branded IDs with validating constructors

Every opaque token that crosses the MCP boundary or a port boundary is a branded type. Plain `string` lets the agent pass a session id where a dataset id was expected and the type system accepts it; brands turn that into a compile error with no runtime cost.

The minimum branded-ID pattern:

```typescript
// src/domain/dataset/dataset-id.ts

const DATASET_ID_PREFIX = 'ds_';
const DATASET_ID_BODY = /^[0-9a-f]{12}$/;

export type DatasetId = string & { readonly __brand: 'DatasetId' };

/** Mint a fresh DatasetId. The only way to obtain a brand without going through `parseDatasetId`. */
export function createDatasetId(): DatasetId {
  return `${DATASET_ID_PREFIX}${crypto.randomUUID().replace(/-/g, '').slice(0, 12)}` as DatasetId;
}

/** Validate then brand. Use this on every untrusted input that should be a DatasetId. */
export function parseDatasetId(raw: string): DatasetId {
  if (!raw.startsWith(DATASET_ID_PREFIX)) {
    throw new ValidationError({
      field: 'dataset_id',
      reason: `Expected an opaque dataset reference starting with "${DATASET_ID_PREFIX}".`,
    });
  }
  const body = raw.slice(DATASET_ID_PREFIX.length);
  if (!DATASET_ID_BODY.test(body)) {
    throw new ValidationError({
      field: 'dataset_id',
      reason: 'Dataset reference is malformed; expected 12 hex characters after the prefix.',
    });
  }
  return raw as DatasetId;
}

/** Type guard for places that already hold an `unknown` and want a non-throwing narrow. */
export function isDatasetId(value: unknown): value is DatasetId {
  return typeof value === 'string' && value.startsWith(DATASET_ID_PREFIX) && DATASET_ID_BODY.test(value.slice(DATASET_ID_PREFIX.length));
}
```

Rules that travel with the brand:

- The bare `as DatasetId` cast is private to the constructor file. Other files call `createDatasetId`, `parseDatasetId`, or `isDatasetId`. Exporting the cast would defeat the brand.
- Rehydrating a brand from Redis, a cache payload, or any external store goes through `parseDatasetId` — the format must be re-checked because cache keys can be poisoned.
- Brands belong in `domain/`. Constructors throw `ValidationError` (a `DomainError` subclass) so the handler boundary maps the failure to the MCP envelope. Never throw a bare `Error`; never return a sentinel.
- Use brands for every opaque token that leaves the boundary or moves across a port: `HandlerId`, `DatasetId`, `DashboardRef`, `RequesterUserId`, `McpSessionId`, etc.

## Local structural types mirroring SDK shapes

The handlers, presenters, and bootstrap interact with `mcp-use/server` and (transitively) `@modelcontextprotocol/sdk`. Importing those SDK types directly throughout the codebase couples every layer to SDK version churn. Instead, declare local structural types under `shared/types/` that mirror only the bits the codebase actually uses. SDK upgrades update one file.

```typescript
// src/shared/types/mcp-types.ts

/**
 * Structural mirror of the MCP CallToolResult envelope.
 * Do not import @modelcontextprotocol/sdk directly from feature code; depend on this.
 */
export interface CallToolResultContent {
  type: string;
  text?: string;
  [key: string]: unknown;
}

export interface CallToolResult {
  [key: string]: unknown;
  content: CallToolResultContent[];
  structuredContent?: Readonly<Record<string, unknown>>;
  _meta?: Readonly<Record<string, unknown>>;
  metadata?: Readonly<Record<string, unknown>>;
  isError?: boolean | undefined;
}
```

Use it like this in a presenter or handler:

```typescript
import type { CallToolResult } from '../shared/types/mcp-types.js';
```

What lives in `shared/types/`:

- `CallToolResult`, `CallToolResultContent`.
- `McpUseToolContext` mirroring the bits of the per-tool execution context the handler depends on (request id, optional auth, capability flags).
- Any other SDK shape used in more than one feature.

What does **not** live there: SDK request/response wire types that are only relevant inside `infrastructure/` (those may import from the SDK directly because that layer is allowed to). Domain entities and value objects do not go here either; they live in `domain/`.

## Explicit return types on every exported function

Every exported function in `domain/`, `application/`, `gateways/`, `handlers/`, `presenters/`, `infrastructure/`, and `shared/` carries an explicit return type annotation. Inferred return types drift across edits — a refactor inside the function silently changes the public contract — and they slow LSP responsiveness as the project grows. The discipline is independent of `isolatedDeclarations` (TS 5.5+); enforce it regardless of TS version.

```typescript
// correct
export function buildToolResponse(rows: ReadonlyArray<DatasetRow>): ToolResponse { /* … */ }

// wrong — inference silently changes the public contract on edit
export function buildToolResponse(rows: ReadonlyArray<DatasetRow>) { /* … */ }
```

The same rule covers exported async functions: the annotation is `Promise<T>`, not `T`.

## `pickDefined()` for `exactOptionalPropertyTypes`

`exactOptionalPropertyTypes` makes `{ key: undefined }` distinct from `{}`. Conditional spreads (`...(x !== undefined ? { key: x } : {})`) are correct but verbose; the codebase standardises on a `pickDefined()` helper to avoid the inconsistency between sites.

```typescript
// src/shared/utils/pick-defined.ts

export function pickDefined<
  T extends Record<string, unknown>,
  K extends keyof T & string,
>(source: T, keys: readonly K[]): { [P in K]?: Exclude<T[P], undefined> } {
  const out: Record<string, unknown> = {};
  for (const key of keys) {
    if (source[key] !== undefined) {
      out[key] = source[key];
    }
  }
  return out as { [P in K]?: Exclude<T[P], undefined> };
}
```

Use at every boundary where an object is built from optional inputs:

```typescript
const command = {
  target: args.target,
  mode: args.mode,
  ...pickDefined(args, ['offset', 'order_by', 'force_refresh']),
};
```

Pick one approach — `pickDefined` or conditional spread — per project and stick with it. Mixing styles is the source of subtle env / DTO bugs.

## Forbidden TypeScript constructs

These are non-negotiable rules 7 and 9 from the SKILL.md, restated here for completeness:

- No bare `any`. No `as any`. No `as unknown as X` double assertion. No `@ts-ignore`. No `z.any()` and no `z.unknown()` in a tool input schema (use a concrete schema).
- `@ts-expect-error` is allowed only with a one-line justification naming the constraint that forces it. The directive self-destructs when the underlying issue is fixed; `@ts-ignore` does not.
- `private` keyword on entity fields is banned in favour of `#` private fields. `private` is compile-time only and bypassable by `as any`; `#` is runtime-private and survives structured cloning and JSON round-trips.
- Numeric `enum` is banned. Use `as const` literal arrays plus `typeof X[number]` unions, or `as const satisfies T` records.
- `class`-as-data is banned. Plain DTOs are `interface`/`type` shapes plus a factory function. Reserve classes for behaviour (entities with invariants, gateways, error hierarchy).
- `Function`, bare `object`, and `{}` are banned in public signatures. Use a specific call signature or `Record<string, unknown>`.

## Verification checklist

- [ ] `tsconfig.json` matches the locked flag list above; running `tsc --noEmit` is wired as a blocking step in the merge gate.
- [ ] `grep -rn ": any\b" src/` and `grep -rn "@ts-ignore" src/` both return zero hits, or each remaining hit has a written justification.
- [ ] Every exported function in `src/domain/`, `src/application/`, `src/gateways/`, `src/handlers/`, `src/presenters/`, `src/infrastructure/`, and `src/shared/` carries an explicit return type annotation.
- [ ] Every relative import inside `src/` uses the `.js` extension and `verbatimModuleSyntax` is on; type-only imports use `import type`.
- [ ] Every opaque ID that crosses the MCP boundary is a branded type with a validating constructor and a `parse*` function; no public `as DatasetId` casts exist outside the constructor file.
- [ ] `shared/types/` contains the local structural mirrors of `CallToolResult` and `McpUseToolContext`, and no file outside `infrastructure/` imports the MCP SDK directly.
