# Test Suite 02: Sentiment Analysis, Audience Perception & Demographic Cohorts

## 1. Module Overview & Architectural Grounding

The **Sentiment Analysis, Audience Perception & Demographic Cohorts** subsystem (`assets/aei.js`, `assets/sentiment-analytics.js`, `assets/radar.js`, `data/sentiment.js`) delivers qualitative AI perception intelligence for Zeo Geo-Radar. It processes evaluative claims extracted from generative AI responses, maps them across 10 standard thematic pillars, computes honest polarity distributions without mathematical coercion, guards against small-sample bias, detects negative anomaly spikes, simulates demographic buyer personas, and audits factual claim integrity via the Hallucination Radar.

### System Architecture Flow

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      SENTIMENT & AUDIENCE PERCEPTION ARCHITECTURE                      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   Client Navigation (/#/app/:slug/visibility?workspace=perception OR /sentiment)      │
│        │                                                                               │
│        ▼                                                                               │
│   [Telemetry Data Ingestion]                                                           │
│   ├─ Wire Contract: SentimentBundleSafe (Backend / Postgres Telemetry)                 │
│   ├─ Shape Normalizer: [ZEO_SENTIMENT_ANALYTICS.toSentimentShape()]                    │
│   │    ├─ Small-sample gate: (pos + neg < 3) ──► Score = NULL (insufficient data)      │
│   │    ├─ Polarity grouping: positive, negative, neutral, mixed                        │
│   │    ├─ Theme mapping: Pricing, Quality, Range, Availability, Brand, Health, etc.    │
│   │    └─ Evidence index: claimIndex, negativeDrivers, promptId, citations            │
│   │                                                                                    │
│   ▼                                                                                    │
│   [Perception Workspace: assets/aei.js] & [Dedicated Sentiment Tab: assets/radar.js]   │
│        │                                                                               │
│        ├── SECTION 1: Brand Sentiment Polarity & Trajectory                            │
│        │    ├─ Polarity bar: Positive (%) / Neutral (%) / Negative (%)                │
│        │    ├─ Minimum 3-claim threshold gating (< 3 claims renders Pending state)     │
│        │    ├─ Score preservation: NULL preserved; never coerced to false 0%          │
│        │    ├─ Per-engine sentiment breakdown (ChatGPT, PPX, GEM, Claude, AIM)        │
│        │    └─ Anomaly Spike Badge (Triggers on negPct >= 15% or negClaims >= 2)      │
│        │                                                                               │
│        ├── SECTION 2: Thematic Attribute Perception Clusters                           │
│        │    ├─ Theme cards: Score, Positive/Negative claim counts, Progress fill       │
│        │    ├─ Fixed 10 themes taxonomy (THEME_LABELS in assets/sentiment-analytics.js)│
│        │    ├─ Attribute accordion: Polarity icon (+, −, ±, ○), mentions count         │
│        │    ├─ Quote pager: Real answer quotes, engine badge, prompt link, sources     │
│        │    └─ Multi-quote carousel cycling (`button[data-action="theme-pager"]`)     │
│        │                                                                               │
│        ├── SECTION 3: Negative Sentiment Drivers & Root Causes                         │
│        │    ├─ Ranked URLs associated with negative claims (sorted descending)         │
│        │    ├─ Primary negative theme badge & example quote extracts (110 chars)       │
│        │    └─ Secure external publisher navigation (`rel="noopener" target="_blank"`) │
│        │                                                                               │
│        ├── SECTION 4: Competitive & Topic Sentiment Benchmarks                         │
│        │    ├─ Cross-brand comparison table (Positive share, Distribution bars)        │
│        │    └─ Topic cluster sentiment matrix (Strongest vs Weakest topics)            │
│        │                                                                               │
│        ├── SECTION 5: Audience Persona Simulation Matrix & Custom Builder              │
│        │    ├─ Cohort recommendation cards: Role, Industry, Tone, AI Recommendation    │
│        │    └─ Custom Persona Builder Modal (`.aei-modal[data-stop="1"]`):             │
│        │         ├─ Empty/whitespace input fallback to default persona definitions     │
│        │         ├─ Special character, quotes & Turkish diacritic sanitization (`esc`)|
│        │         └─ Backdrop overlay dismissal vs inner window click event stop       │
│        │                                                                               │
│        └── SECTION 6: Factual Integrity & Hallucination Radar                          │
│             ├─ Factual Adherence Rate (% supported claims)                             │
│             ├─ Zero-division boundary resilience (`evalClaims === 0` defaults to 100%)│
│             ├─ Supported claims vs Open contradictions                                 │
│             └─ Deep link to Truth Vault (`tab=brand-hub`, `liveTab=hallucinations`)    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure & Test Cases

This directory contains 12 focused, code-grounded Gherkin QA test cases:

| File Name | Case ID | Title / Purpose | Original Coverage |
|:---|:---|:---|:---|
| `01-gherkin-case-perception-workspace-navigation-and-layout.md` | TC-SNT-01 | Perception Workspace Boot, Layout Containers & Section Mounting | SNT-01 |
| `02-gherkin-case-small-sample-gating-and-null-score-preservation.md` | TC-SNT-02 | Small-Sample Guardrail (<3 Claims), Pending Card State & Strict NULL Score Preservation | SNT-02, SNT-18, SNT-19 |
| `03-gherkin-case-polarity-distribution-and-engine-breakdown.md` | TC-SNT-03 | Active Polarity Distribution Bar Segments & 5-Engine Breakdown Rows | SNT-03, SNT-04 |
| `04-gherkin-case-thematic-perception-clusters-and-scores.md` | TC-SNT-04 | Thematic Perception Clusters Grid, 10-Theme Taxonomy & Score Progress Fills | SNT-05 |
| `05-gherkin-case-audience-persona-matrix-and-invitation.md` | TC-SNT-05 | Audience Persona Simulation Cards & Zero-State Demographic Invitation | SNT-06 |
| `06-gherkin-case-custom-persona-builder-modal-lifecycle.md` | TC-SNT-06 | Custom Persona Modal Mount, Event Bubbling Stop (`data-stop`) & Dismissal Paths | SNT-07, SNT-08, SNT-09, SNT-24 |
| `07-gherkin-case-persona-builder-input-fallbacks-and-sanitization.md` | TC-SNT-07 | Persona Builder Empty Input Defaults, Quotes/Diacritic Escaping & XSS Defense | SNT-22, SNT-23 |
| `08-gherkin-case-factual-integrity-and-hallucination-radar.md` | TC-SNT-08 | Factual Adherence Rate, Zero-Division Boundary Safety (100%) & Truth Vault Deep Link | SNT-10, SNT-11, SNT-28 |
| `09-gherkin-case-dedicated-sentiment-tab-and-anomaly-spike.md` | TC-SNT-09 | Dedicated Sentiment Tab, Anomaly Spike Badge Thresholds (`>=15%` / `>=2`) & Root Cause Filter | SNT-12, SNT-13, SNT-20, SNT-21 |
| `10-gherkin-case-theme-accordion-and-multi-quote-pager.md` | TC-SNT-10 | Theme Attribute Accordion, Polarity Icons & Multi-Quote Carousel Pager Cycling | SNT-14, SNT-15, SNT-25 |
| `11-gherkin-case-theme-search-filtering-and-prompt-modal.md` | TC-SNT-11 | Live Theme Keyword Search, Polarity Segment Tabs & Full Response Modal Trigger | SNT-14, SNT-16, SNT-26 |
| `12-gherkin-case-negative-sentiment-drivers-table-and-security.md` | TC-SNT-12 | Negative Sentiment Drivers Ranked Table, Quote Previews & External Link Security | SNT-17, SNT-27 |

---

## 3. Parameter Vocabulary & Test Placeholders

Test scenarios in this suite utilize standardized, bracketed placeholders. The table below defines each placeholder, system mapping, and test variants:

| Placeholder | Meaning & System Mapping | Where & How to Set | Representative Test Variants |
|:---|:---|:---|:---|
| `[DOMAIN]` | Web origin or brand domain under test | Base URL parameter in `openOrReuseTab` or project config | `[DOMAIN]` (e.g. `daikin.com.tr`) |
| `[COUNTRY]` | ISO 3166-1 alpha-2 regional code for market evaluation | Region selector or country card | `all`, `TR`, `US`, `GB` |
| `[LANGUAGE]` | IETF language tag for UI localization | App shell language toggle or `state.lang` | `en` (English), `tr` (Turkish) |
| `[SENTIMENT_CATEGORY]`| High-level polarity bucket | Segment buttons `[data-action="sent-seg"][data-k]` | `all`, `positive`, `negative`, `trending` |
| `[THEME_KEY]` | Standard 10-theme taxonomy identifier | Theme data attribute `data-k` | `pricing`, `quality`, `range`, `availability`, `brand`, `health`, `service`, `packaging`, `sustainability`, `other` |
| `[POLARITY_TYPE]` | Evaluative claim sentiment label | Attribute polarity badge `.apol` | `positive` (`+`), `negative` (`−`), `mixed` (`±`), `neutral` (`○`) |
| `[PERSONA_ROLE]` | Demographic buyer persona title/role | Input `#aeiPersonaRole` | `Enterprise Procurement Director`, `Budget-Conscious Shopper`, `Custom Executive Persona` |
| `[PERSONA_INDUSTRY]` | Industry vertical classification for persona | Input `#aeiPersonaIndustry` | `Technology & SaaS`, `Retail & Luxury`, `General Industry` |
| `[PERSONA_TONE]` | Communication style projected for AI responses | Dropdown `#aeiPersonaTone` | `Formal & Analytical`, `Comparative & Fast`, `Conversational & Quality-Focused` |
| `[EVALUATED_CLAIMS_COUNT]` | Total count of polarized evaluative claims | Telemetry property `totalClaims` | `0` (Zero claims), `2` (Small-sample pending), `150` (Active baseline) |

---

## 4. Ego Browser / MacBook Execution Model

### Physical Topology & Gateway
E2E testing is executed using `ego-browser nodejs` on the physical MacBook gateway connected via SSH.

```
┌─────────────────────────────────┐           ┌─────────────────────────────────┐
│     Linux Host (Development)     │           │      MacBook Gateway (Live)     │
│                                 │   SSH     │                                 │
│  - Test Suite & Gherkin Specs   │──────────►│  - Ego Browser Runtime (Node)   │
│  - Storage / Result Directories │           │  - Active Display / GPU Render  │
│  - SCP Evidence Downloader      │◄──────────│  - Local Screenshot Cache       │
└─────────────────────────────────┘    SCP    └─────────────────────────────────┘
```

### Execution Lifecycle Protocol
1. **Heredoc Dispatch**: The test script is executed remotely via:
   ```bash
   ssh macbook "ego-browser nodejs <<'EOF'
     const task = await useOrCreateTaskSpace('e2e-sentiment-audience-suite');
     const tab = await openOrReuseTab('[APP_URL]/#/app/[SLUG]/visibility?workspace=perception', { wait: true });
     // ... execute semantic actions & assertions
     await completeTaskSpace('e2e-sentiment-audience-suite', { keep: false });
   EOF"
   ```
2. **MacBook Screenshot Capture**: Screenshots are captured directly on the MacBook display to `/tmp/ego-shots/sentiment/`.
3. **Evidence Download via SCP**: Upon scenario completion, the test runner downloads screenshots and network captures to the designated result directory:
   ```bash
   scp macbook:/tmp/ego-shots/sentiment/case-*.png ./01-gherkin-result-case-<slug>/screenshots/
   ```
4. **Result Directory Specification**:
   - Each Gherkin case corresponds to an execution result directory named `0X-gherkin-result-case-<slug>/`.
   - Result directories are **NEVER created as empty placeholders**. They are instantiated only by the test execution runner upon executing the suite.
   - A complete result directory contains:
     - `result.md` (Execution outcome, timing, environment specs, pass/fail status)
     - `evidence.json` (Structured DOM dumps, console errors, state snapshots)
     - `screenshots/*.png` (Visual evidence downloaded from MacBook)
     - `network/*.json` (Recorded HTTP / RPC telemetry)

---

## 5. Traceability & Code Coverage Matrix

| Original Scenario ID | Original Title | New Modular Gherkin Case | Real Code Reference & Gap Hardening |
|:---|:---|:---|:---|
| SNT-01 | Perception Workspace Boot | `01-gherkin-case-perception-workspace-navigation-and-layout.md` | `assets/aei.js:1696` `renderAeiWorkspacePerception`, `.aei-perception-workspace` |
| SNT-02 | Small-Sample Guardrail (<3) | `02-gherkin-case-small-sample-gating-and-null-score-preservation.md` | `assets/aei.js:1715` `totalClaims < 3` renders `.aei-pending-card`, score = `null` |
| SNT-03 | Active Polarity Distribution | `03-gherkin-case-polarity-distribution-and-engine-breakdown.md` | `assets/aei.js:1741` `.aei-sentiment-grid`, `.aei-sent-bar-fill` pos/neu/neg segments |
| SNT-04 | Per-Engine Breakdown | `03-gherkin-case-polarity-distribution-and-engine-breakdown.md` | `assets/aei.js:1756` `.aei-engine-sent-list`, 5 platform mini distribution bars |
| SNT-05 | Thematic Perception Clusters | `04-gherkin-case-thematic-perception-clusters-and-scores.md` | `assets/aei.js:1793` `.aei-attributes-card`, `THEME_LABELS` in `sentiment-analytics.js` |
| SNT-06 | Audience Persona Matrix | `05-gherkin-case-audience-persona-matrix-and-invitation.md` | `assets/aei.js:1829` `.aei-persona-card`, `.aei-persona-grid`, `.aei-p-card` |
| SNT-07 | Custom Persona Modal Open | `06-gherkin-case-custom-persona-builder-modal-lifecycle.md` | `assets/aei.js:2138` `aei-open-persona-builder` sets `st.showPersonaModal = true` |
| SNT-08 | Save Custom Persona | `06-gherkin-case-custom-persona-builder-modal-lifecycle.md` | `assets/aei.js:2145` `aei-save-persona` pushes to `st.customPersonas` |
| SNT-09 | Cancel Persona Modal | `06-gherkin-case-custom-persona-builder-modal-lifecycle.md` | `assets/aei.js:2142` `aei-close-modal` resets `st.showPersonaModal = false` |
| SNT-10 | Hallucination Radar Display | `08-gherkin-case-factual-integrity-and-hallucination-radar.md` | `assets/aei.js:1920` `.aei-hallucination-radar-card`, adherence rate % |
| SNT-11 | Truth Vault Navigation | `08-gherkin-case-factual-integrity-and-hallucination-radar.md` | `assets/aei.js:2122` `aei-goto-truth-vault` switches tab to `brand-hub` |
| SNT-12 | Dedicated Sentiment Tab | `09-gherkin-case-dedicated-sentiment-tab-and-anomaly-spike.md` | `assets/radar.js:3374` `renderSentimentTab`, `.sent-table`, `.stackbar` |
| SNT-13 | Anomaly Spike Warning | `09-gherkin-case-dedicated-sentiment-tab-and-anomaly-spike.md` | `assets/radar.js:3405` `negPct >= 15 || negClaims >= 2` renders `.sent-spike-badge` |
| SNT-14 | Negative Polarity Filter | `11-gherkin-case-theme-search-filtering-and-prompt-modal.md` | `assets/radar.js:3468` `sentSeg === "negative"` filters themes list |
| SNT-15 | Multi-Quote Pager Next | `10-gherkin-case-theme-accordion-and-multi-quote-pager.md` | `assets/radar.js:3503` `theme-pager` increments quote page index |
| SNT-16 | Full Response Prompt Modal | `11-gherkin-case-theme-search-filtering-and-prompt-modal.md` | `assets/radar.js:3525` `sent-open-prompt` triggers prompt modal |
| SNT-17 | Negative Drivers Table | `12-gherkin-case-negative-sentiment-drivers-table-and-security.md` | `assets/sentiment-analytics.js:163` `buildNegativeDrivers`, ranked table |
| SNT-18 | Strict NULL Preservation | `02-gherkin-case-small-sample-gating-and-null-score-preservation.md` | `assets/sentiment-analytics.js:80` `scoreOf(v)` preserves `null`, never `0` |
| SNT-19 | Claim Boundary Transition | `02-gherkin-case-small-sample-gating-and-null-score-preservation.md` | Transition from 2 claims (pending) to 3 claims (active) |
| SNT-20 | Anomaly Spike Click Drilldown| `09-gherkin-case-dedicated-sentiment-tab-and-anomaly-spike.md` | Click `.sent-spike-badge` triggers `sent-inspect-spike` setting `sentSeg = "negative"` |
| SNT-21 | Clean Baseline Spike Absence| `09-gherkin-case-dedicated-sentiment-tab-and-anomaly-spike.md` | Absence of `.sent-spike-badge` when `negPct < 15 && negClaims < 2` |
| SNT-22 | Persona Builder Fallbacks | `07-gherkin-case-persona-builder-input-fallbacks-and-sanitization.md` | Empty role defaults to `"Custom Executive Persona"`, industry to `"General Industry"` |
| SNT-23 | Persona Input Sanitization | `07-gherkin-case-persona-builder-input-fallbacks-and-sanitization.md` | HTML escaping via `esc()` preserves quotes and Turkish diacritics safely |
| SNT-24 | Modal Event Bubbling Stop | `06-gherkin-case-custom-persona-builder-modal-lifecycle.md` | `assets/aei.js:2048` `data-stop="1"` prevents modal window clicks from dismissing |
| SNT-25 | Quote Pager Boundary Locks | `10-gherkin-case-theme-accordion-and-multi-quote-pager.md` | Previous button disabled at index 0, Next button disabled at index N-1 |
| SNT-26 | Theme Search Case-Folding | `11-gherkin-case-theme-search-filtering-and-prompt-modal.md` | `assets/radar.js:3471` case-insensitive keyword search across themes and attributes |
| SNT-27 | Driver Link Security | `12-gherkin-case-negative-sentiment-drivers-table-and-security.md` | `assets/radar.js:3528` publisher links enforce `target="_blank"` and `rel="noopener"` |
| SNT-28 | Zero Evaluated Claims Safety| `08-gherkin-case-factual-integrity-and-hallucination-radar.md` | `assets/aei.js:1911` `evalClaims > 0 ? ... : 100` prevents `NaN%` division |
