# Test Case: Collapsible Technical Telemetry Drawer

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-KPI-10`
- **Purpose**: Verify that clicking the technical telemetry drawer toggle button (`button.ov-tech-drawer-btn[data-action="ov-toggle-tech-drawer"]`) smoothly expands and collapses the telemetry drawer (`.ov-tech-drawer-grid`), updates the drawer button label, maintains the checklist progress badge, and displays 4 accurate technical metrics: Queries Evaluated, Answer Engines, Citations Indexed, and Confidence Tier.

---

## 2. Tester Brief
The Overview Dashboard features a collapsible Technical Telemetry Drawer (`.ov-tech-drawer-wrap`) designed for technical transparency.
The drawer header button shows:
- Caret and label: `▸ Show Technical Telemetry` (when closed) / `▾ Hide Technical Telemetry` (when open).
- Progress badge: `.ov-checklist-progress-badge` displaying evaluated prompts and active responding engines (e.g. `32 prompts · 4 engines`).

When expanded, a 4-card grid (`.ov-tech-drawer-grid`) displays:
1. **Queries Evaluated**: Total active prompts across topic clusters.
2. **Answer Engines**: Number of responding model engines vs total catalog (`X / 5`).
3. **Citations Indexed**: Count of parsed distinct domain citations.
4. **Confidence Tier**: Deterministic multi-pass verification level (e.g. `99.4% · High`).

The tester verifies the drawer toggle action, CSS state, and metric card content.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Component**: `.ov-tech-drawer-wrap` present in hero card.

---

## 4. Gherkin Scenario

```gherkin
Feature: Collapsible Technical Telemetry Drawer
  As a technical auditor or data engineer
  I want to expand the technical telemetry drawer
  So that I can verify query sample depth, engine coverage, citation counts, and confidence verification tier.

  Scenario: Toggling the technical telemetry drawer open and closed
    Given the user is on the Overview Dashboard
    And the technical telemetry drawer is initially collapsed
    When the user clicks the technical drawer button "button[data-action='ov-toggle-tech-drawer']"
    Then the telemetry grid ".ov-tech-drawer-grid" should become visible
    And exactly 4 technical metric cards ".ov-tech-metric-card" should be rendered
    And the metric card "Queries Evaluated" should display the active prompt count
    And the metric card "Answer Engines" should display the responding engine count
    And the metric card "Citations Indexed" should display the total parsed citations
    And the metric card "Confidence Tier" should display the verification tier
    When the user clicks the technical drawer button again
    Then the telemetry grid ".ov-tech-drawer-grid" should be collapsed and removed from the DOM
```

---

## 5. Visual Checks
- **Drawer Button**: `button.ov-tech-drawer-btn` with chevron symbol `▸` or `▾`.
- **Progress Badge**: `.ov-checklist-progress-badge` with rounded pill styling.
- **Drawer Grid**: `.ov-tech-drawer-grid` with 4 cards `.ov-tech-metric-card`.
- **Card Content**: Each card contains `.ov-tech-metric-label`, `.ov-tech-metric-val`, and `.ov-tech-metric-sub`.

---

## 6. Data and Network Checks
- **DOM & State Assertion**:
  ```javascript
  const drawerCheck = await js(String.raw`(() => {
    const btn = document.querySelector('[data-action="ov-toggle-tech-drawer"]');
    if (!btn) return { error: 'Drawer button not found' };

    // 1. Expand
    btn.click();
    const grid = document.querySelector('.ov-tech-drawer-grid');
    const cards = grid ? [...grid.querySelectorAll('.ov-tech-metric-card')] : [];
    const labels = cards.map(c => c.querySelector('.ov-tech-metric-label')?.innerText?.trim());
    const isOpen = !!grid && cards.length === 4;

    // 2. Collapse
    btn.click();
    const isClosed = !document.querySelector('.ov-tech-drawer-grid');

    return {
      isOpen,
      isClosed,
      cardCount: cards.length,
      labels,
      noError: !window.__lastError
    };
  })()`);
  if (!drawerCheck.isOpen || !drawerCheck.isClosed || drawerCheck.cardCount !== 4) {
    throw new Error('Technical telemetry drawer toggle assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-tech-telemetry-drawer/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of collapsed and expanded states captured in result directory.
  - Remote artifacts retrieved via SCP before final test report compilation.
