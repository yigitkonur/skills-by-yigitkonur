# Test Case: Low-Sample Sentiment Scorecard Guard (<3 Claims)

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-KPI-09`
- **Purpose**: Verify that when a brand has fewer than 3 polarized (positive/negative) sentiment claims (`sd.claims < 3` or `sd.score == null`), the Sentiment scorecard renders an em-dash `"–"` rather than misleading `0%` or `100%`, and provides an informative tooltip `title` explaining the statistical sample guard.

---

## 2. Tester Brief
Evaluating sentiment percentages on 1 or 2 isolated mentions produces volatile, statistically ungrounded numbers (e.g. 1 positive mention yields 100%, 1 negative mention yields 0%).
Zeo Geo-Radar enforces a sample size threshold guard:
1. If verified claims are fewer than 3 or `sd.score == null`, the Sentiment scorecard renders `"–"`.
2. The scorecard value element possesses a `title` attribute: `"Not enough data to score — fewer than 3 positive/negative claims"` / `"Puanlamak için yeterli veri yok — 3'ten az olumlu/olumsuz iddia"`.
3. If claims are $\ge 3$, the percentage is displayed normally (e.g. `78.4%`).

The tester verifies this behavior on workspaces with sparse vs robust sentiment data.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Dataset Condition**: Profile bundle with `sd.claims < 3` or simulated low-sample profile.

---

## 4. Gherkin Scenario

```gherkin
Feature: Low-Sample Sentiment Integrity Guard
  As a brand strategist evaluating consumer perception
  I want the Sentiment KPI scorecard to suppress scores when sample sizes are statistically insignificant
  So that I am never misled by extreme 0% or 100% scores based on 1 or 2 claims.

  Scenario Outline: Rendering sentiment score under varying claim counts
    Given the user is on the Overview Dashboard
    When the brand sentiment data contains "<ClaimCount>" verified claims
    Then the Sentiment scorecard value should display "<ExpectedDisplay>"
    And the Sentiment element tooltip should "<TooltipCondition>"

    Examples:
      | ClaimCount | ExpectedDisplay | TooltipCondition                        |
      | 0          | –               | contain "Not enough data" or "3'ten az" |
      | 1          | –               | contain "Not enough data" or "3'ten az" |
      | 2          | –               | contain "Not enough data" or "3'ten az" |
      | 5          | 80.0%           | be empty or standard title              |
```

---

## 5. Visual Checks
- **Sentiment Card**: 4th card in `.aei-kpi-strip.ov-kpi-strip` with label `"Sentiment"` / `"Duygu Durumu"`.
- **Value Field**: `.aei-kpi-val.mono` rendering `"–"` or formatted percentage.
- **Hover Tooltip**: Native browser tooltip `title` displaying the explanation string on hover.

---

## 6. Data and Network Checks
- **DOM & State Assertion**:
  ```javascript
  const sentCheck = await js(String.raw`(() => {
    const card = [...document.querySelectorAll('.aei-kpi-card, .ov-kpi-card')].find(c => {
      const lbl = c.querySelector('.aei-kpi-label, .ov-kpi-label')?.innerText || '';
      return lbl.includes('Sentiment') || lbl.includes('Duygu');
    });
    if (!card) return { skipped: true };

    const valEl = card.querySelector('.aei-kpi-val, .ov-kpi-val');
    const val = valEl?.innerText?.trim();
    const title = valEl?.getAttribute('title') || '';
    const hasSampleGuard = (val === '–') ? (title.includes('fewer than 3') || title.includes("3'ten az")) : true;

    return { val, title, hasSampleGuard, noError: !window.__lastError };
  })()`);
  if (!sentCheck.skipped && !sentCheck.hasSampleGuard) {
    throw new Error('Sentiment em-dash display lacks mandatory sample-size guard tooltip');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-sentiment-low-sample-guard/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux VM.
  - Screenshots of hovered sentiment card captured into result directory.
  - SCP sync from MacBook before generating summary report.
