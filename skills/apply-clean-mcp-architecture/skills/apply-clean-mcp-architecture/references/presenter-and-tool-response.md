# Presenter and ToolResponse

> SKILL.md's *Use case ↔ MCP tool flow* section routes here. After reading you should be able to write a `ToolResponse` builder in `domain/`, an `IMcpPresenter` port in `presenters/`, and the `McpPresenter` implementation that turns a domain response into an MCP `CallToolResult` envelope using `mcp-use`'s `mix(text(...), object(...))` helpers — including the secrets sanitisation policy, `_meta` filtering, and preview-rendering rules.

## The split between domain and wire

Two shapes, one transformation:

- **`ToolResponse`** lives in `domain/`. It is an immutable, fluent-builder value object. The use case constructs it. It carries pure data: a summary, insights, data rows, an opaque handler reference, geo scope, next steps, cost, isError, and a small `_meta` map.
- **`CallToolResult`** is the MCP wire envelope. The presenter constructs it. It carries `content`, `structuredContent`, `_meta`, `isError`. Built using `mcp-use`'s `mix(text(...), object(...))` helpers so the framework owns the wire shape.

The presenter is the only component allowed to construct `CallToolResult`. The use case is the only component allowed to construct `ToolResponse`. Crossing this line is the principal source of presenter rot — once a use case knows about `content` arrays, the use-case test starts asserting against MCP wire shape and stops asserting against the domain decision the use case actually makes.

## `ToolResponse` builder

The cite is `mcp-d4s: src/domain/tool-response/tool-response.ts`. The shape is fluent, immutable, and chainable; every method returns a new instance. The constructor is private; factories or static `create()` are how you start.

```ts
// domain/tool-response/tool-response.ts

export type ToolResponseDataRow = Readonly<Record<string, unknown>>;
export type HandlerId = string;

export interface NextStep {
  readonly tool?: string;
  readonly label: string;
  readonly description?: string;
}

export interface HandlerReference {
  readonly id: HandlerId;
  readonly totalRows: number;
}

interface ToolResponseState {
  readonly summary: string;
  readonly insights: readonly string[];
  readonly data: readonly ToolResponseDataRow[];
  readonly handlerId: HandlerReference | undefined;
  readonly nextSteps: readonly NextStep[];
  readonly cost: number;
  readonly meta: Readonly<Record<string, unknown>>;
  readonly isError: boolean;
}

const EMPTY_STATE: ToolResponseState = {
  summary: '',
  insights: [],
  data: [],
  handlerId: undefined,
  nextSteps: [],
  cost: 0,
  meta: {},
  isError: false,
};

const DEFAULT_PREVIEW_ROWS = 50;

export class ToolResponse {
  readonly #state: ToolResponseState;

  private constructor(state: ToolResponseState) {
    this.#state = state;
  }

  static create(): ToolResponse {
    return new ToolResponse(EMPTY_STATE);
  }

  withSummary(text: string): ToolResponse {
    return new ToolResponse({ ...this.#state, summary: text });
  }

  withInsights(insights: readonly string[]): ToolResponse {
    return new ToolResponse({ ...this.#state, insights: [...insights] });
  }

  withData(
    rows: ReadonlyArray<ToolResponseDataRow>,
    maxItems: number = DEFAULT_PREVIEW_ROWS,
  ): ToolResponse {
    return new ToolResponse({ ...this.#state, data: rows.slice(0, maxItems) });
  }

  withHandlerId(id: HandlerId, totalRows: number): ToolResponse {
    return new ToolResponse({
      ...this.#state,
      handlerId: { id, totalRows },
    });
  }

  withNextSteps(steps: readonly NextStep[]): ToolResponse {
    return new ToolResponse({ ...this.#state, nextSteps: steps.slice(0, 5) });
  }

  withCost(cost: number): ToolResponse {
    return new ToolResponse({ ...this.#state, cost });
  }

  withMeta(key: string, value: unknown): ToolResponse {
    return new ToolResponse({
      ...this.#state,
      meta: { ...this.#state.meta, [key]: value },
    });
  }

  withError(isError: boolean = true): ToolResponse {
    return new ToolResponse({ ...this.#state, isError });
  }

  // Read-only accessors — never mutate state.
  get summary(): string { return this.#state.summary; }
  get insights(): readonly string[] { return this.#state.insights; }
  get data(): readonly ToolResponseDataRow[] { return this.#state.data; }
  get handlerId(): HandlerReference | undefined { return this.#state.handlerId; }
  get nextSteps(): readonly NextStep[] { return this.#state.nextSteps; }
  get cost(): number { return this.#state.cost; }
  get meta(): Readonly<Record<string, unknown>> { return this.#state.meta; }
  get isError(): boolean { return this.#state.isError; }
}
```

A use case constructs one like this:

```ts
// application/<feature>/<feature>.usecase.ts
const response = ToolResponse.create()
  .withSummary(`Analysed ${target} across ${dataPoints} signals.`)
  .withInsights(insights)
  .withData(rows, /* maxItems */ 20)
  .withHandlerId(handlerId, rows.length)
  .withCost(providerResponse.cost)
  .withNextSteps([
    { tool: 'query', label: 'Filter or count this result.' },
    { tool: 'export', label: 'Download the full dataset.' },
  ]);
return response;
```

Why immutable + fluent: the use case never has to ask "did anything mutate this `response` after I returned it?" The presenter receives a frozen value; the test asserts against the same frozen value. Mutation across layer boundaries is invisible in TypeScript and a frequent source of aliasing bugs in concurrent MCP requests.

## `IMcpPresenter` port

The presenter is reached through a port — the handler depends on the port, never on the implementation. This keeps the handler test simple (mock the presenter) and lets you swap the rendering policy without touching every handler.

```ts
// presenters/presenter.port.ts
import type { McpToolResult } from '../shared/types/mcp-types.js';
import type { ToolResponse } from '../domain/tool-response/tool-response.js';

export interface IMcpPresenter {
  render(response: ToolResponse): McpToolResult;
}
```

`McpToolResult` is a local structural mirror of `CallToolResult` defined in `shared/types/mcp-types.ts`; handlers depend on the local mirror, not the SDK type, so SDK churn updates one file. Cite: `mcp-d4s: src/presenters/mcp-presenter.port.ts` and `mcp-d4s: src/shared/types/mcp-types.ts`.

## `McpPresenter` implementation

The presenter is a humble object: `ToolResponse` in, `McpToolResult` out. No business logic. No gateway calls. No conditional branches that depend on which use case produced the response. If you can't write the test as data-in / data-out, the logic does not belong here.

The composition uses `mcp-use`'s response helpers — `markdown`, `object`, `mix` — so the framework owns `content`, `structuredContent`, and `_meta` defaults. Our own `_meta` overrides spread last and win.

```ts
// presenters/mcp-presenter.ts
import { markdown, mix, object as objectResult } from 'mcp-use/server';
import type { McpToolResult } from '../shared/types/mcp-types.js';
import type { ToolResponse } from '../domain/tool-response/tool-response.js';
import type { IMcpPresenter } from './presenter.port.js';

const FORBIDDEN_META_KEYS = new Set([
  'connectionString', 'databasePath', 'downloadUrl', 'download_url',
  'objectKey', 'object_key', 'presignedUrl', 'presigned_url',
  'signedUrl', 'signed_url', 'storageKey', 'storage_key',
  'providerCacheLayer', 'providerCacheOriginalCost',
]);

const URL_PATTERN = /\b(?:https?|file|ftp):\/\/[^\s<>"'`]+/gi;
const DSN_PATTERN = /\b(?:postgres(?:ql)?|redis|rediss):\/\/[^\s<>"'`]+/gi;
const PROVIDER_NAME_PATTERN = /\bdata-?provider[a-z0-9_-]*\b/gi;

const STRUCTURED_PREVIEW_ROWS = 50;
const MARKDOWN_PREVIEW_ROWS = 20;

function sanitiseString(value: string): string {
  return value
    .replace(DSN_PATTERN, '[redacted-dsn]')
    .replace(URL_PATTERN, '[redacted-url]')
    .replace(PROVIDER_NAME_PATTERN, 'data provider');
}

function sanitiseMeta(
  meta: Readonly<Record<string, unknown>>,
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(meta)) {
    if (FORBIDDEN_META_KEYS.has(key)) continue;
    if (typeof value === 'string') {
      out[key] = sanitiseString(value);
    } else {
      out[key] = value;
    }
  }
  return out;
}

export class McpPresenter implements IMcpPresenter {
  render(response: ToolResponse): McpToolResult {
    const markdownRows = response.data.slice(0, MARKDOWN_PREVIEW_ROWS);
    const structuredRows = response.data.slice(0, STRUCTURED_PREVIEW_ROWS);

    const sections: string[] = [];
    if (response.summary) {
      const costSuffix = response.cost > 0
        ? ` (API cost: $${response.cost.toFixed(4)})`
        : '';
      sections.push(`## Summary\n${response.summary}${costSuffix}`);
    }
    if (response.insights.length > 0) {
      sections.push(
        `## Key Insights\n${response.insights.map((i) => `- ${i}`).join('\n')}`,
      );
    }
    if (markdownRows.length > 0) {
      sections.push(`## Data\n${this.#renderTsv(markdownRows)}`);
    }
    if (response.handlerId) {
      const ref = response.handlerId;
      sections.push(
        `## Full Results\nStored as handler_id \`${ref.id}\` (${ref.totalRows} total rows). `
        + 'Use `query` to filter or `export` to download the full dataset.',
      );
    }
    if (response.nextSteps.length > 0) {
      sections.push(
        `## Next Steps\n${response.nextSteps
          .map((s) => `- **${s.tool ?? 'Tip'}**: ${s.label}`)
          .join('\n')}`,
      );
    }

    const rawText = sections.join('\n\n');
    const sanitisedMeta = sanitiseMeta(response.meta);

    const structuredPayload: Record<string, unknown> = {
      summary: response.summary,
      insights: [...response.insights],
      data: [...structuredRows],
      cost: response.cost,
      preview: {
        returnedRows: structuredRows.length,
        totalRows: response.handlerId?.totalRows ?? response.data.length,
        truncated:
          (response.handlerId?.totalRows ?? response.data.length)
          > structuredRows.length,
      },
      ...(response.handlerId
        ? { handlerId: { id: response.handlerId.id, totalRows: response.handlerId.totalRows } }
        : {}),
      nextSteps: [...response.nextSteps],
    };

    // Compose via mcp-use response helpers. mix() flattens content from
    // both helpers; the structuredContent on object() is what MCP-aware
    // clients consume; the markdown body is what prose-only clients see.
    const helperEnvelope = mix(markdown(rawText), objectResult(structuredPayload));

    const meta: Record<string, unknown> = {
      mimeType: 'application/json',
      cost: response.cost,
      ...sanitisedMeta,
    };
    if (response.handlerId) {
      meta.handler_id = response.handlerId.id;
      meta.totalRows = response.handlerId.totalRows;
    }

    return {
      content: helperEnvelope.content,
      structuredContent: structuredPayload,
      _meta: { ...(helperEnvelope._meta ?? {}), ...meta },
      ...(response.isError ? { isError: true } : {}),
    };
  }

  #renderTsv(rows: ReadonlyArray<Record<string, unknown>>): string {
    if (rows.length === 0) return '';
    const columns = [...new Set(rows.flatMap((r) => Object.keys(r)))];
    const header = columns.join('\t');
    const lines = rows.map((r) =>
      columns.map((c) => this.#formatCell(r[c])).join('\t'),
    );
    return ['```tsv', header, ...lines, '```'].join('\n');
  }

  #formatCell(value: unknown): string {
    if (value === null || value === undefined) return '';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value).replace(/\t/g, ' ').replace(/\n/g, ' ');
  }
}
```

Cite: `mcp-d4s: src/presenters/mcp-presenter.ts` for the full presenter, including the deeper redaction passes, the local-database-path pattern, and the surface-parity rule.

## Secrets sanitisation policy

The presenter is the *second* line of defence — the gateway sanitises *first*, before the use case ever sees the message. The presenter sanitises again at the wire boundary as a defence-in-depth pass. Things the presenter must always strip or redact:

- **Forbidden keys in `_meta`.** Any key in `FORBIDDEN_META_KEYS` is removed before the meta is written. The set covers DSNs (`connectionString`, `databasePath`), storage internals (`objectKey`, `storageKey`, `presignedUrl`, `signedUrl`, `download_url`), and cache provenance (`providerCacheLayer`, `providerCacheOriginalCost`).
- **DSN-shaped strings anywhere.** `redis://...`, `postgres://...`, `rediss://...` — replaced with `[redacted-dsn]`.
- **URLs.** Replaced with `[redacted-url]` unless they are explicitly allow-listed (e.g. an opaque dashboard reference path that is itself a capability token under an internal route, see d4s `/v/dv_<ref>` carve-out).
- **Provider names.** "DataForSEO", "Stripe", "Twilio" — replaced with the generic category ("data provider", "payment provider").
- **Local database paths.** `*.duckdb`, `*.sqlite`, `*.db` — replaced with `[redacted-path]`.

The list grows; the rule does not. Every new internal handle (a workspace token, a session reference, a ticket id) needs an entry in the forbidden-keys allow-list and a regex pattern in the text-redaction pass. Anything that leaks into `_meta` or `structuredContent` ends up in the LLM client transcript and, often, in user logs.

## `_meta` filtering and surface parity

`_meta` is the legacy/dashboard-aware surface; `structuredContent` is what MCP-aware clients read. Keys that legacy clients read from `_meta` AND that MCP-aware clients read from `structuredContent` must appear in BOTH. Single-surface keys are fragile because MCP clients vary in which surface they read.

The transport-meta keys that surface in `_meta` (e.g. `handler_id`, `totalRows`, `dashboard_url`, `download_ref`) are split out from the rest of `meta` so they can be written explicitly. The non-transport keys go into `structuredContent.metadata`. This is the surface-parity rule, and it is exhaustively cited in `mcp-d4s: src/presenters/mcp-presenter.ts`.

## Preview rendering rules

- **Markdown / text section: ~20 rows by default.** This is what prose-only clients read; it must fit in a reasonable LLM context budget.
- **`structuredContent.data`: ~50 rows by default.** This is what MCP-aware clients render in tables.
- **Whichever is larger, the response includes a `handler_id`.** The agent uses `handler_id` with the staged `query` and `export` tools to fetch the full dataset on demand.
- **Inline dumps are forbidden.** A use case that produces 5,000 rows must persist all of them under a `handler_id` and return only the preview rows in `data`. Inline dumps blow the LLM context window and starve the rest of the conversation.
- **Format hints (`format: 'markdown' | 'csv' | 'tsv' | 'prose'`) live in `_meta` and the presenter dispatches on them.** The use case sets the hint; the presenter renders.
- **Footer text says what was truncated.** "Showing 20 of 1,234 rows. Use `query` or `export` with the handler_id to continue with the full staged result."

## What you must verify before finishing

- [ ] `ToolResponse` is in `domain/tool-response/`; it is immutable, every `with*` method returns a new instance, the constructor is private, and there is a static factory (`create()`).
- [ ] `IMcpPresenter` is in `presenters/presenter.port.ts`. Handlers depend on this port, not on the concrete `McpPresenter` class. `grep -rE "import .* McpPresenter " src/handlers/` returns no hits; only `IMcpPresenter` is imported.
- [ ] `McpPresenter` calls `mix(markdown(rawText), object(structuredPayload))` from `mcp-use/server`. The wire envelope is built through the framework helpers, not hand-rolled.
- [ ] The presenter sanitises strings (URL pattern, DSN pattern, provider-name pattern) and filters forbidden `_meta` keys before writing the envelope.
- [ ] Tests for the presenter assert that an upstream error containing a DSN, a provider name, or a signed URL produces an envelope where those substrings have been replaced.
- [ ] Markdown preview is bounded (≤ 20 rows by default); structured preview is bounded (≤ 50 rows by default); when truncation occurs, the response carries a `handler_id` for follow-up.
- [ ] The presenter contains no business logic, no gateway calls, no use-case branching. Every method's body is "shape this data into that data".
- [ ] Surface-parity keys (`handler_id`, `totalRows`, `dashboard_url`, `download_ref` if present) appear in both `_meta` and `structuredContent` so clients reading either surface converge on the same view.
