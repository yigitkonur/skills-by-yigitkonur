# Test Case: TC-OPP-10 - Contextual Competitor Mapping Modal Validation & Sanitization

## 1. Case ID and Purpose
- **Case ID:** `TC-OPP-10`
- **Module:** Opportunities Engine (`assets/opportunities.js`, `assets/opportunities.css`)
- **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage & Gap Analysis Pipeline)
- **Traceability:** Maps to Source Scenarios `TC-OPP-12` (Inline Competitor Mapping Modal) and `TC-OPP-17` (Competitor Mapping Modal Input Validation & Domain Sanitization)
- **Purpose:** Test opening the inline competitor mapping modal (`.opps-btn-add-comp`), verify strict defensive validation and domain sanitization boundaries when invalid, empty, or protocol-only domain inputs are submitted, and verify that upon providing valid competitor credentials, the active profile is updated and the opportunity backlog is dynamically recalculated to reflect newly detected competitor citation gaps.

---

## 2. Tester Brief
The tester will verify the competitor mapping modal's validation defenses and data pipeline:
1. Clicking `.opps-btn-add-comp` mounts the modal inside `#modalHolder` with inputs `#oppNewCompName` and `#oppNewCompDomain`.
2. **Defensive Validation Boundary 1 (Empty inputs):** Submitting with both fields blank displays an error toast: `"Please provide both competitor name and domain."` (`Lütfen hem rakip adı hem de alan adı girin.`), keeps `#modalHolder` mounted, and makes no changes to the profile.
3. **Defensive Validation Boundary 2 (Sanitization collision):** Submitting a competitor name with an invalid protocol-only string (`https://` or `http://www.`) causes the domain sanitizer `cleanDomain()` to strip the entire string to `""`. The validation check `!compDomain` catches this, displays the error toast, keeps the modal open, and protects the profile from corrupted entries.
4. **Happy Path:** Submitting a valid competitor (e.g. `[COMPETITOR_NAME]` and `[COMPETITOR_DOMAIN]`) updates `activeProf.brands` and `activeProf.brandDomains`, dismisses the modal, and triggers `generateOpportunities()` to reveal new competitive gaps.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Matching Result Directory:** `10-gherkin-result-case-competitor-mapping-modal-validation/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Inline Competitor Mapping Modal Validation and Domain Sanitization

  Background:
    Given the user is on the Opportunities page for "[DOMAIN]"
    When the user clicks the "Map Competitor" button ".opps-btn-add-comp"
    Then the competitor modal should mount inside "#modalHolder"
    And inputs "#oppNewCompName" and "#oppNewCompDomain" should be visible

  Scenario Outline: Rejecting Invalid Competitor Inputs with Defensive Error Toasts
    When the user types "<CompetitorName>" into "#oppNewCompName"
    And the user types "<CompetitorDomain>" into "#oppNewCompDomain"
    And the user clicks the Save button "[data-action='opp-save-competitor']"
    Then an error toast with class ".toast-error" should be displayed
    And the error toast message should contain "Please provide both competitor name and domain"
    And the modal inside "#modalHolder" should remain open and mounted
    And the active profile brands array should NOT include "<CompetitorName>"

    Examples:
      | CompetitorName | CompetitorDomain | Rationale / Failure Mode                  |
      |                |                  | Both fields empty                         |
      | Acme Corp      |                  | Missing domain field                      |
      | Acme Corp      | https://         | Protocol-only string sanitized to empty   |
      | Acme Corp      | http://www.      | Prefix-only string sanitized to empty     |

  Scenario: Successful Competitor Mapping and Backlog Recalculation
    When the user types "[COMPETITOR_NAME]" into "#oppNewCompName"
    And the user types "https://www.[COMPETITOR_DOMAIN]/" into "#oppNewCompDomain"
    And the user clicks the Save button "[data-action='opp-save-competitor']"
    Then the modal inside "#modalHolder" should be closed and removed
    And the active profile brands should include "[COMPETITOR_NAME]"
    And the active profile brandDomains should map "[COMPETITOR_NAME]" to "[COMPETITOR_DOMAIN]"
    And a success toast should confirm "Competitor mapped successfully"
    And the opportunities backlog should recalculate to include gaps against "[COMPETITOR_NAME]"
```

---

## 5. Visual Checks
1. **Modal Overlay:** `#modalHolder .modal` renders centered with backdrop overlay, title `"Map New Competitor"` / `"Yeni Rakip Eşle"`, and close button (`[data-action="opp-close-comp-modal"]`).
2. **Form Layout:** Contains 2 labeled input fields with placeholders (e.g. `ör. [COMPETITOR_DOMAIN]`).
3. **Error Feedback:** Displays red border or error toast when validation fails.
4. **Modal Preserved on Error:** Focus remains inside the modal so the user does not lose in-progress typing.

---

## 6. Data and Network Checks
1. **Domain Sanitizer Integrity:**
   ```js
   var raw = "https://www.[COMPETITOR_DOMAIN]/products";
   var sanitized = raw.trim().toLowerCase().replace(/^https?:\/\//, "").replace(/^www\./, "").replace(/\/.*$/, "");
   console.assert(sanitized === "[COMPETITOR_DOMAIN]", "Sanitization failed for URL: " + raw);
   ```
2. **Profile State Update:**
   - Inspect `window.profile()` or `window.state.profile`.
   - Verify `brands` array has length incremented by 1.
   - Verify `brandDomains["[COMPETITOR_NAME]"] === "[COMPETITOR_DOMAIN]"`.
3. **Recalculation:**
   - Assert `window.generateOpportunities` runs and updates `window.state.opportunities`.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `10-gherkin-result-case-competitor-mapping-modal-validation/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `modal_open.png` showing empty competitor form.
  2. Capture `modal_error_toast.png` proving error toast on invalid domain `https://`.
  3. Capture `competitor_added_success.png` showing recalculated backlog.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/opportunities-modal/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/10-gherkin-result-case-competitor-mapping-modal-validation/
     ```
  5. Include verification checklist in `result.md`.

### Pass/Fail Criteria
- [ ] Modal opens cleanly on CTA click.
- [ ] Empty or protocol-only domain inputs are rejected with informative error toast.
- [ ] Modal remains open during validation failures with inputs preserved.
- [ ] Valid competitor domain is sanitized and stored, triggering backlog recalculation.
