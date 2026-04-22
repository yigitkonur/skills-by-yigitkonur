# How to Handle Growing Tool Count

Every tool added to the prompt costs tokens and degrades model routing accuracy past a model-specific threshold. This tree helps you choose the right strategy based on your current and projected tool count.

## Decision Tree

```
START: How many tools does your server expose?
|
+-- <10 tools
|   +-- No action needed. Static tool list is fine.
|   +-- Ensure descriptions are concise (<100 tokens each)
|   +-- --> tool-descriptions.md
|
+-- 10-20 tools
|   +-- Which model will consume these tools?
|   |   +-- Gemini 1.5 Pro --> Sweet spot is ~10; consider pruning or grouping
|   |   +-- GPT-4 / 4.1    --> Sweet spot is 15-20; you are at the limit
|   |   +-- Claude 3.5 / 4  --> Sweet spot is 20-30; still safe
|   +-- Can you consolidate CRUD into action-enum patterns?
|   |   +-- YES --> Reduce 4 tools per entity to 1 --> tool-design.md
|   |   +-- NO  --> Organize with clear namespacing (prefix__tool)
|   +-- --> context-engineering.md
|
+-- 20-40 tools
|   +-- Use progressive discovery (expose only relevant tools per task)
|   +-- Option A: Tool groups -- predefine groups, expose per context
|   |   (e.g., "code-review" group = read_file, search_code, get_diff)
|   +-- Option B: Session-based unlocking -- start with 3-5 always-on
|   |   tools, unlock more as the task becomes clear
|   +-- Keep per-model limits in mind:
|   |   +-- Claude: cap active set at 30
|   |   +-- GPT-4:  cap active set at 20
|   |   +-- Gemini: cap active set at 10
|   +-- --> progressive-discovery.md, context-engineering.md
|
+-- 40-100 tools
|   +-- Use meta-tools: list_tools / describe_tools / execute_tool
|   +-- Only 3 tools in prompt regardless of catalog size
|   +-- Hierarchical prefixes for tool IDs (/domain/entity/action)
|   +-- Initial context: ~1.5-2.5k tokens (vs 40k+ for static)
|   +-- --> progressive-discovery.md
|
+-- 100+ tools
|   +-- Use semantic search with embeddings
|   +-- Single find_tools(query) meta-tool + execute_tool
|   +-- Pre-compute embeddings offline; query FAISS/Pinecone at runtime
|   +-- Best for simple single-intent queries (~1.3k initial tokens)
|   +-- For complex multi-step workflows, prefer 4-stage progressive
|   |   disclosure (discover_categories -> get_actions -> get_schema
|   |   -> execute)
|   +-- --> progressive-discovery.md
```

## Key Decision Factors

| Factor | Options | Recommendation |
|---|---|---|
| Tool count vs model limit | Static list vs dynamic discovery | Go dynamic when exceeding model sweet spot |
| Discovery pattern | Groups / meta-tools / semantic search | Groups <40, meta-tools 40-100, semantic 100+ |
| Token budget | Full schemas vs on-demand | On-demand saves 95%+ tokens at 100+ tools |
| Query complexity | Simple intent vs multi-step workflow | Semantic for simple; progressive for multi-step |
| Cache invalidation | Static at startup vs dynamic | Dynamic tool lists nuke prefix cache; use notifications |

## When to Re-evaluate

- When tool count crosses the next threshold (10, 20, 40, 100)
- When switching target models (each has different sweet spots)
- When agents start calling wrong tools or hallucinating tool names
- When initial prompt token count exceeds 40k (compress via discovery)
