# Search Methodology

Operating manual for search subagents. Covers hypothesis generation, search execution, and result formatting.

## Phase 1: Generate Search Hypotheses (NO subagents)

Before touching `gh`, THINK about search diversity. Generate a **MAXIMUM of 20 search hypotheses**. Each hypothesis is a different ANGLE, not a keyword synonym.

**Hypothesis angles to consider:**

| Angle | Example for "WebAssembly table processing" |
|---|---|
| Direct name | `"webassembly table" OR "wasm table"` |
| Curated lists | `awesome-wasm` OR `awesome-webassembly` |
| Language variants | `"wasm" language:Rust`, `"wasm" language:C++` |
| Framework combos | `"wasm" "react"`, `"wasm" "vue"` |
| Use-case variants | `"wasm data grid"`, `"wasm spreadsheet"` |
| Known orgs | `org:aspect-build`, `org:nicolo-ribaudo` |
| Alt terminology | `"WASM" vs "WebAssembly"` vs `"wasm-bindgen"` |
| Compound OR | `termA OR termB OR termC` (single terms only, NOT quoted phrases) |
| README search | `"topic" in:readme stars:>10` for repos with different names |
| Topic tags | `--topic=webassembly` |
| Broad sweep | `"mcp server" --sort=stars --limit=100` then filter by description |
| Generic category | Search the broader CATEGORY, not just the specific product |
| Known org/author | `--owner=BeehiveInnovations` or `user:torvalds` |
| Plugin/skill packages | `"claude plugin" OR "claude code plugin" multi-model` |
| Former/renamed projects | `"zen mcp"`, `"claude-flow"` — repos change names |

**CEILING RULES:**
- Maximum 20 hypotheses total
- Maximum 5 per angle type
- STOP generating when new hypotheses would return >=80% duplicates of existing results
- Shorter, broader queries find more. `"codex mcp"` finds 20 results. `"mcp server codex cli tool"` finds 0.
- For niche topics, 7-10 productive hypotheses often exhaust the space. Don't pad to 20.

**CRITICAL: OR operator rules (P0 — wrong usage returns 0 results):**
- OR works as BARE terms with no outer quotes: `gh search repos codex OR claude OR gemini` — WORKS
- OR INSIDE a quoted string FAILS: `gh search repos "codex OR claude"` — 0 results
- OR between QUOTED PHRASES FAILS: `"codex bridge" OR "codex wrapper"` — 0 results
- **Rule: NEVER put OR inside quotes. Always bare:** `gh search repos termA OR termB --sort=stars`
- For multi-word concepts, run SEPARATE searches

Read `search-hypothesis-thinking.md` for worked examples.

## Phase 2: Execute Searches (max 100 gh API calls)

**Standard search command:**
```bash
gh search repos "QUERY" --limit 30 --sort=stars \
  --json fullName,stargazersCount,description,language,updatedAt \
  --jq '.[] | [.fullName, (.stargazersCount|tostring), .language // "?", (.updatedAt[:10]), (.description // "" | .[:60])] | @tsv'
```

**EXECUTION RULES:**
- Maximum 100 total `gh search repos` calls
- **Pace: max 10 searches per 2 minutes** to avoid GitHub API throttling
- Always `--sort=stars` (never `--sort=updated`)
- Always `--json ... --jq ...` (never raw JSON)
- If a hypothesis returns 0 results: try unquoting, splitting OR terms, or broadening

**MANDATORY: Broad sweep hypotheses (always include 2-3):**
```bash
gh search repos "BROAD_TERM" --sort=stars --limit=100 \
  --json fullName,stargazersCount,description \
  --jq '.[] | select(.description // "" | test("KEYWORD1|KEYWORD2";"i")) | "\(.fullName) \(.stargazersCount)★ \(.description // "" | .[:60])"'
```

**Supplement with web search** (max 5 web searches):
- Always append `site:github.com` for repo discovery
- Try Reddit: `"topic" github site:reddit.com` for community-validated picks

Read `gh-search-syntax-cheatsheet.md` for qualifier reference.
Read `output-format-recipes.md` for jq patterns.

## Phase 3: Deduplicate, Rank & Output

1. Merge all results. Deduplicate by repo fullName (case-insensitive)
2. Sort by stars descending
3. **CEILING: Report a maximum of 50 candidates.**

**Output format — markdown table:**

```markdown
| # | Repo | Stars | Lang | Updated | Description |
|---|------|-------|------|---------|-------------|
| 1 | owner/name | 1234 | TS | 2026-03 | Short desc... |
```

Separate collections/meta-repos from implementations. After the table, provide:
- **Total found:** N unique repos across M searches
- **Search effectiveness:** Which hypotheses found the most unique results
- **Categories:** Group repos into 3-5 natural categories if patterns emerge

## Decision rules

- Well-known topic: fewer hypotheses (8-12), focus on sub-niches
- Niche topic: more hypotheses (15-20), broader OR queries
- <5 results after all hypotheses: the topic may not exist on GitHub. Say so honestly.
- User provides example repos: reverse-engineer better search terms from their topics/description/README
