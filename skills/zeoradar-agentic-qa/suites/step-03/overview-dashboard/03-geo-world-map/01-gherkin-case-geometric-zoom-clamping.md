# Test Case: Geometric Zoom Clamping (1.0x to 9.0x)

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-MAP-05`
- **Purpose**: Verify that the map zoom engine (`applyMapZoom`) strictly clamps the zoom multiplier $z$ within the interval $[1.0, 9.0]$ using a 1.7x step factor, preventing canvas distortion, infinite scaling, negative viewBox dimensions, and guaranteeing that zooming out resets `viewBox` exactly to `data-vb0`.

---

## 2. Tester Brief
Unclamped geometric zoom calculations can lead to runaway scaling, causing SVG maps to invert, vanish, or trigger browser layout crashes.
Zeo Geo-Radar enforces strict geometric boundary clamping:
1. **Zoom In Clamping**: Each click multiplies $z$ by 1.7x, clamped strictly at $9.0$ (`state.mapZoom = Math.min(z * 1.7, 9)`).
2. **Zoom Out Clamping**: Each click divides $z$ by 1.7x, clamped strictly at $1.0$ (`state.mapZoom = Math.max(z / 1.7, 1); if (z < 1.05) z = 1`).
3. When $z \le 1.0$, the original base `viewBox` stored in `data-vb0` is restored.

The tester simulates rapid repeated clicks on Zoom In and Zoom Out buttons and checks `state.mapZoom` and SVG `viewBox`.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/regions`
- **Buttons**: `button[data-action="map-zoom"][data-dir="in"]` and `[data-dir="out"]`

---

## 4. Gherkin Scenario

```gherkin
Feature: Map Geometric Zoom Factor Clamping
  As an exploratory user navigating global regions
  I want zoom controls to clamp reliably at minimum and maximum scale bounds
  So that the map never disappears, scales infinitely, or produces negative viewBox values.

  Scenario: Zoom In clamps at 9.0x maximum threshold
    Given the user is viewing the interactive world map
    When the user clicks the Zoom In button 10 times
    Then "state.mapZoom" should equal 9.0
    And the SVG "viewBox" width and height should be strictly positive

  Scenario: Zoom Out clamps at 1.0x and restores base viewBox
    Given the user is at maximum zoom level on the world map
    When the user clicks the Zoom Out button 10 times
    Then "state.mapZoom" should equal 1.0
    And the SVG "viewBox" attribute should equal "data-vb0"
```

---

## 5. Visual Checks
- **Zoom In**: Map smoothly magnifies, focusing closer on the active market.
- **Max Zoom (9.0x)**: Map remains stable, clearly showing country borders without inversion.
- **Base Reset (1.0x)**: Full world map restored to default coordinates `0 0 1000 600`.

---

## 6. Data and Network Checks
- **Zoom Clamp Assertion**:
  ```javascript
  const zoomClampTest = await js(String.raw`(() => {
    const inBtn = document.querySelector('[data-action="map-zoom"][data-dir="in"]');
    const outBtn = document.querySelector('[data-action="map-zoom"][data-dir="out"]');
    const svg = document.querySelector('#mapPane svg');
    if (!inBtn || !outBtn || !svg) return { error: 'Zoom controls or SVG not found' };

    // 1. Zoom In 10 times
    for (let i = 0; i < 10; i++) inBtn.click();
    const maxZoom = window.state?.mapZoom;

    // 2. Zoom Out 10 times
    for (let i = 0; i < 10; i++) outBtn.click();
    const minZoom = window.state?.mapZoom;
    const minVb = svg.getAttribute('viewBox');
    const vb0 = svg.getAttribute('data-vb0');

    return {
      maxZoom,
      maxClamped: maxZoom <= 9.0 && maxZoom >= 8.9,
      minZoom,
      minClamped: minZoom === 1.0,
      vbRestored: minVb === vb0,
      noError: !window.__lastError
    };
  })()`);
  if (!zoomClampTest.maxClamped || !zoomClampTest.minClamped || !zoomClampTest.vbRestored || !zoomClampTest.noError) {
    throw new Error('Geometric zoom clamping assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-geometric-zoom-clamping/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of 9.0x zoomed map and 1.0x reset map saved in result directory.
  - SCP sync from MacBook to host before final test report compilation.
