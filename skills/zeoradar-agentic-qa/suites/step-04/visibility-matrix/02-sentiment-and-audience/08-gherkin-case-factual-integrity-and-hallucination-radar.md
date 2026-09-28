# Test Case: TC-SNT-08 - Factual Integrity Radar & Zero-Division Boundary Safety

## 1. Case ID and Purpose
- **Case ID:** `TC-SNT-08`
- **Module:** Answer Engine Insights (`assets/aei.js`, `assets/radar.js`)
- **Parent Contract:** Spec 11 (Answer Engine Insights Multi-Platform Visibility Architecture, Wave 4 Packet C3)
- **Traceability:** Maps to Source Scenarios `SNT-10`, `SNT-11`, and `SNT-28`
- **Purpose:** Verify that Section 4 of the Perception workspace (`.card.aei-hallucination-radar-card`) renders the Factual Integrity & Hallucination Radar, calculates the factual adherence rate percentage, guarantees zero-division boundary resilience (rendering `100%` rather than `NaN%` when evaluated claims equal 0), displays counts for Supported Claims, Open Contradictions, and Total Alerts, and provides seamless navigation to the Brand Hub Truth Vault (`aei-goto-truth-vault`).

---

## 2. Tester Brief
The tester or automated agent examines the Hallucination Radar card:
1. Locate `.card.aei-hallucination-radar-card` at the bottom of the Perception workspace.
2. Confirm header elements:
   - Shield icon with title: *"Factual Integrity & Hallucination Radar"*.
   - Subtitle: *"Audit verified brand claims and monitor hallucination rates across generative AI engines."*
   - Deep-link button: `button[data-action="aei-goto-truth-vault"]`.
3. Verify metric readouts:
   - Factual Adherence Rate percentage in `.aei-sentiment-summary strong.text-green`.
   - Adherence bar fill: Green segment for supported claims, Red segment for contradictions.
   - Metric bullets: Supported claims (`.pos.mono`), Open contradictions (`.neg.mono`), Total alerts (`.dim.mono`).
4. Test zero-division edge case:
   - In a project with 0 evaluated claims (`evalClaims === 0`), assert adherence rate displays `100%` and status renders `Clean` without generating `NaN%` or dividing by zero.
5. Click `button[data-action="aei-goto-truth-vault"]`:
   - Router transitions to `tab="brand-hub"`.
   - Truth Vault live tab is set to `liveTab="hallucinations"`.
   - Brand Hub Truth Vault screen mounts cleanly.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=perception`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Evaluated Claims Count `[EVALUATED_CLAIMS_COUNT]`:** `0` (Zero claims edge case) vs `>0` (Active audit)
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `08-gherkin-result-case-factual-integrity-and-hallucination-radar/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Factual Integrity & Hallucination Radar Verification and Zero-Division Safety

  Background:
    Given the user is on the "perception" workspace of Zeo Geo-Radar
    Then the hallucination radar card ".card.aei-hallucination-radar-card" should be visible

  Scenario: Factual Integrity Card Anatomy and Metrics Display
    Then the adherence rate element ".aei-sentiment-summary strong.text-green" should display a percentage
    And the metric summary ".aei-sent-metrics" should render:
      | Metric Selector  | Metric Label (EN)     | Metric Label (TR)      |
      | .pos.mono        | Supported Claims      | Desteklenen İddia      |
      | .neg.mono        | Open Contradictions   | Açık Çelişki           |
      | .dim.mono        | Total Alerts          | Toplam Uyarı           |
    And the per-engine breakdown should list rows for active platforms

  Scenario: Zero-Division Boundary Resilience
    Given a brand project with zero evaluated claims ("evalClaims === 0")
    When the factual adherence rate is computed
    Then the displayed adherence rate must equal "100%"
    And the displayed value must not equal "NaN%" or "null%"
    And the adherence bar fill should render 100% green width

  Scenario: Deep-Link Navigation to Brand Hub Truth Vault
    When the user clicks "button[data-action='aei-goto-truth-vault']"
    Then "window.state.tab" should equal "brand-hub"
    And "window.brandHubState().liveTab" should equal "hallucinations"
    And the page view should transition to the Brand Hub Truth Vault
```

---

## 5. Visual Checks
1. **Adherence Bar Fill:** Dual-color segmented bar (`height: 12px`, `border-radius: 6px`) with green fill proportional to adherence rate and red fill for contradicted claims.
2. **Text Contrast:** `.text-green` adherence rate rendered in bold 16px font.
3. **Open Contradictions Readout:** Muted gray when 0 contradictions; bold red warning when open contradictions $> 0$.
4. **Action Button:** Subdued button with diagonal arrow icon (`arrowUpR`) linking out of the workspace.

---

## 6. Data and Network Checks
1. **Math Integrity Assertion:**
   ```js
   const evalClaims = cov.evaluatedClaims || 0;
   const suppClaims = cov.supportedClaims || 0;
   const expectedRate = evalClaims > 0 ? Math.round((suppClaims / evalClaims) * 100) : 100;
   const displayedRate = parseInt(document.querySelector(".aei-sentiment-summary strong.text-green").textContent);
   assert(displayedRate === expectedRate, "Adherence rate calculation mismatch");
   ```
2. **Navigation State Transition:**
   - Confirm router executes `navigate({ route: "app", slug, tab: "brand-hub" })`.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `08-gherkin-result-case-factual-integrity-and-hallucination-radar/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`hallucination_radar_card.png`, `zero_division_100_percent.png`, `truth_vault_navigated.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/sentiment/tc-snt-08-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/02-sentiment-and-audience/08-gherkin-result-case-factual-integrity-and-hallucination-radar/screenshots/
     ```
  4. Write execution report `result.md` verifying adherence rates, metric counts, and route transitions.

### Pass/Fail Criteria
- [ ] Card renders adherence rate and metric readouts.
- [ ] Zero evaluated claims safely defaults to 100% without `NaN`.
- [ ] Navigation button successfully switches route to Brand Hub Truth Vault.
- [ ] No unhandled exceptions occur during audit rendering.
