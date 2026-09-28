# Test Case: TC-SNT-06 - Custom Persona Builder Modal Lifecycle & Event Bubbling Stop

## 1. Case ID and Purpose
- **Case ID:** `TC-SNT-06`
- **Module:** Answer Engine Insights (`assets/aei.js`, `assets/aei.css`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture, BMD-SNT-04)
- **Traceability:** Maps to Source Scenarios `SNT-07`, `SNT-08`, `SNT-09`, and `SNT-24`
- **Purpose:** Verify that clicking "Create Custom Persona" mounts the Custom Persona Builder Modal (`.aei-modal`), that clicking inside the modal card does not trigger premature dismissal due to event bubbling isolation (`data-stop="1"`), that clicking the overlay backdrop (`.aei-overlay`) or Cancel button cleanly dismisses the modal without altering state, and that submitting valid inputs pushes the new persona to `st.customPersonas`, displays a toast notification, and dynamically renders the new persona card in `.aei-persona-grid`.

---

## 2. Tester Brief
The tester or automated agent exercises the modal lifecycle and event isolation mechanics:
1. Click `button[data-action="aei-open-persona-builder"]`.
2. Verify that `.aei-overlay` and `.aei-modal` mount into the DOM.
3. Test event bubbling isolation (`data-stop="1"`):
   - Click inside the modal body or card padding.
   - Assert the modal remains open (does not close).
4. Test backdrop dismissal:
   - Click outside the modal card directly on `.aei-overlay`.
   - Assert the modal unmounts and `st.customPersonas` is unmodified.
5. Re-open the modal, fill in valid values:
   - Role: `Chief Procurement Officer`.
   - Industry: `Enterprise Retail`.
   - Tone: `Formal & Analytical`.
6. Click `button[data-action="aei-save-persona"]`:
   - Modal dismisses.
   - Toast notification appears: `✓ Persona created`.
   - The new persona is appended to `window.aeiState.customPersonas`.
   - `.aei-persona-grid` re-renders and displays the new persona card.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=perception`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Test Role `[PERSONA_ROLE]`:** `Chief Procurement Officer`
- **Test Industry `[PERSONA_INDUSTRY]`:** `Enterprise Retail`
- **Test Tone `[PERSONA_TONE]`:** `Formal & Analytical`
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `06-gherkin-result-case-custom-persona-builder-modal-lifecycle/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Custom Persona Builder Modal Lifecycle, Event Bubbling Stop, and Persistence

  Background:
    Given the user is on the "perception" workspace of Zeo Geo-Radar
    And the persona simulation card is visible

  Scenario: Modal Mount and Form Inputs Inspection
    When the user clicks "button[data-action='aei-open-persona-builder']"
    Then the modal overlay ".aei-overlay" should be visible
    And the modal dialog ".aei-modal" should be attached to the DOM
    And the modal dialog must carry attribute "data-stop='1'"
    And the modal should render the following form inputs:
      | Input Selector              | Input Type | Purpose                           |
      | input#aeiPersonaRole        | text       | Persona role and job title        |
      | input#aeiPersonaIndustry    | text       | Industry sector vertical          |
      | select#aeiPersonaTone       | select     | Search communication tone         |

  Scenario: Inner Window Click Event Bubbling Stop
    Given the custom persona builder modal is currently open
    When the user clicks inside the modal card ".aei-modal .body"
    Then the modal dialog ".aei-modal" must remain open
    And the overlay ".aei-overlay" must remain attached to the DOM

  Scenario: Dismissal via Backdrop Overlay Click
    Given the custom persona builder modal is currently open
    When the user clicks directly on the outer backdrop ".aei-overlay"
    Then the modal dialog ".aei-modal" should be removed from the DOM
    And "window.aeiState.showPersonaModal" should equal false

  Scenario: Saving Custom Persona and Dynamic Grid Update
    Given the custom persona builder modal is open
    When the user enters "[PERSONA_ROLE]" into "input#aeiPersonaRole"
    And the user enters "[PERSONA_INDUSTRY]" into "input#aeiPersonaIndustry"
    And the user selects "[PERSONA_TONE]" from "select#aeiPersonaTone"
    And the user clicks the save button "button[data-action='aei-save-persona']"
    Then the modal dialog should be dismissed
    And a success toast notification should be displayed
    And "window.aeiState.customPersonas" should contain an entry with role "[PERSONA_ROLE]"
    And the persona grid ".aei-persona-grid" should display a new card for "[PERSONA_ROLE]"
```

---

## 5. Visual Checks
1. **Modal Centering:** Centered horizontally and vertically over the viewport with `z-index: 1100`.
2. **Backdrop Shadow:** `.aei-overlay` provides dimming backdrop (`background: rgba(0,0,0,0.5)`).
3. **Form Controls:** Clean input styling (`.pe-input`, `.pe-select`) with high contrast text and focus outline.
4. **Toast Notification:** Temporary floating notification (e.g. `✓ Persona created`) anchored to top/bottom right.

---

## 6. Data and Network Checks
1. **Event Bubbling Stop Verification:**
   - Confirm handler checks `ev.target.closest("[data-stop]")` before dismissing.
2. **State Persistence Verification:**
   ```js
   const personas = window.aeiState.customPersonas;
   const last = personas[personas.length - 1];
   assert(last.role === "Chief Procurement Officer", "Role must match entered input");
   assert(last.industry === "Enterprise Retail", "Industry must match entered input");
   assert(last.tone === "Formal & Analytical", "Tone must match entered input");
   ```
3. **Clean Rerender:** Verify modal removal does not leave orphan DOM nodes or freeze scrolling on `document.body`.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `06-gherkin-result-case-custom-persona-builder-modal-lifecycle/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`persona_modal_mounted.png`, `inner_click_bubbling_stop.png`, `persona_saved_grid_updated.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/sentiment/tc-snt-06-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/02-sentiment-and-audience/06-gherkin-result-case-custom-persona-builder-modal-lifecycle/screenshots/
     ```
  4. Write execution report `result.md` verifying modal actions, state objects, and grid elements.

### Pass/Fail Criteria
- [ ] Modal mounts upon clicking create button.
- [ ] Clicking inside the modal card does not close it (`data-stop="1"`).
- [ ] Clicking the backdrop dismisses the dialog cleanly.
- [ ] Saving updates `customPersonas` and re-renders the grid with the new persona.
