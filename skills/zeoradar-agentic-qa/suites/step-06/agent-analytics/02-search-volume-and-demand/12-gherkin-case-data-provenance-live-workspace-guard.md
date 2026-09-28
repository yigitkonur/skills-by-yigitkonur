# Case 12: Data Provenance Boundaries & Mock Template Leakage Prevention

## 1. Case ID and Purpose
- **Case ID**: `TC-VOL-12`
- **Purpose**: Verify that when connected to a live workspace (`volLiveSource() === true`), Prompt Volumes derives prompt queries and volume metrics strictly from verified provider database payloads (`data.topPrompts`, `data.rows`), strictly prevents the leakage of synthetic mockup prompt templates (`VOL_PROMPT_TEMPLATES`), renders honest unmeasured states (`renderVolumeNotMeasured`) when data has not yet been collected rather than fabricating arbitrary numbers, and enforces strict server-backed provenance notes in export popovers.

## 2. Tester Brief
The tester switches the environment to live provider mode (`ZEO_DATA_PROVIDER.getMode() === 'live'`), opens the Keyword Workspace, and inspects the prompts table. The tester asserts that no mock template strings (e.g. `"Describe your typical {kw} process"`) appear in the rendered DOM, verifies that unmeasured engine volumes display honest dashes (`–`) instead of fabricated distributions, inspects keywords with zero measurements to confirm that `renderVolumeNotMeasured` is displayed, and checks the Export Answers popover `#volExportPopover` to confirm live provenance disclosure.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Mode: `live` (`window.ZEO_DATA_PROVIDER.getMode() === 'live'`)
  - Forbidden Mock Strings: `"Describe your typical"`, `"methods and approaches"`, `"Process for choosing"`
- **Prerequisites**:
  - Live data provider connected.

## 4. Gherkin Scenario

```gherkin
Feature: Data Provenance Enforcement & Mock Template Leakage Prevention
  As a Brand Governance and Data Ethics Officer
  I want live client workspaces to display only real, provider-backed search telemetry
  So that synthetic mockup queries or placeholder calculations never mislead enterprise stakeholders

  Background:
    Given the application is configured in "live" provider mode
    And "window.volLiveSource()" returns true
    And the user navigates to "[APP_URL]/#/[SLUG]/volumes"

  Scenario: Verify zero mock template string leakage in live workspace
    When the Keyword Workspace table is rendered
    Then all rendered prompt texts should originate from "data.topPrompts" or "data.rows"
    And the DOM text content should not contain any string from "VOL_PROMPT_TEMPLATES":
      | Describe your typical |
      | methods and approaches |
      | Process for choosing   |

  Scenario: Render honest unmeasured state for keywords without live data
    Given an active keyword that has not yet completed volume ingestion
    When the user views the Keyword Workspace for this keyword
    Then the view should render the unmeasured notice ".vol-not-measured-card"
    And the message should state:
      """
      Keyword measurements not available yet
      """
    And the application should not generate synthetic Poisson numbers to fill the gap

  Scenario: Enforce live provenance notice in Export popover
    When the user opens the Export popover "#volExportPopover"
    Then the popover should display the live provenance notice:
      """
      The server exports only provider-backed execution summaries.
      """
    And synthetic client-side citation overrides should be disabled
```

## 5. Visual Checks
- **Live Source Badge**: `.vol-source-badge.provider` renders with green live dot.
- **Unmeasured Card**: Clean empty state card with info icon, reassuring typography, and refresh CTA.
- **Export Popover**: Muted italic provenance note explaining live server grounding.

## 6. Data and Network Checks
- **Strict Provenance Assertions**:
  ```javascript
  assert.strictEqual(window.volLiveSource(), true);
  const bodyText = document.body.textContent;
  const mockTemplates = window.VOL_PROMPT_TEMPLATES || [];
  mockTemplates.forEach(tmpl => {
    assert.strictEqual(bodyText.includes(tmpl.substring(0, 20)), false, 'Template leaked into live DOM');
  });
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `02-gherkin-result-case-data-provenance-live-workspace-guard/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-vol-12-live-source-badge.png`
     - `/tmp/ego-shots/tc-vol-12-not-measured-card.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-vol-12-*.png ./02-gherkin-result-case-data-provenance-live-workspace-guard/
     ```
