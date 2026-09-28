# Test Case: TC-CS-05 - SSE Stream Disconnection & Partial Draft Rescue

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-05`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #46 (Content Studio Pipeline, Facts Grounding & AI Streaming)
- **Traceability:** Maps to Source Scenario `TC-CS-13` (SSE Stream Disconnection & Partial Draft Rescue)
- **Purpose:** Test network resilience and error handling during live AI SSE streaming. When an active streaming connection to `/api/chat` is interrupted or severed mid-transmission, the system must execute differentiated recovery: if partial tokens were already accumulated (`fullContent.trim().length > 0`), the rescue handler invokes `finalizeDraft(fullContent)` to salvage the draft into the editor with zero data loss; if zero tokens were received, the error handler traps the failure, rendering `.wiz-error-box` with an actionable "Retry Generation ↻" CTA.

---

## 2. Tester Brief
The tester will simulate network interruptions during AI draft streaming across two distinct operational boundaries:
1. **Condition A: Mid-Stream Disconnection (Partial Tokens Buffered):**
   - After receiving 100+ tokens, the network stream is abruptly aborted or rejects with a network error.
   - The stream reader's catch block (lines 2720–2729 of `assets/content-studio.js`) detects `fullContent.trim().length > 0`.
   - Instead of discarding the user's generated tokens, it executes the **Partial Draft Rescue Path**:
     - Calls `finalizeDraft(fullContent)`.
     - Injects accumulated content into `#edContentBody`.
     - Sets `state.view = "editor"`, preserving all received content.
2. **Condition B: Immediate Disconnection (Zero Tokens Buffered):**
   - The connection fails immediately upon dispatch before any SSE chunks arrive.
   - `fullContent.trim()` is empty.
   - The stream reader executes `handleGenerationFailure(streamErr)`.
   - Sets `wiz.isGeneratingDraft = false`.
   - Renders `.wiz-error-box` with a clear explanation of the network error and a prominent "Retry Generation ↻" button.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Matching Result Directory:** `05-gherkin-result-case-stream-disconnection-and-partial-draft-rescue/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: SSE Stream Disconnection and Partial Draft Rescue

  Background:
    Given the user is on Step 4 of the Content Creation Wizard
    And draft generation has been initiated

  Scenario: Mid-Stream Disconnection Triggers Partial Draft Rescue Path (Zero Data Loss)
    Given the SSE stream has buffered at least 150 tokens of partial content
    When the network connection to "/api/chat" is abruptly aborted
    Then the stream error catch block should detect non-empty buffered content
    And "finalizeDraft(fullContent)" should be called
    And the application view should automatically transition to "editor"
    And the editor canvas "#edContentBody" should contain the rescued partial article
    And no error crash screen should be displayed

  Scenario: Immediate Connection Failure Triggers Actionable Error Box
    Given zero tokens have been received from "/api/chat"
    When the fetch request rejects with a network connection error
    Then the wizard state "isGeneratingDraft" should be set to false
    And the wizard should remain in Step 4
    And the error container ".wiz-error-box" should be mounted in the DOM
    And the error box should contain an explicit "Retry Generation ↻" button
    When the user clicks "Retry Generation ↻"
    Then the error box should clear and draft streaming should restart
```

---

## 5. Visual Checks
1. **Rescued Editor View:** When partial draft is rescued, the editor mounts `#edContentBody` with an amber notice or standard draft text preserving all headings and paragraphs received up to the disconnect.
2. **Error Box UI:** `.wiz-error-box` renders with red border tint, warning triangle icon (`⚠️`), clear descriptive failure text, and primary button `button.btn.black` with text `"Retry Generation ↻"` / `"Yeniden Dene ↻"`.

---

## 6. Data and Network Checks
1. **Catch Block Logic Inspection:**
   ```js
   .catch(function (streamErr) {
     var isMockTransport = window.ZEO_DATA_PROVIDER && typeof window.ZEO_DATA_PROVIDER.getTransport === 'function' && window.ZEO_DATA_PROVIDER.getTransport() === 'mock';
     if (!isMockTransport && (!fullContent || !fullContent.trim())) {
       handleGenerationFailure(streamErr);
       resolveStream();
       return;
     }
     finalizeDraft(fullContent);
     resolveStream();
   });
   ```
2. **Rescued Word Count:** Verify that `#edContentBody.innerText.split(/\s+/).length` matches the token buffer size.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `05-gherkin-result-case-stream-disconnection-and-partial-draft-rescue/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `stream_abort_rescued_editor.png` verifying partial draft rescue in editor.
  2. Capture `stream_zero_tokens_error_box.png` verifying error box and retry CTA.
  3. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/content-rescue/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/05-gherkin-result-case-stream-disconnection-and-partial-draft-rescue/
     ```
  4. Include verification checklist in `result.md`.

### Pass/Fail Criteria
- [ ] Mid-stream abort rescues partial content into `#edContentBody` without crashing.
- [ ] Immediate connection error renders `.wiz-error-box`.
- [ ] Error box displays actionable "Retry Generation ↻" button.
- [ ] Clicking retry resets error state and initiates a fresh request.
