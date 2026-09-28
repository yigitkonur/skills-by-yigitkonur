# TC-BH-08: Entity Hierarchy DAG Cycle Quarantine and Edge Sanitization

## 1. Case ID and Purpose
- **Case ID:** `TC-BH-08`
- **Purpose:** Verify that the entity hierarchy graph builder (`assets/entity-graph.js`) detects cyclic back-edges via `detectCycles()`, partitions them into a quarantined edge list via `sanitizeHierarchyDAG()`, and displays a quarantine alert banner while preserving acyclic edges without crashing the rendering engine.
- **Target Result Directory:** `01-brand-hub-ground-truth/08-gherkin-result-case-entity-graph-cycle-quarantine/`

---

## 2. Tester Brief
Corporate entity structures (parent companies, brands, subsidiaries, product divisions) are modeled as a Directed Acyclic Graph (DAG).
1. Accidental circular parent-child assignments (e.g. Acme Holdings -> Brand X -> Subsidiary Y -> Acme Holdings) create infinite loops in graph traversals.
2. `ZeoEntityGraph.detectCycles(hierarchy)` executes depth-first traversal to identify all back-edges.
3. `ZeoEntityGraph.sanitizeHierarchyDAG(hierarchy)` partitions the input into `{ clean: [...], quarantined: [...] }`.
4. The visualizer renders clean edges in the tree and displays a prominent warning box for quarantined edges.
5. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Target Subsystem:** `assets/entity-graph.js` & `assets/entity-analytics.js`.
- **Target Route:** `[APP_URL]/#/[SLUG]/kb` -> Subtab `entities` (or Visualizer).
- **Fixtures & Placeholders:**
  - Cyclic Edge Fixture:
    - Node A: `ent_corp_a` -> Parent: `ent_corp_b`
    - Node B: `ent_corp_b` -> Parent: `ent_corp_c`
    - Node C: `ent_corp_c` -> Parent: `ent_corp_a` (Circular loop)

---

## 4. Gherkin Scenario

```gherkin
Feature: Entity Hierarchy DAG Cycle Quarantine

  Scenario: Cyclic back-edge detection and quarantine partitioning
    Given the test user is inspecting the Entity Hierarchy Visualizer
    When a circular parent-child relationship is introduced in the entity edge list
    Then the DAG cycle detector "detectCycles" should identify the circular back-edge
    And the edge sanitizer "sanitizeHierarchyDAG" should partition the cyclic edge into quarantine
    And the clean edge list should remain strictly acyclic
    And the UI should display the cyclic warning box ".entity-dag-visualizer .quarantine-alert"

    Examples:
      | CycleChain              | QuarantinedCount | CleanCount |
      | ent_a -> ent_b -> ent_a | 1                | 1          |
```

---

## 5. Visual Checks
- **Visualizer Elements:**
  - Visualizer Container: `.entity-dag-visualizer`.
  - Quarantine Box: `.entity-dag-visualizer .quarantine-alert` or `.alert.warning`.
  - Tree Nodes: Root Brands indicated with `🏛️` prefix and `.badge` `Root Brand`.
  - Subsidiary Nodes: Indicated with `↳` prefix.
- **Screenshot Points:**
  - `01_dag_acyclic_tree.png` (Clean hierarchy tree rendering).
  - `02_dag_quarantine_alert.png` (Quarantined cyclic edge warning banner).

---

## 6. Data and Network Checks
- **Algorithmic Assertions (`assets/entity-graph.js`):**
  ```js
  const cycles = window.ZeoEntityGraph.detectCycles(cyclicHierarchy);
  assert(cycles.length === 1);
  assert(cycles[0].cycle.includes("ent_corp_a"));

  const sanitized = window.ZeoEntityGraph.sanitizeHierarchyDAG(cyclicHierarchy);
  assert(sanitized.quarantined.length === 1);
  assert(sanitized.clean.length === 2);
  ```

---

## 7. Evidence and Reporting
- **Result Directory:** `01-brand-hub-ground-truth/08-gherkin-result-case-entity-graph-cycle-quarantine/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-bh-dag-cycles');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/kb', { wait: true, timeout: 30 });
await wait(2);

const dagAssertion = await js(String.raw`(() => {
  if (!window.ZeoEntityGraph) return { error: "ZeoEntityGraph not mounted" };
  const graph = window.ZeoEntityGraph;

  const cyclicEdges = [
    { childEntityId: "brand_alpha", parentEntityId: "brand_beta" },
    { childEntityId: "brand_beta", parentEntityId: "brand_gamma" },
    { childEntityId: "brand_gamma", parentEntityId: "brand_alpha" }
  ];

  const detected = graph.detectCycles(cyclicEdges);
  const sanitized = graph.sanitizeHierarchyDAG(cyclicEdges);

  return {
    detectedCount: detected.length,
    quarantinedCount: sanitized.quarantined.length,
    cleanCount: sanitized.clean.length,
    cycleNodes: detected[0] ? detected[0].cycle : []
  };
})()`);

cliLog('DAG Cycle Test Result: ' + JSON.stringify(dagAssertion));
if (dagAssertion.detectedCount !== 1 || dagAssertion.quarantinedCount !== 1) {
  throw new Error('Entity DAG failed to detect or quarantine cyclic back-edges');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-bh-dag-cycles', { keep: false })`.
