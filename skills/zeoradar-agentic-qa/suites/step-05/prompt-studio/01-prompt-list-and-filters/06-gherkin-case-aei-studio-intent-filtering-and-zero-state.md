# Test Case 06: AEI Studio 5-Intent Taxonomy Chips & Zero-Match Empty State

## 1. Case ID and Purpose
- **Case ID**: `TC-PLIST-06-INTENT-FILTER`
- **Purpose**: Verify that the Prompts & Citations Studio (`workspace=studio`) renders the 45/55 split-screen layout, enables intent-based query isolation across 5 discrete intent chips (`all`, `info`, `comm`, `trans`, `nav`), and renders the dedicated `.aei-empty-state.dim` component when an intent selection matches zero tracked prompts.

---

## 2. Tester Brief
The tester navigates to `[APP_URL]/#/[SLUG]/visibility?workspace=studio` and:
1. Verifies that the studio workspace mounts with the left master card `.aei-studio-master` and right detail card `.aei-studio-detail`.
2. Verifies the 5 intent filter chips (`.aei-intent-chip`): All, Info, Comm, Trans, Nav.
3. Clicks each intent chip sequentially and confirms that visible prompt items `.aei-master-item` only include prompts with matching intent tags.
4. Selects an intent chip with zero matching prompts (or inputs a filter yielding zero results) and confirms that `.aei-empty-state.dim` displays `"No prompts match the active filters."`.
5. Clicks the "All" chip to restore the complete prompt catalog.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/visibility?workspace=studio`
- **Pre-existing Data**: Prompts tagged with diverse intent values (`informational`, `commercial`, `transactional`, `navigational`).
- **Intent Selectors**:
  - `button.aei-intent-chip[data-intent="all"]`
  - `button.aei-intent-chip[data-intent="info"]`
  - `button.aei-intent-chip[data-intent="comm"]`
  - `button.aei-intent-chip[data-intent="trans"]`
  - `button.aei-intent-chip[data-intent="nav"]`

---

## 4. Gherkin Scenario

```gherkin
Feature: Prompts & Citations Studio Intent Filter Chips & Empty State

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Prompts & Citations Studio at "[APP_URL]/#/[SLUG]/visibility?workspace=studio"
    And the workspace container ".aei-studio-workspace" has rendered

  @smoke @aei @intent
  Scenario Outline: Filter master prompt items by search intent classification
    When the tester clicks the intent filter chip "<IntentChip>"
    Then the clicked chip should gain class ".active"
    And all other intent filter chips should lose class ".active"
    And each visible prompt item ".aei-master-item" should match the classification "<ExpectedIntent>"

    Examples:
      | IntentChip                                           | ExpectedIntent |
      | button.aei-intent-chip[data-intent='info']           | info           |
      | button.aei-intent-chip[data-intent='comm']           | comm           |
      | button.aei-intent-chip[data-intent='trans']          | trans          |
      | button.aei-intent-chip[data-intent='nav']            | nav            |

  @edge @empty @aei
  Scenario: Selecting an intent with zero matching prompts displays dedicated empty state
    Given an intent classification has zero associated project prompts
    When the tester clicks the corresponding intent filter chip
    Then the master list container should render ".aei-empty-state.dim"
    And the text content should display "No prompts match the active filters."
    When the tester clicks the "All" intent filter chip
    Then the empty state notice should disappear
    And all prompt items should re-render in the master list
```

---

## 5. Visual Checks
1. **Split-Screen Proportion**: The container `.aei-studio-workspace` maintains a 45% (master) to 55% (forensic detail) desktop split.
2. **Intent Chips**: Intent pills render with rounded corners and distinct border accents when active.
3. **Empty State Component**: `.aei-empty-state.dim` renders centered with muted typography and padding.

---

## 6. Data and Network Checks
1. **Client Intent Filter Audit**:
   ```javascript
   const activeIntentChip = document.querySelector('.aei-intent-chip.active');
   const intentKey = activeIntentChip.getAttribute('data-intent');
   assert.ok(['all', 'info', 'comm', 'trans', 'nav'].includes(intentKey), 'Active intent must be valid enum');

   if (intentKey !== 'all') {
     const items = document.querySelectorAll('.aei-master-item');
     items.forEach(item => {
       const text = item.textContent.toLowerCase();
       assert.ok(text.includes(intentKey) || text.includes(intentKey === 'trans' ? 'satın alma' : intentKey),
         `Prompt item must match active intent ${intentKey}`);
     });
   }
   ```
2. **State Consistency**: Check `window.aeiState.studioIntentFilter` matches the clicked intent key.

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-aei-studio-intent-filtering-and-zero-state/`
- **Execution Model Notice**: Ego Browser on macOS executes tests and captures viewport screenshots to `/tmp/shots/aei-intent-[INTENT].png` prior to SCP download.
- **Report Contents**:
  - `status.json`: Execution log and assertion status.
  - `screenshot-intent-filtered.png`: Master list displaying filtered intent queries.
  - `screenshot-intent-empty.png`: Dedicated `.aei-empty-state` display.
