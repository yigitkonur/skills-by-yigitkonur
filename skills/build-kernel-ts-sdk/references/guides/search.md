# Kernel Search API: Multi-Provider Web Search & Content Extraction

Introduced in September 2026 across `@onkernel/sdk@0.123.0`, `@onkernel/cli@0.47.0`, and the Kernel MCP server, the Search API provides a unified web discovery and content retrieval engine for browser automation agents. It eliminates the need for managing separate accounts or rate limits across third-party search vendors.

---

## 1. Core Architecture

The Search API operates across three layers:
1. **Multi-Engine Federation**: Unifies 10 search engines under a single portable query interface.
2. **Intelligent Routing**: Dynamically directs queries based on capability matching, latency, cost, and automatic fallback on error.
3. **Integrated Content Extraction**: Retrieves clean markdown or text either at query time (inline) or lazily (deferred), backed by either provider text caches or Kernel's cloud browsers.

### Supported Providers
`'brave' | 'exa' | 'perplexity' | 'context' | 'parallel' | 'valyu' | 'octen' | 'you' | 'tavily' | 'serpapi'`

---

## 2. Routing Strategies

When submitting a search request, configure how Kernel routes the query:

- **`auto` (Recommended)**: Automatically selects the optimal provider based on parameter support, real-time availability, and latency. Supports automatic fallback:
  ```ts
  const searchConfig = {
    strategy: {
      type: 'auto',
      fallback_on: ['error', 'timeout', 'empty'],
    },
  };
  ```
- **`pinned`**: Forces execution through a specific provider (e.g. `provider: 'exa'`). Fails immediately if the provider errors or does not support requested filters.
- **`fallback`**: Attempts an ordered array of providers sequentially, moving to the next provider when conditions in `fallback_on` are met.

---

## 3. Query Parameters & Portable Filters

Kernel normalizes common search filters across all providers:

| Parameter | Type | Description |
|---|---|---|
| `query` | `string` | Search query text (required) |
| `max_results` | `number` | Maximum number of results to return (1–100, default 10) |
| `country` | `string` | 2-letter ISO country code for localized results |
| `language` | `string` | 2-letter ISO language code |
| `recency` | `'day' \| 'week' \| 'month' \| 'year'` | Time filter for recent content |
| `start_date` / `end_date` | `string` | ISO 8601 timestamps for date range filtering |
| `include_domains` | `string[]` | Restrict results to specific domains |
| `exclude_domains` | `string[]` | Exclude specific domains |
| `safe_search` | `'off' \| 'moderate' \| 'strict'` | Content safety filter |
| `strict_params` | `boolean` | If `true`, fails if chosen provider cannot honor all filters exactly |

---

## 4. Content Extraction Modes

Kernel provides rich page content extraction alongside search ranking:

### Inline Extraction (At Search Time)
Extract content directly in the search response:

```ts
import Kernel from '@onkernel/sdk';

const kernel = new Kernel();

const search = await kernel.search.create({
  query: 'deep research agent frameworks 2026',
  max_results: 5,
  strategy: { type: 'auto' },
  content: {
    format: 'markdown', // 'markdown' | 'text'
    max_chars: 15000,
    source: 'auto',     // 'auto' | 'provider' | 'browser'
  },
});

for (const result of search.results) {
  console.log(`[#${result.rank}] ${result.title}`);
  if (result.content?.status === 'ok') {
    console.log(result.content.text);
  }
}
```

### Deferred Extraction (Post-Search)
Search results are retained free of charge for **24 hours**. You can inspect results and extract content selectively for only the most relevant pages:

```ts
// 1. Run lightweight search without content extraction
const search = await kernel.search.create({
  query: 'kernel unikernel architecture',
  max_results: 10,
});

// 2. Later: Extract full rendered DOM markdown for top 2 results
const details = await kernel.search.contents.fetch(search.id, {
  limit: 2,
  content: {
    source: 'browser',
    browser: { mode: 'render' }, // uses real cloud browser DOM navigation
    max_chars: 25000,
  },
});
```

### Content Source & Browser Modes
- **`source: 'auto'`**: Uses provider text if fresh within `max_age_hours`, otherwise fetches via browser.
- **`source: 'provider'`**: Uses only the search engine's pre-indexed text cache.
- **`source: 'browser'`**: Fetches the live URL using Kernel's cloud browser infrastructure.
  - `browser.mode: 'curl'`: Ultra-fast HTTP request from within Kernel's microVM network (handles redirects, zero JS evaluation).
  - `browser.mode: 'render'`: Full headless browser DOM rendering (executes client JS, waits for layout, captures dynamic content).

---

## 5. TypeScript SDK Reference (`@onkernel/sdk@0.123.0`)

```ts
// Search resource methods on client
const id = 'srch_01jsearch12345';
await kernel.search.create(params);                         // returns APIPromise<Search>
await kernel.search.retrieve(id);                           // returns APIPromise<Search>
await kernel.search.providers.list();                       // returns APIPromise<ProviderListResponse>
await kernel.search.contents.fetch(id, params);             // returns APIPromise<ContentsAPI.Response>
```

---

## 6. CLI Reference (`@onkernel/cli@0.47.0`)

```bash
# List available search providers
kernel search providers

# Run auto-routed search
kernel search "kernel browser sdk tutorial" --max-results 5

# Run search pinned to Exa provider
kernel search "autonomous agentic browsing" --provider exa --max-results 5

# Run advanced search with domain filter and content using --request JSON
kernel search --request '{"query":"autonomous agentic browsing","strategy":{"provider":"exa"},"include_domains":["github.com","arxiv.org"],"content":{"format":"markdown"}}'

# Inspect a retained search without incurring provider billing
kernel search get srch_01jsearch12345

# Fetch deferred rendered content for specific search result
kernel search contents srch_01jsearch12345 --limit 3 --content-source browser --content-browser-mode render
```
