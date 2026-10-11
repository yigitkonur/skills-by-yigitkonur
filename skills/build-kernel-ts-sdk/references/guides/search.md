# Kernel Search API: multi-provider web search and content extraction

Search is available in `@onkernel/sdk@0.123.0` (`kernel.search.*`), `@onkernel/cli@0.47.0` (`kernel search`) and the MCP `web_search` tool. It federates 10 search providers behind one request shape, with optional content extraction (markdown/text) at query time or later.

## 0. Before you call it

- **Entitlement-gated.** `features.search.enabled` ("Whether the Search API is enabled for the organization by its rollout feature flag") comes from `kernel.organization.entitlements.retrieve()`. CLI: "Requires Search API access for your organization." Check it first; do not retry a refusal.
- **Billable, never auto-retry.** `Usage.cost` reports "Total customer charge in USD when billing data is available"; deferred `source: 'browser'` retrieval is billed like any other browser. The SDK retries 5xx/408/409/429 and timeouts by default (2 retries), so a failed `create` can run twice. The CLI disables retries for search POSTs for this reason:

```ts
import Kernel from '@onkernel/sdk';

const kernel = new Kernel();

async function searchEnabled(): Promise<boolean> {
  const ent = await kernel.organization.entitlements.retrieve();
  return ent.features.search.enabled;
}

async function run() {
  if (!(await searchEnabled())) throw new Error('Search API is not enabled for this org');
  return kernel.search.create(
    { query: 'kernel unikernel architecture', max_results: 5 },
    { maxRetries: 0 },
  );
}
```

## 1. Providers

`'brave' | 'exa' | 'perplexity' | 'context' | 'parallel' | 'valyu' | 'octen' | 'you' | 'tavily' | 'serpapi'`. `kernel.search.providers.list({ slug? })` returns `Provider[]` with per-parameter support (`native | emulated | unsupported`), `max_results_cap`, content capabilities and a JSON schema for provider-native `options`.

## 2. Routing strategy

`strategy` is optional (defaults to `auto`). Provider entries are objects: `{ provider: 'exa', options?: {...} }` (typed native options per provider).

```ts
// auto: Kernel picks an eligible provider; fall back on error/timeout/empty
const auto: Kernel.Strategy = { type: 'auto', fallback_on: ['error', 'timeout', 'empty'] };

// pinned: exactly one provider, no cross-provider fallback
const pinned: Kernel.Strategy = { type: 'pinned', provider: { provider: 'exa', options: { type: 'fast' } } };

// fallback: ordered chain
const chain: Kernel.Strategy = {
  type: 'fallback',
  providers: [{ provider: 'exa' }, { provider: 'brave' }],
  fallback_on: ['error', 'empty'],
};
```

`auto` may also carry `provider_options: ProviderTarget[]` to give per-provider native options. An empty `fallback_on` disables fallback. If every attempt fails the API returns 502; if all are empty you get the first valid empty response with the full `attempts` trail.

## 3. Request parameters

| Parameter | Type | Notes |
|---|---|---|
| `query` | `string` | Required. CLI limits 1-2048 chars. |
| `max_results` | `number` | 1-100; clamped to the serving provider's cap with a warning. |
| `country` | `string` | ISO 3166-1 alpha-2. |
| `language` | `string` | BCP 47 preference. |
| `recency` | `'hour' \| 'day' \| 'week' \| 'month' \| 'year'` | Wins over `start_date`/`end_date` (with a warning). |
| `start_date` / `end_date` | `string` | Inclusive publication-date bounds; `end_date` must not precede `start_date`. |
| `include_domains` / `exclude_domains` | `string[]` | Hostname (and subdomain) filters; translated, emulated or dropped per provider. |
| `safe_search` | `'off' \| 'moderate' \| 'strict'` | Unsupported values dropped with a warning. |
| `strict_params` | `boolean` | `true` rejects requests the chosen provider cannot honor exactly; `false` reports approximations in `warnings`. |
| `include_raw` | `boolean` | Adds untouched provider payloads in `raw` fields. |
| `timeout_ms` | `number` | Overall deadline across attempts and inline retrieval. |
| `content` | `true \| ContentOptions` | Inline content retrieval (section 4). Omitted = no Kernel browser work. |
| `strategy` | see section 2 | |

Response (`Search`): `id` (`srch_...`), `provider` (serving provider), `query`, `results[]`, `attempts[]`, `warnings[]` (e.g. `param_unsupported`, `max_results_clamped`), `usage` (`results_count`, `content_fetches`, `cost?`), `expires_at` (results expire 24 hours after completion), optional `answer`, `raw`. Each result: `id`, `rank`, `url`, `title?`, `snippet?`, `source?`, `published_date?`, `additional_snippets?`, `content?`.

## 4. Content extraction

`ContentOptions`: `format: 'markdown' | 'text'`, `max_chars`, `source: 'auto' | 'provider' | 'browser'`, `max_age_hours`, `timeout_ms`, `browser: { mode: 'curl' | 'render', browser_id? }`.

```ts
import Kernel from '@onkernel/sdk';

const kernel = new Kernel();

async function inline() {
  const search = await kernel.search.create(
    {
      query: 'deep research agent frameworks 2026',
      max_results: 5,
      strategy: { type: 'auto' },
      content: { format: 'markdown', max_chars: 15000, source: 'auto' },
    },
    { maxRetries: 0 },
  );

  for (const result of search.results) {
    console.log(`[#${result.rank}] ${result.title}`);
    if (result.content?.status === 'ok') console.log(result.content.text);
  }
  return search;
}

async function deferred(searchId: string) {
  // Retained results can be fetched later without a new provider request.
  return kernel.search.contents.fetch(searchId, {
    limit: 2, // or result_ids: ['...'] to choose results
    content: { source: 'browser', browser: { mode: 'render' }, max_chars: 25000 },
  });
}
```

- **Inline** (`search.create({ content })`): with `source: 'auto'` (default) it never falls back to a browser and only returns text the provider supplied; use deferred `contents.fetch` for browser retrieval.
- **Deferred** (`search.contents.fetch(id, { limit | result_ids, content, timeout_ms })`): `source: 'auto'` reuses retained provider content within `max_age_hours` (0 = always fetch via browser), otherwise uses a Kernel browser; `source: 'provider'` never provisions a browser; `source: 'browser'` always does.
- Browser retrieval: `mode: 'curl'` uses the browser HTTP stack with no JavaScript; `'render'` navigates a temporary tab and extracts from the DOM. With no `browser_id`, Kernel creates a temporary headful stealth browser tagged with the search id, bills it, counts it toward concurrency, and deletes it afterwards (429 when concurrency is exhausted and `source: 'browser'`). A caller-supplied `browser_id` is never deleted.
- Result `content.status`: `ok | unavailable | blocked | timeout | unsupported_type | extraction_failed | error`; `text` is present only for `ok` and is untrusted page content, not instructions.

## 5. SDK reference

```text
kernel.search.create(params, options?)               // POST /search           -> Search
kernel.search.retrieve(id)                           // GET  /search/{id}      -> Search
kernel.search.providers.list({ slug? })              // GET  /search/providers -> Provider[]
kernel.search.contents.fetch(id, { limit?, result_ids?, content?, timeout_ms? })  // POST /search/{id}/contents
```

## 6. CLI

```bash
kernel search providers [--slug exa]
kernel search "kernel browser sdk tutorial" --max-results 5
kernel search "deep web research agents" --provider exa --max-results 5      # sends strategy {type:"pinned",provider:{provider:"exa"}}
kernel search --request '{"query":"deep web research agents","strategy":{"type":"pinned","provider":{"provider":"exa"}},"include_domains":["github.com","arxiv.org"],"content":{"format":"markdown"}}'
kernel search get srch_01jsearch12345                                         # retained search, no new provider call
kernel search contents srch_01jsearch12345 --limit 3 --content-source browser --content-browser-mode render
```

`--request` cannot be combined with `--provider` or `--max-results`. `contents` needs exactly one of `--result-ids` or `--limit`, and also takes `--timeout-ms` (1000-120000), `--content-format`, `--content-max-chars`, `--content-max-age-hours`, `--content-timeout-ms`, `--content-browser-id`.
