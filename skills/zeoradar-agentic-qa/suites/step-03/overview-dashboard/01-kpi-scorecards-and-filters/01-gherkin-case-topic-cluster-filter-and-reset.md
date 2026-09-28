# Test Case: Topic Cluster Filter Mutation & Global Reset

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-KPI-07`
- **Purpose**: Verify that filtering by topic clusters updates the shell filter chip badge `.cnt`, scopes the dashboard metrics and technical telemetry prompt count, and that clicking the global reset button `.freset[data-action="reset-filters"]` idempotently purges filter state (`state.topics = null`, `state.platforms = null`, `state.promptType = null`) and unmounts the reset button.

---

## 2. Tester Brief
The shell filter bar includes a topic filter chip (`.fchip[data-pop="topics"]`).
Filtering by a topic restricts evaluated prompts and answers to only that cluster.
The tester verifies that:
1. Selecting a cluster updates `state.topics`, displays a count badge `.cnt`, and updates the telemetry drawer badge (e.g. `8 prompts · 4 engines`).
2. The global reset button `.freset[data-action="reset-filters"]` appears in the filter bar.
3. Clicking the reset button completely resets all filters, restores the original prompt count in the telemetry drawer, and removes the `.freset` button from the DOM.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Topic Cluster**: Valid cluster key present in `p.clusters` (e.g. `[TOPIC_CLUSTER] = "klima-modelleri"`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Topic Cluster Filtering and Global Filter Reset
  As an organic search manager
  I want to filter the Overview Dashboard by specific topic clusters and reset filters easily
  So that I can analyze topic performance in isolation and quickly return to the global view.

  Scenario Outline: Filtering by topic cluster and restoring with global reset
    Given the user is on the Overview Dashboard
    When the user opens the topic filter popover ".fchip[data-pop='topics']"
    And the user selects the topic cluster option "<TopicCluster>"
    Then the topic chip should display the count badge ".cnt" with text "1"
    And the global reset button "[data-action='reset-filters']" should become visible
    And the technical drawer progress badge should reflect the filtered prompt count
    When the user clicks the reset filters button "[data-action='reset-filters']"
    Then "state.topics" should be null
    And the topic chip count badge ".cnt" should be removed
    And the global reset button should disappear from the DOM
    And the technical drawer progress badge should restore the full prompt count

    Examples:
      | TopicCluster    |
      | [TOPIC_CLUSTER] |
```

---

## 5. Visual Checks
- **Topic Chip**: `.filterbar .fchip[data-pop="topics"]` with `.cnt` pill when filtered.
- **Reset Button**: `.filterbar .freset[data-action="reset-filters"]` displaying `↺ Reset filters` / `↺ Filtreleri sıfırla`.
- **Telemetry Badge**: `.ov-checklist-progress-badge` reflecting filtered vs restored prompt counts.

---

## 6. Data and Network Checks
- **Filter & Reset Verification**:
  ```javascript
  const resetCheck = await js(String.raw`(() => {
    const p = (typeof profile === 'function') ? profile() : window.state?.activeProfileBundle;
    const firstCluster = p && p.clusters ? Object.keys(p.clusters)[0] : null;
    if (!firstCluster) return { skipped: true };

    // Apply topic filter
    window.state.topics = new Set([firstCluster]);
    window.rerender();
    const filteredText = document.querySelector('.ov-checklist-progress-badge')?.innerText;

    // Reset filters
    const resetBtn = document.querySelector('[data-action="reset-filters"]');
    if (!resetBtn) return { error: 'Reset button missing when filter active' };
    resetBtn.click();

    const restoredText = document.querySelector('.ov-checklist-progress-badge')?.innerText;
    const resetStillPresent = !!document.querySelector('[data-action="reset-filters"]');

    return {
      topicsNull: window.state.topics === null,
      resetStillPresent,
      filteredText,
      restoredText,
      noError: !window.__lastError
    };
  })()`);
  if (!resetCheck.skipped) {
    if (!resetCheck.topicsNull || resetCheck.resetStillPresent || !resetCheck.noError) {
      throw new Error('Filter reset invariant failed');
    }
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-topic-cluster-filter-and-reset/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of filtered state and post-reset state saved in result directory.
  - SCP sync to reporting repository upon completion.
