# Test Case: TC-CS-11 - Revision Restoration with Dirty In-Flight Edits

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-11`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #91 (Revision History & Archival)
- **Traceability:** Maps to Source Scenario `TC-CS-18` (Version History Restoration with Dirty Unsaved Edits & Immutable Snapshot Head)
- **Purpose:** Test edge-case resilience when restoring historical revisions while the editor contains unpersisted, dirty scratch edits in `#edContentBody`. Assert that the restoration engine cleanly replaces uncommitted scratch text with the historical revision's canonical HTML, generates a new sequential head version snapshot without corrupting the committed audit trail, and avoids throwing runtime errors or leaving mixed content fragments on the canvas.

---

## 2. Tester Brief
The tester will verify editor behavior during dirty-state restoration:
1. An article has at least two committed revisions (`v1.0` and `v2.0`).
2. The user types uncommitted scratch text into `#edContentBody` (e.g. `<p>DIRTY SCRATCH CONTENT THAT SHOULD BE OVERWRITTEN BY RESTORATION</p>`) without taking a manual snapshot.
3. The user opens the History tab and clicks "Restore this version" on `v1.0`.
4. **Behavioral Invariants:**
   - Unsaved scratch text is cleanly discarded.
   - Canvas `#edContentBody` is completely overwritten with the clean HTML of `v1.0`.
   - A new head revision `v3.0` is committed with note `"Restored from v1.0"`.
   - Committed history entries `v1.0` and `v2.0` remain completely intact.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Matching Result Directory:** `11-gherkin-result-case-revision-restoration-with-dirty-unsaved-edits/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Restoring Prior Revision Overwrites In-Flight Scratch Edits Safely

  Background:
    Given the user is editing an article with committed revisions "v1.0" and "v2.0"
    And the current head version is "v2.0"

  Scenario: Dirty Scratch Edits Are Discarded in Favor of Canonical Restored Version
    Given the user types dirty scratch text "DIRTY UNCOMMITTED TEXT" into "#edContentBody"
    And no manual snapshot is taken for these scratch edits
    When the user navigates to the History tab and clicks "Restore this version" on "v1.0"
    Then the editor canvas "#edContentBody" should NOT contain "DIRTY UNCOMMITTED TEXT"
    And the canvas HTML should exactly match the draft of revision "v1.0"
    And a new head revision "v3.0" should be unshifted into the timeline
    And the head revision note should state "Restored from v1.0"
    And prior revisions "v1.0" and "v2.0" should be preserved immutably
```

---

## 5. Visual Checks
1. **Canvas Cleanliness:** After restoration, no lingering remnants or corrupted fragments of the dirty scratch text appear in the editor.
2. **Timeline Integrity:** Revision cards update instantly, showing `v3.0` at the top of the list, followed by `v2.0` and `v1.0`.
3. **Sidebar Stats Recalculation:** Word count, headings, and readability immediately update to reflect the restored `v1.0` content.

---

## 6. Data and Network Checks
1. **Draft Replacement Verification:**
   ```js
   const edBody = document.getElementById('edContentBody');
   console.assert(!edBody.innerHTML.includes('DIRTY UNCOMMITTED TEXT'), "Dirty text leaked into restored canvas!");
   ```
2. **Sequential Version Counter:**
   - Verify `nextVer` calculation: `'v' + (proj.history.length + 1) + '.0'`.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `11-gherkin-result-case-revision-restoration-with-dirty-unsaved-edits/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `dirty_scratch_text_in_canvas.png` showing in-flight dirty content.
  2. Capture `restored_canvas_clean_v1.png` proving complete replacement with v1.0.
  3. Capture `history_timeline_v3_head.png` showing immutable 3-version history.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/content-dirty-restore/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/11-gherkin-result-case-revision-restoration-with-dirty-unsaved-edits/
     ```
  5. Include verification checklist in `result.md`.

### Pass/Fail Criteria
- [ ] Dirty in-flight scratch edits are discarded upon version restoration.
- [ ] Historical draft completely and accurately populates `#edContentBody`.
- [ ] New sequential head revision `v(N+1).0` is generated with correct attribution.
- [ ] Previous committed revisions remain unaltered in timeline and memory.
