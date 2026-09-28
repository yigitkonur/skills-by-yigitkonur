# Test Case: TC-SNT-07 - Persona Builder Input Fallbacks, Diacritics & XSS Defense

## 1. Case ID and Purpose
- **Case ID:** `TC-SNT-07`
- **Module:** Answer Engine Insights (`assets/aei.js`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture, BMD-SNT-04)
- **Traceability:** Maps to Source Scenarios `SNT-22` and `SNT-23`
- **Purpose:** Verify that submitting the Custom Persona Builder modal with empty or whitespace-only inputs safely applies localized fallback values (`"Custom Executive Persona"`, `"General Industry"`, `"Formal & Analytical"`), and verify that entering arbitrary strings containing single/double quotes, Turkish diacritics, and script payloads sanitizes via `esc()`, preventing Cross-Site Scripting (XSS) while preserving faithful unicode string representation in `window.aeiState.customPersonas`.

---

## 2. Tester Brief
The tester or automated agent conducts adversarial and edge-case testing on the Persona Builder inputs:
1. Open the persona builder modal.
2. Clear all input fields completely or enter pure whitespace spaces (`"   "`).
3. Click `Save Persona`:
   - Verify the modal does not crash or corrupt state.
   - Confirm fallback defaults are assigned:
     - Role defaults to `"Custom Executive Persona"` (EN) or `"Özel Yönetici Personası"` (TR).
     - Industry defaults to `"General Industry"` (EN) or `"Genel Sektör"` (TR).
     - Tone defaults to `"Formal & Analytical"` (EN) or `"Resmi ve Analitik"` (TR).
4. Re-open the modal and enter adversarial strings containing quotes, Turkish diacritics, and HTML tags:
   - Role: `<script>alert('xss')</script> "İhracat Direktörü"`
   - Industry: `Toptan & Perakende 'Sektörü'`
5. Click `Save Persona`:
   - Verify no alert popups or unescaped script execution occur.
   - Confirm the rendered card safely displays the sanitized text without DOM injection.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=perception`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Adversarial Input Payload:** `<script>alert('xss')</script> "İhracat Direktörü"`
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `07-gherkin-result-case-persona-builder-input-fallbacks-and-sanitization/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Persona Builder Empty Input Fallbacks and Special Character Sanitization

  Background:
    Given the user is on the "perception" workspace of Zeo Geo-Radar
    And the custom persona builder modal is open

  Scenario Outline: Applying Localized Fallbacks for Empty or Whitespace Inputs
    When the user enters "<EmptyValue>" into "input#aeiPersonaRole"
    And the user enters "<EmptyValue>" into "input#aeiPersonaIndustry"
    And the user clicks "button[data-action='aei-save-persona']"
    Then the new persona card in ".aei-persona-grid" should display role "<ExpectedRole>"
    And the new persona card should display industry "<ExpectedIndustry>"
    And the modal should be closed cleanly

    Examples:
      | EmptyValue | ExpectedRole (EN)        | ExpectedIndustry (EN) |
      |            | Custom Executive Persona | General Industry      |
      |            | Custom Executive Persona | General Industry      |

  Scenario: Sanitization of Quotes, Turkish Diacritics, and XSS Injections
    When the user enters '<script>alert("xss")</script> "İhracat Direktörü"' into "input#aeiPersonaRole"
    And the user enters "Gıda & Şekerleme 'Sektörü'" into "input#aeiPersonaIndustry"
    And the user clicks "button[data-action='aei-save-persona']"
    Then the modal should close without executing any JavaScript alert dialogs
    And the rendered role in ".aei-p-head strong" should contain escaped text
    And no "<script>" HTML tags should be injected into the DOM
    And Turkish characters "İ", "ş", "ö" should be preserved legibly
```

---

## 5. Visual Checks
1. **Fallback Card Rendering:** The generated persona card displays `"Custom Executive Persona"` and `"General Industry"` cleanly without empty blanks.
2. **Special Characters:** Quotation marks and ampersands render as literal readable characters without raw entity glitches (e.g. `&amp;` double encoding).
3. **Typography:** Turkish diacritics (`İ`, `ı`, `ş`, `ç`, `ö`, `ü`, `ğ`) render in the native font family without tofu glyphs or fallback substitutions.

---

## 6. Data and Network Checks
1. **State String Inspection:**
   ```js
   const personas = window.aeiState.customPersonas;
   const p = personas[personas.length - 1];
   assert(p.role.includes("İhracat"), "Unicode Turkish characters must be preserved in state");
   ```
2. **DOM Security Check:**
   ```js
   const scripts = document.querySelectorAll(".aei-p-card script");
   assert(scripts.length === 0, "No script tags may be injected into persona cards");
   ```

---

## 7. Evidence and Reporting
- **Target Result Directory:** `07-gherkin-result-case-persona-builder-input-fallbacks-and-sanitization/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`empty_input_fallbacks.png`, `sanitized_special_chars.png`, `turkish_diacritics_card.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/sentiment/tc-snt-07-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/02-sentiment-and-audience/07-gherkin-result-case-persona-builder-input-fallbacks-and-sanitization/screenshots/
     ```
  4. Write execution report `result.md` verifying sanitized strings, fallback values, and security assertions.

### Pass/Fail Criteria
- [ ] Empty or whitespace inputs trigger localized fallbacks.
- [ ] Special characters and quotes render safely without XSS.
- [ ] Turkish diacritics are preserved accurately.
- [ ] Modal closes and updates the persona grid without errors.
