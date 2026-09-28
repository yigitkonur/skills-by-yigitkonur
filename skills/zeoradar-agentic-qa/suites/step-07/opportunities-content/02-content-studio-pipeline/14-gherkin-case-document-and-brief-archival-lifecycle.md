# Test Case: TC-CS-14 - Content Project Archival & Restoration Lifecycle

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-14`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #91 (Revision History & Archival)
- **Traceability:** Maps to Source Scenario `TC-CS-12` (Archival & Restoration Lifecycle)
- **Purpose:** Test the document and brief archival lifecycle in the Content Studio dashboard (`.wf-table`), verifying that users can archive completed or deprecated projects via row actions, that archived assets are filtered out of active views and segregated under the "Archived" pill filter, and that clicking "Restore" returns an archived asset to active draft status with full content preserved.

---

## 2. Tester Brief
The tester will verify the archival and restoration workflow:
1. In the Workflows dashboard table (`.wf-table`), locating an active article or brief.
2. Clicking the row actions menu trigger (`.wf-actions-cell .icon-btn`) opens the dropdown menu.
3. Clicking "Archive" (`.wf-dropdown-item`):
   - Sets `project.status = "archived"`.
   - Immediately hides the project from the "All", "Content Generation", and "Optimization" views.
4. Clicking the "Archived" filter pill (`.wf-pill[data-filter="archived"]`):
   - Displays all archived projects and briefs.
   - The status pill renders with muted gray `.wf-status-pill.archived`.
   - The row actions cell displays an explicit **Restore** button (`restoreProject`).
5. Clicking "Restore":
   - Transitions status back to `"draft"`.
   - Removes it from the Archived list and restores it to the active working table.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Target Project Under Test `[ARTICLE_TITLE]`:** Existing article in Content Studio
- **Matching Result Directory:** `14-gherkin-result-case-document-and-brief-archival-lifecycle/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Content Studio Document Archival and Restoration Lifecycle

  Background:
    Given the user is on the Workflows dashboard for "[DOMAIN]"
    And the projects table ".wf-table" displays active articles

  Scenario: Archiving an Active Article from Row Actions
    When the user opens the actions dropdown for article "[ARTICLE_TITLE]"
    And the user selects the "Archive" action
    Then the article "[ARTICLE_TITLE]" should be removed from the active table view
    And a toast notification should confirm the project was archived

  Scenario: Viewing and Restoring an Archived Project
    When the user clicks the "Archived" filter pill ".wf-pill[data-filter='archived']"
    Then the table should display archived assets
    And the article "[ARTICLE_TITLE]" should be visible in the list
    And its status pill should have class ".archived"
    
    When the user clicks the "Restore" button for article "[ARTICLE_TITLE]"
    Then the article should disappear from the "Archived" table view
    
    When the user switches back to the "All" filter pill
    Then the article "[ARTICLE_TITLE]" should reappear in the active list
    And its status should be "Draft"
```

---

## 5. Visual Checks
1. **Filter Pills:** Segmented pill bar (`.wf-pill-segmented`) highlights the selected filter (`all`, `generation`, `optimization`, `archived`).
2. **Status Badges:**
   - Active drafts: Blue/Neutral badge.
   - Archived: Muted gray badge with padlock or archive icon.
3. **Restore Action:** Replaces the three-dots dropdown menu with a direct "Restore" button on archived rows for quick recovery.

---

## 6. Data and Network Checks
1. **Status Mutation:**
   ```js
   const proj = window.ContentStudioState.projects.find(p => p.title === "[ARTICLE_TITLE]");
   console.assert(proj.status === "archived", "Project status not updated to archived");
   ```
2. **Persistence Check:**
   - Verify `save-content-project` RPC is called with `{ status: "archived" }`.
   - Verify `localStorage` reflects the updated status.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `14-gherkin-result-case-document-and-brief-archival-lifecycle/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `row_actions_archive_clicked.png` showing archive dropdown option.
  2. Capture `archived_pill_view.png` showing archived table with Restore button.
  3. Capture `project_restored_to_active.png` showing restored draft in main table.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/content-archival/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/14-gherkin-result-case-document-and-brief-archival-lifecycle/
     ```
  5. Include verification checklist in `result.md`.

### Pass/Fail Criteria
- [ ] Archiving removes asset from active view instantly.
- [ ] Archived tab segregates archived projects accurately.
- [ ] Restore button returns project to draft status in active table.
- [ ] Article draft content and revisions remain completely intact through the archival cycle.
