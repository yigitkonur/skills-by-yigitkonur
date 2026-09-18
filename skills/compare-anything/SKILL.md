---
name: compare-anything
description: Use this skill to turn any document list, tool collection, candidate set, or context into an interactive, weighted comparison matrix and executable Astro page using the high-performance canvas comparison interface. Trigger phrases include "compare these tools", "create a comparison matrix", "build a benchmark page", "compare libraries", "generate comparison table", "compare framework options", "setup comparison template".
---

# Compare Anything: Interactive Weighted Matrix Builder

Transform arbitrary document sets, product collections, architectural candidates, benchmark data, or raw context into a full-featured, hardware-accelerated HTML5 Canvas comparison matrix with user-adjustable weights, multi-rule sorting, instant filtering, side-by-side comparison dock, and rich cell evidence dialogs.

## When to use this skill

- Comparing 2 or more named candidates (tools, libraries, AI models, cloud runtimes, databases, frameworks) across multidimensional criteria.
- Converting raw documentation, articles, URLs, benchmark numbers, or research notes into a structured, executable comparison matrix.
- User requests: "compare these items", "build a matrix for X vs Y", "scaffold a benchmark comparison page", "turn this document list into a comparison interface".

## When NOT to use this skill

- Generating unstructured brainstorm lists without concrete evaluation.
- Brief 2-paragraph casual summaries where interactive weighting and empirical criteria add no value.
- Benchmarking a single product in isolation without comparative alternatives.

---

## Capabilities & Architecture (Full Feature Parity)

Every generated comparison matrix includes:
1. **60fps Virtualized HTML5 Canvas Table** (`GenericCanvasTable`):
   - Zero-lag horizontal/vertical virtual scrolling powered by `CanvasTablePainter`.
   - High-DPI Retina canvas rendering with right-edge gradient blur indicator (`CanvasScrollEdge`).
   - Keyboard accessibility: Arrow keys, Home, End, PageUp, PageDown, Enter, Space, and `Cmd+C` clipboard copying.
   - Screen-reader accessible ARIA grid behind the canvas.
2. **Interactive Weight Customization**:
   - Clicking or hovering any criterion label opens a floating weight popover with a slider (`0` to `10` in `0.5` increments).
   - Live recalculation of weighted scores and animated column re-ranking.
   - Corner "Reset Weights" button to restore defaults.
3. **Multi-Rule Drag-and-Drop Sorting** (`GenericTableToolbar`):
   - Multi-level priority sorting (e.g. 1st: Overall Score desc, 2nd: Monthly Price asc, 3rd: Open Source).
   - Drag-and-drop rule reordering powered by `@dnd-kit/core` and `@dnd-kit/sortable`.
4. **Multi-Field Categorized Filtering**:
   - Condition filters for `boolean`, `select`, and `multiselect` criteria with active filter counter badges.
5. **Floating Side-by-Side Compare Dock** (`.compare-dock`):
   - Appears fixed at the bottom when 1 or more candidates are checked.
   - Circular brand avatars with `+N` overflow counter.
   - "Hide Identical" toggle in compare mode to instantly isolate key differentiators.
   - "Clear Selection" and "Compare Selected / Exit Comparison" buttons.
6. **Deep Cell Detail Modal** (`<dialog className="canvas-table-dialog">`):
   - Clicking any cell inspects the value, secondary notes, evidence quotes, source URLs, and confidence ratings (`verified`, `vendor-claimed`, `community`, `unverified`).
   - Score contribution bar and weight multiplier breakdown.
7. **Full-Width Table Layout Toggle**:
   - Switch between standard container and edge-to-edge full width with `localStorage` persistence.

---

## Instant Context-to-Matrix Workflow

When the user supplies **ANY** context (product list, URLs, benchmark table, or research notes), immediately execute this sequence:

```
Context Ingestion  ──>  Criteria & Grouping  ──>  Evidence Population  ──>  JSON Scaffold & Validation  ──>  Hermetic Build & Live Launch
 (2–30 items)           (3–6 Groups, 10–25)        (Values + Citations)     (scripts/scaffold-matrix)         (Astro /compare/<slug>)
```

### Step 1: Ingest Candidates from Context
Extract 2 to 30 items. For each item determine:
- `id`: Kebab-case slug (e.g. `qdrant`, `milvus`, `pinecone`).
- `name`: Official display name.
- `accent`: Canonical brand hex color (e.g. `#dc2626`).
- `website`: Official canonical homepage or repository URL.
- `summary`: One-sentence executive summary.
- `tags`: Key classification tags (e.g. `["Open Source", "Rust", "Distributed"]`).

### Step 2: Formulate Criteria Groups & Metrics
Organize the comparison into **3 to 6 logical groups** (e.g. *Architecture & Licensing*, *Core Capabilities*, *Performance & Footprint*, *Developer Experience*, *Pricing*).
Define **10 to 25 orthogonal criteria**:
- `type`: `boolean`, `number`, `price`, `select`, `multiselect`, `text`, `url`, or `date`.
- `unit`: Optional unit string (`ms`, `GB`, `req/s`, `$/mo`, `%`).
- `higherIsBetter`: `true` for speed/throughput, `false` for latency/price/memory footprint.
- `defaultWeight`: `0` to `10` (default `5` to `8` for critical criteria).
- `options`: Required for `select` and `multiselect`, with optional numeric `rank`.

### Step 3: Populate Cell Values & Evidence
Populate `item.values[criterionKey]` for all candidates.
For metrics that require verification, provide structured cell evidence:
```json
{
  "value": 14.2,
  "secondary": "10M 1536-dim vectors",
  "evidence": "Measured 99th percentile query latency under 500 QPS load",
  "sourceUrl": "https://qdrant.tech/benchmarks",
  "confidence": "verified"
}
```

### Step 4: Scaffold & Validate the Matrix Dataset
Write the complete dataset to `content/matrix/<slug>.json` (or use the scaffold helper):

```bash
# Optional: scaffold a skeleton with default groups and items:
node scripts/scaffold-matrix.mjs --slug <slug> --title "<Title>" --items "Item 1, Item 2, Item 3"

# Validate schema integrity:
node scripts/validate-matrix-schema.mjs content/matrix/<slug>.json
```

The validation script ensures:
- All required keys match `ComparisonMatrixSchema`.
- All criteria reference valid group IDs.
- Hex colors and URL formats are valid.

### Step 5: Hermetic Build & Verification
Run the repository golden verification suite:

```bash
npm run build:frontend && npm run typecheck && npm run test:workshop && node scripts/workshop-validate.mjs
```

### Step 6: Expose Live Preview & Present Findings
1. Verify the route responds with HTTP 200:
   ```bash
   curl -s -L -o /dev/null -w "%{http_code}\n" http://127.0.0.1:4321/compare/<slug>/
   ```
2. If live tunnel is active, verify via the tunnel URL:
   ```bash
   curl -s -L -o /dev/null -w "%{http_code}\n" <tunnel-url>/compare/<slug>/
   ```
3. Deliver the response with:
   - Live URL to the interactive canvas table.
   - Quick executive overview table of the candidates.
   - Key differentiators identified by the matrix.
   - Recommended candidate based on specific priorities.
