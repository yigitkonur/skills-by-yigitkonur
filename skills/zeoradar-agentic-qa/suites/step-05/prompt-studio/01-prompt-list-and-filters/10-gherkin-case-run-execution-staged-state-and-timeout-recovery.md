# Test Case 10: In-Flight Staged Run Tracking, 90s Timeout Alert & Polling Resumption

## 1. Case ID and Purpose
- **Case ID**: `TC-PLIST-10-STAGED-RUN-TIMEOUT`
- **Purpose**: Verify that an active replacement measurement run is strictly isolated in the staged publication state (`publicationState: 'staged'`, `"Staged replacement — not current"`), keeping existing published project metrics intact until sealed, and that if the 90-second client tracking budget expires (`onStop('limit')`), the UI displays the `"Live tracking stopped"` notice and allows operator resumption via `data-action="rn-resume-tracking"` without disrupting worker execution.

---

## 2. Tester Brief
The tester will:
1. Open the Measurement Run dialog on the Overview Cockpit at `[APP_URL]/#/[SLUG]/overview`.
2. Confirm run execution (with replacement token if applicable) via `button[data-action="rn-confirm"]` or `button[data-action="rn-start"]`.
3. Verify that the modal transitions to `view === 'started'`:
   - Headline displays: `"Measurement running — this dialog follows the authoritative run state."`
   - Run row displays status chip `"Running"`.
   - Publication chip displays `"Staged replacement — not current"`.
   - Analyzed cells increment dynamically as worker tasks complete.
4. Simulate tracking budget timeout (after 90 seconds or triggering orchestrator `onStop('limit')`).
5. Assert that:
   - Yellow alert banner appears stating `"Live tracking stopped"`.
   - Subtitle explains `"This dialog stopped following the run because the tracking time budget ran out. The run itself is unaffected and may still be going..."`.
   - A button `button[data-action="rn-resume-tracking"]` is rendered.
6. Click `button[data-action="rn-resume-tracking"]` and assert that live polling resumes immediately until status reaches `"Sealed"` and publication state transitions to `"Published · current"`.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/overview`
- **Watchdog Parameter**: 90,000 ms (`maxDurationMs: 90000`) polling limit in `assets/run-now.js`.
- **Dynamic Elements**:
  - Publication Chip: `span.badge` with text `"Staged replacement — not current"`
  - Timeout Banner: `.banner.mt8` with title `"Live tracking stopped"`
  - Resume Action: `button.btn.small[data-action="rn-resume-tracking"]`

---

## 4. Gherkin Scenario

```gherkin
Feature: Measurement In-Flight Staged Tracking & Watchdog Timeout Recovery

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Overview Cockpit at "[APP_URL]/#/[SLUG]/overview"
    And initiates an on-demand measurement run in the run modal

  @smoke @run-now @staged
  Scenario: In-flight replacement run is staged while preserving published data
    When the tester confirms execution via "button[data-action='rn-confirm']"
    Then the run dialog should transition to view "started"
    And the headline should read "Measurement running — this dialog follows the authoritative run state."
    And the run row status badge should display "Running"
    And the publication badge must display "Staged replacement — not current"
    And the background overview metrics must continue showing the existing published baseline

  @watchdog @timeout @recovery
  Scenario: Client polling timeout triggers tracking stopped alert and enables clean resumption
    Given the measurement run has been in-flight for over 90 seconds
    When the orchestrator triggers the polling limit stop event "onStop('limit')"
    Then the run modal should render the alert banner "Live tracking stopped"
    And the message should state "the tracking time budget ran out"
    And the action button "button[data-action='rn-resume-tracking']" should be visible
    When the tester clicks "button[data-action='rn-resume-tracking']"
    Then the tracking stopped banner should disappear
    And active polling should resume tracking the in-flight run
    And once all cells complete, the status should seal with publication badge "Published · current"
```

---

## 5. Visual Checks
1. **Running Status Indicator**: In-flight run displays accent colored `"Running"` chip and live cell counters (e.g. `64/192 cells analyzed`).
2. **Staged Publication Chip**: `.badge` renders with neutral/muted border and explicit text `"Staged replacement — not current"`.
3. **Timeout Banner**: When tracking stops, `.banner.mt8` renders with help icon, bold headline `"Live tracking stopped"`, and inline `"Resume tracking"` button.
4. **Sealed Completion State**: Headline updates to `"Run sealed and published."` with green check styling.

---

## 6. Data and Network Checks
1. **Staged State Verification**:
   ```javascript
   const startedRun = window.ZeoRunNow._testDlg && window.ZeoRunNow._testDlg.started;
   if (startedRun) {
     assert.strictEqual(startedRun.publicationState, 'staged', 'In-flight run must be marked staged');
   }
   ```
2. **Watchdog Resume Trigger**:
   ```javascript
   const resumeBtn = document.querySelector('button[data-action="rn-resume-tracking"]');
   assert.ok(resumeBtn !== null, 'Resume tracking button must be available upon timeout');
   // Click triggers rnStartLifecyclePolling() without re-dispatching run-now command
   ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-run-execution-staged-state-and-timeout-recovery/`
- **Execution Model Notice**: Ego Browser drives automation on macOS. Snapshots of the running staged state, timeout banner, and sealed completion are recorded to `/tmp/shots/run-staged-[STEP].png` and transferred via SCP.
- **Report Contents**:
  - `status.json`: Execution log and polling lifecycle duration.
  - `screenshot-run-staged.png`: In-flight staged run display.
  - `screenshot-timeout-banner.png`: 90-second timeout warning with resume button.
  - `screenshot-run-sealed.png`: Completed sealed run with published badge.
