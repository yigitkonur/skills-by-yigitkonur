# Test Case: TC-VIS-09 - Pure Parametric Response Detection & Citation Suppression

## 1. Case ID and Purpose
- **Case ID:** `TC-VIS-09`
- **Module:** Answer Engine Insights (`assets/aei.js`, `assets/aei.css`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture, D6 Parametric Integrity)
- **Traceability:** Maps to Source Scenarios `VIS-13` and `VIS-21`
- **Purpose:** Verify that when an AI model answers a prompt purely from its internal parametric weights without performing live web search (0 search queries and 0 retrieved citations), the system suppresses synthetic or empty citation leaf nodes, renders the dedicated `.aei-parametric-notice.card` with an amber indicator dot, and clearly explains to the user that the answer was synthesized from parametric memory rather than live citations.

---

## 2. Tester Brief
The tester or automated agent validates the system's honesty when handling purely parametric answers:
1. In traditional SEO tools, zero-citation prompts frequently fail with broken UI trees or fabricate placeholder citations.
2. In Zeo Geo-Radar, `assets/aei.js` evaluates `!hasAnyQueriesOrSources`.
3. When true:
   - The Stage 2 container suppresses all `.aei-branch` and `.aei-sources-leaf` nodes.
   - The system injects `.aei-parametric-notice.card`.
   - The notice contains an 8px circular amber indicator (`.aei-chip-dot`).
   - The explanatory text clarifies: *"Parametric Response · No search queries or citation sources attached to this execution. The engine synthesized its answer directly from internal parametric model weights."*
   - In Stage 1 header, the search pill indicates parametric mode with amber status rather than green live web search.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=studio`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Selected Prompt:** A factual/definitional prompt answered without search (e.g. `What year was [BRAND] founded?` or "Inverter klima nasıl çalışır?")
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `09-gherkin-result-case-pure-parametric-response-detection/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Pure Parametric Answer Detection and Citation Leaf Suppression

  Background:
    Given the user is in the "studio" workspace of Zeo Geo-Radar
    And the active prompt execution has 0 search queries and 0 citation sources
    Then the detail pane ".aei-studio-detail" should render Stage 2 retrieval forensics

  Scenario: Parametric Notice Card Rendering
    Then the notice card ".aei-parametric-notice.card" must be rendered inside Stage 2
    And the notice card should display an amber indicator dot ".aei-chip-dot"
    And the notice title should state "Parametric Response" or "Parametrik Yanıt"
    And the notice body text should explain synthesis from internal parametric model weights

  Scenario: Suppression of Hallucinated and Empty Tree Leaves
    Then the count of ".aei-branch" elements in Stage 2 must equal 0
    And the count of ".aei-sources-leaf" elements in Stage 2 must equal 0
    And the count of ".aei-leaf-item" elements in Stage 2 must equal 0
    And no broken images or empty table rows should be present in the container

  Scenario: Stage 1 Header Parametric Status Indication
    When Stage 1 answer header ".aei-ans-head" is displayed for a parametric response
    Then the web search status chip should display an amber dot rather than green
    And the chip text should indicate parametric or unretrieved state
```

---

## 5. Visual Checks
1. **Notice Card Aesthetics:** `.aei-parametric-notice.card` displays a clean card container with subtle amber border (`border: 1px solid rgba(245, 158, 11, 0.3)`) and soft background tint.
2. **Amber Chip Dot:** 8px circular dot with solid amber color (`var(--amber, #f59e0b)`).
3. **Typography:** Explanatory text in `.sub` or `p` tag is clean, high-contrast, and formatted with `font-size: 12.5px`, `color: var(--ink-3)`.
4. **No Broken Placeholders:** Confirm no empty tree branches, dangling connector lines, or blank SVG nodes.

---

## 6. Data and Network Checks
1. **Zero Queries/Sources Gate Assertion:**
   ```js
   const hasQueries = (a.searchQueries && a.searchQueries.length > 0);
   const hasSources = (a.sources && a.sources.length > 0);
   assert(!hasQueries && !hasSources, "Must have 0 queries and 0 sources for parametric test");
   assert(document.querySelector(".aei-parametric-notice.card") !== null, "Notice must render");
   ```
2. **Leaf Suppression Assertion:**
   ```js
   const leaves = document.querySelectorAll(".aei-fanout-tree .aei-sources-leaf");
   assert(leaves.length === 0, "No citation leaves allowed in parametric view");
   ```

---

## 7. Evidence and Reporting
- **Target Result Directory:** `09-gherkin-result-case-pure-parametric-response-detection/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`parametric_notice_card.png`, `leaf_suppression_verified.png`, `header_amber_chip.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/visibility/tc-vis-09-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/01-platform-engine-benchmark/09-gherkin-result-case-pure-parametric-response-detection/screenshots/
     ```
  4. Write execution report `result.md` verifying query counts, card existence, and leaf suppression.

### Pass/Fail Criteria
- [ ] Parametric notice card renders when queries and citations are 0.
- [ ] Notice displays amber dot indicator and parametric explanation text.
- [ ] No citation leaves or branch nodes are rendered.
- [ ] Stage 1 header accurately conveys parametric status.
