# Test Case: TC-CS-06 - AI Gateway HTTP Error Traps & Rate Limit Retry Loop

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-06`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #46 (Content Studio Pipeline, Facts Grounding & AI Streaming)
- **Traceability:** Maps to Source Scenarios `TC-CS-05` (AI Gateway 401/403/429 Error Traps) and `TC-CS-14` (AI Gateway HTTP 429 Rate Limit State & "Retry ↻" Recovery)
- **Purpose:** Test resilience against upstream AI Gateway API failures, verifying that HTTP 401 (Unauthorized), HTTP 403 (Forbidden), and HTTP 429 (Rate Limit / Quota Exceeded) status codes are cleanly classified and trapped, rendering an actionable error box (`.wiz-error-box`) with exact user guidance and a prominent "Retry Generation ↻" button that re-initiates generation upon click.

---

## 2. Tester Brief
The tester will simulate various HTTP error responses from `/api/chat`:
1. **HTTP 401 / 403 (Auth/Credentials):** Displays message: `"AI Gateway authentication error (HTTP 401/403). Please check your API credentials."`.
2. **HTTP 429 (Rate Limit / Quota):** Displays message: `"AI Gateway quota or rate limit exceeded (HTTP 429). Please retry shortly."` (`Yapay zeka ağ geçidi kota veya hız sınırı aşıldı (HTTP 429)`).
3. In all error conditions:
   - Sets `wiz.isGeneratingDraft = false`.
   - Sets `wiz.generationError = errorMessage`.
   - Mounts `.wiz-error-box`.
   - Renders button: `<button type="button" class="btn black" onclick="ContentStudio.wizardGenerateContent()">Retry Generation ↻</button>`.
4. **Recovery Verification:**
   - Clicking "Retry Generation ↻" resets `wiz.generationError = null`, sets `wiz.isGeneratingDraft = true`, clears `wiz.streamingDraft`, and dispatches a fresh request.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Simulated HTTP Status Codes:** `401`, `403`, `429`
- **Matching Result Directory:** `06-gherkin-result-case-ai-gateway-http-errors-and-rate-limit-retry/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: AI Gateway HTTP Error Classification and Rate Limit Retry Recovery

  Background:
    Given the user is on Step 3 of the Content Creation Wizard
    And candidate title and platforms are configured
    And the user clicks "Generate Content & Brief"

  Scenario Outline: Trapping Specific AI Gateway HTTP Error Codes
    When the endpoint "/api/chat" responds with HTTP status "<StatusCode>"
    Then the wizard should remain in Step 4
    And the streaming state "wizard.isGeneratingDraft" should be false
    And the error container ".wiz-error-box" should be mounted in the DOM
    And the error message should contain "<ExpectedErrorMessage>"
    And the error box should render an explicit "Retry Generation ↻" button

    Examples:
      | StatusCode | ExpectedErrorMessage                                           |
      | 401        | AI Gateway authentication error (HTTP 401/403)                  |
      | 403        | AI Gateway authentication error (HTTP 401/403)                  |
      | 429        | AI Gateway quota or rate limit exceeded (HTTP 429)              |

  Scenario: Rate Limit Recovery via Actionable Retry Button
    Given the wizard is displaying the HTTP 429 error box ".wiz-error-box"
    When the rate limit period expires and the user clicks "Retry Generation ↻"
    Then the wizard state "generationError" should be cleared to null
    And the streaming state "isGeneratingDraft" should be set back to true
    And the error box ".wiz-error-box" should be unmounted
    And a new streaming request to "/api/chat" should be dispatched
```

---

## 5. Visual Checks
1. **Error Box Design:** `.wiz-error-box` has distinctive border, alert icon, and localized text.
2. **Retry Button Affordance:** Black button with circular arrow icon (`↻`) and high visual affordance.
3. **No Synthetic Fallback Slop:** Verify that in non-mock transport modes, the application does not silently pretend generation succeeded when the API actually failed.

---

## 6. Data and Network Checks
1. **Status Code Mapping:**
   ```js
   if (status === 401 || status === 403) {
     errMessage = T('AI Gateway authentication error (HTTP 401/403). Please check your API credentials.', '...');
   } else if (status === 429) {
     errMessage = T('AI Gateway quota or rate limit exceeded (HTTP 429). Please retry shortly.', '...');
   }
   ```
2. **State Cleanup on Retry:** Verify `ContentStudioState.wizard.generationError` is null after retry click.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `06-gherkin-result-case-ai-gateway-http-errors-and-rate-limit-retry/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `error_box_http429.png` showing rate limit message and retry button.
  2. Capture `error_box_http401.png` showing authentication error message.
  3. Capture `retry_initiated.png` confirming restart of stream.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/content-http-errors/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/06-gherkin-result-case-ai-gateway-http-errors-and-rate-limit-retry/
     ```
  5. Include verification metrics in `result.md`.

### Pass/Fail Criteria
- [ ] HTTP 401, 403, and 429 produce designated error notices.
- [ ] No silent fallbacks or deceptive synthetic content appear on real failures.
- [ ] Actionable "Retry Generation ↻" button resets error and triggers new request.
