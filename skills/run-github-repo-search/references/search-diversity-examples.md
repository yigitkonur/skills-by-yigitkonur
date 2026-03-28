# Search Diversity Examples

Five complete worked examples showing hypothesis generation for different domains.

## Example 1: "MCP server for Codex CLI" (niche, emerging)

Hypotheses that WORKED:
```
1. "codex mcp" --sort=stars                              → 20 results (best)
2. "codex mcp server" --sort=stars                       → 10 results
3. "codex bridge" OR "codex wrapper" --sort=stars        → 8 results, 4 unique
4. "codex subagent" OR "codex orchestrat" --sort=stars   → 12 results, 6 unique
5. "codex" "claude" "mcp" --sort=stars                   → 15 results, 2 unique
6. "codex mcp" language:TypeScript --sort=stars           → 10 results, 0 unique
7. "codex mcp" language:Python --sort=stars               → 10 results, 1 unique
```

Hypotheses that FAILED (0 results):
```
"mcp server codex cli"           → too specific
"codex agent mcp"                → wrong combo
"model context protocol codex"   → too formal
```

**Takeaway:** 7 hypotheses, ~40 unique repos. Broad + OR patterns dominated.

## Example 2: "WebAssembly table data processing" (cross-cutting)

```
1. "webassembly table" OR "wasm table" --sort=stars
2. "wasm data grid" OR "wasm spreadsheet" --sort=stars
3. awesome-wasm OR awesome-webassembly --sort=stars
4. "wasm" language:Rust "table" OR "grid" --sort=stars
5. "emscripten" "table" OR "grid" --sort=stars
6. "wasm" "react" "table" --sort=stars
7. "ag-grid wasm" OR "handsontable wasm" --sort=stars
8. "wasm-bindgen" table OR grid --sort=stars
9. "WASM" "csv" OR "parquet" OR "dataframe" --sort=stars
```

**Dimensions explored:** naming (wasm/webassembly/emscripten), languages (Rust/C++), frameworks (React), use-cases (table/grid/spreadsheet/csv/parquet), toolchain (wasm-bindgen)

## Example 3: "Self-hosted Notion alternative" (product replacement)

```
1. "notion alternative" OR "notion clone" --sort=stars
2. "self-hosted" "notes" OR "wiki" OR "knowledge base" --sort=stars
3. awesome-selfhosted --sort=stars
4. "outline" OR "appflowy" OR "affine" OR "anytype" --sort=stars
5. "block editor" OR "notion-like" --sort=stars
6. "self-hosted" "workspace" OR "collaboration" --sort=stars
```

**Key angle:** Search by known product names (hypothesis 4) often finds more than generic terms.

## Example 4: "Rust HTTP framework" (well-known, saturated space)

```
1. "http framework" language:Rust --sort=stars
2. "web framework" language:Rust --sort=stars
3. "actix" OR "axum" OR "rocket" OR "warp" --sort=stars
4. awesome-rust "http" OR "web" --sort=stars
5. "rest api" language:Rust --sort=stars
```

**Takeaway:** For saturated spaces, fewer hypotheses (5-8). Focus on known names + curated lists.

## Example 5: "AI code review bot" (emerging, many synonyms)

```
1. "code review" "ai" OR "llm" OR "gpt" --sort=stars
2. "code review bot" OR "code review agent" --sort=stars
3. "coderabbit" OR "greptile" OR "codex review" --sort=stars
4. "pr review" "ai" OR "automated" --sort=stars
5. "pull request" "review" "bot" --sort=stars
6. "static analysis" "llm" OR "ai" --sort=stars
7. "code review" --topic=artificial-intelligence --sort=stars
8. "code review" language:TypeScript stars:>50 --sort=stars
9. "code review" language:Python stars:>50 --sort=stars
```

**Key angles:** synonyms (code review/pr review/pull request review), known products, AI terms (ai/llm/gpt), modality (bot/agent/automated)
