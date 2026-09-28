# Test Case: About Zeo Radar Metadata Popover, Engine Coverage & Snapshot Verification

## 1. Case ID & Purpose
- **Case ID:** `TC-PREF-07-ABOUT-RADAR-INFO`
- **Purpose:** Verify the "About Zeo Radar" info popover (`assets/radar.js` lines 5390–5415), ensuring that clicking the question mark button (`.foot-btn[data-action="info-pop"]`) in the sidebar footer renders `#infoPop .info-pop`, displays system snapshot metrics (measurement date, monitored assets count, prompts/answers ratio, engines count), and dismisses cleanly on re-clicking the trigger button.

---

## 2. Tester Brief
The tester (human or AI agent) will click the info button (`.foot-btn[data-action="info-pop"]`), assert that `#infoPop` opens, inspect the key-value rows (`.kv`) for measurement date, monitored assets, and answer engines, verify data attribution text (`"Zeo measurement"` / `"Zeo ölçümü"`), click the info button again, and assert that `#infoPop` is dismissed.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** `#infoPop` closed
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test

---

## 4. Gherkin Scenario

```gherkin
Feature: Preferences - About Zeo Radar Metadata Popover

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the info popover "#infoPop" is currently closed

  @info @metadata @popover @positive
  Scenario: Clicking info button displays snapshot metadata and toggles closed
    When the user clicks the footer button ".foot-btn[data-action='info-pop']"
    Then the info popover "#infoPop .info-pop" should be visible
    And the popover title should contain "Zeo Radar"
    And the metadata list should contain at least 4 key-value rows ".kv"
    And the metadata should display measurement date and platform coverage
    When the user clicks the footer button ".foot-btn[data-action='info-pop']"
    Then the info popover "#infoPop" should be closed
```

---

## 5. Visual Checks
- **Popover Styling:**
  - Floats above the sidebar footer with compact padding and dark/light token border.
  - Key-value pairs align with muted label on left and strong value on right.
- **Attribution Footer:**
  - `"Built by Zeo · zeo.org"` link is rendered neatly at bottom.

---

## 6. Data & Network Checks
- **DOM & Content Assertions:**
  ```javascript
  const pop = document.querySelector('#infoPop .info-pop');
  assert(pop !== null, "Info popover must be mounted");
  const kvRows = pop.querySelectorAll('.kv');
  assert(kvRows.length >= 4, "Must contain at least 4 metadata rows");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-about-radar-metadata-inspection/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of metadata fields and toggle behavior.
  - `evidence.json`: Captured metadata KV row text.
  - `screenshots/07-about-info-open.png`: View of the opened About Zeo Radar popover.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/pref/case-07-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
