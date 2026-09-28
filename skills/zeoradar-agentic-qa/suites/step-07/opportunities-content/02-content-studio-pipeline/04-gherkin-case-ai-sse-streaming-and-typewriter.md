# Test Case: TC-CS-04 - AI SSE Streaming Draft Generation & Background Resilience

## 1. Case ID and Purpose
- **Case ID:** `TC-CS-04`
- **Module:** Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)
- **Parent Contract:** Issue #46 (Content Studio Pipeline, Facts Grounding & AI Streaming)
- **Traceability:** Maps to Source Scenarios `TC-CS-04` (AI SSE Streaming Draft Generation) and `TC-CS-15` (Background Draft Generation Resilience across View / Subtab Switches)
- **Purpose:** Test Step 4 of the Content Creation Wizard, validating that triggering draft generation dispatches a streaming HTTP request (`POST /api/chat` with `{ stream: true }`), parses incoming Server-Sent Events (`data: {...}` lines), appends token text to `#wizLiveTokenOutput` via real-time typewriter ticker, increments the streaming token counter, and maintains background execution resilience if the user navigates between subtabs or views while generation is in flight, seamlessly transitioning into the AEO Editor upon completion.

---

## 2. Tester Brief
The tester will verify the streaming mechanics and background stability:
1. Advancing through the wizard to Step 3 and clicking "Generate Content & Brief →" invokes `ContentStudio.wizardGenerateContent()`.
2. The wizard advances to Step 4, setting `wiz.isGeneratingDraft = true`.
3. The stream reader parses incoming SSE chunks:
   - Evaluates `data: {...}` lines.
   - Extracts `parsed.choices[0].delta.content`.
   - Appends incoming markdown/HTML tokens into `#wizLiveTokenOutput` inside `.wiz-streaming-preview`.
   - Live token counter (`.wiz-streaming-counter`) increments dynamically (e.g. `245 tokens streamed`).
4. **Background Navigation Invariant:** If the user clicks another tab (e.g. `ContentStudio.switchTab('tools')`) during streaming, the SSE reader continues buffering in global memory without aborting.
5. On stream completion, `finalizeDraft()` persists the project and switches `ContentStudioState.view = "editor"`, mounting `#edContentBody` with the complete generated article.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/workflows`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Matching Result Directory:** `04-gherkin-result-case-ai-sse-streaming-and-typewriter/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: AI SSE Streaming Token Pipeline and Background Generation Resilience

  Background:
    Given the user is on Step 3 of the Content Creation Wizard
    And a candidate title and target AI engines are configured
    When the user clicks the "Generate Content & Brief" button

  Scenario: Real-Time SSE Stream Consumption and Typewriter Output
    Then the wizard should advance to Step 4
    And the streaming preview container ".wiz-streaming-preview" should mount
    And the token output element "#wizLiveTokenOutput" should be visible
    And the streaming state "wizard.isGeneratingDraft" should equal true
    
    When SSE data chunks are received from "/api/chat"
    Then the text in "#wizLiveTokenOutput" should accumulate incrementally
    And the token counter ".wiz-streaming-counter" should increment above 50
    
    When the stream reader completes
    Then the wizard state "isGeneratingDraft" should become false
    And the application view should automatically transition to "editor"
    And the editor canvas "#edContentBody" should contain the finalized article

  Scenario: Background Draft Generation Resilience across Tab Switching
    Given AI draft generation is actively streaming in Step 4
    When the user switches to the "tools" subtab during active token streaming
    Then the stream reader should continue buffering incoming SSE tokens in memory
    When the streaming finishes in the background
    Then "finalizeDraft()" should execute atomically
    And the new project should be persisted to storage
    And returning to the editor should reveal the complete generated draft without data loss
```

---

## 5. Visual Checks
1. **Streaming Animation:** Step 4 displays a pulsing indicator, live token counter, and scrolling text box.
2. **Typewriter Effect:** `#wizLiveTokenOutput` renders monospace or clean text with a blinking caret (`|`) at the end of incoming text.
3. **Editor Transition:** On completion, the screen smoothly transitions to the full AEO Editor layout without a full page refresh.

---

## 6. Data and Network Checks
1. **Request Payload Inspection:**
   - Endpoint: `POST /api/chat`
   - Headers: `Content-Type: application/json`
   - Body contains: `{ stream: true, messages: [...] }`.
2. **Grounding Prompts Presence:**
   - Prompt contains `# BRAND GROUND TRUTH` (verified facts).
   - Prompt contains `# TARGET KEYWORD & CITATION GAPS`.
3. **Stream Chunk Format:**
   ```
   data: {"id":"chatcmpl-...","choices":[{"delta":{"content":"[BRAND]"}}]}
   ```

---

## 7. Evidence and Reporting
- **Target Result Directory:** `04-gherkin-result-case-ai-sse-streaming-and-typewriter/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `streaming_typewriter_active.png` showing live token stream and counter.
  2. Capture `background_tab_switched.png` proving token accumulation continues.
  3. Capture `stream_completed_editor.png` verifying finalized draft in editor canvas.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/content-streaming/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/04-gherkin-result-case-ai-sse-streaming-and-typewriter/
     ```
  5. Include verification metrics in `result.md`.

### Pass/Fail Criteria
- [ ] SSE stream consumes chunks and increments token counter.
- [ ] `#wizLiveTokenOutput` renders text dynamically without crashing.
- [ ] Switching subtabs or views during generation does not interrupt the stream.
- [ ] On completion, view transitions cleanly to `editor` with populated draft.
