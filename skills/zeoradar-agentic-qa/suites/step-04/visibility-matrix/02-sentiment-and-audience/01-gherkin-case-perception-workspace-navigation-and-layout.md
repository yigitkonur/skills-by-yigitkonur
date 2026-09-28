# Test Case: TC-SNT-01 - Perception Workspace Navigation and Section Mounting

## 1. Case ID and Purpose
- **Case ID:** `TC-SNT-01`
- **Module:** Answer Engine Insights (`assets/aei.js`, `assets/aei.css`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture, Perception Workspace)
- **Traceability:** Maps to Source Scenario `SNT-01`
- **Purpose:** Verify that navigating to `/#/app/:slug/visibility?workspace=perception` mounts the qualitative intelligence workspace (`.aei-perception-workspace`), selects the "Perception & Audience" tab (`.aei-tab[data-ws="perception"].active`), and successfully instantiates the four foundational perception sections: Sentiment Polarity & Trajectory, Thematic Attribute Perception Clusters, Audience Persona Simulation Matrix, and Factual Integrity & Hallucination Radar.

---

## 2. Tester Brief
The tester or automated agent navigates directly to the Perception workspace via query parameter:
1. Load `/#/app/[SLUG]/visibility?workspace=perception`.
2. Verify that `window.aeiState.workspace` initializes to `"perception"`.
3. Confirm that the top-level tab switcher reflects `.active` on the third tab (`button.aei-tab[data-ws="perception"]`).
4. Validate that the root container `.aei-perception-workspace` is mounted in the DOM.
5. Confirm all four core functional cards are instantiated:
   - Brand Sentiment Polarity Card (`.card.aei-sentiment-card`).
   - Thematic Attribute Clusters Card (`.card.aei-attributes-card`).
   - Audience Persona Card (`.card.aei-persona-card`).
   - Factual Integrity & Hallucination Radar Card (`.card.aei-hallucination-radar-card`).

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=perception`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `all` (or `US`, `TR`)
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `01-gherkin-result-case-perception-workspace-navigation-and-layout/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Perception Workspace Boot and Core Section Layout

  Background:
    Given the user is authenticated in Zeo Geo-Radar
    And the current brand project is "[DOMAIN]"
    When the user navigates to "/#/app/[SLUG]/visibility?workspace=perception"
    Then the root page container ".aei-page" should mount within 10 seconds

  Scenario: Workspace State and Navigation Tab Activation
    Then the global state "window.aeiState.workspace" should equal "perception"
    And the navigation tab button "button.aei-tab[data-ws='perception']" should have class "active"
    And other navigation tabs "button.aei-tab:not([data-ws='perception'])" should not have class "active"
    And the browser URL hash should contain "workspace=perception"

  Scenario: Core Functional Cards Mounting
    Then the perception workspace container ".aei-perception-workspace" must be attached to the DOM
    And the container should house the following cards in sequential order:
      | Card Selector                    | Section Purpose                                |
      | .card.aei-sentiment-card         | Brand Sentiment Polarity & Trajectory          |
      | .card.aei-attributes-card        | Thematic Attribute Perception Clusters         |
      | .card.aei-persona-card           | Audience Persona Simulation & Custom Builder   |
      | .card.aei-hallucination-radar-card| Factual Integrity & Hallucination Radar       |
    And no JavaScript errors should be thrown in the developer console
```

---

## 5. Visual Checks
1. **Pill Tab Visual State:** The `Perception & Audience` tab displays active styling (solid background, contrasting text, and icon highlight).
2. **Layout Vertical Rhythm:** Cards inside `.aei-perception-workspace` display consistent vertical spacing (`margin-bottom: 24px` or grid gap `20px`).
3. **Card Headers:** Each card features an `.aei-card-head` with a clean `h3` heading and descriptive `.sub` subtitle.
4. **Responsive Integrity:** On narrower viewports (tablets/laptops, 1024px), cards resize fluidly without horizontal clipping.

---

## 6. Data and Network Checks
1. **URL Parameter Parsing:**
   ```js
   const params = new URLSearchParams(window.location.hash.split("?")[1] || "");
   assert(params.get("workspace") === "perception", "URL parameter must be perception");
   assert(window.aeiState.workspace === "perception", "State workspace must be perception");
   ```
2. **Data Provider Telemetry Ingestion:**
   - Confirm `getSentimentData(p)` resolves valid sentiment telemetry or safe fallback shapes via `ZEO_SENTIMENT_ANALYTICS.toSentimentShape()`.
3. **Absence of Memory Leaks:** Verify previous workspace components (e.g. Studio master list, Performance trend canvas) are completely removed from the DOM.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `01-gherkin-result-case-perception-workspace-navigation-and-layout/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`perception_workspace_overview.png`, `active_tab_highlight.png`, `all_cards_mounted.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/sentiment/tc-snt-01-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/02-sentiment-and-audience/01-gherkin-result-case-perception-workspace-navigation-and-layout/screenshots/
     ```
  4. Write execution report `result.md` verifying state parameters, DOM selectors, and layout hierarchy.

### Pass/Fail Criteria
- [ ] Direct deep-link navigation loads the Perception workspace.
- [ ] Active tab button is `Perception & Audience`.
- [ ] All 4 core cards mount cleanly in `.aei-perception-workspace`.
- [ ] No unhandled JavaScript runtime exceptions occur.
