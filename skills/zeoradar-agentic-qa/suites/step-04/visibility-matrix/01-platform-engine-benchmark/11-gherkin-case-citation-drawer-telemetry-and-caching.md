# Test Case: TC-VIS-11 - Citation Drawer Telemetry Resolution, Caching & Footprint Table

## 1. Case ID and Purpose
- **Case ID:** `TC-VIS-11`
- **Module:** Citation Drawer Subsystem (`assets/radar.js`, `assets/radar.css`)
- **Parent Contract:** Spec 09 / Spec 11 (Citation Intelligence & Authoritative Telemetry Pipeline)
- **Traceability:** Maps to Source Scenarios `VIS-14`, `VIS-15`, `VIS-26`, and `VIS-27`
- **Purpose:** Verify that clicking any citation trigger (`[data-action="open-citation-drawer"]`) mounts the slide-in Citation Drawer (`#citationDrawerHolder`), queries `ZEO_DATA_PROVIDER.loadResource("citationDetail")` when the URL is uncached, stores the response in `state.citationDetailCache[norm]`, displays telemetry cards (Domain, Category Badge, Occurrences, First/Last Seen dates), renders the historical occurrence footprint table, gracefully displays an empty notice when a newly discovered domain has 0 historical occurrences, and reloads instantly from client memory on subsequent invocations.

---

## 2. Tester Brief
The tester or automated agent exercises the Citation Drawer data pipeline:
1. Click a citation trigger with an unvisited URL (e.g. `[CITATION_URL]`):
   - Drawer mounts to `document.body` with `#citationDrawerHolder`.
   - Temporary loading state displays `.bh-tv-loading` and `.spinner`.
   - Data provider resolves telemetry; drawer transitions to `status = "ready"`.
   - Telemetry cards display Domain, Category badge (`cat-owned`, `cat-competition`, `cat-earned`), Total Occurrences, First Seen, and Last Seen dates.
   - Footprint table displays historical rows with Date, Engine chip, Prompt ID, and Rank.
2. Close the drawer, click the identical citation trigger again, and verify:
   - Drawer opens immediately in `status = "ready"` without showing the loading spinner, proving client-side memory cache utilization (`state.citationDetailCache[norm]`).
3. Open a citation trigger for a newly discovered domain with zero recorded historical occurrences:
   - Footprint table displays the graceful empty notice: *"No recorded occurrences found for this citation across evaluated executions."*
   - Occurrences KPI displays `0`; First/Last seen display `"–"` without throwing JS exceptions.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/app/[SLUG]/visibility?workspace=studio`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Citation URL `[CITATION_URL]`:** `[CITATION_URL]` (e.g. `tr.wikipedia.org/wiki/[BRAND]`)
- **Unindexed Domain URL:** `example-new-discovery.com/page`
- **UI Language `[LANGUAGE]`:** `en` (or `tr`)
- **Matching Result Directory:** `11-gherkin-result-case-citation-drawer-telemetry-and-caching/` *(Do not create empty directory ahead of execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Citation Drawer Telemetry Resolution, In-Memory Caching, and Footprint Table

  Background:
    Given the user is on the "studio" workspace of Zeo Geo-Radar
    Then at least one citation leaf or domain row "[data-action='open-citation-drawer']" should exist

  Scenario: First Drawer Open with Network Fetch and Telemetry Display
    Given the citation URL "[CITATION_URL]" is not in "window.state.citationDetailCache"
    When the user clicks the citation trigger for "[CITATION_URL]"
    Then the drawer holder "#citationDrawerHolder" should be attached to "document.body"
    And the loading spinner ".bh-tv-loading .spinner" should display briefly while in flight
    And upon fetch resolution, the drawer status should transition to "ready"
    And the drawer title "#citationDrawerTitle" should display the normalized URL
    And the domain summary card should display the domain and category badge ".cat-badge"
    And the 3 KPI cards ".bh-tv-kpis .bh-kpi-card" should render:
      | KPI Title   | Expected Format |
      | Occurrences | [0-9]+          |
      | First Seen  | YYYY-MM-DD or – |
      | Last Seen   | YYYY-MM-DD or – |
    And the footprint table ".zr-citation-detail-content table.tbl" should render historical rows

  Scenario: Instant Subsequent Open via In-Memory Cache
    Given the citation URL "[CITATION_URL]" has already been cached in "window.state.citationDetailCache"
    When the user closes the drawer
    And the user clicks the citation trigger for "[CITATION_URL]" again
    Then the drawer should open immediately with status "ready"
    And the loading spinner ".bh-tv-loading .spinner" must not appear in the DOM
    And no new network request should be dispatched to the data provider

  Scenario: Graceful Empty Footprint Handling for Newly Discovered Domains
    When the user opens the citation drawer for an unindexed domain with 0 occurrences
    Then the Occurrences KPI ".bh-kpi-num" should equal "0"
    And the First Seen and Last Seen KPIs should display "–"
    And the footprint container should display the empty state message:
      | Expected Text (EN)                                                          | Expected Text (TR)                                                         |
      | No recorded occurrences found for this citation across evaluated executions. | Değerlendirilen çalıştırmalarda bu kaynak için kayıtlı görünüm bulunamadı. |
    And no JavaScript errors should be thrown
```

---

## 5. Visual Checks
1. **Slide-In Panel Layout:** `.zr-drawer-panel.zr-citation-drawer` has fixed width `480px`, anchored to the right viewport edge with full height.
2. **Backdrop Dimmer:** `.zr-drawer-backdrop` overlays the main workspace with semi-transparent tint (`background: rgba(0,0,0,0.4)`).
3. **Category Badges:**
   - `.cat-owned`: Green pill.
   - `.cat-competition`: Red pill.
   - `.cat-earned`: Blue pill.
4. **Footprint Table Alignment:** Date (mono), Engine (small chip), Prompt ID (truncated mono), Rank (`#1` bold right-aligned).

---

## 6. Data and Network Checks
1. **Cache Verification:**
   ```js
   const norm = window.normalizeCitationUrl(rawUrl);
   assert(window.state.citationDetailCache[norm] != null, "Telemetry data must be cached");
   ```
2. **Provider Call Parameters:**
   - `dp.loadResource("citationDetail", { projectId, urlNormalized })` called with sanitized domain/path.
3. **Retry Flow on Network Failure:**
   - On mock error, `.bh-conflict-alert.card` renders.
   - Clicking `button[data-action="retry-citation-detail"]` invokes `openCitationDrawer(rawUrl, true)` with `force = true`.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `11-gherkin-result-case-citation-drawer-telemetry-and-caching/`
- **Execution Model (MacBook / Ego Browser):**
  1. Automated test runs inside Ego Browser via `ego-browser nodejs`.
  2. Captured visual screenshots (`drawer_loading_spinner.png`, `drawer_telemetry_ready.png`, `drawer_empty_occurrences.png`) are stored in the MacBook task space.
  3. Transfer screenshots from MacBook to repository runner via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/visibility/tc-vis-11-*.png .agents/skills/zeoradar-agentic-qa/suites/step-04/visibility-matrix/01-platform-engine-benchmark/11-gherkin-result-case-citation-drawer-telemetry-and-caching/screenshots/
     ```
  4. Write execution report `result.md` verifying network payloads, cache keys, and table rows.

### Pass/Fail Criteria
- [ ] Drawer mounts on click and resolves telemetry.
- [ ] Telemetry data is stored in `state.citationDetailCache`.
- [ ] Subsequent opens bypass network loading spinner.
- [ ] Newly discovered domains with 0 occurrences render graceful empty state message.
