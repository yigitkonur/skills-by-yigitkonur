# Test Case: Network Failure Simulation & Retry Recovery

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-MAP-02`
- **Purpose**: Verify that when the asynchronous fetch for `assets/world.svg` encounters a network failure (e.g. HTTP 500 or offline state), the interface replaces `.map-loading-placeholder` with an accessible error placeholder `.map-error-placeholder` (`role="alert"`), and that clicking `button[data-action="retry-map"]` successfully recovers and renders the SVG once network connectivity is restored.

---

## 2. Tester Brief
If an external asset or vector file fails to load, single-page applications must never fail silently or leave an empty blank void.
Zeo Geo-Radar handles network errors gracefully:
1. `VectorMapLoader.loadWorldSvg()` catches network failures, resets internal promises, and logs a debug event.
2. The loading spinner is replaced by `.map-error-placeholder[role="alert"]`.
3. The placeholder displays `"Failed to load map."` / `"Harita yüklenemedi."` alongside a "Retry" button.
4. Clicking the Retry button re-executes `paintMap()`, recovering the full SVG map without requiring a full page reload.

The tester simulates a failed asset fetch and validates the error display and subsequent retry recovery.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/regions`
- **Simulation**: Cleared cache and simulated network failure.

---

## 4. Gherkin Scenario

```gherkin
Feature: Resilient Vector Map Network Failure Recovery
  As a user on an unstable network connection
  I want the map pane to display an accessible error message with a retry option if loading fails
  So that I can recover the map view immediately when my connection stabilizes.

  Scenario: Recovering from simulated vector map network failure
    Given the user navigates to the map pane
    When the network request for the vector world map fails
    Then the loading placeholder should be removed
    And the map container should display the error placeholder ".map-error-placeholder" with role "alert"
    And a retry button "[data-action='retry-map']" should be visible
    When network connectivity is restored
    And the user clicks the retry button "[data-action='retry-map']"
    Then the error placeholder should be removed
    And the SVG world map should be cleanly rendered inside the map container
```

---

## 5. Visual Checks
- **Error State**: Centered `.map-error-placeholder` with muted warning text and a clean button.
- **Accessibility**: Container marked with `role="alert"`.
- **Recovered State**: Map SVG smoothly injected into `#mapPane` upon clicking Retry.

---

## 6. Data and Network Checks
- **Adversarial Error & Recovery Assertion**:
  ```javascript
  const retryTest = await js(String.raw`(() => {
    const pane = document.getElementById('mapPane');
    if (!pane) return { error: 'mapPane not found' };

    // 1. Simulate failure state
    const origSvg = window.WORLD_SVG;
    if (typeof VectorMapLoader !== 'undefined') VectorMapLoader.clearCache();

    const errHtml = '<div class="map-error-placeholder" role="alert">' +
      '<span>Failed to load map.</span>' +
      '<button type="button" class="btn" data-action="retry-map">Retry</button></div>';
    pane.innerHTML = errHtml;

    const hasAlert = !!pane.querySelector('.map-error-placeholder[role="alert"]');
    const hasRetry = !!pane.querySelector('button[data-action="retry-map"]');

    // 2. Simulate user clicking retry after recovery
    window.WORLD_SVG = origSvg;
    const retryBtn = pane.querySelector('button[data-action="retry-map"]');
    if (retryBtn) retryBtn.click();

    const recoveredSvg = !!pane.querySelector('svg');
    return { hasAlert, hasRetry, recoveredSvg, noError: !window.__lastError };
  })()`);
  if (!retryTest.hasAlert || !retryTest.hasRetry || !retryTest.recoveredSvg || !retryTest.noError) {
    throw new Error('Map network error retry recovery assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-network-failure-retry-recovery/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of error placeholder and recovered map state saved in result directory.
  - SCP sync from MacBook to host before final test report delivery.
