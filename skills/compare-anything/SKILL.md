---
name: compare-anything
description: Use this skill to turn any document list, tool collection, candidate set, or context into an interactive, weighted comparison matrix and executable Astro page using the high-performance canvas comparison interface. Trigger phrases include "compare these tools", "create a comparison matrix", "build a benchmark page", "compare libraries", "generate comparison table", "compare framework options", "setup comparison template".
---

# Compare Anything: Multi-Wave Autonomous Matrix Engine

Transform arbitrary document lists, technical notes, URLs, or product collections into a full-featured, hardware-accelerated HTML5 Canvas comparison matrix using a structured, anti-hallucinatory, 4-wave sub-agent steering architecture with streaming transitions, self-healing validation gates, and dynamic weighting.

## When to use this skill

- Comparing 2 to 30 named candidates (developer tools, libraries, AI models, vector databases, frameworks, cloud runtimes) across multidimensional technical criteria.
- Transforming human-written document sets into a deep, orthogonal evaluation matrix that expands far beyond initial marketing claims.
- User triggers: "compare these tools", "create a comparison matrix", "build a benchmark page", "compare libraries", "generate comparison table", "compare framework options", "setup comparison template".

---

## The 4-Wave Pipelined Steering Architecture

```
                                  [ STREAMING PIPELINE (Max 10 Concurrent Workers) ]
                               ┌────────────────────────────────────────────────────────┐
                               │ Tool 1: [Wave 2: Research] ──> [Wave 3: Verification] │
[Phase 0: Docs] ──> [Wave 1]  ──┤ Tool 2: [Wave 2: Research] ──> [Wave 3: Verification] ├──> [Wave 4: Assemble] ──> [Astro Canvas]
 (Markdown / URLs)   (Taxonomy)│ ...                                                   │      (Final Matrix)       (/compare/<slug>)
                               │ Tool N: [Wave 2: Research] ──> [Wave 3: Verification] │
                               └────────────────────────────────────────────────────────┘
```

### Core Execution Guarantees
1. **Unconstrained AI Taxonomy Expansion**: Human-written docs only highlight a subset of features. The AI must expand beyond them into up to **15–20 categories** and **30–80+ granular criteria** (primitives, performance, security, developer ergonomics, economics).
2. **Streaming / Pipelined Transitions**: No barrier synchronization between Wave 2 and Wave 3! As soon as Tool A finishes Wave 2 research and passes schema validation, immediately launch Wave 3 verification for Tool A.
3. **Concurrency Pool Cap**: Maintain a pool of **maximum 10 active parallel sub-agents** at any time to respect external rate-limits and search APIs while maximizing 80-CPU throughput.
4. **Self-Healing Validation Gates**: Scripts deterministically inspect subagent outputs. If an agent outputs invalid types or unevidenced high-confidence claims, the lead agent automatically sends targeted error feedback for an immediate retry.
5. **Anti-Hallucination & Uncertainty Tracking**: Unverified metrics are tagged `uncertainty.isUncertain = true`. Predictions carry explicit range bounds `[min, max]`. All claims with >=80% confidence require citation URLs and quotes.

---

## Step-by-Step Steering Protocol

### Phase 0: Document Ingestion
1. Read all provided documents, URLs, or markdown notes.
2. Identify the core subject label (e.g. `"Vector Databases"`, `"Agentic Coding Tools"`, `"ORM Frameworks"`).
3. Create a scratch directory for this run:
   ```bash
   mkdir -p .tmp/matrix-<slug>/tools
   ```

### Wave 1: Candidate Discovery & Taxonomy Contract
1. Synthesize candidate tools (2 to 30 items) with:
   - `id`: Unique kebab-case slug.
   - `name`: Official display name.
   - `website`: Canonical URL.
   - `accent`: Hex brand color.
   - `summary`: One-sentence overview.
   - `tags`: Key classification labels.
2. Formulate **multidimensional criteria groups** (up to 15–20 categories if justified) and **30 to 80+ criteria**:
   - `key`: Alphanumeric camelCase key.
   - `label`: Clear column/row display title.
   - `groupId`: Matching group ID.
   - `type`: `boolean`, `number`, `price`, `select`, `multiselect`, `text`, `url`, `date`.
   - `unit`: Optional unit suffix (`ms`, `tokens`, `GiB`, `$/mo`, `req/s`).
   - `higherIsBetter`: `true` or `false`.
   - `defaultWeight`: `0` to `10` (default `5`–`8`).
   - `description`: Explicit guidance for researchers on how to evaluate this criterion.
3. Save and freeze the criteria contract:
   - Write to `.tmp/matrix-<slug>/criteria-contract.json`.

### Wave 2: Pipelined Anti-Hallucination Research (Max 10 Workers)
1. For each discovered candidate tool, dispatch a research subagent using `invoke_subagent`:
   - Inject the frozen `criteria-contract.json`.
   - Apply the prompt from [`references/prompts/wave2-tool-researcher.md`](references/prompts/wave2-tool-researcher.md).
   - Instruct the agent to save output to `.tmp/matrix-<slug>/tools/<id>-research.json`.
2. **Self-Healing Validation Gate**:
   - As each agent reports completion, immediately validate:
     ```bash
     node scripts/validate-wave2-research.mjs --tool-data .tmp/matrix-<slug>/tools/<id>-research.json --criteria .tmp/matrix-<slug>/criteria-contract.json
     ```
   - **On Validation Failure**: Send the exact error messages back to the subagent using `send_message` requesting a corrected JSON.
   - **On Validation Pass**: Immediately advance this tool to Wave 3!

### Wave 3: Pipelined Verification & Ambiguity Resolution
1. Immediately upon a tool passing Wave 2, dispatch a dedicated verification subagent for that tool:
   - Apply the prompt from [`references/prompts/wave3-tool-verifier.md`](references/prompts/wave3-tool-verifier.md).
   - Tool verifier audits citations against primary GitHub repositories and official docs.
   - For ambiguous or low-confidence entries (`<0.8`), conduct targeted research via web search or research-mcp.
   - If discrepancies exist, update the value and append `verificationAudit: { status: "corrected", notes: "..." }`.
   - If genuinely unresolvable, mark `uncertainty: { isUncertain: true, reason: "..." }`.
   - Save verified tool data to `.tmp/matrix-<slug>/tools/<id>-verified.json`.
2. **Verification Gate**:
   - Run:
     ```bash
     node scripts/validate-wave3-verification.mjs --tool-data .tmp/matrix-<slug>/tools/<id>-verified.json
     ```

### Wave 4: Master Assembly & Compilation
1. When all tools complete verification, compile into the final dataset:
   - Collect all `.tmp/matrix-<slug>/tools/*-verified.json`.
   - Assemble top-level `groups`, `criteria`, `items`, and `metadata.waveStats`.
   - Write final matrix to `content/matrix/<slug>.json`.
2. Validate final matrix integrity:
   ```bash
   node scripts/validate-matrix-schema.mjs content/matrix/<slug>.json
   ```
3. Run the repository golden verification suite:
   ```bash
   npm run build:frontend && npm run typecheck && npm run test:workshop && node scripts/workshop-validate.mjs
   ```
4. Verify HTTP 200 on local port 4321 and live tunnel:
   ```bash
   curl -s -L -o /dev/null -w "%{http_code}\n" http://127.0.0.1:4321/compare/<slug>/
   ```
5. Clean up temporary directory `.tmp/matrix-<slug>/`.

---

## Schema Reference for Cell Evidence & Uncertainty

Every cell in `item.values[criterionKey]` can hold a primitive or this rich audit object:

```json
{
  "value": 14.5,
  "secondary": "10M vectors, 512 dimensions",
  "confidence": {
    "score": 0.95,
    "level": "high",
    "tier": "verified"
  },
  "prediction": {
    "isEstimate": true,
    "range": [12.0, 16.0],
    "rationale": "Measured on AWS c6i.4xlarge under 500 QPS load"
  },
  "evidence": {
    "quote": "Average p99 latency observed between 12ms and 16ms",
    "sourceUrl": "https://example.com/benchmarks",
    "verifiedAt": "2026-09-18T12:00:00Z",
    "verifierAgent": "verifier-1"
  },
  "uncertainty": {
    "isUncertain": false
  },
  "verificationAudit": {
    "status": "confirmed",
    "notes": "Verified against official benchmark repository commit history."
  }
}
```

---

## Frontend Presentation in Canvas Template

The flexible Canvas template (`GenericCanvasTable.tsx`) automatically handles:
- **Uncertainty Highlighting**: Cells with `uncertainty.isUncertain = true` receive an amber cautionary background tint (`cell.caution`).
- **Prediction Badges**: Estimated values display `(est.)` in secondary labels.
- **Deep Audit Modal**: Clicking any cell displays:
  - Visual **Confidence Meter** (0%–100% bar, High/Medium/Low trust).
  - Citation quote blockquote with verified source link.
  - **Verification Stamp** (`✓ Verified Primary Source` or `✏️ Corrected in Verification`).
  - **Uncertainty Card** highlighting ambiguity reasons and conflicting claims.
  - Dynamic weight slider and cell score contribution.
