# Test Case: TC-CS-08 - Floating Selection Toolbar Positioning, Clamping & Dismissal

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-08`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #46 (Content Studio Pipeline, Facts Grounding & AI Streaming)
- **Traceability:** Maps to Source Scenarios `TC-CS-07` (Floating Selection Toolbar & AI Rewrite) and `TC-CS-17` (Floating Selection Toolbar `#edFloatBar` Auto-Dismissal on Document Click & RAF Clamping)
- **Purpose:** Test the dynamic floating selection toolbar (`#edFloatBar`), verifying that highlighting text inside `#edContentBody` mounts the toolbar with smooth `requestAnimationFrame` alignment, clamps its geometry within viewport edges ($10\text{px} \le x \le \text{viewportWidth} - 10\text{px}$), flips below selection when too close to the top viewport edge, enables one-click inline AI rewriting, and immediately dismisses upon clicking outside or deselecting text.

---

## 2. Tester Brief
The tester will verify the floating selection toolbar's lifecycle and geometry:
1. When a user selects a range of text inside `#edContentBody`, the `selectionchange` listener schedules `#edFloatBar` positioning via `requestAnimationFrame`.
2. `#edFloatBar` receives the `.show` class and displays rapid actions: Bold, Italic, H1, H2, and inline "AI Rewrite" (`.ed-float-ai`).
3. **Clamping & Flipping Geometry:**
   - Normal position: Centered horizontally $10\text{px}$ above selection bounding rect.
   - Near top edge (`rect.top - height < 10`): Flips to position $10\text{px}$ below the selection.
   - Near screen edges: Clamps left position so it never overflows offscreen.
4. Clicking "AI Rewrite" in the floating bar applies deterministic AEO restructuring to the selected text.
5. **Click-Away Auto-Dismissal:** Clicking anywhere outside `#edContentBody` (or collapsing the selection) removes `.show` and instantly hides the toolbar.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Matching Result Directory:** `08-gherkin-result-case-floating-selection-toolbar-and-clamping/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Floating Selection Toolbar Dynamic Mounting, Clamping, and Auto-Dismissal

  Background:
    Given the user is in an active Content Studio editor
    And the editor canvas "#edContentBody" contains multiline text

  Scenario: Text Selection Mounts Clamped Floating Toolbar
    When the user selects a non-empty text range inside "#edContentBody"
    Then the floating toolbar "#edFloatBar" should have class "show"
    And its computed "top" coordinate should be greater than or equal to 10
    And its computed "left" coordinate should be greater than or equal to 10
    And its computed right boundary should not exceed "window.innerWidth - 10"
    And the floating toolbar should contain an AI Rewrite button ".ed-float-ai"

  Scenario: Top-Edge Inversion (Flipping Below Selection)
    Given the user selects text in the first line of the document near the top of the viewport
    When the calculated top offset is less than 10px
    Then the floating toolbar should flip and position its top below the selection bounding rect

  Scenario: Auto-Dismissal on Click-Away or Deselection
    Given the floating toolbar "#edFloatBar" is visible with class "show"
    When the user clicks the document title ".editor-doc-title" outside the canvas
    Then the selection should collapse
    And the floating toolbar "#edFloatBar" should lose class "show"
    And the floating toolbar should no longer be visible in the viewport
```

---

## 5. Visual Checks
1. **Pill Aesthetics:** `#edFloatBar` renders as a dark floating pill with rounded corners (`20px`), subtle shadow, and clean SVG icons.
2. **Smooth Transitions:** Toolbar fades in and out with CSS opacity and transform transitions (`transition: opacity 0.15s, transform 0.15s`).
3. **No Viewport Clipping:** The bar never clips off the left, right, or top edges of the screen across desktop and tablet viewports.

---

## 6. Data and Network Checks
1. **Geometry Calculation:**
   ```js
   var bar = document.getElementById('edFloatBar');
   var rect = window.getSelection().getRangeAt(0).getBoundingClientRect();
   var barTop = parseFloat(bar.style.top);
   var barLeft = parseFloat(bar.style.left);
   console.assert(barTop >= 10, "Top boundary violation: " + barTop);
   console.assert(barLeft >= 10 && barLeft <= (window.innerWidth - bar.offsetWidth - 10), "Left boundary violation: " + barLeft);
   ```

---

## 7. Evidence and Reporting
- **Target Result Directory:** `08-gherkin-result-case-floating-selection-toolbar-and-clamping/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `float_bar_mounted.png` showing floating pill above selected text.
  2. Capture `float_bar_flipped_below.png` showing flipped placement at top boundary.
  3. Capture `float_bar_dismissed.png` proving dismissal after outside click.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/editor-floatbar/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/08-gherkin-result-case-floating-selection-toolbar-and-clamping/
     ```
  5. Include verification metrics in `result.md`.

### Pass/Fail Criteria
- [ ] Text selection reliably mounts `#edFloatBar.show`.
- [ ] Coordinates are clamped within viewport boundaries.
- [ ] Top inversion triggers when selection is near upper viewport edge.
- [ ] Clicking outside immediately dismisses `#edFloatBar`.
