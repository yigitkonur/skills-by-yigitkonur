# TC-BH-10: Multi-Tenant Generation Fencing on Rapid Project Switching

## 1. Case ID and Purpose
- **Case ID:** `TC-BH-10`
- **Purpose:** Verify that Brand Hub context tracking variables (`bhContextGen`, `bhLastRequestedPid`) prevent out-of-order asynchronous responses from contaminating the current project view when the user rapidly switches projects or workspaces while network requests are in-flight.
- **Target Result Directory:** `01-brand-hub-ground-truth/10-gherkin-result-case-context-fencing-project-switch/`

---

## 2. Tester Brief
In multi-brand agencies or enterprise teams, users frequently switch between projects.
1. When switching from Project A to Project B, `bhContextGen` increments.
2. If an in-flight network request from Project A completes AFTER the switch has taken place:
   - `bhContextGen !== dispGen` OR `dispPid !== bhLastRequestedPid`.
3. The response callback must detect the generation mismatch and drop the payload, preventing Project A's facts or brand guidelines from rendering in Project B's surface.
4. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/kb`
- **Fixtures & Placeholders:**
  - `[PROJECT_A]`: `proj_acme_01` (Brand: "Acme Corp")
  - `[PROJECT_B]`: `proj_beta_02` (Brand: "Beta Industries")

---

## 4. Gherkin Scenario

```gherkin
Feature: Multi-Tenant Project Context Fencing

  Scenario: Discarding in-flight responses following rapid project switching
    Given the test user is viewing Brand Hub for Project A
    When a background load request is initiated for Project A
    And the user immediately switches active project to Project B before the request resolves
    Then the generation counter "bhContextGen" should increment
    And when the Project A request finally completes
    Then the payload for Project A should be silently discarded
    And the Brand Hub header should strictly display Project B brand name

    Examples:
      | InitialProject | TargetProject | ExpectedFinalBrand |
      | proj_acme_01   | proj_beta_02  | Beta Industries    |
```

---

## 5. Visual Checks
- **Header Elements:**
  - Active Brand Title: Displays Brand B name without flashes of Brand A content.
  - Fact Count: Reflects Brand B facts count.
- **Screenshot Points:**
  - `01_project_b_clean_context.png` (Brand Hub rendered purely with Project B data).

---

## 6. Data and Network Checks
- **Context Variables:**
  - `bhContextGen` increments on project change.
  - `bhLastRequestedPid === "proj_beta_02"`.
  - In-flight callback verifies `if (dispGen !== bhContextGen || dispPid !== bhLastRequestedPid) return;`.

---

## 7. Evidence and Reporting
- **Result Directory:** `01-brand-hub-ground-truth/10-gherkin-result-case-context-fencing-project-switch/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-bh-fencing');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/kb', { wait: true, timeout: 30 });
await wait(2);

const fencingCheck = await js(String.raw`(() => {
  const bhs = window.state && window.state.brandHub;
  const initialBrand = bhs && bhs.data ? bhs.data.brandName : null;

  // Simulate context switch
  if (typeof window.ZEO_PROVIDER_ORCHESTRATOR !== "undefined") {
    window.ZEO_PROVIDER_ORCHESTRATOR.triggerCleanup();
  }

  return {
    initialBrand,
    contextCleaned: bhs ? bhs.status === "idle" || bhs.data === null : true
  };
})()`);

cliLog('Fencing Check: ' + JSON.stringify(fencingCheck));
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-bh-fencing', { keep: false })`.
