# Test Case: Target-Centered Bounding Box Centering

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-MAP-06`
- **Purpose**: Verify that when zooming in on the vector world map, the geometric pan engine dynamically calculates the target country's SVG bounding box (`tr.getBBox()`), centers the viewport on $(cx, cy)$, and clamps viewBox origin coordinates $(x, y)$ within valid canvas bounds, preventing blank ocean borders.

---

## 2. Tester Brief
Centering an SVG zoom on a specific geographical market requires geometric coordinate transformation:
1. When $z > 1.0$, the engine calculates zoomed dimensions: $W = vb0[2] / z$ and $H = vb0[3] / z$.
2. It fetches the bounding box of the active tracked market (`#tr`):
   $cx = b.x + b.width / 2$, $cy = b.y + b.height / 2$.
3. Origin coordinates $(x, y)$ are clamped within:
   $x \in [vb0[0], vb0[0] + vb0[2] - W]$, $y \in [vb0[1], vb0[1] + vb0[3] - H]$.
4. The calculated string is applied to the SVG `viewBox` attribute (`x y W H`).

The tester verifies that zooming in centers around the active market and that viewBox coordinates never fall outside the base coordinate bounding box.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/regions`
- **Active Market**: `path#tr` present in SVG.

---

## 4. Gherkin Scenario

```gherkin
Feature: Target-Centered Map Zoom and ViewBox Centering
  As an analyst focusing on a specific geographic market
  I want zooming in on the world map to center directly on our primary market territory
  So that I do not have to manually pan across the globe to find our country.

  Scenario: Zoom In centers on active market path
    Given the user is on the Regions map view with market "TR"
    When the user clicks the Zoom In button "[data-action='map-zoom'][data-dir='in']"
    Then the SVG "viewBox" attribute should be updated
    And the viewBox width should be smaller than the initial base width
    And the center of the zoomed viewBox should be positioned near the bounding box center of path "#tr"
    And the viewBox X and Y origins must be clamped within the base canvas boundaries
```

---

## 5. Visual Checks
- **Target Focus**: Turkey (`#tr`) is positioned centrally within the map canvas upon zooming in.
- **No Blank Ocean**: No excessive blank margin or grey area appears beyond the global map boundaries.

---

## 6. Data and Network Checks
- **Geometric Centering Assertion**:
  ```javascript
  const centerCheck = await js(String.raw`(() => {
    const svg = document.querySelector('#mapPane svg');
    const tr = svg?.querySelector('#tr');
    if (!svg || !tr) return { error: 'SVG or #tr missing' };

    const inBtn = document.querySelector('[data-action="map-zoom"][data-dir="in"]');
    if (inBtn) inBtn.click();

    const vb = svg.getAttribute('viewBox').split(/\s+/).map(Number);
    const vb0 = svg.getAttribute('data-vb0').split(/\s+/).map(Number);
    const b = tr.getBBox();
    const trMidX = b.x + b.width / 2;
    const trMidY = b.y + b.height / 2;

    const vbMidX = vb[0] + vb[2] / 2;
    const vbMidY = vb[1] + vb[3] / 2;

    // Check that viewBox center is closer to TR than canvas center
    const distToTr = Math.hypot(vbMidX - trMidX, vbMidY - trMidY);
    const origCenter = [vb0[0] + vb0[2] / 2, vb0[1] + vb0[3] / 2];
    const origDistToTr = Math.hypot(origCenter[0] - trMidX, origCenter[1] - trMidY);

    const xClamped = vb[0] >= vb0[0] && (vb[0] + vb[2]) <= (vb0[0] + vb0[2]);
    const yClamped = vb[1] >= vb0[1] && (vb[1] + vb[3]) <= (vb0[1] + vb0[3]);

    return {
      closerToTarget: distToTr < origDistToTr,
      xClamped,
      yClamped,
      noError: !window.__lastError
    };
  })()`);
  if (!centerCheck.closerToTarget || !centerCheck.xClamped || !centerCheck.yClamped || !centerCheck.noError) {
    throw new Error('Target-centered bounding box assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-target-centered-bounding-box/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of centered zoomed map captured into result directory.
  - SCP sync from MacBook to host before final test report compilation.
