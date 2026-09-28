# Test Case: ccTLD Geographic Targeting & Locale Auto-Deduction Engine

## 1. Case ID & Purpose
- **Case ID:** `TC-ONB-04-CCTLD-GEO-DEDUCTION`
- **Purpose:** Validate automatic country (`selectedRegion`) and primary response language (`selectedLanguage`) deduction based on domain ccTLD patterns, known brand lists, vanity TLD fallbacks (US/en), and ensure that user manual overrides to Region/Language are respected without being overwritten by subsequent domain edits.

---

## 2. Tester Brief
The tester inputs various international and regional domains into `#ob-domain-input` on Step 3. The tester verifies that `.tr` (and Turkish brand patterns like `[DOMAIN]`) automatically set Region to `"TR"` and Language to `"tr"`, `.co.uk` sets Region to `"UK"` and Language to `"en"`, `.de` sets Region to `"DE"` and Language to `"de"`, and `.fr` sets Region to `"FR"` and Language to `"fr"`. The tester tests vanity and non-ccTLD extensions (`.io`, `.ai`, `.xyz`) to verify default fallback to `"US"` / `"en"`. Finally, the tester manually changes the Region dropdown to `"UK"`, edits the domain, and asserts that the user's manual override is preserved.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/onboarding`
- **Prerequisite State:** Step 3 (`activeStep === 3`), brand name entered
- **Placeholders Used:**
  - `[DOMAIN]`: Base application domain
  - `[TEST_DOMAIN]`: Domain string under test
  - `[EXPECTED_REGION]`: Country code (`TR`, `UK`, `DE`, `FR`, `US`)
  - `[EXPECTED_LANGUAGE]`: Locale tag (`tr`, `en`, `de`, `fr`)
  - `[MARKET_BADGE]`: Expected market badge text

---

## 4. Gherkin Scenario

```gherkin
Feature: Onboarding Step 3 - ccTLD Geographic and Language Deduction Engine

  Background:
    Given the user is on Step 3 of the onboarding wizard at "[APP_URL]/#/onboarding"

  @sanity @cctld @geo-targeting
  Scenario Outline: ccTLD patterns auto-deduce matching country and response language
    When the user types "<domain_string>" into "#ob-domain-input"
    And waits 300 milliseconds for deduction to resolve
    Then the detected market pill "#ob-domain-detected-pill" should contain "<market_badge>"
    And the region select "#ob-region-select" value should be "<expected_region>"
    And the language select "#ob-language-select" value should be "<expected_lang>"
    And the SVG world map should highlight country "<expected_region>"

    Examples:
      | domain_string       | market_badge                               | expected_region | expected_lang |
      | [DOMAIN]            | 🇹🇷 Turkey (TR) · Turkish                   | TR              | tr            |
      | [COMPETITOR_DOMAIN] | 🇹🇷 Turkey (TR) · Turkish                   | TR              | tr            |
      | bbc.co.uk           | 🇬🇧 United Kingdom (UK) · English           | UK              | en            |
      | zalando.de          | 🇩🇪 Germany (DE) · German                   | DE              | de            |
      | lefigaro.fr         | 🇫🇷 France (FR) · French                    | FR              | fr            |
      | linear.app          | 🇺🇸 United States (US) · English            | US              | en            |
      | developer.io        | 🇺🇸 United States (US) · English            | US              | en            |
      | startup.ai          | 🇺🇸 United States (US) · English            | US              | en            |
      | unknownbrand.xyz    | 🇺🇸 United States (US) · English            | US              | en            |

  @positive @user-override @immunity
  Scenario: User manual dropdown selection is not overwritten by domain changes
    Given the domain "[DOMAIN]" has deduced region "TR" and language "tr"
    When the user manually changes the region select "#ob-region-select" to "DE"
    And changes the language select "#ob-language-select" to "de"
    And then edits the domain input "#ob-domain-input" to "example-brand.com.tr"
    Then the region select should remain "DE"
    And the language select should remain "de"
    And the internal state should record "regionTouched: true" and "localeTouched: true"
```

---

## 5. Visual Checks
- **Detected Market Badge:**
  - Pill element `.ob-market-badge` displays the corresponding flag emoji (🇹🇷, 🇬🇧, 🇩🇪, 🇫🇷, 🇺🇸), Country Name, Country Code, and Primary Language name.
- **World Map Dynamic Highlight:**
  - SVG world map `#ob-world-map` dynamically applies class `.ob-map-country-selected` and pulsed marker `.ob-pulse-marker` on the deduced country centroid.

---

## 6. Data & Network Checks
- **Deduction Function Assertions (`assets/onboarding.js:98`):**
  ```javascript
  assert(window.obRegionFromDomain('garanti.com.tr') === 'TR');
  assert(window.obRegionFromDomain('bbc.co.uk') === 'UK');
  assert(window.obRegionFromDomain('zalando.de') === 'DE');
  assert(window.obRegionFromDomain('startup.io') === ''); // Vanity falls back to US in caller
  ```
- **State Property:**
  ```javascript
  const ob = window.state.onboarding;
  assert(ob.selectedRegion === 'TR' || ob.selectedRegion === 'US');
  assert(ob.selectedLanguage === 'tr' || ob.selectedLanguage === 'en');
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `04-gherkin-result-case-cctld-geographic-auto-deduction/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, market deduction matrix results, override test log.
  - `evidence.json`: State snapshot of `selectedRegion`, `selectedLanguage`, and touch flags.
  - `screenshots/01-deduced-tr-market.png`: Turkish market deduction badge and highlighted map.
  - `screenshots/02-deduced-uk-market.png`: UK market deduction badge.
  - `screenshots/03-deduced-de-market.png`: Germany market deduction badge.
- **MacBook Execution Protocol:** Ego Browser triggers automated assertions on MacBook display; visual screenshots downloaded via SCP.
