# Case 11: Keyword Hierarchy Mindmap & Semantic Tree Navigation

## 1. Case ID and Purpose
- **Case ID**: `TC-VOL-11`
- **Purpose**: Verify that the Hierarchy Mindmap module (`data-tab="mindmap"`) renders an interactive canvas of semantic keyword parent-child relationships, responds to depth selection (levels 1, 2, or 3) and child limit controls (2, 3, or 5 branches), displays a floating tooltip with prompt volume upon node hover, and allows direct navigation from mindmap nodes into the detailed Keyword Workspace.

## 2. Tester Brief
The tester switches to the Mindmap sub-tab (`data-tab="mindmap"`), verifies that the SVG tree renders root and child nodes with connecting branch lines, changes the tree depth select to 2 and child branch limit to 3, hovers over a child node to verify that the floating tooltip panel `.vol-node-tooltip` displays accurate volume and an "Inspect" link, and clicks the node to confirm transition into the Keyword Workspace.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Root Keyword: `[KEYWORD_TERM]` (e.g. "klima")
  - Depth Options: 1, 2, 3
  - Branch Limit Options: 2, 3, 5
- **Prerequisites**:
  - Prompt Volumes page loaded.

## 4. Gherkin Scenario

```gherkin
Feature: Hierarchy Mindmap & Semantic Topic Expansion
  As a Content Architect
  I want to explore keyword hierarchies and semantic topic expansions in a visual mindmap
  So that I can identify content cluster gaps and prioritize sub-topics for AI visibility

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/volumes"
    When the user switches to the Mindmap tab "button.volumes-tab-btn[data-tab='mindmap']"
    Then the mindmap container ".mindmap-canvas-container" should be visible

  Scenario: Render semantic topic nodes and connecting branches
    Then the mindmap canvas should display a central root node for "[DOMAIN]" or active topic
    And child semantic expansion nodes should be rendered connected by SVG line paths
    And node labels should display keyword terms and volume badges

  Scenario: Adjust hierarchy depth and child branch limits
    When the user selects depth "2" from "select[data-action='vol-mindmap-depth']"
    And selects child limit "3" from "select[data-action='vol-mindmap-limit']"
    Then the mindmap tree should re-layout
    And each parent node should display at most 3 child branches
    And the tree should expand to 2 levels of hierarchy depth

  Scenario: Inspect node details and navigate to Keyword Workspace
    When the user hovers over a semantic node in the mindmap
    Then the floating tooltip ".vol-node-tooltip" should appear near the cursor
    And the tooltip should display keyword volume and intent classification
    When the user clicks the node or the tooltip action "Inspect Keyword"
    Then the active tab should switch to the Keyword Workspace
    And the workspace should load the clicked node term as active keyword
```

## 5. Visual Checks
- **Node Geometry**: Central root node with distinctive styling; child nodes radiating outward with smooth bezier connecting curves.
- **Floating Tooltip**: Semi-transparent card hovering adjacent to node with dark backdrop, white text, and action buttons.
- **Re-layout Transition**: Smooth layout transition upon depth change without canvas flickering.

## 6. Data and Network Checks
- **Mindmap State Synchronizations**:
  ```javascript
  assert.strictEqual(window.volumesState.activeTab, 'mindmap');
  const svgNodes = document.querySelectorAll('.mindmap-canvas-container .mindmap-node');
  assert.ok(svgNodes.length > 0, 'Mindmap must contain rendered nodes');
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `02-gherkin-result-case-hierarchy-mindmap-navigation/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-vol-11-mindmap-canvas.png`
     - `/tmp/ego-shots/tc-vol-11-node-tooltip.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-vol-11-*.png ./02-gherkin-result-case-hierarchy-mindmap-navigation/
     ```
