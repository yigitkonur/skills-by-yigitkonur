# Choosing Response Format

The format of tool responses directly impacts token consumption, model comprehension, and downstream usability. This tree routes you to the right serialization, pagination, and audience strategy for each data shape.

## Decision Tree

```
START: What shape is the response data?
|
+-- TABULAR (rows and columns, database results, list outputs)
|   +-- Do cells contain nested objects or arrays?
|   |   +-- NO  --> Use TSV (tab-separated values)
|   |   |   Headers once, no braces/quotes/commas
|   |   |   Saves 30-40% tokens vs JSON arrays
|   |   +-- YES --> Fall back to YAML or JSON
|   +-- --> tool-responses.md
|
+-- STRUCTURED (key-value, hierarchical, API response data)
|   +-- Will the response be piped into another tool as input?
|   |   +-- YES --> Use JSON (programmatic interoperability)
|   |   +-- NO  --> Default to YAML
|   |       ~30% fewer tokens than JSON (no braces, no key quotes)
|   |       Model processes both equally well
|   +-- Offer a response_format enum: yaml | json
|   +-- --> tool-responses.md
|
+-- VARIABLE SIZE (could be small or very large)
|   +-- How many items could the result contain?
|   |   +-- <100 items --> Return all, no pagination needed
|   |   +-- 100-5000 items --> Paginate with first-page-plus-summary
|   |   |   Return page 1 + total_results + has_more + hint string
|   |   |   Agent decides in one turn whether to fetch page 2
|   |   +-- 5000+ items --> Truncate with signal
|   |       Hard cap + "[...truncated -- N chars omitted. Narrow query.]"
|   +-- --> context-engineering.md
|
+-- Does the response serve different audiences?
|   +-- YES --> Use content annotations
|   |   +-- audience: ["user", "assistant"] for main results (priority 1.0)
|   |   +-- audience: ["assistant"] for debug/telemetry (priority 0.3)
|   |   +-- The model sees everything; the user sees only user-facing
|   |   +-- --> tool-responses.md
|   +-- NO  --> Single audience, no annotations needed
|
+-- Does the tool return varying detail levels?
|   +-- YES --> Add response_format enum: concise | detailed
|   |   +-- concise (default): browsing, scanning, initial discovery
|   |   |   ~72 tokens per response
|   |   +-- detailed: when agent needs IDs/metadata for follow-up calls
|   |   |   ~206 tokens per response
|   |   +-- 65% token reduction using concise as default
|   |   +-- --> tool-responses.md
|   +-- NO  --> Single format is fine
|
+-- Does the response shape need to be guaranteed?
    +-- YES --> Declare outputSchema + return structuredContent
    |   Agent knows exact shape before calling; SDK validates at runtime
    |   Always also return text content for backward compatibility
    |   --> tool-responses.md
    +-- NO  --> Text content is sufficient
```

## Key Decision Factors

| Factor | Options | Recommendation |
|---|---|---|
| Data shape | Tabular vs structured vs mixed | TSV for tables, YAML for structured, JSON for interop |
| Token efficiency | JSON vs YAML vs TSV | TSV best for tables (30-40% savings), YAML for objects (30%) |
| Result set size | Small vs large | Paginate at 100+; truncate with signal at 5000+ |
| Audience | Single vs dual (user + model) | Use content annotations when debug data helps the model |
| Detail level | Fixed vs variable | Add concise/detailed enum for 65% token savings |
| Schema guarantee | Loose vs strict | Use outputSchema when downstream tools depend on shape |

## When to Re-evaluate

- When token cost per session is high (switch more responses to TSV or YAML)
- When agents request page 2 on >50% of calls (increase default page size)
- When agents never request detailed format (make it the only format)
- When a downstream tool starts consuming the response (consider JSON or outputSchema)
- When users complain about seeing debug info (add content annotations)
