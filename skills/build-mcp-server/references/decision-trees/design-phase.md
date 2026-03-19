# Designing a New MCP Server

When starting a new MCP server, the most impactful decisions happen before you write any tool code. This tree routes you through API consolidation, intent-based design, schema shape, and description strategy.

## Decision Tree

```
START: How many API endpoints does this server wrap?
|
+-- 1-3 endpoints
|   +-- Map each to one tool (1:1 is fine at small scale)
|   +-- Keep schemas flat, under 6 params --> schema-design.md
|
+-- 4-10 endpoints
|   +-- Do 3+ endpoints always get called together for one user task?
|   |   +-- YES --> Consolidate into a single intent-based tool
|   |   |         (e.g., deploy_project wraps create + config + deploy + domain)
|   |   |         --> tool-design.md
|   |   +-- NO  --> Keep separate, but design around user intents
|   |             (verb + resource, not endpoint names)
|   |             --> tool-design.md
|   +-- Are there CRUD operations across multiple entity types?
|       +-- >3 entity types --> Use combined manage_entity(action=enum) pattern
|       +-- <=3 entity types --> Keep separate CRUD tools
|       --> tool-design.md
|
+-- 10+ endpoints
|   +-- Group by user intent, not by API path
|   +-- Target <20 tools after consolidation
|   +-- See tool-count.md for progressive discovery if still >20
|
+-- For ALL tools, apply these design checks:
    +-- Schema shape: Flat, 3-6 params, no nesting >1 level --> schema-design.md
    +-- Description: First 5 words = verb + resource --> tool-descriptions.md
    +-- Description length: Under 100 tokens total --> tool-descriptions.md
    +-- Parameter names: Unambiguous, self-documenting --> schema-design.md
```

## Key Decision Factors

| Factor | Options | Recommendation |
|---|---|---|
| API-to-tool mapping | 1:1 mapping vs intent consolidation | Consolidate when 3+ calls always happen together |
| CRUD pattern | Separate tools vs combined action enum | Combine when >3 entity types to keep tool count low |
| Schema depth | Nested objects vs flat params | Always flat; split tool before nesting 2+ levels |
| Parameter count | Few vs many | Target 3-6; split tool if exceeding 15 |
| Description style | Verbose explanation vs front-loaded verb | Front-load verb+resource in first 5 words |

## When to Re-evaluate

- When you add a 4th entity type to separate CRUD tools (switch to combined pattern)
- When agent transcripts show multi-step call sequences that could be one tool
- When total tool count crosses 15 (revisit consolidation opportunities)
- When model accuracy drops on tool selection (descriptions may need tightening)
