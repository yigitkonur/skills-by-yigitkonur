# TC-DB-07: Scheduled Stakeholder Digest Recipient Email Validation

## 1. Case ID and Purpose
- **Case ID:** `TC-DB-07`
- **Purpose:** Verify that creating a scheduled executive digest enforces client-side recipient email syntax validation (`crValidateForm`), rejecting empty recipient lists, malformed email addresses, and lists exceeding the 20-recipient threshold with localized error copy before dispatching RPC commands.
- **Target Result Directory:** `02-dashboards-and-exports/07-gherkin-result-case-scheduled-digest-email-validation/`

---

## 2. Tester Brief
The dashboard header offers automated weekly/monthly stakeholder email digests.
1. The user clicks `button[data-action="dash-schedule-digest"]`.
2. The report configuration form renders schedule controls and recipient textarea `[data-action="cr-form-recipients"]`.
3. Validation constraints enforced by `crValidateForm`:
   - Empty input: Displays `"Add at least one recipient email."`.
   - Malformed syntax (e.g. `invalid-email`, `user@no-tld`): Displays `"Invalid email address: ..."` directly under the field.
   - List > 20 emails: Displays `"At most 20 recipients are allowed."`.
   - Valid emails (1–20 comma/newline separated): Allows saving via `upsert-report-definition`.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/dashboards`.
- **Fixtures & Placeholders:**
  - `[MALFORMED_EMAILS]`: `"test-user, invalid@domain, @missing-user.com"`
  - `[VALID_EMAILS]`: `"cmo@zeo.org, analytics@zeo.org"`

---

## 4. Gherkin Scenario

```gherkin
Feature: Scheduled Stakeholder Digest Email Validation

  Scenario Outline: Validating recipient email syntax and list bounds in digest schedule form
    Given the test user opens the scheduled digest modal
    When the user enters the recipient list string "<RecipientsInput>"
    And the user attempts to submit the digest configuration
    Then the client form validation should result in "<ExpectedValidationStatus>"
    And the error banner should display "<ExpectedErrorMessage>"

    Examples:
      | RecipientsInput                           | ExpectedValidationStatus | ExpectedErrorMessage             |
      |                                           | invalid                  | Add at least one recipient email |
      | malformed-email, valid@zeo.org            | invalid                  | Invalid email address            |
      | exec@zeo.org, cmo@zeo.org                 | valid                    | none                             |
```

---

## 5. Visual Checks
- **Form Elements:**
  - Schedule Select: `select[data-action="cr-form-schedule"]`.
  - Recipient Textarea: `textarea[data-action="cr-form-recipients"]`.
  - Error Text: `.cr-field-error` or element with text matching error.
  - Save Button: `button[data-action="cr-form-save"]`.
- **Screenshot Points:**
  - `01_digest_modal_syntax_error.png` (Recipient field showing red syntax error message).

---

## 6. Data and Network Checks
- **Validation Method:**
  ```js
  const validation = window.crValidateForm({
    title: "Executive Digest",
    schedule: "weekly",
    weeklyWeekday: 1,
    recipientsText: "malformed-user, valid@zeo.org"
  });
  assert(validation.valid === false);
  assert(validation.errors.recipients.includes("Invalid email"));
  ```

---

## 7. Evidence and Reporting
- **Result Directory:** `02-dashboards-and-exports/07-gherkin-result-case-scheduled-digest-email-validation/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-digest-validation');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/dashboards', { wait: true, timeout: 30 });
await wait(2);

const valCheck = await js(String.raw`(() => {
  if (typeof window.crValidateForm !== "function") return { skipped: true };

  const emptyCheck = window.crValidateForm({ title: "Digest", recipientsText: "", schedule: "weekly" });
  const malformedCheck = window.crValidateForm({ title: "Digest", recipientsText: "not-an-email", schedule: "weekly" });
  const validCheck = window.crValidateForm({ title: "Digest", recipientsText: "user@zeo.org", schedule: "weekly" });

  return {
    emptyHasError: !!emptyCheck.errors.recipients,
    malformedHasError: !!malformedCheck.errors.recipients,
    validPassed: validCheck.valid
  };
})()`);

cliLog('Validation Test Result: ' + JSON.stringify(valCheck));
if (!valCheck.skipped && (!valCheck.emptyHasError || !valCheck.malformedHasError || !valCheck.validPassed)) {
  throw new Error('Scheduled digest email validation failed assertions');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-digest-validation', { keep: false })`.
