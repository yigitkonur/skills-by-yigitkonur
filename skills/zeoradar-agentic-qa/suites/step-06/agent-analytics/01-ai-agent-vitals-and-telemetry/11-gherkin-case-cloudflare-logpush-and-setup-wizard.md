# Case 11: Cloudflare Logpush Snippet Validation & 5-Step Setup Wizard

## 1. Case ID and Purpose
- **Case ID**: `TC-AA-11`
- **Purpose**: Verify that the 5-step Integration Setup Wizard modal (`.aa-wizard`) guides users cleanly from domain selection through provider configuration (Dokploy, Cloudflare, CloudFront, Fastly) to completion, that the Server Logs Integration Console tabs (`cloudflare`, `dokploy`, `webhook`) provide accurate configuration snippets, that Cloudflare Logpush cURL commands include proper placeholder tokens (`{ZONE_ID}`, `{CLOUDFLARE_API_KEY}`, `{SECRET_KEY}`), and that copy-to-clipboard actions succeed with confirmation toasts.

## 2. Tester Brief
The tester launches the Setup Wizard via the header button `button[data-action="aa-open-wizard"]`, steps through each of the 5 wizard stages, selects a provider (e.g. Dokploy), confirms integration, and exits the modal. Next, on the Server Logs tab, the tester traverses the Integration Console tabs, inspects the Cloudflare Logpush cURL template to ensure no real secrets or broken tokens exist, clicks the "Copy Snippet" button to confirm clipboard handling and toast appearance, and checks the Webhook JSON schema for required fields.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Required Cloudflare Placeholders: `{ZONE_ID}`, `{CLOUDFLARE_API_KEY}`, `{SECRET_KEY}`
  - Required Webhook Schema Keys: `bot`, `platform`, `path`, `status`, `timestamp`
- **Prerequisites**:
  - Agent Analytics module loaded.

## 4. Gherkin Scenario

```gherkin
Feature: Edge Integration Console & 5-Step Setup Wizard
  As an Edge Integration Architect
  I want setup wizards and copyable logpush configurations to guide proxy setup
  So that Cloudflare and Dokploy logs can be securely routed into Zeo Geo-Radar

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/agentanalytics"

  Scenario: Complete 5-Step Integration Setup Wizard
    When the user clicks the setup button "button.aa-btn-setup[data-action='aa-open-wizard']"
    Then the setup wizard modal ".aa-wizard" should open at Step 1
    When the user clicks "button[data-action='aa-wizard-next']" to advance to Step 2
    Then provider options for Dokploy, Cloudflare, CloudFront, and Fastly should be displayed
    When the user selects provider card ".aa-provider-card[data-p='dokploy']"
    And advances through Step 3 and Step 4
    Then Step 5 should display integration success confirmation
    When the user clicks the close action
    Then the wizard modal should close and "window.AgentAnalyticsState.wizardOpen" should be false

  Scenario Outline: Inspect and copy Integration Console snippets
    Given the user switches to the Server Logs tab "button.aa-tab-item[data-tab='logs']"
    When the user clicks the console tab "button.aa-console-tab[data-tab='<integration_tab>']"
    Then the console snippet area should display the setup guide for "<integration_tab>"
    And the snippet text should contain required token "<expected_token>"
    When the user clicks the copy snippet button "button[data-action='aa-copy-snippet']"
    Then a success toast should appear stating "Configuration snippet copied to clipboard."

    Examples:
      | integration_tab | expected_token         |
      | cloudflare      | logpush/jobs           |
      | cloudflare      | {ZONE_ID}              |
      | cloudflare      | {SECRET_KEY}           |
      | dokploy         | traefik.http.routers   |
      | webhook         | "timestamp": "2026-"   |
```

## 5. Visual Checks
- **Wizard Modal**: Multi-step progress indicator in modal header (dots/numbered steps).
- **Code Blocks**: Formatted with monospace font and high-contrast dark background (`.aa-snippet-box`).
- **Copy Feedback**: Button briefly shows checked state or toast notification appears.

## 6. Data and Network Checks
- **Wizard State Progression**:
  ```javascript
  const state = window.AgentAnalyticsState;
  assert.strictEqual(state.wizardStep, 1);
  // After stepping
  assert.strictEqual(state.wizardProvider, 'dokploy');
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `01-gherkin-result-case-cloudflare-logpush-and-setup-wizard/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-aa-11-wizard-step2.png`
     - `/tmp/ego-shots/tc-aa-11-cf-snippet.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-aa-11-*.png ./01-gherkin-result-case-cloudflare-logpush-and-setup-wizard/
     ```
