# Test Case: Shell Date Range Calendar Popover & Presets

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-KPI-04`
- **Purpose**: Verify that opening the shell filter bar date range chip (`.fchip[data-pop="date"]`) displays the interactive calendar modal popover (`.fpop.dr-pop[data-stop="1"]`), allows selecting date presets (`snap`, `7`, `14`, `30`) or custom calendar day cells, and updates the displayed date label upon applying.

---

## 2. Tester Brief
The shell filter bar contains a persistent Date Range chip (`.fchip[data-pop="date"]`). Clicking this chip opens a popover containing:
- Quick presets: "Snapshot Day", "Last 7 Days", "Last 14 Days", "Last 30 Days".
- Month header and calendar day grid (`.dr-day`).
- Action buttons: "Reset Date" (`.clear[data-action="date-reset"]`) and "Apply Selection" (`button[data-action="date-apply"]`).

The tester verifies that:
1. Clicking the chip toggles the popover into the open state.
2. Clicking a preset option or calendar days highlights the range.
3. Clicking Apply commits the selection into `state.expanded["date-range-label"]` and closes the popover.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Shell Filter Bar**: Mounted and visible at the top of the interface.

---

## 4. Gherkin Scenario

```gherkin
Feature: Shell Date Range Calendar Popover
  As a marketing strategist reviewing historical campaigns
  I want to select custom date ranges and presets from the global filter bar
  So that the entire dashboard updates to reflect the specified timeframe.

  Scenario Outline: Selecting date presets in calendar popover
    Given the user is on the Overview Dashboard
    When the user clicks the shell date range filter chip ".fchip[data-pop='date']"
    Then the calendar popover ".fpop.dr-pop" should be visible
    When the user clicks the date preset option "<PresetKey>"
    And the user clicks the Apply button "button[data-action='date-apply']"
    Then the popover should close
    And the date filter chip label should reflect the preset "<PresetLabel>"

    Examples:
      | PresetKey | PresetLabel   |
      | snap      | Snapshot Day  |
      | 7         | Last 7 Days   |
      | 14        | Last 14 Days  |
      | 30        | Last 30 Days  |
```

---

## 5. Visual Checks
- **Filter Chip**: `.filterbar .fchip[data-pop="date"]` displaying calendar icon and date text.
- **Popover Element**: `.fpop.dr-pop[data-stop="1"]` appearing positioned under the chip.
- **Calendar Grid**: `.dr-month` with day cells `.dr-day` marked `.snap`, `.inrange`, or `.sel`.
- **Action Buttons**: `.clear[data-action="date-reset"]` and `.btn.black.small[data-action="date-apply"]`.

---

## 6. Data and Network Checks
- **DOM & State Assertion**:
  ```javascript
  const datePopCheck = await js(String.raw`(() => {
    const chip = document.querySelector('.filterbar .fchip[data-pop="date"]');
    if (chip) chip.click();
    
    const pop = document.querySelector('.fpop.dr-pop');
    const isPopVisible = pop && window.getComputedStyle(pop).display !== 'none';
    
    // Click 14D preset
    const preset14 = document.querySelector('.opt[data-action="date-preset"][data-k="14"]');
    if (preset14) preset14.click();
    
    // Click Apply
    const applyBtn = document.querySelector('button[data-action="date-apply"]');
    if (applyBtn) applyBtn.click();
    
    return {
      popWasOpened: isPopVisible,
      selectedPreset: window.state?.expanded?.['date-preset'],
      noError: !window.__lastError
    };
  })()`);
  if (!datePopCheck.popWasOpened || datePopCheck.selectedPreset !== '14') {
    throw new Error('Date popover preset selection failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-shell-date-picker-popover/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or test runner.
  - Screenshots of open calendar popover and applied state saved in result directory.
  - SCP synchronization from MacBook to local reporting folder.
