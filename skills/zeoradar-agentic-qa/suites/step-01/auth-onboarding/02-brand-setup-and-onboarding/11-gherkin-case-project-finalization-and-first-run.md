# Test Case: Project Finalization Confirmation Modal, RPC Dispatch & Dashboard Hand-off

## 1. Case ID & Purpose
- **Case ID:** `TC-ONB-11-PROJECT-FINALIZATION`
- **Purpose:** Validate opening the execution confirmation modal (`.ob-exec-modal`), verifying itemized summary counts (Prompts, Personas, Keywords, Persona bindings), submitting project finalization via `onboarding-finalize`, triggering first visibility measurement run dispatch, and smoothly transferring the user to the active dashboard (`/#/`).

---

## 2. Tester Brief
From Step 5 with review completed, the tester clicks the primary action "Continue to finalize →" (`button.ob-prompts-continue`). The tester verifies that the modal dialog opens, displaying exact counts matching accepted review items. The tester confirms creation by clicking "Create project & start first run" (`submitPromptsExecution()`), observes the button loading state (`"Creating…"`), confirms backend response, asserts the success state (`"Your project is ready"`), and clicks "Go to dashboard →" to confirm seamless transition to `/#/`.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/onboarding`
- **Prerequisite State:** Step 5 (`activeStep === 5`), at least 1 prompt selected
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[PROJECT_NAME]`: Generated project name based on brand (`"[BRAND]"`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Onboarding Step 5 - Execution Modal and Project Creation

  Background:
    Given the user is on Step 5 of the onboarding wizard at "[APP_URL]/#/onboarding"
    And at least one prompt is selected in the review accordion

  @sanity @ui @modal
  Scenario: Clicking finalize button opens confirmation modal with accurate summary
    When the user clicks "button.ob-prompts-continue" ("Continue to finalize →")
    Then the modal overlay ".overlay.ob-dialog-overlay" should appear
    And the execution modal "section.ob-exec-modal" should be visible
    And the modal title "h2#ob-exec-title" should display "Create your project with these selections?"
    And the summary rows ".ob-live-summary-row" should accurately report:
      | category        |
      | Prompts         |
      | Personas        |
      | Keywords        |
      | Persona prompts |

  @positive @modal-cancellation
  Scenario: Clicking cancel or backdrop closes modal without submitting
    Given the execution modal is open
    When the user clicks "button.ob-modal-close" or the cancel button
    Then the modal "section.ob-exec-modal" should be removed from view
    And the active step should remain 5

  @positive @submission @finalization
  Scenario: Confirming creation dispatches RPC, schedules first run and enters dashboard
    Given the execution modal is open
    When the user clicks the confirm button ".ob-modal-foot button.btn.black"
    Then the button text should change to "Creating…"
    And the button should have attribute "disabled"
    And the backend RPC "onboarding-finalize" should be dispatched
    When the finalization call completes successfully
    Then the modal header should update to "Your project is ready"
    And summary details should show the Project Name and First Run scheduled date
    When the user clicks "Go to dashboard →"
    Then the active workspace should switch to the newly created project
    And the application should route to "[APP_URL]/#/"
```

---

## 5. Visual Checks
- **Modal Typography & Layout:**
  - Clean centered modal dialog (`max-width: 520px`, rounded corners 12px, backdrop blur).
  - Summary row icons: Prompts (doc), Personas (users), Keywords (sparkle), Persona prompts (layers).
- **Post-Finalize Success Screen:**
  - Success badge with animated checkmark or celebration icon.
  - Primary button text: `"Go to dashboard →"`.

---

## 6. Data & Network Checks
- **Finalize RPC Payload:**
  - Dispatches POST to `/functions/v1/onboarding-finalize` with payload:
    ```json
    {
      "workspaceId": "ws_...",
      "brand": "[BRAND]",
      "domain": "[DOMAIN]",
      "country": "[COUNTRY]",
      "locale": "[LANGUAGE]",
      "engineWeights": { "chatgpt": 35, "gemini": 35, "perplexity": 20, "claude": 10 },
      "topics": ["..."],
      "prompts": ["..."],
      "personas": ["..."]
    }
    ```
  - Response status: 200 OK with `{ projectId: "proj_...", firstRunDay: "2026-09-25" }`.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `11-gherkin-result-case-project-finalization-and-first-run/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, RPC execution telemetry, first run verification.
  - `evidence.json`: Finalize request payload and server response body.
  - `screenshots/01-finalize-modal-opened.png`: Open execution confirmation modal.
  - `screenshots/02-finalize-loading-state.png`: In-flight creation spinner.
  - `screenshots/03-finalize-success-screen.png`: "Your project is ready" dialog view.
  - `screenshots/04-dashboard-first-landed.png`: Active project dashboard with initial run queue.
- **MacBook Execution Protocol:** Ego Browser submits confirmation and captures final dashboard state on MacBook; assets retrieved via SCP.
