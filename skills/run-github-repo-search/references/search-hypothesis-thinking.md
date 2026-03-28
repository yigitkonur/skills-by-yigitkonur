# Search Hypothesis Thinking

How to generate diverse, high-quality search hypotheses. Read this before Phase 1.

## The Core Idea

You are NOT doing keyword substitution. You are thinking about the SHAPE of the problem space.

For any topic, there are multiple ANGLES of discovery:
- People call the same thing by different names
- The same tool can be built in different languages
- Curated "awesome-X" lists exist for most technologies
- Specific organizations are known for building in a space
- The tool might be combined with different frameworks

Each angle becomes a search hypothesis. Each hypothesis should use OR/AND to cover as much ground as possible in a single API call.

## Worked Example 1: "MCP server for Codex CLI"

**Real results from testing (2026-03-28):**

| # | Hypothesis | Query | Results | Unique Finds |
|---|---|---|---|---|
| 1 | Broad direct | `"codex mcp" --sort=stars` | 20 | 20 |
| 2 | Server-specific | `"codex mcp server" --sort=stars` | 10 | 3 |
| 3 | Bridge/wrapper | `"codex bridge" OR "codex wrapper" --sort=stars` | 8 | 4 |
| 4 | Subagent angle | `"codex subagent" OR "codex orchestrat" --sort=stars` | 12 | 6 |
| 5 | Multi-CLI | `"codex" "claude" "mcp" --sort=stars` | 15 | 2 |
| 6 | Async angle | `"codex async" mcp --sort=stars` | 5 | 1 |
| 7 | Language: TS | `"codex mcp" language:TypeScript --sort=stars` | 10 | 0 |
| 8 | Language: Python | `"codex mcp" language:Python --sort=stars` | 10 | 1 |
| 9 | Topic-based | `"codex" --topic=mcp --sort=stars` | 10 | 2 (mostly noise) |
| 10 | README deep | `"codex" in:readme "mcp server" --sort=stars` | 8 | 1 |

**Total: ~40 unique repos from 10 hypotheses. Hypotheses 1, 3, 4 were most productive.**

**Hypotheses that FAILED (0 results):**
- `"mcp server codex cli"` — too specific
- `"codex agent mcp"` — wrong combination
- `"model context protocol codex"` — too formal
- `"codex cli mcp tool"` — too many terms

**Lesson: Shorter phrases + OR operators beat long exact phrases every time.**

## Worked Example 2: "WebAssembly for heavy table data processing"

| # | Angle | Hypothesis |
|---|---|---|
| 1 | Direct | `"webassembly table" OR "wasm table" --sort=stars` |
| 2 | Data grid | `"wasm data grid" OR "wasm spreadsheet" --sort=stars` |
| 3 | Curated lists | `awesome-wasm OR awesome-webassembly --sort=stars` |
| 4 | Rust→WASM | `"wasm" language:Rust "table" OR "grid" --sort=stars` |
| 5 | C++→WASM | `"emscripten" "table" OR "grid" --sort=stars` |
| 6 | React combos | `"wasm" "react" "table" --sort=stars` |
| 7 | Known libs | `"ag-grid wasm" OR "handsontable wasm" --sort=stars` |
| 8 | Binding layer | `"wasm-bindgen" table OR grid --sort=stars` |
| 9 | Performance angle | `"webassembly" "performance" "data" --sort=stars` |
| 10 | Alt terms | `"WASM" "csv" OR "parquet" OR "dataframe" --sort=stars` |

**Note how each hypothesis explores a DIFFERENT dimension:**
- Names: webassembly vs wasm vs emscripten
- Languages: Rust vs C++
- Frameworks: React
- Use cases: table, grid, spreadsheet, csv, parquet
- Layers: wasm-bindgen (toolchain), ag-grid (consumer lib)

## Worked Example 3: "Self-hosted Notion alternative"

| # | Angle | Hypothesis |
|---|---|---|
| 1 | Direct | `"notion alternative" OR "notion clone" --sort=stars` |
| 2 | Self-hosted | `"self-hosted" "notes" OR "wiki" OR "knowledge base" --sort=stars` |
| 3 | Curated | `awesome-selfhosted --sort=stars` |
| 4 | Product names | `"outline" OR "appflowy" OR "affine" OR "anytype" --sort=stars` |
| 5 | Block editor | `"block editor" OR "notion-like" --sort=stars` |
| 6 | Topic tags | `--topic=note-taking --topic=self-hosted --sort=stars` |

## When to STOP Generating Hypotheses

- You've covered: direct names, alternative terms, language variants, curated lists, known orgs, framework combos
- New hypotheses would return >=80% repos you've already seen
- You've hit 20 hypotheses
- The topic is narrow enough that 8-10 hypotheses exhaust the space

## The OR Operator — CRITICAL RULES

**OR only works between SINGLE TERMS, not quoted phrases.**

WORKS: `gh search repos "codex OR claude OR gemini mcp" --sort=stars`
FAILS: `gh search repos '"codex bridge" OR "codex wrapper"' --sort=stars` → 0 results

**Instead of OR-ing phrases, use separate searches or unquoted terms:**
```bash
# BAD (0 results):
gh search repos '"codex bridge" OR "codex wrapper"' --sort=stars

# GOOD (separate searches):
gh search repos "codex bridge" --sort=stars
gh search repos "codex wrapper" --sort=stars

# GOOD (unquoted, broader):
gh search repos "codex bridge wrapper mcp" --sort=stars
```

## The Broad Sweep Hypothesis — ALWAYS INCLUDE

The single most impactful improvement: **always run a broad category search sorted by stars**.

```bash
gh search repos "BROAD_CATEGORY" --sort=stars --limit=100 \
  --json fullName,stargazersCount,description \
  --jq '.[] | select(.description // "" | test("KEYWORD1|KEYWORD2";"i")) | "\(.fullName) \(.stargazersCount)★"'
```

Example: Searching for "codex mcp server" missed pal-mcp-server (11,329 stars) because its name doesn't contain "codex". But `gh search repos "mcp server" --sort=stars --limit=100` with description filter for "codex|CodexCLI" catches it immediately.

**Why this works:** High-star repos with non-obvious names are invisible to narrow keyword searches but always appear in broad category sweeps.

## The Generic Category Hypothesis

Don't just search for the specific product. Search the CATEGORY it belongs to.

| Specific (narrow) | Category (broad) |
|---|---|
| "codex mcp server" | "mcp server" (then filter) |
| "wasm table library" | "webassembly" (then filter) |
| "notion self-hosted alternative" | "self-hosted notes" (then filter) |

The best solution often isn't product-specific — it's a generic tool that happens to support your product.
