# Test Case: Dual-Surface Map Parity (Regions vs Volumes)

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-MAP-10`
- **Purpose**: Verify dual-surface architectural parity between the shell Regions map pane (`#mapPane`) and the Prompt Volumes Regional Heatmap (`#volHeatmapHost`), ensuring both surfaces share the unified `VectorMapLoader` in-memory cache (`window.WORLD_SVG`) and render consistent choropleth and country path definitions.

---

## 2. Tester Brief
Zeo Geo-Radar renders the interactive world map in two distinct application contexts:
1. **Shell Regions Tab**: Located in `#mapPane` under the general brand overview.
2. **Prompt Volumes Regional Heatmap**: Located in `#volHeatmapHost` under the Volumes module.

The tester verifies that:
1. Both surfaces source vector markup through `VectorMapLoader`, avoiding redundant network transfers.
2. `window.WORLD_SVG` remains populated and shared across route transitions.
3. Both surfaces preserve SVG node integrity, country IDs (`#tr`, `#us`), and choropleth classification styles without mutual interference.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/regions` and `[APP_URL]/#/[SLUG]/volumes`
- **Shared Asset**: `VectorMapLoader` caching engine.

---

## 4. Gherkin Scenario

```gherkin
Feature: Dual-Surface Map Architecture Parity
  As a software architect
  I want the world map component to share caching and rendering pipelines across application modules
  So that users experience fast, consistent map visualizations regardless of which module they access.

  Scenario: Switching between Regions pane and Volumes heatmap
    Given the user navigates to the "Regions" pane
    Then the map pane "#mapPane" should render the SVG world map
    And "VectorMapLoader.isMapLoaded()" should be true
    When the user navigates to the "Volumes" module
    Then the heatmap container "#volHeatmapHost" should render the SVG world map
    And the map should be hydrated from the shared in-memory cache "window.WORLD_SVG"
    And country paths should maintain their quantile classification
```

---

## 5. Visual Checks
- **Consistency**: Map dimensions, geographic projection, and visual styling match identically across both modules.
- **Instant Hydration**: Second map load occurs without spinner delay.

---

## 6. Data and Network Checks
- **Cache Parity Assertion**:
  ```javascript
  const parityCheck = await js(String.raw`(() => {
    const isLoaded = typeof VectorMapLoader !== 'undefined' ? VectorMapLoader.isMapLoaded() : false;
    const hasWorldSvg = typeof window.WORLD_SVG === 'string' && window.WORLD_SVG.length > 5000;
    
    // Check if current host has svg
    const currentSvg = !!document.querySelector('#mapPane svg, #volHeatmapHost svg');

    return {
      isLoaded,
      hasWorldSvg,
      currentSvg,
      noError: !window.__lastError
    };
  })()`);
  if (!parityCheck.isLoaded || !parityCheck.hasWorldSvg || !parityCheck.currentSvg || !parityCheck.noError) {
    throw new Error('Dual-surface map parity assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-dual-surface-map-parity/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of map in Regions and Volumes modules saved in result directory.
  - SCP sync from MacBook to host before final test report compilation.
