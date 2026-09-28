# TC-ACC-08: Unprovisioned Stripe Customer Handling (`openUnlinkedCustomerModal`)

## 1. Case ID and Purpose
- **Case ID:** `TC-ACC-08`
- **Purpose:** Verify that clicking "Manage Billing" on a workspace without an active Stripe subscription handles `customer_unlinked` or `not_found` error codes cleanly by opening `openUnlinkedCustomerModal()`, presenting friendly guidance and steering the user to plan selection rather than crashing with an unhandled exception.
- **Target Result Directory:** `03-account-team-billing/08-gherkin-result-case-unprovisioned-stripe-customer/`

---

## 2. Tester Brief
Free tier workspaces or newly provisioned pilot tenants do not possess a Stripe Customer ID.
1. When the user clicks `button[data-account-action="billing-manage"]`:
2. The client calls `create-billing-portal-intent`.
3. The server responds with `{ ok: false, error: { code: "customer_unlinked" } }`.
4. The client catches this condition and opens the Unlinked Customer Modal (`openUnlinkedCustomerModal()`):
   - Title: `"No Active Billing Subscription"` / `"Aktif Faturalama Aboneliği Yok"`.
   - Action Button: `[data-account-action="billing-buy-more"]` pointing to subscription tier options.
5. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Owner of unlinked workspace).
- **Target Route:** `[APP_URL]/#/[SLUG]/account?tab=billing`.
- **Target Button:** `button[data-account-action="billing-manage"]`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Unprovisioned Stripe Customer Handling

  Scenario Outline: Opening plan selection modal when managing billing without a linked Stripe customer
    Given the test user is viewing the Billing tab in language "<Language>"
    And the workspace has no linked Stripe customer record
    When the user clicks the manage billing button "[data-account-action='billing-manage']"
    Then the billing portal intent should return error code "customer_unlinked"
    And the unlinked customer modal ".acct-modal" should be opened
    And the modal title should contain "<ExpectedModalTitle>"
    And the modal should render the buy more button "[data-account-action='billing-buy-more']"

    Examples:
      | Language | ExpectedModalTitle               | ActionButtonText   |
      | en       | No Active Billing Subscription   | View Plans         |
      | tr       | Aktif Faturalama                 | Planları İncele    |
```

---

## 5. Visual Checks
- **Modal Elements:**
  - Container: `.acct-modal`.
  - Header: `h3` or `.modal-title` containing `"No Active Billing Subscription"`.
  - Action Button: `button[data-account-action="billing-buy-more"]`.
  - Dismiss: `button[data-account-action="close-modal"]`.
- **Screenshot Points:**
  - `01_unlinked_customer_modal.png` (Modal steering user to subscription tiers).

---

## 6. Data and Network Checks
- **Command RPC:**
  - Command: `create-billing-portal-intent`.
  - Response: `{ ok: false, error: { code: "customer_unlinked" } }`.

---

## 7. Evidence and Reporting
- **Result Directory:** `03-account-team-billing/08-gherkin-result-case-unprovisioned-stripe-customer/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-unlinked-stripe');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/account?tab=billing', { wait: true, timeout: 30 });
await wait(2);

const modalCheck = await js(String.raw`(() => {
  const origCall = window.ZEO_DATA_PROVIDER.callCommand;
  window.ZEO_DATA_PROVIDER.callCommand = (cmd, payload) => {
    if (cmd === 'create-billing-portal-intent') {
      return Promise.resolve({
        ok: false,
        error: { code: "customer_unlinked", message: "No customer on file" }
      });
    }
    return origCall.apply(this, arguments);
  };

  const btn = document.querySelector('[data-account-action="billing-manage"]');
  if (btn) { btn.disabled = false; btn.click(); }

  return new Promise(resolve => {
    setTimeout(() => {
      window.ZEO_DATA_PROVIDER.callCommand = origCall;
      const modal = document.querySelector('.acct-modal');
      const title = modal ? modal.querySelector('h3, .modal-title')?.innerText?.trim() : null;
      const buyBtn = modal ? modal.querySelector('[data-account-action="billing-buy-more"]') : null;
      resolve({
        modalFound: !!modal,
        title,
        hasBuyBtn: !!buyBtn
      });
    }, 400);
  });
})()`);

cliLog('Unlinked Customer Result: ' + JSON.stringify(modalCheck));
if (!modalCheck.modalFound || !modalCheck.title.includes("No Active Billing")) {
  throw new Error('Unlinked customer modal failed to open upon customer_unlinked error');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-unlinked-stripe', { keep: false })`.
