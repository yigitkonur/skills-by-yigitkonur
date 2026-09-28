# Suite 01: AI Agent Vitals, Crawler Telemetry & Edge Server Logs

## 1. Overview & Architecture

This suite specifies end-to-end and modular Gherkin QA test cases for the **Agent Analytics & AI Traffic Monitoring** module of Zeo Geo-Radar. It exercises the frontend interface (`assets/agent-analytics.js`, `assets/agent-analytics.css`), backend PostgreSQL schema (`backend/db/migrations/20260921140000_web_vitals_audits.sql`), edge telemetry handlers, and the synthetic Core Web Vitals audit runner (`run-vitals-audit`).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        AI AGENT ANALYTICS & TELEMETRY ARCHITECTURE                     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   Client Navigation (/#/app/:slug/agentanalytics)                                      │
│        │                                                                               │
│        ▼                                                                               │
│   [window.renderAgentAnalyticsPage(p)] ◄──► [window.AgentAnalyticsState]               │
│        │                                                                               │
│        ├── 1. Global Header & Context Bar (`.aa-header`)                               │
│        │    ├─ Domain Badge (`.aa-domain-badge`) & Connection Dot (`.aa-status-dot`)   │
│        │    └─ Setup Wizard Trigger (`button[data-action="aa-open-wizard"]`)           │
│        │                                                                               │
│        ├── 2. Global Filter Toolbar (`.aa-filter-toolbar`)                             │
│        │    ├─ Date Range (`24h`, `7d`, `30d`, `90d`)                                  │
│        │    ├─ Compare Period (`previous_period`, `previous_year`, `none`)             │
│        │    ├─ Granularity (`daily`, `hourly`, `weekly`)                               │
│        │    └─ Quick Bot & Platform Filter Chips                                       │
│        │                                                                               │
│        ├── 3. Sub-Tab Navigation Bar (`.aa-tabs-bar`)                                  │
│        │    ├─ Overview (`data-tab="overview"`): Cockpit KPIs, Bot Progress Bars       │
│        │    ├─ Pages (`data-tab="pages"`): Web Vitals Audit Runner (`run-vitals-audit`)│
│        │    ├─ Bot Visits (`data-tab="bot-visits"`): Platforms, UAs & Deep Dive Branch│
│        │    ├─ Server Logs (`data-tab="logs"`): Edge Logs Table, Status Filters, Drawer│
│        │    └─ Settings (`data-tab="settings"`): Multi-domain & IndexNow Key Flow      │
│        │                                                                               │
│        └── 4. Slide-Over Drawers & Modals                                              │
│             ├─ Visit Details Drawer (`.zr-drawer-panel.aa-drawer`)                     │
│             ├─ All Answers & Citations Drawer (`.aa-answer-drawer`)                    │
│             └─ 5-Step Integration Setup Wizard Modal (`.aa-wizard`)                    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Vocabulary & Placeholders

The test scenarios in this suite utilize standardized placeholder tokens to decouple test logic from specific test tenants, locales, and environments:

| Placeholder Token | Description & Permitted Values | Example Values |
|---|---|---|
| `[DOMAIN]` | Active project domain under test | `[DOMAIN]` (e.g. `daikin.com.tr`) |
| `[COUNTRY]` | 2-letter ISO country code | `US`, `TR`, `GB`, `DE` |
| `[LANGUAGE]` | UI localization preference (`en` or `tr`) | `en` (English), `tr` (Türkçe) |
| `[BOT_NAME]` | Registered AI crawler identifier or name | `GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended`, `Amazonbot`, `ByteSpider`, `other` |
| `[AUDIT_STRATEGY]` | Synthetic audit runner emulation profile | `mobile`, `desktop` |
| `[CWV_METRIC]` | Google Core Web Vitals metric key | `fcp`, `lcp`, `tti`, `speedIndex`, `tbt`, `cls` |
| `[LOG_FILTER_STATUS]` | HTTP response status filter option | `all`, `200`, `404`, `500` |
| `[LOG_FILTER_PLATFORM]`| AI platform filter option | `all`, `ChatGPT`, `Claude`, `Perplexity`, `Gemini`, `Amazon` |
| `[INTEGRATION_PROVIDER]`| Edge telemetry ingestion provider | `cloudflare`, `dokploy`, `webhook` |

---

## 3. Test Case Inventory & Traceability Matrix

This directory decomposes the monolithic test specification into 12 atomic, executable Gherkin test cases. Every requirement from the original specification is mapped below:

| Case ID & File Name | Target Feature / Focus | Originating Scenario & Section | Coverage Rationale |
|---|---|---|---|
| `01-gherkin-case-initial-render-unconnected-hero.md` | Initial render, disconnected state & hero banner | Scenario 1 (§3) & §2.1 | Proves baseline UI honesty when no live telemetry stream exists. |
| `02-gherkin-case-crawler-classification-distribution.md` | Known crawler recognition & traffic share bars | Scenario 3 (§3) & §4.2 | Validates catalog classification for GPTBot, ClaudeBot, etc. with `Scenario Outline`. |
| `03-gherkin-case-bot-deep-dive-inspection.md` | Single-bot deep-dive view branch & trend SVGs | Scenario 3 (§3) & §2.5 | Exercises dedicated bot inspector, KPI trio, donut chart, and back navigation. |
| `04-gherkin-case-unknown-spoofed-crawler-telemetry.md` | Unrecognized, spoofed & empty User-Agents | Scenario 7 (§3) & §4.4 | Tests defensive classification under `other` and graceful fallback without crashes. |
| `05-gherkin-case-http-status-distribution-5xx-impact.md` | HTTP status codes, 200 OK Rate & 5xx degradation | Scenario 8 (§3) & §2.6 | Verifies negative badge styling (`.aa-pill.neg`) and OK rate drop on server errors. |
| `06-gherkin-case-vitals-runner-core-metrics-audit.md` | Core Web Vitals audit execution & thresholds | Scenario 2 (§3) & §4.1, §4.3 | Tests `run-vitals-audit` command, 6 metrics, and score color badges across strategies. |
| `07-gherkin-case-vitals-runner-failure-resilience.md` | Vitals runner error handling & lock release | Scenario 9 (§3) & §4.5 | Proves spinner clears, button re-enables, and toast renders on audit rejection. |
| `08-gherkin-case-vitals-strategy-toggle-race-condition.md` | Mid-run strategy switching & re-entrancy | Scenario 10 (§3) & §4.5 | Guards against concurrent double-dispatch and validates payload strategy preservation. |
| `09-gherkin-case-server-logs-filtering-and-search.md` | Edge server logs path search & dropdown filters | Scenario 4 (§3) & §2.6 | Tests real-time log querying by path substring, HTTP status, and AI platform. |
| `10-gherkin-case-slide-over-drawer-lifecycle-keyboard.md` | Slide-over drawers, backdrop & keyboard Escape | Scenario 11 (§3) & §4.6 | Asserts drawer DOM mounting, backdrop dismissal, close buttons, and focus management. |
| `11-gherkin-case-cloudflare-logpush-and-setup-wizard.md` | 5-step setup wizard & Cloudflare snippet copy | Scenario 6, 12 (§3) & §2.6 | Verifies modal wizard progression, cURL snippet placeholder tokens, and copy toast. |
| `12-gherkin-case-telemetry-export-provenance-boundary.md` | Telemetry CSV export demo vs live boundary | Scenario 5, 12 (§3) & §1.5 | Proves zero-visit export format and ensures sample export is omitted in live mode. |

---

## 4. Execution Model: Ego Browser & MacBook Architecture

Zeo Geo-Radar test automation operates under a distributed execution architecture:
1. **Ego Browser on MacBook**:
   - The browser automation engine (`ego-browser`) executes on an external macOS runner (`macbook`).
   - Browser sessions adhere to a strict 5-phase lifecycle:
     1. `useOrCreateTaskSpace("zeo-radar-step06-...")`
     2. `openOrReuseTab(targetUrl)`
     3. User interactions (clicks, keyboard input, toggles)
     4. Synchronous DOM and state assertions (`tab.js(...)`)
     5. `completeTaskSpace()` in a dedicated final block.
2. **Evidence Collection via SCP**:
   - Screenshots captured on the MacBook host (e.g. `/tmp/ego-shots/*.png`) are transferred to the local repository test results directory via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/*.png ./01-gherkin-result-case-<slug>/
     ```
   - **Crucial Rule**: Result directories (e.g. `01-gherkin-result-case-<slug>/`) are created on demand **only when tests are actively executed**, never pre-created as empty directories.

---

## 5. Element Catalog & CSS Selectors Reference

### Header & Controls
- `.aa-container`: Root container.
- `.aa-header`: Global header bar.
- `.aa-domain-badge`: Domain indicator button (`data-action="aa-open-add-domain"`).
- `.aa-connection-indicator`: Status container (`.aa-connected` vs `.aa-disconnected`).
- `.aa-status-dot.online.pulse`: Pulsing green live indicator.
- `button[data-action="aa-open-wizard"]`: Launches setup wizard.

### Tabs & Viewports
- `button.aa-tab-item[data-tab="overview"]`: Macro crawler overview cockpit.
- `button.aa-tab-item[data-tab="pages"]`: Core Web Vitals and URL monitoring.
- `button.aa-tab-item[data-tab="bot-visits"]`: Bot platforms, user-agents, and deep dive.
- `button.aa-tab-item[data-tab="logs"]`: Edge server logs and integration console.

### Vitals Audit Runner
- `input.aa-input[data-action-input="aa-vitals-url"]`: Target audit URL input.
- `button.aa-pill[data-action="aa-vitals-strategy"][data-strat="mobile|desktop"]`: Strategy toggles.
- `button.btn[data-action="aa-run-vitals"]`: Audit trigger button.
- `.aa-vitals-score-badge`: Lighthouse score pill (`0-100`).
- `.aa-vitals-grid`: 6-card grid for FCP, LCP, TTI, Speed Index, TBT, CLS.

### Drawers & Modals
- `.zr-drawer-panel.aa-drawer`: Slide-over inspector panel.
- `.zr-drawer-backdrop[data-action="aa-close-drawer"]`: Semi-transparent backdrop overlay.
- `.aa-drawer-x[data-action="aa-close-drawer"]`: Top-right close button.
- `.aa-answer-drawer`: Multi-tab answer and citation inspector slide-over.
