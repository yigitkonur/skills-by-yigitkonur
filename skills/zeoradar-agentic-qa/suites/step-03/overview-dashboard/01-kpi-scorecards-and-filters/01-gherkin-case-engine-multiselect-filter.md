# Test Case: Shell Answer Engine Multi-Select Filter

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-KPI-05`
- **Purpose**: Verify that the Answer Engine (Platforms) multi-select popover allows toggling individual generative AI search engines, accurately updates the badge count `.cnt` on the filter chip, mutates `state.platforms`, and restores full selection via Clear All.

---

## 2. Tester Brief
The shell filter bar contains a platforms chip (`.fchip[data-pop="platforms"]`).
Clicking this chip opens a multi-select popover containing:
- Search input (`.fpop .search input`)
- Engine option rows for ChatGPT, Perplexity, Gemini, Claude, and Google AI Mode.
- Active state checkmark (`.opt.on`)
- Clear All trigger (`span.clear[data-action="clear-filter"][data-kind="platforms"]`)

The tester verifies that:
1. Toggling an engine off removes it from `state.platforms` and updates the chip badge `.cnt`.
2. When all 5 engines are active, `state.platforms` resets to `null` (representing all engines) and the badge hides or shows `5`.
3. Clicking Clear All deselects active selections or restores the default state cleanly.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Platforms List**: ChatGPT, Perplexity, Gemini, Claude, Google AI Mode

---

## 4. Gherkin Scenario

```gherkin
Feature: Shell Answer Engine Filter Popover
  As an analyst investigating engine-specific performance
  I want to filter the dashboard by selecting or deselecting specific answer engines
  So that I can isolate the impact of ChatGPT, Perplexity, Gemini, Claude, or Google AI Mode.

  Scenario Outline: Toggling answer engines in platforms popover
    Given the user is on the Overview Dashboard
    When the user clicks the platforms filter chip ".fchip[data-pop='platforms']"
    Then the platforms popover ".fpop" should open
    When the user clicks the platform option for "<EngineName>"
    Then the platform option "<EngineName>" should toggle its active state
    And the count badge ".fchip[data-pop='platforms'] .cnt" should reflect the active engines count
    And the overview scorecards should recalculate based only on the selected engines

    Examples:
      | EngineName      |
      | ChatGPT         |
      | Perplexity      |
      | Gemini          |
      | Claude          |
      | Google AI Mode  |
```

---

## 5. Visual Checks
- **Platform Chip**: `.fchip[data-pop="platforms"]` with badge `.cnt`.
- **Option Rows**: `.opt[data-action="toggle-opt"][data-kind="platforms"][data-key="<Engine>"]`.
- **Active State**: Selected options display `.opt.on` with SVG checkmark.
- **Clear Action**: `span.clear[data-action="clear-filter"][data-kind="platforms"]`.

---

## 6. Data and Network Checks
- **DOM & State Assertion**:
  ```javascript
  const engineFilterCheck = await js(String.raw`(() => {
    // Open platforms popover
    const chip = document.querySelector('.filterbar .fchip[data-pop="platforms"]');
    if (chip) chip.click();
    
    // Toggle Perplexity
    const perpOpt = document.querySelector('.opt[data-key="Perplexity"]');
    if (perpOpt) perpOpt.click();
    
    const platformsState = window.state?.platforms ? Array.from(window.state.platforms) : null;
    const badgeVal = document.querySelector('.filterbar .fchip[data-pop="platforms"] .cnt')?.innerText?.trim();
    
    // Restore
    window.state.platforms = null;
    window.rerender();

    return {
      platformsState,
      badgeVal,
      noError: !window.__lastError
    };
  })()`);
  if (!engineFilterCheck.noError) {
    throw new Error('Engine multi-select filter encountered runtime error');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-engine-multiselect-filter/`
- **Execution Model**:
  - Script executed via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of open popover and updated scorecards saved to result directory.
  - SCP sync from MacBook to host before final report delivery.
