# Zod at the Boundary

> SKILL.md's *Zod at the handler boundary only* rule (number 6 in the non-negotiable list) routes here. This reference fixes the architectural placement of Zod in an MCP server: which file owns the schema, how `schema.parse(input)` runs at the handler edge, how `ZodError` is converted to a `ValidationError` (a `DomainError` subclass) by the handler-boundary error mapper, where shared field fragments live, and how gateway responses are narrowed back from `unknown`. Schema-authoring mechanics — field-bound recipes, refinement helpers, output-schema patterns, alias preprocessors, and `mcp-use/server` registration details — belong to `build-mcp-use-server` (`references/04-tools/`); this file does not duplicate them.

After reading, an agent should know exactly where to place a Zod schema, how parsing failures become `DomainError`s, and how to safely admit an `unknown` provider response into the application layer.

## Where Zod lives in the codebase

| File | Owns |
|---|---|
| `handlers/<feature>/<tool>.handler.ts` | The tool's input Zod schema placement (usually a `z.ZodRawShape`). The schema is inline unless reused. |
| `handlers/schemas/` | Shared Zod field fragments reused across tools (filter elements, common date strings, pagination tokens). |
| `handlers/<feature>/<tool>.handler.ts` (the handler body) | The single `schema.parse(input)` call. |
| `infrastructure/middleware/error-handlers.ts` | The error mapper that catches `ZodError` and turns it into `ValidationError` before the MCP envelope is built. |
| `infrastructure/config/runtime-config.ts` | The Zod schema that validates `process.env`. The only other place a Zod schema is allowed. |

Zod **never** lives in:

- `domain/` — domain trusts its inputs. Re-validating is wasted work and couples the layer to a parser library.
- `application/` — use cases trust their commands. They receive validated, typed input or they receive nothing.
- `gateways/` for tool-input validation or use-case command validation. Gateway-local schemas may narrow external provider responses before crossing a port; see *Gateway-response narrowing* below.
- `presenters/` — the presenter is a humble mapper; it has no validation surface.

Zod has two architectural validation seams in an MCP server: the handler boundary (tool input from the MCP wire) and the env boundary (`process.env` in `runtime-config.ts`). Gateway-local response narrowing is allowed as an adapter concern, not as a second application validation layer.

## The boundary-parse pattern

The handler is the trust boundary. It parses, and on success it hands a typed command to the use case. On failure, it throws a `ValidationError` that the error mapper converts into the MCP envelope.

The factory the codebase uses (`defineTool()` from `handlers/define-tool.ts`) wraps the raw `ZodRawShape` in `z.object(...).strict()` for registration with `mcp-use`. Inside the `execute` function, `mcp-use` has already parsed the input against that schema by the time the body runs — so the typed argument the handler receives is already `z.infer<z.ZodObject<TSchema>>`. For schemas authored explicitly inside the handler (refinement objects, secondary parses against a stricter schema, narrowing parses against a `z.discriminatedUnion`), the call shape is:

```typescript
// src/handlers/datasets/inspect-dataset.handler.ts
import { z, ZodError } from 'zod';
import { defineTool } from '../define-tool.js';
import { parseDatasetId } from '../../domain/dataset/dataset-id.js';
import { ValidationError } from '../../domain/errors.js';
import type { InspectDatasetUseCase } from '../../application/datasets/inspect-dataset.usecase.js';
import type { IMcpPresenter } from '../../presenters/mcp-presenter.port.js';

const inspectDatasetSchema = {
  dataset_id: z.string().trim().min(1).describe(
    'Opaque dataset reference returned by an analysis tool (handler_id).',
  ),
  include_schema: z.boolean().optional().describe(
    'When true, also return the column metadata for the dataset.',
  ),
};

// A secondary, stricter schema applied inside the handler. The boundary parse
// against this object surfaces a ZodError that the mapper turns into ValidationError.
const InspectDatasetCommand = z.object({
  datasetId: z.string().regex(/^ds_[0-9a-f]{12}$/),
  includeSchema: z.boolean(),
}).strict();

export function createInspectDatasetHandler(
  useCase: InspectDatasetUseCase,
  presenter: IMcpPresenter,
) {
  return defineTool({
    name: 'inspect-dataset',
    description: '<usecase>Return schema and row count for a staged dataset.</usecase>',
    annotations: { title: 'Inspect Dataset', readOnlyHint: true },
    schema: inspectDatasetSchema,
    execute: async (args) => {
      // Step 1 — schema.parse(input) at the handler boundary.
      // ZodError thrown here is caught by the error mapper and converted to ValidationError.
      const command = InspectDatasetCommand.parse({
        datasetId: args.dataset_id,
        includeSchema: args.include_schema ?? false,
      });

      // Step 2 — promote the validated string into a branded ID. The brand
      // constructor itself throws ValidationError on a malformed shape.
      const datasetId = parseDatasetId(command.datasetId);

      // Step 3 — delegate to the use case with a typed, trusted command.
      const response = await useCase.inspect({
        datasetId,
        includeSchema: command.includeSchema,
      });
      return presenter.render(response);
    },
  });
}
```

The error mapper that catches `ZodError` and converts it lives at the handler-pipeline boundary. The shape it expects is:

```typescript
// src/infrastructure/middleware/error-handlers.ts (excerpt)
import { ZodError } from 'zod';
import { ValidationError, type DomainError } from '../../domain/errors.js';

export function toDomainError(err: unknown): DomainError {
  if (err instanceof ZodError) {
    const first = err.issues[0];
    return new ValidationError({
      field: first?.path.join('.') ?? '(root)',
      reason: first?.message ?? 'Invalid input.',
      issues: err.issues.map((issue) => ({
        path: issue.path.join('.'),
        message: issue.message,
        code: issue.code,
      })),
    });
  }
  // already a DomainError? pass through.
  // anything else? wrap in a generic DomainError; the mapper logs cause chain to stderr.
  // (Full mapping: see references/error-contracts.md.)
  // ...
}
```

Three properties that this pattern guarantees:

- **No raw Zod shape escapes the MCP boundary.** The model receives a `ValidationError` envelope with `field`, `reason`, and `recoveryHint`, never an opaque Zod issue dump.
- **The use case sees a typed, trusted input.** It does not import Zod, has no `safeParse`, and never re-validates.
- **A single mapper site translates the failure once.** Every handler that throws `ZodError` (whether by the `mcp-use` registration parse or an explicit `.parse()` inside the body) produces the same envelope shape.

`schema.parse(input)` is preferred over `safeParse` at the handler boundary precisely because the throw is what activates the mapper. Reserve `safeParse` for places where partial success is part of the design — generally inside `infrastructure/` and never inside a handler body.

## Tool-specific schemas inline; shared fragments under `handlers/schemas/`

The default placement is **inline in the handler**. A schema that exists for one tool, lives next to that tool. Splitting per-tool schemas into a separate file makes drift between schema and handler likely and adds an import for no benefit.

A schema fragment is shared **only** when:

- It is consumed by two or more handlers, **and**
- It expresses a concept that is materially the same in all callers (a SERP filter element, a paginated continuation token, a `target` URL field with the same trim and length rules).

Shared fragments live in `handlers/schemas/<topic>.ts` and export typed `z.ZodTypeAny` values. They never `import` from `application/` or `domain/` other than for type-only utilities. Re-export discipline: no barrel files; the consumer imports the named export from the topic file directly.

## Schema versus runtime types — the relationship

For each tool, the schema is the single source of truth for the **handler-input** shape. Use cases work with a different shape (the **command**), and gateways work with yet another (the **request**). Five distinct types per tool is normal:

1. **Handler input** — `z.infer<z.ZodObject<TSchema>>`. Authored by the schema.
2. **Use-case command** — pure TypeScript shape under `application/<feature>/`. Often renames fields from `snake_case` (MCP wire convention) to `camelCase`.
3. **Gateway request** — pure TypeScript shape under `gateways/<provider>/`. Often a thinner subset.
4. **Gateway response** — pure TypeScript shape; the gateway's adapter returns this.
5. **Presenter row** — pure TypeScript shape under `presenters/`; what the `ToolResponse` builder consumes.

Do not infer the use-case command from `z.infer<>` and reuse it as the gateway request. Each layer's types describe what *that* layer needs; collapsing them is the most common architectural decay vector and the source of provenance leaks (cache-key fields → tool response).

The exception: when the use-case command is genuinely identical to the handler input (rare; usually only true for trivial single-arg tools), `type Command = z.infer<typeof CommandSchema>` is acceptable, and the `CommandSchema` is declared inside the handler. The use case still does not import Zod — it imports the *type alias*, not the schema.

## Boundary invariants (defer mechanics to `build-mcp-use-server`)

These architectural invariants apply to every tool input schema:

- Tool input schemas live at the handler boundary.
- Top-level handler input objects are strict.
- Boundary schemas do not use `z.any()` or `z.unknown()`.
- Use cases and domain code receive validated commands and do not revalidate.
- Shared field fragments live under `handlers/schemas/` only after two or more handlers use the same concept.

For field-level recipes, `.describe()` wording, refinement-vs-transform choice, output schemas, generated types, and exact `mcp-use/server` registration mechanics, load `build-mcp-use-server` and follow its `references/04-tools/` cluster.

## Gateway-response narrowing — `unknown` → schema → typed

The handler boundary is the inbound trust seam. The gateway boundary is the **outbound** trust seam: provider responses arrive as `unknown` (after `await response.json()` or `await sdk.call()` returning `Promise<unknown>`), and they must be narrowed before crossing the port back into the application. The narrowing tool is the same — Zod — but the schema lives **inside the gateway file**, not under `handlers/schemas/`.

```typescript
// src/gateways/dataforseo/dataforseo-backlinks-gateway.ts
import { z } from 'zod';
import { ProviderError } from '../../domain/errors.js';
import type { IBacklinksGateway, BacklinksResult } from '../../domain/ports/backlinks-gateway-port.js';

// The provider response shape we depend on. Drifts in upstream releases
// surface here as a parse failure and are reclassified to ProviderError
// before crossing the port.
const BacklinksApiResponse = z.object({
  status_code: z.number().int(),
  tasks: z.array(z.object({
    result: z.array(z.object({
      target: z.string(),
      backlinks_count: z.number().int().nonnegative(),
      referring_domains: z.number().int().nonnegative(),
    })).nullable(),
  })),
}).strict();

export class DataForSeoBacklinksGateway implements IBacklinksGateway {
  constructor(private readonly client: ProviderHttpClient) {}

  async fetchSummary(target: string): Promise<BacklinksResult> {
    const raw: unknown = await this.client.post('/v3/backlinks/summary/live', { targets: [target] });
    const parsed = BacklinksApiResponse.safeParse(raw);
    if (!parsed.success) {
      throw new ProviderError(
        'DataForSEO returned an unexpected response shape.',
        'dataforseo',
        'The provider may have rolled out a backwards-incompatible response change. Retry; if the failure persists, escalate.',
        // include cause for stack continuity, never for the model
        { cause: parsed.error } as ErrorOptions,
      );
    }
    const row = parsed.data.tasks[0]?.result?.[0];
    if (!row) {
      throw new ProviderError('DataForSEO returned no result row for the requested target.', 'dataforseo');
    }
    return {
      target: row.target,
      backlinkCount: row.backlinks_count,
      referringDomains: row.referring_domains,
    };
  }
}
```

Why this lives in the gateway, not in `shared/`:

- The shape is provider-specific. A second provider implementing the same port has its own narrowing schema.
- The `ProviderError` reclassification is part of the gateway's contract (rule 11 in SKILL.md). Pulling the schema out splits a single responsibility across files.
- The use case sees `BacklinksResult` only — a clean domain type — never the provider's response shape.

The handler-boundary schema and the gateway-response schema are separate concerns. Do not import handler schemas into a gateway, and do not import gateway response schemas into a handler.

## Verification checklist

- [ ] Every Zod schema in `src/` lives under `handlers/`, `handlers/schemas/`, `infrastructure/config/`, or inside a single gateway file. `grep -rln "from 'zod'" src/domain src/application` returns zero hits.
- [ ] Every handler's `execute` function is shaped `parse(input) → command → useCase.invoke(command) → presenter.render(response)`; no use case imports Zod.
- [ ] The error mapper catches `ZodError` and converts it to `ValidationError` at exactly one site (`infrastructure/middleware/error-handlers.ts`), and that site sets `field`, `reason`, and structured `issues`.
- [ ] Every gateway that calls an external API admits the response as `unknown`, parses it against a schema declared in the same gateway file, and reclassifies parse failures as `ProviderError` before the value crosses the port.
- [ ] No `z.any()` and no `z.unknown()` appears in any tool input schema; every field has `.describe()` and explicit bounds.
