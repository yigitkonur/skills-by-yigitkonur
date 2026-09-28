# TC-BH-07: Truth Vault Hallucination Telemetry and Audit Visualizer

## 1. Case ID and Purpose
- **Case ID:** `TC-BH-07`
- **Purpose:** Verify the Truth Vault contradiction detection surface: the executive KPI rail (Total Alerts, Open Contradictions, Critical Contradictions, Fact Adherence Rate), segmented audit progress bar, audit retry trigger, and multi-dimensional filtering across severity, verdict, status, and AI engine platforms.
- **Target Result Directory:** `01-brand-hub-ground-truth/07-gherkin-result-case-truth-vault-hallucinations/`

---

## 2. Tester Brief
The Truth Vault cross-references AI-generated responses against verified Ground Truth facts to detect brand hallucinations and contradictory citations.
1. The user navigates to the `hallucinations` tab via `.brand-hub-tab-btn[data-tab="hallucinations"]`.
2. The KPI rail renders 4 scorecards: Total Alerts, Open Contradictions, Critical Contradictions, and Fact Adherence Rate percentage (`94%`).
3. The Audit Telemetry card renders a segmented progress bar illustrating the proportion of supported claims vs alerts.
4. The filter toolbar enables slicing by:
   - Severity: `critical`, `warning`, `info`.
   - Verdict: `contradicted`, `unsupported`, `unverifiable`.
   - Engine: `ChatGPT`, `Gemini`, `Claude`, `Perplexity`.
5. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Owner or Workspace Member).
- **Target Route:** `[APP_URL]/#/[SLUG]/kb` -> Subtab `hallucinations`.
- **Fixtures & Placeholders:**
  - `[DOMAIN]`: `zeo.org`
  - `[SEVERITY_LEVEL]`: `critical`
  - `[ENGINE_PLATFORM]`: `ChatGPT`

---

## 4. Gherkin Scenario

```gherkin
Feature: Truth Vault Hallucination Telemetry

  Scenario Outline: Inspecting Truth Vault KPI scorecards and filtering contradiction alerts
    Given the test user is on the Brand Hub Truth Vault tab
    Then the KPI rail ".bh-tv-kpis" should display 4 metric cards
    And the Fact Adherence Rate ".big-num.text-green" should be rendered
    And the audit telemetry segmented bar ".bh-audit-progress-wrap" should be visible
    When the user selects severity filter "<SeverityFilter>"
    And the user selects AI engine "<EngineFilter>"
    Then the contradiction alert list should only display items matching "<SeverityFilter>" and "<EngineFilter>"

    Examples:
      | SeverityFilter | EngineFilter |
      | critical       | ChatGPT      |
      | warning        | Perplexity   |
      | all            | all          |
```

---

## 5. Visual Checks
- **KPI Rail Elements:**
  - Container: `.bh-tv-kpis`.
  - Cards: `.bh-tv-kpi-card`.
  - Metrics: `.big-num` values, danger styling `.text-danger` for open/critical contradictions, and green styling `.text-green` for adherence rate.
- **Audit Progress Elements:**
  - Segmented Bar: `.bh-audit-progress-wrap`.
  - Segments: `.bh-audit-seg.supported`, `.bh-audit-seg.alert`, `.bh-audit-seg.remaining`.
  - Refresh Action: `button.btn.small[data-action="bh-hallucinations-retry"]`.
- **Screenshot Points:**
  - `01_truth_vault_overview.png` (KPI rail and audit progress).
  - `02_truth_vault_filtered_alerts.png` (Alerts filtered by critical severity).

---

## 6. Data and Network Checks
- **Resource Loading:**
  - Resource: `truthVault` or `brandHubAudit`.
  - Asserts adherence rate formula: `(supportedClaims / totalEvaluatedClaims) * 100`.
- **Filter Action Event:**
  - Changing severity select fires `change` event on `select[data-action="bh-tv-filter-severity"]`.

---

## 7. Evidence and Reporting
- **Result Directory:** `01-brand-hub-ground-truth/07-gherkin-result-case-truth-vault-hallucinations/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-bh-truth-vault');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/kb', { wait: true, timeout: 30 });
await wait(2);

await click('.brand-hub-tab-btn[data-tab="hallucinations"]');
await wait(2);

const tvCheck = await js(String.raw`(() => {
  const kpis = document.querySelectorAll('.bh-tv-kpi-card');
  const progBar = document.querySelector('.bh-audit-progress-wrap');
  const sevSel = document.querySelector('select[data-action="bh-tv-filter-severity"]');
  const engineSel = document.querySelector('select[data-action="bh-tv-filter-engine"]');

  return {
    kpiCardsCount: kpis.length,
    hasProgressBar: !!progBar,
    hasSeverityFilter: !!sevSel,
    hasEngineFilter: !!engineSel
  };
})()`);

cliLog('Truth Vault State: ' + JSON.stringify(tvCheck));
if (tvCheck.kpiCardsCount < 4 || !tvCheck.hasProgressBar) {
  throw new Error('Truth Vault KPI scorecards or audit telemetry progress bar failed to render');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-bh-truth-vault', { keep: false })`.
