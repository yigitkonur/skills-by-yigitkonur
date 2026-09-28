# Test Case: Vector Map Loader On-Demand Caching

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-MAP-01`
- **Purpose**: Verify that `VectorMapLoader` asynchronously loads the SVG world map on demand, caches the markup in memory (`window.WORLD_SVG`), deduplicates concurrent in-flight requests, and serves subsequent renders with zero network overhead without relying on external tile servers.

---

## 2. Tester Brief
The interactive world map does not use bulky third-party tile providers (Google Maps, Mapbox, Leaflet).
Instead, `VectorMapLoader` (`assets/vector-map-loader.js`):
1. Checks if `window.WORLD_SVG` is already in memory.
2. If absent, fetches `assets/world.svg` (or resolves embedded static data).
3. Caches the string in `window.WORLD_SVG`.
4. Subsequent calls to `VectorMapLoader.loadWorldSvg()` resolve immediately from cache.

The tester verifies that navigating between tabs or calling `paintMap()` repeatedly does not trigger duplicate fetch requests once loaded.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/regions`
- **Module**: `VectorMapLoader` loaded in global window scope.

---

## 4. Gherkin Scenario

```gherkin
Feature: Vector Map On-Demand Loading and Memory Caching
  As a performance-conscious engineer
  I want the vector world map to load on demand and cache in memory
  So that initial page bundle size remains minimal and subsequent map views render instantaneously.

  Scenario: Initial on-demand fetch and subsequent cache hit
    Given the user is on the Overview Dashboard
    When the user navigates to the "Regions" map view
    Then the vector map loader should load the world map SVG
    And "window.WORLD_SVG" should contain valid SVG markup
    And "VectorMapLoader.isMapLoaded()" should return true
    When the user navigates away to "Overview" and returns to "Regions"
    Then the map should render immediately from memory without triggering a new network request
```

---

## 5. Visual Checks
- **Map Canvas**: `#mapPane svg` rendered cleanly without lag.
- **No Tile Flicker**: Vector paths appear instantaneously without partial tile chunking.

---

## 6. Data and Network Checks
- **Cache & Performance Assertion**:
  ```javascript
  const cacheCheck = await js(String.raw`(() => {
    const isLoaded = typeof VectorMapLoader !== 'undefined' ? VectorMapLoader.isMapLoaded() : false;
    const hasWorldSvg = typeof window.WORLD_SVG === 'string' && window.WORLD_SVG.length > 5000;
    const paneSvg = !!document.querySelector('#mapPane svg');

    return {
      isLoaded,
      hasWorldSvg,
      paneSvg,
      noError: !window.__lastError
    };
  })()`);
  if (!cacheCheck.isLoaded || !cacheCheck.hasWorldSvg || !cacheCheck.paneSvg || !cacheCheck.noError) {
    throw new Error('Vector map loader caching assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-vector-map-loader-caching/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of loaded vector map saved in result directory.
  - SCP sync from MacBook to host before logging final test report.
