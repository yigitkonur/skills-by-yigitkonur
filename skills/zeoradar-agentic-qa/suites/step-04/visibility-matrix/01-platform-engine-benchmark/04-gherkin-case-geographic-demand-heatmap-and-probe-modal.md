# Test Case: TC-VIS-04 - Geographic Demand Heatmap, Country Filtering & Probe Modal

## 1. Case ID and Purpose
- **Case ID:** `TC-VIS-04`
- **Module:** Answer Engine Insights (`assets/aei.js`, `assets/aei.css`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture, GSS-CGA-05)
- **Traceability:** Maps to Source Scenarios `VIS-06` and `VIS-07`
- **Purpose:** Verify that the Geographic Search Demand & Visibility Heatmap card (`.card.aei-geo-card`) renders regional search demand distribution across measured and unmeasured markets, clicking a measured country card (`.aei-country-card.measured`, e.g. `TR`, `US`) filters the global region state and synchronizes the URL (`region=TR`), and clicking an unmeasured country card (`.aei-country-card.unmeasured`, e.g. `FR`) opens the regional probe provisioning modal (`.aei-overlay .aei-modal`).

---

## 2. Tester Brief
The tester or automated agent interacts with the Geographic Search Demand section:
1. Locate `.card.aei-geo-card` and verify the grid of country cards (`.aei-geo-grid`).
2. Identify a measured country card (e.g. `TR`), click it, and verify:
   - `st.filters.region` updates to `"TR"`.
   - The global region select dropdown synchronizes to `"TR"`.
   - The URL parameter reflects `region=TR`.
   - Matrix and KPI cards recalculate for the localized regional probe data.
3. Identify an unmeasured country card (e.g. `FR`), click it, and verify:
   - The regional probe provisioning modal mounts (`.aei-overlay .aei-modal`).
   - The modal displays the country name, prompt quota allocation instructions, and action buttons.
   - Clicking the modal close button or backdrop dismisses the dialog cleanly.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=performance`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Measured Country `[COUNTRY]`:** `TR` or `US`
- **Unmeasured Country `[COUNTRY]`:** `FR`, `DE`, or `IT`
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `04-gherkin-result-case-geographic-demand-heatmap-and-probe-modal/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Geographic Search Demand Heatmap, Country Filtering, and Probe Provisioning Modal

  Background:
    Given the user is on the "performance" workspace of Zeo Geo-Radar
    Then the geographic demand card ".card.aei-geo-card" should be visible

  Scenario Outline: Filtering Localized Visibility by Clicking Measured Country Card
    When the user clicks the measured country card ".aei-country-card.measured[data-country='<CountryCode>']"
    Then "window.aeiState.filters.region" should equal "<CountryCode>"
    And the persistent region select "select[data-action-change='aei-select-region']" should have value "<CountryCode>"
    And the URL hash should contain "region=<CountryCode>"
    And the benchmark matrix should recalculate visibility for "<CountryCode>"

    Examples:
      | CountryCode | CountryName   |
      | TR          | Turkey        |
      | US          | United States |

  Scenario Outline: Opening Probe Provisioning Modal for Unmeasured Markets
    When the user clicks the unmeasured country card ".aei-country-card.unmeasured[data-country='<CountryCode>']"
    Then the modal overlay ".aei-overlay" should be appended to the DOM
    And the modal dialog ".aei-modal" should be visible within the viewport
    And the modal header should reference "<CountryCode>" or "<CountryName>"
    And the modal should display a prompt quota allocation action button
    When the user clicks the modal close button ".aei-modal .close"
    Then the modal overlay ".aei-overlay" should be removed from the DOM

    Examples:
      | CountryCode | CountryName |
      | FR          | France      |
      | DE          | Germany     |
```

---

## 5. Visual Checks
1. **Heatmap Grid Layout:** `.aei-geo-grid` arranges country cards in a responsive multi-column grid.
2. **Measured vs Unmeasured Visual Distinction:**
   - `.aei-country-card.measured`: Exhibits solid borders, search volume badges, and green/accent visibility pills.
   - `.aei-country-card.unmeasured`: Exhibits dashed border (`border: 1px dashed var(--border)`), muted text, and a `+ Provision Probe` affordance.
3. **Modal Dialog Appearance:**
   - Semi-transparent backdrop (`.aei-overlay`).
   - Centered card panel (`.aei-modal`) with clear typography, input counters, and primary action button.

---

## 6. Data and Network Checks
1. **State Synchronization:**
   ```js
   assert(window.aeiState.filters.region === "TR", "State region must be TR");
   const sel = document.querySelector("select[data-action-change='aei-select-region']");
   assert(sel && sel.value === "TR", "Select element must reflect state region");
   ```
2. **URL Parameter Reflection:** Verify URL contains `&region=TR`.
3. **Modal Mount Lifecycle:** Verify `.aei-overlay` does not leak event listeners or create duplicate DOM elements on repeated opens/closes.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `04-gherkin-result-case-geographic-demand-heatmap-and-probe-modal/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`geo_heatmap_grid.png`, `measured_country_filtered.png`, `probe_provisioning_modal.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/visibility/tc-vis-04-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/01-platform-engine-benchmark/04-gherkin-result-case-geographic-demand-heatmap-and-probe-modal/screenshots/
     ```
  4. Write execution report `result.md` documenting filter updates, modal open/close lifecycle, and assertion logs.

### Pass/Fail Criteria
- [ ] Measured country card updates `st.filters.region` and syncs URL.
- [ ] Unmeasured country card launches `.aei-overlay .aei-modal`.
- [ ] Modal close button unmounts the dialog without residual overlays.
- [ ] No unhandled exceptions occur during region transitions.
