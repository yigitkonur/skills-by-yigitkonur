# scrape_pages — Structured Content Extraction

## What It Does

Scrapes 1–50 URLs and extracts structured content using AI-powered extraction. Strips navigation, ads, footers, and boilerplate. Returns only the content you request via pipe-separated extraction targets.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `urls` | `string[]` | Yes | — | 1–50 URLs to scrape. Recommended: 3–5. |
| `what_to_extract` | `string` | No | — | Pipe-separated extraction targets. |
| `use_llm` | `bool` | No | `true` | AI extraction post-processing. Set false for raw content. |
| `timeout` | `int` | No | `30` | Timeout in seconds per URL (5–120). |
| `model` | `string` | No | `openai/gpt-oss-120b:nitro` | Extraction model. Alt: `x-ai/grok-4.1-fast` (adds web search). |

## Token Budget

Total budget: 32K tokens distributed across URLs.

| URLs | Tokens per URL | Depth |
|------|---------------|-------|
| 1 | 32,000 | Maximum extraction |
| 3 | ~10,700 | Deep extraction |
| 5 | ~6,400 | Balanced |
| 10 | ~3,200 | Summary |
| 50 | ~640 | Scan mode |

**Recommendation:** 3–5 URLs for most tasks. This gives 6–10K tokens per URL — enough for thorough extraction without losing detail.

## When to Use

- After `search_google` — to read the pages you found
- Extracting documentation, API references, configuration syntax
- Pulling pricing tables, feature matrices, comparison data
- Getting code examples from tutorials and guides
- Reading GitHub READMEs, changelogs, and release notes

## When NOT to Use

- For Reddit content — use `fetch_reddit` instead (better comment handling)
- When you need community opinions — use `search_reddit` + `fetch_reddit`
- When you already have the answer — don't scrape just to cite
- For paywalled content — scrape_pages cannot bypass auth

## Extraction Target Formulation

### The Pipe-Separated Pattern

Use `|` to separate distinct extraction targets. Each target is a category of information you want.

**Good extraction targets:**
```
"pricing tiers | free tier limits | API rate limits | auth methods | SDKs"
"breaking changes | removed APIs | migration steps | before and after code"
"benchmark results | methodology | hardware specs | versions tested"
"configuration options | default values | required fields | example configs"
```

**Bad extraction targets:**
```
"extract all information"              → Too vague, wastes tokens
"pricing"                              → Too broad, missing specifics
"everything about authentication"      → No structure
```

### Extraction Templates by Use Case

| Use Case | Extraction Template |
|----------|-------------------|
| Library README | `"features \| installation \| API examples \| requirements \| limitations"` |
| Pricing page | `"pricing tiers \| included limits \| overage costs \| free tier \| enterprise"` |
| API documentation | `"endpoints \| auth methods \| rate limits \| request format \| response format \| errors"` |
| Changelog | `"breaking changes \| new features \| deprecations \| migration steps"` |
| Benchmark article | `"results \| methodology \| hardware \| versions \| caveats"` |
| Security advisory | `"CVE ID \| CVSS score \| affected versions \| patched version \| mitigation"` |
| Tutorial | `"prerequisites \| steps \| code examples \| common errors \| expected output"` |
| GitHub Issues | `"issue description \| reproduction steps \| workarounds \| fix status"` |
| Comparison article | `"feature matrix \| pros \| cons \| use cases \| recommendation"` |
| Config reference | `"options \| defaults \| types \| required fields \| examples \| deprecated"` |

## use_llm Modes

### use_llm=true (default)

- AI processes the raw HTML/markdown and extracts only what you specified
- Strips navigation, ads, footers, cookie banners
- Returns clean, structured content
- Best for: most use cases, especially documentation and articles

### use_llm=false

- Returns mostly raw cleaned content
- Lower latency, lower cost
- Best for: debugging scraping issues, when you need raw HTML structure
- Use when: you suspect LLM extraction is losing important content

### Model Selection

- `openai/gpt-oss-120b:nitro` (default) — Best for extraction accuracy
- `x-ai/grok-4.1-fast` — Adds web search capability to extraction

## Composing with Other Tools

### Standard: search_google → scrape_pages

The most common workflow. search_google finds URLs, scrape_pages reads them.

```
1. search_google: 5-7 keywords → ~50-70 URLs
2. Review: Pick 3-5 most relevant URLs
3. scrape_pages: Extract structured content
```

### Verification: deep_research → scrape_pages

When deep_research makes claims, verify them by scraping the cited sources.

```
1. deep_research: Structured analysis
2. Identify claims that need verification
3. scrape_pages: Extract data from authoritative sources
4. Compare: deep_research claims vs scraped facts
```

### Price Comparison: search_google → scrape_pages (multiple)

```
1. search_google: "[service A] pricing", "[service B] pricing"
2. scrape_pages batch 1: Service A pricing page
   Extract: "pricing tiers | limits | overage | free tier"
3. scrape_pages batch 2: Service B pricing page
   Extract: same template
4. Compare extracted pricing data
```

## Failure Modes

| Failure | Symptoms | Fix |
|---------|----------|-----|
| Anti-bot protection | Empty or partial HTML, Cloudflare challenge | Try different URL format; use cached/CDN version |
| JavaScript-heavy SPA | Missing dynamic content | Increase `timeout` to 60–120s |
| Paywall | "Access Denied" or login form | Find alternative free source |
| Rate limiting | Timeout or 429 errors | Reduce batch size; add delays |
| Token overflow | Truncated extraction | Reduce URL count; narrow extraction targets |
| Wrong content extracted | Navigation or sidebar content | Make extraction targets more specific |

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|--------------|---------------|-----|
| Scraping 50 URLs at once | 640 tokens per URL = useless summaries | Use 3–5 URLs for meaningful extraction |
| Vague extraction targets | "get all info" wastes tokens on irrelevant content | Use specific pipe-separated targets |
| Scraping Reddit URLs | scrape_pages loses comment threading | Use fetch_reddit for Reddit content |
| Not filtering search_google results | Scraping irrelevant pages wastes budget | Review URLs before scraping |
| Scraping the same content twice | Duplicate effort | Track scraped URLs across calls |
| Using scrape_pages for known facts | Unnecessary tool call | Only scrape when you need to verify or discover |

## Advanced Patterns

### Multi-Source Fact Extraction

When you need to compare data across sources:

```
# Batch 1: Official docs
scrape_pages(
    urls=["https://docs.example.com/api/limits"],
    what_to_extract="rate limits | quotas | throttling behavior | error codes"
)

# Batch 2: Community-reported limits
scrape_pages(
    urls=["https://stackoverflow.com/questions/..."],
    what_to_extract="actual limits reported | workarounds | undocumented limits"
)
```

### Configuration Extraction

When you need exact config syntax:

```
scrape_pages(
    urls=["https://docs.example.com/configuration"],
    what_to_extract="all configuration options | types | default values | required vs optional | environment variables | example YAML"
)
```

### Changelog Scanning

When evaluating upgrade risk:

```
scrape_pages(
    urls=["https://github.com/org/repo/releases"],
    what_to_extract="breaking changes | deprecations | new features | migration steps | version numbers affected"
)
```

## Key Insight

scrape_pages is your reading tool. It transforms raw web pages into structured, relevant data. The quality of your extraction depends entirely on the specificity of your `what_to_extract` targets. Pipe-separated targets with 4–6 specific categories consistently outperform vague requests.

## Steering notes from production testing

### Pipe-separated extraction targets

**Good:** `"pricing|features|limitations|compatibility"` -- produces structured tables.
**Bad:** `"tell me about this page"` -- produces unstructured prose.

### Token budget: ~32K total

| URLs | Tokens/URL | Best for |
|---|---|---|
| 1-2 | 16K-32K | Deep single-page analysis |
| 3-5 | 6.4K-10K | Standard verification (recommended) |
| 10+ | <3.2K | Too shallow for most needs |

### Source credibility hierarchy

1. Official docs 2. Changelogs 3. GitHub Issues/PRs 4. Stack Overflow 5. Expert blogs 6. AI summaries (avoid for verification)
