# TC-BH-09: Entity Root Resolution Traversal Depth Clamping

## 1. Case ID and Purpose
- **Case ID:** `TC-BH-09`
- **Purpose:** Verify that recursive entity parent resolution (`resolveRootEntity` in `assets/entity-graph.js`) strictly halts traversal at `MAX_TRAVERSAL_DEPTH = 10` hops when inspecting deeply nested entity chains, preventing browser thread blocking, call-stack overflow, and catastrophic backtracking.
- **Target Result Directory:** `01-brand-hub-ground-truth/09-gherkin-result-case-entity-graph-depth-clamping/`

---

## 2. Tester Brief
Corporate hierarchy structures can be maliciously or erroneously structured with excessively deep nesting.
1. The constant `MAX_TRAVERSAL_DEPTH = 10` sets an upper bound on parent traversal.
2. When searching for the root brand of an entity 15 levels deep:
   - Level 15 -> 14 -> 13 -> 12 -> 11 -> 10 -> 9 -> 8 -> 7 -> 6 -> 5 -> ... -> 0.
3. The traversal must clamp after precisely 10 iterations and return entity `ent_5`, rather than traversing all the way to `ent_0` or throwing `Maximum call stack size exceeded`.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Target Subsystem:** `assets/entity-graph.js`.
- **Target Method:** `ZeoEntityGraph.resolveRootEntity(entityId, hierarchy, options)`.
- **Fixtures & Placeholders:**
  - `[MAX_TRAVERSAL_DEPTH]`: `10`
  - Linear 15-node chain: `ent_15` parent is `ent_14`, `ent_14` parent is `ent_13`, down to `ent_0`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Entity Root Resolution Depth Clamping

  Scenario Outline: Halting root entity traversal at maximum depth of 10 hops
    Given an entity hierarchy with a linear chain of <ChainLength> levels
    When the system resolves the root entity for the leaf node "<LeafNode>"
    Then the traversal depth should clamp at <MaxDepth>
    And the returned entity identifier should be "<ExpectedClampedNode>"
    And the main execution thread should not freeze or overflow

    Examples:
      | ChainLength | LeafNode | MaxDepth | ExpectedClampedNode |
      | 15          | ent_15   | 10       | ent_5               |
      | 25          | ent_25   | 10       | ent_15              |
```

---

## 5. Visual Checks
- **Visualizer Node Display:**
  - Leaf node detail popup displays depth badge: `.badge.dim` with `Depth: 10+ (Clamped)`.
- **Screenshot Points:**
  - `01_deep_hierarchy_node.png` (Deeply nested entity node in graph visualizer).

---

## 6. Data and Network Checks
- **Algorithmic Invariant:**
  - `window.ZeoEntityGraph.MAX_TRAVERSAL_DEPTH === 10`.
  - Return value of `resolveRootEntity("ent_15", hierarchy, { maxDepth: 10 })` is strictly `"ent_5"`.

---

## 7. Evidence and Reporting
- **Result Directory:** `01-brand-hub-ground-truth/09-gherkin-result-case-entity-graph-depth-clamping/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-bh-depth-clamp');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/kb', { wait: true, timeout: 30 });
await wait(2);

const clampCheck = await js(String.raw`(() => {
  if (!window.ZeoEntityGraph) return { error: "ZeoEntityGraph missing" };
  const graph = window.ZeoEntityGraph;

  // Construct 15-level chain
  const deepChain = [];
  for (let i = 1; i <= 15; i++) {
    deepChain.push({ childEntityId: "ent_" + i, parentEntityId: "ent_" + (i - 1) });
  }

  const rootClamped = graph.resolveRootEntity("ent_15", deepChain, { maxDepth: 10 });
  return {
    maxDepthConstant: graph.MAX_TRAVERSAL_DEPTH,
    rootClamped
  };
})()`);

cliLog('Depth Clamp Assertions: ' + JSON.stringify(clampCheck));
if (clampCheck.rootClamped !== "ent_5") {
  throw new Error('Root traversal failed to clamp at 10 hops, got: ' + clampCheck.rootClamped);
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-bh-depth-clamp', { keep: false })`.
