# Test Case: TC-CS-10 - Revision History Snapshots & Immutability Contract

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-10`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #91 (Revision History & Archival)
- **Traceability:** Maps to Source Scenarios `TC-CS-09` (Revision Snapshot Creation) and `TC-CS-10` (Head Version Audit Restoration)
- **Purpose:** Validate the immutable versioning and audit history engine in the Content Studio. Test manual revision snapshot creation with custom notes and sequential `v(N+1).0` tagging, and assert the immutability contract during version restoration: restoring an older historical snapshot never deletes, truncates, or overwrites previous revisions; instead, it extracts the target draft, updates the canvas, and commits a brand-new sequential head revision explicitly attributed to the restored version tag.

---

## 2. Tester Brief
The tester will verify revision management in the History sidebar tab:
1. In an active article, clicking the "History" tab (`.ed-side-tab:nth-child(3)`) displays the revision timeline (`.ed-history-timeline`).
2. **Creating Snapshot:**
   - Clicking "Snapshot" (`button[data-action="create-snapshot"]`) prompts for an optional revision note.
   - Computes `nextVer = 'v' + (proj.history.length + 1) + '.0'`.
   - Adds snapshot card to the top of the timeline with author, timestamp, and version tag `v2.0`.
3. **Restoring Version (`restoreVersion(vTag)`):**
   - Clicking "Restore this version" on `v1.0` extracts its draft into `#edContentBody`.
   - **Immutability Invariant:** Does NOT roll back or truncate `v2.0`.
   - Commits a new head revision `v3.0` with note: `"Restored from v1.0"` / `"v1.0 sürümünden geri yüklendi"`.
   - History length increments from 2 to 3.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Initial Document State:** Project with initial revision `v1.0`
- **Matching Result Directory:** `10-gherkin-result-case-revision-history-snapshots-and-immutability/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Immutable Document Versioning and Audit Restoration

  Background:
    Given the user is editing an article in Content Studio
    And the document has an initial revision "v1.0"
    When the user clicks the "History" tab in the editor sidebar
    Then the revision timeline ".ed-history-timeline" should be visible

  Scenario: Creating a Manual Revision Snapshot
    Given the user edits the document draft in "#edContentBody"
    When the user clicks the "Snapshot" button in the History panel
    And the user enters the revision note "Updated competitor facts"
    Then a new revision card should appear at the top of the timeline
    And the new revision version tag should be "v2.0"
    And the new revision note should display "Updated competitor facts"
    And the total revision count should equal 2

  Scenario: Immutability Contract upon Restoring an Older Version
    Given the document has revisions "v2.0" (head) and "v1.0" (historical)
    When the user clicks "Restore this version" on revision "v1.0"
    Then the draft content in "#edContentBody" should revert to match "v1.0"
    And a brand-new head revision should be created with tag "v3.0"
    And the head revision note should state "Restored from v1.0"
    And the previous revision "v2.0" must still exist in the timeline
    And the total revision count should equal 3 (Zero history truncation)
```

---

## 5. Visual Checks
1. **History Timeline:** Vertical line with node dots representing revision points.
2. **Revision Cards:** `.ed-history-card` displays version tag badge (e.g. `v1.0`, `v2.0`), author label, timestamp (`"Just now"` / `"Az önce"`), and user note.
3. **Restore Button:** Present on non-head revisions as a subtle border button: `button.ed-hist-restore`.

---

## 6. Data and Network Checks
1. **Immutability Contract Assertion:**
   ```js
   const proj = window.ContentStudioState.projects.find(p => p.id === window.ContentStudioState.activeProjectId);
   console.assert(proj.history.length === 3, "History truncated during restore! Length: " + proj.history.length);
   console.assert(proj.history[0].version === "v3.0", "New head version mismatch: " + proj.history[0].version);
   console.assert(proj.history[0].note.includes("Restored from v1.0"), "Missing restore note attribution");
   console.assert(proj.history[1].version === "v2.0", "Prior version v2.0 lost");
   console.assert(proj.history[2].version === "v1.0", "Historical version v1.0 lost");
   ```
2. **Backend Persistence:**
   - Verify `save-content-project` RPC dispatches revision records to `public.content_studio_revisions`.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `10-gherkin-result-case-revision-history-snapshots-and-immutability/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `snapshot_v2_created.png` showing v2.0 added to timeline.
  2. Capture `version_v1_restored_as_v3.png` showing v3.0 head with preserved v2.0.
  3. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/content-revisions/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/10-gherkin-result-case-revision-history-snapshots-and-immutability/
     ```
  4. Include verification checklist in `result.md`.

### Pass/Fail Criteria
- [ ] Manual snapshot creates sequential version tag `v(N+1).0`.
- [ ] Restoring an older revision creates a new head revision.
- [ ] Full revision history is preserved without truncation or data loss.
- [ ] Editor canvas immediately updates with restored HTML draft.
