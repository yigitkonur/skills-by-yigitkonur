# Test Case 09: Discovered Candidate Batch Commit, Counters & Table Synchronization

## 1. Case ID and Purpose
- **Case ID**: `TC-PCREAT-09-COMMIT-IMPORT`
- **Purpose**: Verify that clicking the commit action in Step 3 of the AI Discovery Wizard dispatches the batch command `import-discovered-prompts` containing strictly selected items, closes the wizard cleanly, renders actionable import/skip summary toasts, and automatically refreshes the master prompt table and capacity counters via `dgReload()`.

---

## 2. Tester Brief
The tester will:
1. Open the AI Discovery review matrix with 8 candidate items (e.g. 7 novel items selected, 1 duplicate item unselected).
2. Verify that the Commit button `button[data-action="dg-discover-commit"]` reflects the selected count (e.g. `"Import 7 Prompts"`).
3. Click the Commit button.
4. Verify that:
   - Command `import-discovered-prompts` is dispatched to the server.
   - The wizard modal closes.
   - A success toast notification appears detailing the import result (e.g. `"7 prompts imported successfully, 1 duplicate skipped"`).
   - The master table reloads and displays the 7 newly imported prompts.
   - The capacity counter in `.count-pill b` increments by 7.
   - The SVG capacity ring stroke expands proportionally.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial State**: Wizard Step 3 with verified candidates.
- **Commit Trigger**: `button.btn.small.black[data-action="dg-discover-commit"]`
- **Capacity Counter**: `.count-pill b`

---

## 4. Gherkin Scenario

```gherkin
Feature: Discovered Candidate Batch Import & Workbench Synchronization

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And the AI Discovery Wizard is mounted on Step 3 with 7 selected novel prompts and 1 unselected duplicate

  @smoke @ai-wizard @import
  Scenario: Commit selected candidates and verify database insertion and counter updates
    Given the capacity counter in ".count-pill b" reads "40"
    When the tester clicks the commit button "button[data-action='dg-discover-commit']"
    Then the command "import-discovered-prompts" should be dispatched with 7 items
    And the discovery wizard overlay should close
    And a toast notification should confirm:
      """
      7 prompts imported successfully
      """
    And the master prompt table "table.tbl.dg-tbl" should reload
    And all 7 imported prompts should be visible in the table
    And the capacity counter ".count-pill b" should increment to "47"
    And the SVG capacity circle should recalculate to "18.894 40.2"
```

---

## 5. Visual Checks
1. **Commit Button Readout**: Commit button displays clear call-to-action text: `"Import N Prompts"` (Turkish: `"N Promptu İçe Aktar"`).
2. **Success Toast**: Appears at top-center with emerald border and text summarizing imported vs skipped prompts.
3. **Table Refresh**: Table rows populate without requiring a full browser page refresh.

---

## 6. Data and Network Checks
1. **Import Command Payload**:
   - Verify `import-discovered-prompts` payload:
     ```json
     {
       "projectId": "[PROJECT_ID]",
       "items": [
         {
           "text": "Daikin Altherma 3 Isı Pompası",
           "topicName": "Seasonal Collections",
           "type": "non_brand",
           "country": "US",
           "locale": "en",
           "intent": "comm"
         }
       ]
     }
     ```
2. **Server Response Verification**:
   - Response `{ ok: true, data: { insertedCount: 7, skippedCount: 1 } }`.

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-ai-review-selective-commit-and-import/`
- **Execution Model Notice**: Automated via Ego Browser on macOS. Screenshots of the commit action, toast notification, and refreshed workbench are recorded to `/tmp/shots/discovery-import-[STEP].png` and retrieved via SCP.
- **Report Contents**:
  - `status.json`: Test execution log and command round-trip latency.
  - `screenshot-commit-modal.png`: Review step showing commit button.
  - `screenshot-import-toast.png`: Confirmation toast with import/skip counts.
  - `screenshot-table-reloaded.png`: Master table displaying newly imported prompts and updated capacity ring.
