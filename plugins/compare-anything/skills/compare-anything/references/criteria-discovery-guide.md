# Criteria Discovery & Taxonomy Guide

When comparing anything—from developer tools and database engines to cloud providers and LLM harnesses—the most critical phase is establishing **orthogonal, non-redundant criteria**.

---

## The 4-Phase Discovery Workflow

```
1. Document Ingestion  ──>  2. Feature Extraction  ──>  3. Orthogonal Clustering  ──>  4. Typed Schema Emission
   (URLs / PDFs / Docs)     (Raw capability pool)       (3–6 Groups × 10–25 Criteria)  (matrix.json)
```

### Phase 1: Ingestion & Candidate Scoping
1. Confirm the candidate set is bounded (minimum 2, optimal 3–30).
2. Gather primary source documents:
   - Official documentation & pricing pages
   - GitHub READMEs, release notes, and architecture diagrams
   - Empirical benchmark runs or test logs
   - Third-party audits or independent research papers

### Phase 2: Feature Matrix Extraction
List every distinct claim, feature, or metric mentioned across the documents into an unstructured table:
- e.g. "supports MCP", "p99 latency < 50ms", "MIT license", "costs $20/user/mo", "requires cloud signup", "local model support".

### Phase 3: Orthogonal Clustering (Expand to Domain Depth)
Consolidate the raw feature pool into **3 to 20 logical groups**, depending on domain complexity. Shallow domains (e.g. simple CLI tools) may need only 3–5 groups; deep technical domains (e.g. databases, AI platforms, cloud runtimes) justify 10–20 groups to capture architecture, performance, security, developer experience, economics, and operational dimensions. Avoid overlapping criteria. A well-designed matrix typically spans at least these core areas:

1. **General & Architecture** (Foundations)
   - Runtime, framework, open-source status, license, host environment, platforms.
2. **Core Capabilities** (Functional)
   - The specific primary tasks the entities perform (e.g. prompt caching, code completion, branch switching).
3. **Advanced / Differentiation** (Moats)
   - Cutting-edge features that separate leaders from followers (e.g. local agent loop, multi-file edits, subagents).
4. **Performance & Footprint** (Empirical)
   - Measurable, quantitative benchmarks (e.g. memory usage, latency, export duration, token throughput).
5. **Commercial & Licensing** (Operational)
   - Monthly cost, free tier limits, seats, enterprise SSO, self-hosting.

### Phase 4: Criterion Normalization
For every candidate criterion:
- Assign an unambiguous `key` (camelCase, e.g. `supportsMcp`).
- Define the correct `CriterionType` (do not default to freeform text if a boolean, enum, or number works).
- State the directionality:
  - Is higher better? (e.g. Context window: `higherIsBetter: true`)
  - Is lower better? (e.g. Monthly price, CPU usage: `higherIsBetter: false`)
- Set a sensible baseline weight (default `5` on a scale of 0–10).
