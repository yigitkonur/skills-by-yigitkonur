# Test Case: TC-VIS-08 - Stage 2 Query Fanout Cascade Tree, Latencies & Citation Leaves

## 1. Case ID and Purpose
- **Case ID:** `TC-VIS-08`
- **Module:** Answer Engine Insights (`assets/aei.js`, `assets/aei.css`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture, R2 Multi-Hop Query Pipeline)
- **Traceability:** Maps to Source Scenarios `VIS-12` and `VIS-24`
- **Purpose:** Verify that Stage 2 of the Generative Retrieval Pipeline (`.aei-fanout-tree`) renders a hierarchical tree topology separating the Root Seed Query (`.aei-node.root`, depth 0) with execution latency, Hop 1 Fanout queries (`.aei-node.fanout`) with sub-query latency tags (`latency: Xms`), and retrieved citation leaf nodes (`.aei-sources-leaf .aei-leaf-item`) tagged with domain classification badges (`tier-owned`, `tier-competitor`, `tier-earned`).

---

## 2. Tester Brief
The tester or automated agent inspects Stage 2 in the Studio detail pane:
1. When viewing a web-retrieved prompt execution, verify the hierarchical tree structure:
   - Root Seed Node (`.aei-node.root`): Displays the seed prompt text, depth indicator (`depth 0`), and total root execution latency (e.g. `latency: 840ms`).
   - Hop 1 Fanout Branches (`.aei-branch`): Displays the sub-queries dispatched by the AI model during web search retrieval, along with query retrieval latency (e.g. `latency: 210ms`) and optional engine badge.
   - Citation Leaves (`.aei-sources-leaf`): Lists the publisher URLs fetched under each sub-query.
2. Confirm each citation leaf renders:
   - Favicon or link icon.
   - Truncated display domain / URL.
   - Classification badge: `.tier-owned` (brand's own domain), `.tier-competitor` (competitor domain), or `.tier-earned` (neutral publisher/editorial).
   - Click action `data-action="open-citation-drawer"` with `data-url` attribute.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=studio`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Prompt:** A web-retrieved prompt (e.g. `[PROMPT_QUERY]` or "en iyi inverter klima modelleri 2026")
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `08-gherkin-result-case-stage-2-query-fanout-cascade-and-latencies/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Stage 2 Hierarchical Query Fanout Cascade Tree and Citation Leaves

  Background:
    Given the user is in the "studio" workspace of Zeo Geo-Radar
    And a web-retrieved prompt with search queries is active in the detail pane
    Then Stage 2 container ".aei-fanout-tree" should be rendered

  Scenario: Root Seed Node Inspection
    Then the root node ".aei-node.root" should be visible
    And the root node tag ".aei-node-tag" should contain "Root Seed" or "Kök Tohum"
    And the root node body should display the prompt text in bold
    And the root node body should display "depth 0"
    And the root node body should display a valid execution latency formatted as "latency: [0-9]+ms"

  Scenario: Hop 1 Fanout Sub-Query Branches and Retrieval Latency
    When the fanout tree renders sub-query branches ".aei-branch"
    Then each branch must contain a fanout node ".aei-node.fanout"
    And the fanout node tag ".aei-node-tag" should display "Hop 1 Fanout" or "1. Aşama Yayılım"
    And the fanout node body should display the derived search query text
    And when sub-query latency is available, it should display "latency: [0-9]+ms" in a monospaced span

  Scenario Outline: Citation Leaf Nodes and Relationship Tiers
    When citation leaves are rendered under a fanout branch in ".aei-sources-leaf"
    Then each leaf item ".aei-leaf-item" should have attribute "data-action='open-citation-drawer'"
    And the leaf item should have a non-empty "data-url" attribute
    And the leaf item should display a relationship tier badge "<TierClass>" matching domain type "<DomainType>"

    Examples:
      | DomainType          | TierClass        | BadgeLabel (EN) | BadgeLabel (TR) |
      | Monitored Brand     | tier-owned       | Owned           | Kendi Sitesi    |
      | Competitor Domain   | tier-competitor  | Competitor      | Rakip           |
      | Third-Party Media   | tier-earned      | Earned          | Kazanılmış      |
```

---

## 5. Visual Checks
1. **Tree Cascade Indentation:** Distinct visual hierarchy with left vertical connector lines connecting `.aei-branch` elements to the root seed node.
2. **Hop 1 Branch Styling:** Sub-queries styled with distinct tag chips and monospaced latency indicators (`font-size: 11px`, `color: var(--ink-3)`).
3. **Citation Leaf Badges:**
   - `.tier-owned`: Solid green background or border with green text.
   - `.tier-competitor`: Orange/red border with contrasting text.
   - `.tier-earned`: Blue or purple border with neutral text.
4. **Interactive Affordance:** Citation leaf items exhibit pointer cursor, hover highlight (`background: var(--panel-subtle)`), and underline on URL text.

---

## 6. Data and Network Checks
1. **Data Source Truthfulness:**
   - Confirm citation sources originate from `cached.execution.citations` or `a.sources`.
   - Confirm query strings originate from `a.searchQueries`.
2. **Latency Metric Verification:**
   - Root latency matches `a.latency_ms` or `pr.latency_ms`.
   - Sub-query latency matches `q.latency_ms`.
3. **Clean Attribute Binding:** Verify `data-url` on `.aei-leaf-item` contains normalized URL without illegal characters or unescaped HTML entities.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `08-gherkin-result-case-stage-2-query-fanout-cascade-and-latencies/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`fanout_tree_root.png`, `hop1_branches_latency.png`, `citation_leaves_tiers.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/visibility/tc-vis-08-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/01-platform-engine-benchmark/08-gherkin-result-case-stage-2-query-fanout-cascade-and-latencies/screenshots/
     ```
  4. Write execution report `result.md` verifying tree nodes, latency metrics, and leaf attributes.

### Pass/Fail Criteria
- [ ] Root Seed node renders with depth 0 and latency metric.
- [ ] Hop 1 Fanout nodes display derived queries and latency tags.
- [ ] Citation leaves display valid domain tiers (`tier-owned`, `tier-competitor`, `tier-earned`).
- [ ] All citation leaf elements carry `data-action="open-citation-drawer"` and valid `data-url`.
