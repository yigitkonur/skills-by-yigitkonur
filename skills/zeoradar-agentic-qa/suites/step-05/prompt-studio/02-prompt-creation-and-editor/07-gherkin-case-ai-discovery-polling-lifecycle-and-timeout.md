# Test Case 07: Asynchronous AI Task Polling, Stage Animations & 40s Timeout Handling

## 1. Case ID and Purpose
- **Case ID**: `TC-PCREAT-07-AI-POLLING-TIMEOUT`
- **Purpose**: Verify that Step 2 (Synthesis) of the AI Discovery Wizard dispatches the background task to Trigger.dev (`suggest-project-prompts`), renders animated loading feedback and dynamic worker stage text, and manages the 40-second / 30-tick polling watchdog budget, advancing to Review on completion or gracefully transitioning to the Error recovery step (`state.step = 'error'`) upon polling budget expiration.

---

## 2. Tester Brief
The tester will:
1. Open the AI Discovery Wizard in the Prompt Designer Workbench.
2. Configure topics and click `button[data-action="dg-discover-generate"]`.
3. Verify that the wizard shifts to Step 2 (`dispatching` / `polling`):
   - Loading title displays `"Generating Prompts via AI"`.
   - Sparkle animation `.wizard-spark` and progress bar `.wizard-progress-fill` are visible.
   - Dynamic status text updates as worker milestones occur (`"Analyzing brand topics…"`, `"Generating prompt queries…"`).
4. Verify standard happy-path progression to Step 3 (Review) upon worker completion.
5. In a simulated stalled worker scenario (exceeding 40s or triggering `onStop('limit')`):
   - Verify that polling halts cleanly without infinite loops.
   - Verify the wizard shifts to Step 4 (Error).
   - Verify error banner displays `dependency_unavailable` (or server timeout notice).
   - Assert that the retry button `button[data-action="dg-discover-retry"]` is enabled and re-dispatches the job.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/prompts?workspace=designer`
- **Polling Watchdog Budget**: 40 seconds / 30 maximum ticks.
- **Component Selectors**:
  - Loading Title: `.wizard-load-title`
  - Dynamic Stage: `.wizard-stage`
  - Progress Bar: `.wizard-progress-fill`
  - Error Step Root: `.zr-wizard.wizard-frame` with step `'error'`
  - Retry Trigger: `button[data-action="dg-discover-retry"]`

---

## 4. Gherkin Scenario

```gherkin
Feature: AI Discovery Polling Watchdog Lifecycle & Timeout Recovery

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the AI Discovery Wizard at "[APP_URL]/#/[SLUG]/prompts?workspace=designer"
    And has configured topics in Step 1

  @smoke @ai-wizard @polling
  Scenario: Dispatch AI generation task and observe live stage updates until completion
    When the tester clicks the generate button "button[data-action='dg-discover-generate']"
    Then the wizard should transition to the loading step
    And the title ".wizard-load-title" should display "Generating Prompts via AI"
    And the progress bar ".wizard-progress-fill" should animate
    And the stage description ".wizard-stage" should update dynamically
    When the background Trigger.dev worker completes successfully
    Then the wizard should transition to step "review"
    And the review curation table should be rendered

  @watchdog @timeout @error
  Scenario: Worker stall exceeding 40-second polling budget transitions to error step with retry
    Given the tester dispatches the AI generation task
    When the worker remains unsealed beyond the 40-second polling limit
    And the orchestrator triggers "onStop('limit')"
    Then the wizard should transition to step "error"
    And the modal should render an error banner with "dependency_unavailable"
    And the retry button "button[data-action='dg-discover-retry']" should be visible
    When the tester clicks the retry button
    Then the wizard should re-enter the loading step and dispatch a new generation task
```

---

## 5. Visual Checks
1. **Loading State Presentation**: Sparkle icon (`✨`) animates above title `"Generating Prompts via AI"`. Progress bar width smoothly expands.
2. **Error State Presentation**: Red accent banner (`style*="#fee2e2"`) appears containing error details and diagnostic configuration guidance for `TRIGGER_SECRET_KEY` and AI Gateway.

---

## 6. Data and Network Checks
1. **Polling Orchestration Audit**:
   ```javascript
   const designerState = window.ZEO_PROMPT_DESIGNER._getState();
   if (designerState.step === 'polling') {
     assert.ok(designerState.batchId !== null, 'Active batchId must be tracked during polling');
   }
   ```
2. **Timeout Transition Check**:
   ```javascript
   // Verify onStop callback transitions to error step
   assert.strictEqual(window.ZEO_PROMPT_DESIGNER._getState().step, 'error', 'Timeout must transition step to error');
   ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-ai-discovery-polling-lifecycle-and-timeout/`
- **Execution Model Notice**: Automated through Ego Browser on macOS. Screen captures of the loading animation and error dialog are stored in `/tmp/shots/discovery-polling-[STEP].png` and pulled via SCP.
- **Report Contents**:
  - `status.json`: Execution verdict, polling duration, and tick count.
  - `screenshot-polling-loading.png`: In-flight loading animation with stage copy.
  - `screenshot-timeout-error.png`: Step 4 error display with retry button.
