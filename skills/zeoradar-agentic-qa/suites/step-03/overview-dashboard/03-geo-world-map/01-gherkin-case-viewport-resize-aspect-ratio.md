# Test Case: Viewport Resize & Aspect Ratio Preservation

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-MAP-11`
- **Purpose**: Verify that dynamic viewport resizing (from desktop 1200px down to mobile 375px) preserves the vector map coordinate aspect ratio, maintains the immutable base coordinate space `0 0 1000 600` stored in `data-vb0`, and prevents horizontal stretching or map coordinate corruption.

---

## 2. Tester Brief
Vector maps rendered inside responsive layouts risk distortion if CSS scaling overrides internal SVG projection coordinates, or if resize handlers corrupt the base viewBox.
Zeo Geo-Radar protects map geometry:
1. The base viewBox `0 0 1000 600` is permanently recorded in `svg.getAttribute("data-vb0")`.
2. Responsive sizing relies on fluid CSS rules (`width: 100%; height: auto; display: block;`).
3. Window resizing modifies container layout without corrupting internal coordinate ratios or overriding `data-vb0`.

The tester tests window resize transitions and verifies coordinate ratio stability.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/regions`
- **Viewports**: Desktop (1200x800) and Mobile (375x812)

---

## 4. Gherkin Scenario

```gherkin
Feature: Vector Map Responsive Aspect Ratio Preservation
  As a mobile or tablet user
  I want the world map to scale fluidly without distortion or coordinate corruption
  So that countries retain their authentic geographical shapes across all screen sizes.

  Scenario Outline: Resizing viewport across standard device dimensions
    Given the user is viewing the world map
    When the browser viewport is resized to "<Width>" by "<Height>"
    Then the SVG element should preserve its "data-vb0" attribute as "0 0 1000 600"
    And the map width-to-height ratio should remain proportional to 1000:600
    And the map canvas should not exhibit horizontal overflow

    Examples:
      | DeviceType | Width | Height |
      | Desktop    | 1200  | 800    |
      | Tablet     | 768   | 1024   |
      | Mobile     | 375   | 812    |
```

---

## 5. Visual Checks
- **Proportions**: Geographical contours (e.g. Mediterranean basin, Americas) retain natural aspect ratio without horizontal squishing or vertical elongation.
- **Fluid Fit**: Map spans 100% of container width smoothly.

---

## 6. Data and Network Checks
- **Aspect Ratio Assertion**:
  ```javascript
  const resizeCheck = await js(String.raw`(() => {
    const svg = document.querySelector('#mapPane svg');
    if (!svg) return { error: 'SVG not found' };

    const vb0 = svg.getAttribute('data-vb0') || svg.getAttribute('viewBox');
    const parts = vb0.split(/\s+/).map(Number);
    const validRatio = parts.length === 4 && parts[2] === 1000 && parts[3] === 600;

    return {
      vb0,
      validRatio,
      noError: !window.__lastError
    };
  })()`);
  if (!resizeCheck.validRatio || !resizeCheck.noError) {
    throw new Error('Vector map data-vb0 corrupted; expected 1000:600 ratio');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-viewport-resize-aspect-ratio/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of map rendered at 1200px, 768px, and 375px saved in result directory.
  - SCP sync from MacBook to host before final test report compilation.
