# Step 08.2 — Dashboards, Widgets & Export System QA Suite

## 1. Overview & Architecture

The Zeo Geo-Radar Dashboard and Export subsystem provides executive reporting surfaces, modular analytical visualizations, client-side sanitized CSV data downloads, server-compiled binary PDF generation via asynchronous export intents, graceful browser print fallbacks, and scheduled stakeholder email digest automation.

This test suite provides granular, adversarial, code-grounded Gherkin test cases verifying:
- Dashboard template catalogs and custom layout construction (column spans, grid ordering, widget additions).
- 16 distinct analytical visualization widgets (`VIZ_BY_KEY`) across Chart and Table view modes.
- CSV spreadsheet formula injection defense neutralizing `=+\-@\t\r` prefixes with single-quote escaping (`'`), while preserving valid numerics and percentages.
- Byte-level UTF-8 Byte Order Mark (`\uFEFF`) binary Blob encoding ensuring non-ASCII characters decode accurately in Excel.
- Asynchronous Export Intent RPC lifecycle (`create-export-intent`) with in-flight duplicate click locking (`xpBusy`).
- Graceful degradation: PDF compilation server failures falling back to styled `window.print()` with temporary `body.printing` state flags.
- Scheduled executive digest validation enforcing 1–20 recipient emails syntax rules and external domain stakeholder confirmation.
- Tenant context invalidation aborting stale pending downloads during workspace switching.

---

## 2. Vocabulary & Placeholders

All test cases in this directory adhere to the standardized parameter vocabulary:

| Placeholder | Semantic Type | Description / Example Values |
| :--- | :--- | :--- |
| `[DOMAIN]` | Domain Name | Target brand domain under test (e.g., `zeo.org`, `acme.com`). |
| `[COUNTRY]` | Market Country Code | Target market country (e.g., `US`, `TR`, `UK`, `DE`). |
| `[LANGUAGE]` | Language Code | Application UI language (e.g., `en`, `tr`). |
| `[PROJECT_ID]` | UUID / String | Unique identifier of the active project (e.g., `proj_01j7xyz...`). |
| `[DASHBOARD_ID]` | String / Slug | Identifier of custom or system dashboard (e.g., `dash_executive_01`). |
| `[WIDGET_ID]` | String / Timestamp | Unique identifier of a widget instance (e.g., `v1711200000000`). |
| `[VIZ_TYPE]` | Widget Enum | Visualization key (e.g., `vis-score`, `sov`, `platform-matrix`, `cit-share`). |
| `[EXPORT_KIND]` | Intent Enum | Kind of export (e.g., `dashboard_pdf`, `viz_csv`, `report_summary`). |
| `[EXPORT_FORMAT]` | Format Enum | File format (e.g., `csv`, `pdf`, `json`). |
| `[RECIPIENT_EMAIL]` | Email Address | Stakeholder email address (e.g., `cmo@acme.com`, `agency@partner.org`). |

---

## 3. Ego Browser / MacBook Execution Model

Test execution runs within an isolated **Ego Browser** instance operating on a remote host (MacBook environment):
1. **Remote Execution:** Automated driver scripts are executed on the MacBook via SSH using the `ego-browser nodejs` CLI harness.
2. **Artifact Generation:** Visual snapshots and downloaded blobs are stored locally on the MacBook.
3. **Evidence Ingestion (SCP):** The executor retrieves captured screenshots from the MacBook via SCP (`scp macbook:/tmp/ego-artifacts/*.png <case-result-dir>/`) before compiling the final execution report.
4. **Result Directories:** Each test case references its designated result directory following the convention:
   `02-dashboards-and-exports/01-gherkin-result-case-<short-slug>/`. Result directories are created exclusively upon test execution, never pre-populated with empty folders.

---

## 4. Test Case Inventory

| Case File | Title & Core Verification | Scenarios Covered |
| :--- | :--- | :--- |
| [`01-gherkin-case-dashboard-catalog-and-layout.md`](./01-gherkin-case-dashboard-catalog-and-layout.md) | Dashboard Catalog & Custom Layout Builder | Template switching, grid layout customization, column span settings. |
| [`02-gherkin-case-widget-creation-and-modes.md`](./02-gherkin-case-widget-creation-and-modes.md) | Widget Catalog & Chart/Table Modes | 16 visualization types in `VIZ_BY_KEY`, mode toggling, topic filtering. |
| [`03-gherkin-case-csv-formula-injection-defense.md`](./03-gherkin-case-csv-formula-injection-defense.md) | CSV Formula Injection Defense | Prepending `'` to `=+\-@\t\r`, preserving valid numerics/percentages. |
| [`04-gherkin-case-csv-utf8-bom-integrity.md`](./04-gherkin-case-csv-utf8-bom-integrity.md) | UTF-8 BOM (`\uFEFF`) Binary Encoding | Verifying `\uFEFF` Byte Order Mark and `charset=utf-8` MIME headers. |
| [`05-gherkin-case-pdf-export-and-print-fallback.md`](./05-gherkin-case-pdf-export-and-print-fallback.md) | PDF Export & Graceful Print Fallback | Server compilation failure falling back to `window.print()` and `.printing`. |
| [`06-gherkin-case-export-intent-inflight-lock.md`](./06-gherkin-case-export-intent-inflight-lock.md) | Export Intent In-Flight Lock (`xpBusy`) | Preventing parallel duplicate downloads with `busy` rejection code. |
| [`07-gherkin-case-scheduled-digest-email-validation.md`](./07-gherkin-case-scheduled-digest-email-validation.md) | Stakeholder Digest Email Validation | Enforcing 1–20 valid recipient emails syntax rules (`crValidateForm`). |
| [`08-gherkin-case-scheduled-digest-external-warning.md`](./08-gherkin-case-scheduled-digest-external-warning.md) | External Recipient Guard & Confirmation | Detecting external email domains via `crExternalRecipients` checkbox. |
| [`09-gherkin-case-export-error-code-mapping.md`](./09-gherkin-case-export-error-code-mapping.md) | Export Error Code Localized Mapping | Normalized toast copy for `rate_limited`, `access_suspended`, etc. |
| [`10-gherkin-case-export-tenant-switch-abort.md`](./10-gherkin-case-export-tenant-switch-abort.md) | Cross-Tenant Export Invalidation | Aborting pending export download if tenant context changes in-flight. |

---

## 5. Traceability & Coverage Matrix

| Original Monolithic Section (`02-dashboards-and-exports.md`) | New Modular Case File | Coverage Status | Notes & Invariants Added |
| :--- | :--- | :---: | :--- |
| **Section 1 & 7.1**: Dashboard Catalog & Layout | `01-gherkin-case-dashboard-catalog-and-layout.md` | Full | Template selection, widget addition modal, grid reordering. |
| **Section 2**: 16 Visualization Types | `02-gherkin-case-widget-creation-and-modes.md` | Full | Covers `vis-score`, `sov`, `platform-matrix`, chart/table mode toggles. |
| **Section 3 & 7.2**: CSV Formula Injection Defense | `03-gherkin-case-csv-formula-injection-defense.md` | Full | Tests vectors `=cmd`, `+SUM`, `-@HYPER`, `@SUM`, `\t`, `\r` vs `-12.5%`. |
| **Section 3.1 & 7.3**: UTF-8 BOM (`\uFEFF`) Verification | `04-gherkin-case-csv-utf8-bom-integrity.md` | Full | Intercepts `Blob` constructor; verifies `charCodeAt(0) === 0xFEFF`. |
| **Section 5 & 7.4**: PDF Server Failure & Print Fallback | `05-gherkin-case-pdf-export-and-print-fallback.md` | Full | Mocks rejection; verifies `window.print()`, `body.printing`, button reset. |
| **Section 4 & 7.6**: Export Intent In-Flight Lock (`xpBusy`) | `06-gherkin-case-export-intent-inflight-lock.md` | Full | Proves parallel triggers return `{ ok: false, code: "busy" }`. |
| **Section 6 & 7.5**: Scheduled Digest Recipient Validation | `07-gherkin-case-scheduled-digest-email-validation.md` | Full | Verifies `crValidateForm` rejects malformed emails and enforces 20 cap. |
| **Section 6.1**: External Domain Recipient Warning | `08-gherkin-case-scheduled-digest-external-warning.md` | Full | Verifies `crExternalRecipients` triggers external confirmation checkbox. |
| **Section 4.1**: Localized Error Code Mapping | `09-gherkin-case-export-error-code-mapping.md` | Full | Validates mapped user copy instead of raw server exception strings. |
| **Section 4 (Step 5)**: Multi-Tenant Stale Invalidation | `10-gherkin-case-export-tenant-switch-abort.md` | Full | Verifies `orch.begin(["tenantGen"])` aborts stale download on switch. |
