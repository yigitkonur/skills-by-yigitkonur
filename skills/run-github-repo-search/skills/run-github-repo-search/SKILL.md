---
name: run-github-repo-search
description: "Use skill if you are searching GitHub for repositories matching a technology, pattern, library, or framework using diverse search hypotheses and gh CLI."
---

# GitHub Repo Search

Discover all relevant GitHub repositories for a given topic through systematic, diverse search hypotheses executed via `gh` CLI and web search.

## Trigger boundary

**Use when:** searching for GitHub repos by topic, technology, or need
**Do NOT use when:** evaluating known repos for quality (use `run-github-repo-evaluate` instead)

## Workflow

### Phase 1: Generate Search Hypotheses (NO subagents)

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
| Plugin/skill packages | `"claude plugin" OR "claude code plugin" multi-model` — not all tools are MCP servers |
| Former/renamed projects | `"zen mcp"`, `"claude-flow"` — repos change names |

**CEILING RULES:**
- Maximum 20 hypotheses total
- Maximum 5 per angle type
- STOP generating when new hypotheses would return >=80% duplicates of existing results
- Shorter, broader queries find more. `"codex mcp"` finds 20 results. `"mcp server codex cli tool"` finds 0.
- For niche topics, 7-10 productive hypotheses often exhaust the space. Don't pad to 20.

**CRITICAL: OR operator rules (P0 — wrong usage returns 0 results):**
- OR works as BARE terms with no outer quotes: `gh search repos codex OR claude OR gemini` — WORKS
- OR INSIDE a quoted string FAILS: `gh search repos "codex OR claude"` → 0 results
- OR between QUOTED PHRASES FAILS: `"codex bridge" OR "codex wrapper"` → 0 results
- **Rule: NEVER put OR inside quotes. Always bare:** `gh search repos termA OR termB --sort=stars`
- For multi-word concepts, run SEPARATE searches: one for "codex bridge", another for "codex wrapper"
- When a hypothesis returns 0, try: unquoting, dropping terms, or splitting into multiple searches

**Anti-patterns (from real testing):**
- Multi-word exact phrases return 0: `"mcp server codex cli"` → 0 results
- OR between quoted phrases returns 0: `"codex bridge" OR "codex wrapper"` → 0 results (see above)
- `--topic=X` is too broad — finds megarepos tangentially related
- `in:readme` is noisy — add `stars:>10` to suppress megarepos: `"topic" in:readme stars:>10`
- `--sort=updated` surfaces forks and junk — **always use `--sort=stars`**

Read `references/search-hypothesis-thinking.md` for worked examples.

### Phase 2: Execute Searches (max 100 gh API calls)

For each hypothesis, run `gh search repos` with token-efficient output:

**Standard search command:**
```bash
gh search repos "QUERY" --limit 30 --sort=stars \
  --json fullName,stargazersCount,description,language,updatedAt \
  --jq '.[] | [.fullName, (.stargazersCount|tostring), .language // "?", (.updatedAt[:10]), (.description // "" | .[:60])] | @tsv'
```

**Quick enumeration (when you just need names):**
```bash
gh search repos "QUERY" --limit 30 --sort=stars \
  --json fullName,stargazersCount \
  --jq '.[] | "\(.fullName) \(.stargazersCount)★"'
```

**EXECUTION RULES:**
- Maximum 100 total `gh search repos` calls across ALL hypotheses
- **Pace: max 10 searches per 2 minutes** to avoid GitHub API throttling
- Always `--sort=stars` (never `--sort=updated`)
- Always `--json ... --jq ...` (never raw JSON — 7x token bloat)
- Track which hypothesis found which repo
- **If a hypothesis returns 0 results:** try unquoting phrases, splitting OR terms, or broadening. Don't just skip — 0 results usually means bad syntax, not no repos.

**MANDATORY: Broad sweep hypotheses (always include 2-3):**
Search the broad CATEGORY sorted by stars, then filter by description keywords. Run 2-3 sweeps with DIFFERENT category terms — a single sweep misses repos in adjacent categories:
```bash
gh search repos "BROAD_TERM_1" --sort=stars --limit=100 \
  --json fullName,stargazersCount,description \
  --jq '.[] | select(.description // "" | test("KEYWORD1|KEYWORD2";"i")) | "\(.fullName) \(.stargazersCount)★ \(.description // "" | .[:60])"'
```
Example for "self-hosted Notion alternative": sweep 1 = "block editor", sweep 2 = "self-hosted notes", sweep 3 = "collaborative wiki". Each catches different repos.

**For product-replacement searches** (finding alternatives to X): the "known product names" hypothesis often outperforms ALL other angles. Prioritize it — search each known competitor by name individually.

**Supplement with web search** (max 5 web searches):
- Always append `site:github.com` for repo discovery
- Try Reddit: `"topic" github site:reddit.com` for community-validated picks
- Use web search tools available in your environment
- Web search indexes README content better than `gh search repos` — use it as a backstop

Read `references/gh-search-syntax-cheatsheet.md` for qualifier reference.
Read `references/output-format-recipes.md` for jq patterns.

### Phase 3: Deduplicate, Rank & Output

1. Merge all results. Deduplicate by repo fullName (case-insensitive)
2. Sort by stars descending
3. **CEILING: Report a maximum of 50 candidates.** If >50 found, cut at 50th by stars. Note total found count.

**Output format — markdown table:**

```markdown
| # | Repo | Stars | Lang | Updated | Description |
|---|------|-------|------|---------|-------------|
| 1 | owner/name | 1234 | TS | 2026-03 | Short desc... |
```

**Separate collections from implementations:** If results include curated lists (awesome-X), meta-repos, or settings repos, list them in a separate "Collections/Meta" section below the main table. Only rank actual tool implementations in the primary table.

After the table, provide:
- **Total found:** N unique repos across M searches
- **Search effectiveness:** Which hypotheses found the most unique results
- **Categories:** Group repos into 3-5 natural categories if patterns emerge

## Decision rules

- If topic is well-known (React, Docker): fewer hypotheses (8-12), focus on sub-niches
- If topic is niche: more hypotheses (15-20), broader OR queries
- If <5 results after all hypotheses: the topic may not exist on GitHub. Say so honestly.
- If user provides example repos: use those to reverse-engineer better search terms (check their topics, description keywords, README content)

## Reference routing

| File | Read when |
|---|---|
| `references/search-hypothesis-thinking.md` | Starting Phase 1 — generating hypotheses |
| `references/gh-search-syntax-cheatsheet.md` | Building search queries — qualifier reference |
| `references/output-format-recipes.md` | Formatting gh output — jq patterns |
| `references/search-diversity-examples.md` | Need more angle inspiration for a specific domain |
| `references/web-search-patterns.md` | Supplementing gh search with web search |
| `references/dedup-and-rank.md` | Merging results from multiple searches |
