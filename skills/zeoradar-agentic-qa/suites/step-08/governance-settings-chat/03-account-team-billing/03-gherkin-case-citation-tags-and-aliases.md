# TC-ACC-03: Citation Taxonomy Tags and Entity Alias Collision Protection

## 1. Case ID and Purpose
- **Case ID:** `TC-ACC-03`
- **Purpose:** Verify the configuration of 7-category citation classification tags (`upsert-citation-tag`) and entity alias mapping (`map-entity-alias`), ensuring that assigning an alias already mapped to another brand triggers duplicate detection and displays a localized rejection error.
- **Target Result Directory:** `03-account-team-billing/03-gherkin-result-case-citation-tags-and-aliases/`

---

## 2. Tester Brief
Accurate AEO citation tracking requires categorizing external URLs and resolving brand aliases.
1. Subtab `citations`:
   - Categories: `Owned`, `Social`, `Competition`, `Partner`, `Editorial`, `Wiki`, `Review`.
   - Adding a pattern (e.g. `*.techcrunch.com/*` as `Editorial`) calls `upsert-citation-tag`.
2. Subtab `matching`:
   - Mapping an alias (e.g. `[BRAND] Agency` -> `[BRAND]`) calls `map-entity-alias`.
   - Collision Defense: If `[BRAND] Agency` is already mapped to Competitor B, the server returns `{ code: "duplicate_alias" }`.
   - The UI catches this and renders: `"This alias is already assigned to another brand."` / `"Bu takma ad zaten başka bir markaya atanmış."`.
3. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com` (Owner role).
- **Target Route:** `[APP_URL]/#/[SLUG]/settings`.
- **Target Category:** `Editorial`.
- **Target Alias:** `Acme Corp Global`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Citation Taxonomy Tags and Entity Alias Collision

  Scenario Outline: Mapping entity aliases with duplicate collision protection
    Given the test user is on the Settings matching subtab
    When the user attempts to map alias "<AliasName>" to brand "<TargetBrand>"
    And the alias is already assigned to another brand
    Then the mutation command "map-entity-alias" should be rejected with "duplicate_alias"
    And the UI should display error notice "<ExpectedErrorMessage>"

    Examples:
      | AliasName         | TargetBrand | ExpectedErrorMessage                               |
      | Acme Corp Global  | [BRAND]     | This alias is already assigned to another brand.   |
      | [BRAND] Solutions | Acme Corp   | Bu takma ad zaten başka bir markaya atanmış        |
```

---

## 5. Visual Checks
- **Citation Tags UI:**
  - Category Pills: `.citation-tag-pill` with color-coded classes (`.tag-owned`, `.tag-editorial`, etc.).
- **Alias Matching UI:**
  - Input: `#settings-alias-input`.
  - Error Box: `.alias-error-banner` or modal alert.
- **Screenshot Points:**
  - `01_citation_tags_catalog.png` (Configured citation category tags).
  - `02_duplicate_alias_error.png` (Duplicate alias collision notice).

---

## 6. Data and Network Checks
- **Command RPCs:**
  - `upsert-citation-tag`: `{ category: "Editorial", pattern: "*.techcrunch.com/*" }`.
  - `map-entity-alias`: `{ alias: "Acme Corp Global", action: "add" }`.

---

## 7. Evidence and Reporting
- **Result Directory:** `03-account-team-billing/03-gherkin-result-case-citation-tags-and-aliases/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-tags-aliases');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/settings', { wait: true, timeout: 30 });
await wait(2);

const aliasCheck = await js(String.raw`(() => {
  let errorShown = false;
  let errorText = null;

  const origCall = window.ZEO_DATA_PROVIDER.callCommand;
  window.ZEO_DATA_PROVIDER.callCommand = (cmd, payload) => {
    if (cmd === 'map-entity-alias') {
      return Promise.resolve({
        ok: false,
        error: { code: "duplicate_alias", message: "This alias is already assigned to another brand." }
      });
    }
    return origCall.apply(this, arguments);
  };

  const addBtn = document.querySelector('[data-action="settings-alias-add"]');
  if (addBtn) addBtn.click();

  return new Promise(resolve => {
    setTimeout(() => {
      window.ZEO_DATA_PROVIDER.callCommand = origCall;
      const errEl = document.querySelector('.alias-error, .toast');
      resolve({
        errorRendered: !!errEl,
        errorMsg: errEl ? errEl.innerText.trim() : null
      });
    }, 400);
  });
})()`);

cliLog('Alias Collision State: ' + JSON.stringify(aliasCheck));
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-tags-aliases', { keep: false })`.
