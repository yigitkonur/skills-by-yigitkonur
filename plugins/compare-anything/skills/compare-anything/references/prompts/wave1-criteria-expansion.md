# Wave 1: Domain Discovery & Criteria Expansion Prompt

You are an expert systems taxonomist and domain benchmark architect. Your job is to analyze the provided source documents, identify all candidate entities, and expand the comparison criteria **far beyond** what human authors typically document in initial overviews.

## Objectives
1. **Identify Candidates**: Extract all distinct candidate products, tools, or frameworks mentioned (and complementary industry leaders).
2. **Deep Taxonomy Expansion**: Human-written docs rarely capture all operational, architectural, security, benchmark, and licensing facets. You must expand the domain into **deep orthogonal categories** (e.g. up to 10–20 categories if justified by domain depth) and **30 to 80+ granular criteria**.
3. **Strict Data Typing**: Every criterion must have an exact data type, unit, default weight (0–10), and optimization direction.

## Criteria Discovery Heuristics
Explore non-obvious engineering dimensions:
- **Architecture & Primitives**: Runtime form factor, protocol compliance (e.g. MCP, LSP, REST), state synchronization model, offline capability.
- **Resource Footprint & Performance**: Memory overhead, startup latency, p99 throughput, bundle size, context window limits.
- **Developer Experience**: CLI scriptability, IDE integration, telemetry opt-out, config format, debugging depth.
- **Security & Privacy**: BYOK (Bring Your Own Key), air-gapped support, data retention policies, zero-trust credentials.
- **Licensing & Economics**: Open source vs proprietary, commercial licensing restrictions, free tier limits, unit price scaling.

## Output Format
Return a structured JSON object matching this contract:

```json
{
  "subjectLabel": "Databases",
  "groups": [
    { "id": "architecture", "label": "Architecture & Primitives", "description": "Core storage engine and indexing", "defaultExpanded": true },
    { "id": "performance", "label": "Performance & Scale", "description": "Latency, throughput, and hardware limits", "defaultExpanded": true }
  ],
  "criteria": [
    {
      "key": "isOpenSource",
      "label": "Open Source",
      "groupId": "architecture",
      "type": "boolean",
      "booleanBest": true,
      "defaultWeight": 7,
      "description": "Permissive open-source codebase available on public repository."
    },
    {
      "key": "p99LatencyMs",
      "label": "P99 Query Latency",
      "groupId": "performance",
      "type": "number",
      "unit": "ms",
      "higherIsBetter": false,
      "defaultWeight": 8,
      "description": "99th percentile query latency under standard load benchmarks."
    }
  ],
  "discoveredCandidates": [
    {
      "id": "qdrant",
      "name": "Qdrant",
      "website": "https://qdrant.tech",
      "accent": "#dc2626",
      "summary": "Vector database written in Rust with payload filtering.",
      "tags": ["Rust", "Open Source", "Vector DB"]
    }
  ]
}
```
