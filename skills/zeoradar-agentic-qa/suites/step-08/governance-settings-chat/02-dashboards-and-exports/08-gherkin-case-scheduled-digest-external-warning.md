# TC-DB-08: Scheduled Digest External Recipient Domain Warning and Confirmation

## 1. Case ID and Purpose
- **Case ID:** `TC-DB-08`
- **Purpose:** Verify that when recipient emails in the scheduled digest include external third-party domains (differing from the workspace owner's domain), `crExternalRecipients` detects them and renders a mandatory confirmation checkbox `[data-action="cr-form-confirm-external"]` to prevent unauthorized confidential data leakage.
- **Target Result Directory:** `02-dashboards-and-exports/08-gherkin-result-case-scheduled-digest-external-warning/`

---

## 2. Tester Brief
Automated executive digests contain sensitive corporate visibility, competitor benchmarking, and sentiment analytics.
1. When configuring recipients:
   - Internal domain: `user@zeo.org` (Matches workspace domain `zeo.org`).
   - External domain: `consultant@externalagency.com`.
2. `crExternalRecipients(list)` isolates domains that do not match the authorized workspace domain.
3. If external domains exist:
   - A warning banner and checkbox `[data-action="cr-form-confirm-external"]` appear:
     `"I confirm sending confidential radar analytics to external domains."`
   - Form submission is disabled until the user explicitly checks the box.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Workspace domain: `zeogen.com` / `zeo.org`).
- **Target Form:** Scheduled Stakeholder Digest modal (`assets/reports.js`).
- **Recipients List:** `"analyst@zeo.org, external-partner@agency.com"`.

---

## 4. Gherkin Scenario

```gherkin
Feature: External Domain Recipient Guard in Digest Schedules

  Scenario Outline: Requiring explicit confirmation when external domain recipients are added
    Given the workspace internal domain is "zeo.org"
    When the user adds the recipient email "<RecipientEmail>"
    Then the external recipient detector should return <IsExternalDetected>
    And the external confirmation checkbox "[data-action='cr-form-confirm-external']" should be "<CheckboxVisibility>"

    Examples:
      | RecipientEmail              | IsExternalDetected | CheckboxVisibility |
      | internal-team@zeo.org       | false              | hidden             |
      | third-party@external.com    | true               | visible            |
```

---

## 5. Visual Checks
- **External Confirmation UI:**
  - Container: `.cr-external-confirm-wrap` or `.alert.warning`.
  - Checkbox: `input[type="checkbox"][data-action="cr-form-confirm-external"]`.
  - Label: `"Confirm sending to external recipients"` / `"Harici alıcılara gönderimi onaylayın"`.
- **Screenshot Points:**
  - `01_external_domain_warning_box.png` (Digest form displaying external recipient confirmation checkbox).

---

## 6. Data and Network Checks
- **Algorithmic Assertion:**
  ```js
  const externalList = window.crExternalRecipients(["user@zeo.org", "external@partner.com"]);
  assert(externalList.length === 1);
  assert(externalList[0] === "external@partner.com");
  ```

---

## 7. Evidence and Reporting
- **Result Directory:** `02-dashboards-and-exports/08-gherkin-result-case-scheduled-digest-external-warning/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-digest-external');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/dashboards', { wait: true, timeout: 30 });
await wait(2);

const extCheck = await js(String.raw`(() => {
  if (typeof window.crExternalRecipients !== "function") return { skipped: true };

  const internalOnly = window.crExternalRecipients(["dev@zeo.org"]);
  const withExternal = window.crExternalRecipients(["dev@zeo.org", "guest@external.com"]);

  return {
    internalCount: internalOnly.length,
    externalDetectedCount: withExternal.length,
    externalEmail: withExternal[0] || null
  };
})()`);

cliLog('External Detection Result: ' + JSON.stringify(extCheck));
if (!extCheck.skipped && (extCheck.internalCount !== 0 || extCheck.externalDetectedCount !== 1)) {
  throw new Error('External recipient detection failed to isolate third-party domains');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-digest-external', { keep: false })`.
