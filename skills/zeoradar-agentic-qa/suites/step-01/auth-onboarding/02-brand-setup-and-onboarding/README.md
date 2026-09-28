# Test Suite 02: Brand Setup & Guided Onboarding Wizard

## 1. Module Overview & Architectural Grounding

The **Brand Setup & Guided Onboarding Wizard** subsystem (`assets/onboarding.js`, `assets/onboarding.css`, `assets/auth.js` brand seed phase) coordinates the initial setup experience for zero-workspace or new brand accounts. It connects domain verification, ccTLD geographic/language inference, AI engine weight allocation, asynchronous topic and persona discovery via Trigger.dev background tasks, inline prompt review, and project finalization with first measurement scheduling.

### Onboarding Pipeline Lifecycle
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ONBOARDING PIPELINE LIFECYCLE                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   Auth Seed Phase (/#/auth -> step: 'brand_setup')                              │
│   ├── User enters Brand Name ("[BRAND]") & Domain ("[DOMAIN]")         │
│   └── Writes state.onboardingSeed ──► zeoPersistOnboardingSeed()                │
│                                                                                 │
│   Guided Wizard Frame (/#/onboarding)                                           │
│   ├── Step 1: Welcome Screen (Hero Modal, Workspace Mission, Value Props)       │
│   ├── Step 2: Daily Analysis Demo (Platform Badges, SVG Simulation Chart)       │
│   ├── Step 3: Geographic Targeting & Engine Profiles                            │
│   │   ├── Domain validation, protocol/port stripping & Favicon probe           │
│   │   ├── Auto-deduction of Country & Language via ccTLD & brand patterns       │
│   │   ├── Industry Presets (E-Commerce 🛍️, SaaS 💻, Finance 🏦)                 │
│   │   └── Advanced Engine Sliders (ChatGPT, Gemini, Perplexity, Claude)         │
│   ├── Step 4: Topic Selection & Discovery                                       │
│   │   ├── Dispatches onboarding-suggest (topics, personas, keywords)            │
│   │   ├── Topic pill selection matrix (max 10 limit enforcement)                │
│   │   ├── Duplicate custom topic prevention & inline creation                   │
│   │   └── Custom topic injection & regeneration trigger                         │
│   └── Step 5: Suggestion Review & Finalize                                      │
│       ├── Prompts, Personas, Keywords accordion review                          │
│       ├── Inline row editing & selection toggling                               │
│       ├── Staged suggest-persona-prompts binding                                │
│       ├── Poller budget tracking (5m) & timeout recovery panel                  │
│       ├── Execution Confirmation Modal (.ob-exec-modal)                         │
│       └── Dispatches onboarding-finalize ──► switchTenant ──► /#/               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure & Test Cases

This directory contains 12 focused, modular Gherkin QA test cases:

| File Name | Case ID | Title / Purpose | Original Coverage |
|:---|:---|:---|:---|
| `01-gherkin-case-brand-seed-bridging.md` | TC-ONB-01 | Brand Setup Seed Phase, Storage Bridging & Redirection | TC-ONB-01 |
| `02-gherkin-case-wizard-navigation-and-skip.md` | TC-ONB-02 | 5-Step Guided Walkthrough Navigation, Dot Stepper & Skip Action | TC-ONB-02, TC-ONB-03 |
| `03-gherkin-case-domain-sanitization-and-cleaning.md` | TC-ONB-03 | Dirty Domain Sanitization (Protocols, Auth, Ports, Paths) | TC-ONB-11 |
| `04-gherkin-case-cctld-geographic-auto-deduction.md` | TC-ONB-04 | ccTLD Geographic Targeting & Locale Auto-Deduction Engine | TC-ONB-04, TC-ONB-12 |
| `05-gherkin-case-industry-engine-presets.md` | TC-ONB-05 | Industry Engine Presets Weight Allocation & Synchronized Cards | TC-ONB-05 |
| `06-gherkin-case-custom-engine-sliders-and-bounds.md` | TC-ONB-06 | Advanced Engine Weight Sliders, Custom Preset & Zero-Bound Normalization | TC-ONB-06, TC-ONB-14 |
| `07-gherkin-case-topic-matrix-selection-and-ceiling.md` | TC-ONB-07 | Topic Selection Matrix, Progress Fill & 10-Topic Ceiling | TC-ONB-07 |
| `08-gherkin-case-custom-topic-injection-and-duplicates.md` | TC-ONB-08 | Custom Topic Inline Creation, Duplicate Prevention & Regeneration | TC-ONB-08, TC-ONB-13 |
| `09-gherkin-case-suggestion-polling-and-idempotency.md` | TC-ONB-09 | Trigger.dev Asynchronous Polling, Idempotency & Poller Resurrection | TC-ONB-15, TC-ONB-17 |
| `10-gherkin-case-suggestion-review-and-inline-editing.md` | TC-ONB-10 | Suggestion Review Accordion, Inline Prompt Editing & Inclusion Gating | TC-ONB-09 |
| `11-gherkin-case-project-finalization-and-first-run.md` | TC-ONB-11 | Project Finalization Confirmation Modal, RPC Dispatch & Dashboard Hand-off | TC-ONB-10 |
| `12-gherkin-case-onboarding-gating-and-guardrails.md` | TC-ONB-12 | Wizard Form Gating, Step Jump Blocking & Zero-Selection Guardrails | TC-ONB-16, TC-ONB-18 |

---

## 3. Parameter Vocabulary & Test Placeholders

Test scenarios in this suite use standardized, bracketed placeholders. The table below defines each placeholder, how it is set, and representative variants:

| Placeholder | Meaning & System Mapping | Where & How to Set | Representative Test Variants |
|:---|:---|:---|:---|
| `[APP_URL]` | Base origin URL of the running web application | Base URL parameter in `openOrReuseTab` | `https://zeoradar.endpoints.lol` |
| `[DOMAIN]` | Domain or target website under test | `#ob-domain-input` or `obCleanDomain(raw)` | `daikin.com.tr`, `bbc.co.uk`, `zalando.de`, `airfrance.fr` |
| `[COUNTRY]` | ISO 3166-1 alpha-2 country code targeting locale evaluation | `#ob-region-select` or `state.onboarding.selectedRegion` | `TR`, `UK`, `DE`, `FR`, `US` |
| `[LANGUAGE]` | IETF language tag for evaluation and prompts | `#ob-language-select` or `state.onboarding.selectedLanguage`| `tr` (Turkish), `en` (English), `de` (German), `fr` (French) |
| `[BRAND_NAME]` | Brand display name under observation | `#ob-brand-input` or `#auth-brand-name` | `Daikin`, `[BRAND]`, `Revolut`, `Lufthansa` |
| `[INDUSTRY_PRESET]`| Standard engine preset card identifier | `.ob-preset-card[data-preset]` | `ecommerce`, `saas`, `finance`, `custom` |
| `[TOPIC_NAME]` | Topic title pill identifier or custom string | `#custom-topic-input` or `.topic-pill` | `"[CUSTOM_TOPIC]"`, `"Online Flight Booking"`, `"Corporate Cards"` |
| `[ENGINE_WEIGHTS]` | Percentage distribution across the 4 AI engines | `#ob-slider-{engine}` or `state.onboarding.engineWeights` | `{ chatgpt: 35, gemini: 35, perplexity: 20, claude: 10 }` |

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
     const task = await useOrCreateTaskSpace('e2e-onboarding-wizard-suite');
     const tab = await openOrReuseTab('[APP_URL]/#/onboarding', { wait: true });
     // ... execute semantic actions & assertions
     await completeTaskSpace('e2e-onboarding-wizard-suite', { keep: false });
   EOF"
   ```
2. **MacBook Screenshot Capture**: Screenshots are captured directly on the MacBook display to `/tmp/ego-shots/onboarding/` or `~/Desktop/shots/`.
3. **Evidence Download via SCP**: Upon scenario completion, the test runner downloads screenshots and network captures to the designated result directory:
   ```bash
   scp macbook:/tmp/ego-shots/onboarding/case-01-*.png ./01-gherkin-result-case-brand-seed-bridging/screenshots/
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
| TC-ONB-01 | Seed Bridge | `01-gherkin-case-brand-seed-bridging.md` | `assets/auth.js:1331` `handleBrandSetupSubmit`, `state.onboardingSeed` persistence |
| TC-ONB-02 | Step Navigation | `02-gherkin-case-wizard-navigation-and-skip.md` | `assets/onboarding.js:3000` `setOnboardingStep`, dots `.zr-step-dots` |
| TC-ONB-03 | Skip Walkthrough | `02-gherkin-case-wizard-navigation-and-skip.md` | `assets/onboarding.js:3015` `skipOnboardingWalkthrough`, direct exit to `/#/` |
| TC-ONB-04 | Domain Validation | `04-gherkin-case-cctld-geographic-auto-deduction.md` | `assets/onboarding.js:98` `obRegionFromDomain`, `obIsTurkishDomainOrBrand` |
| TC-ONB-05 | Engine Presets | `05-gherkin-case-industry-engine-presets.md` | `assets/onboarding.js:3049` `obSelectEnginePreset`, preset definitions |
| TC-ONB-06 | Custom Weights | `06-gherkin-case-custom-engine-sliders-and-bounds.md` | `assets/onboarding.js:3060` `obSetEngineWeight`, toggle `#ob-advanced-toggle-btn` |
| TC-ONB-07 | Topic Limit Gating | `07-gherkin-case-topic-matrix-selection-and-ceiling.md` | `assets/onboarding.js:352` `maxTopics: 10`, `assets/onboarding.js:1301` toast gating |
| TC-ONB-08 | Custom Topic | `08-gherkin-case-custom-topic-injection-and-duplicates.md` | `assets/onboarding.js:3180` `saveCustomTopic`, `obTopicsNeedRegen` note |
| TC-ONB-09 | Suggestion Review | `10-gherkin-case-suggestion-review-and-inline-editing.md` | `assets/onboarding.js:3250` `obStartRowEdit`, `obSaveRowEdit`, prompt toggles |
| TC-ONB-10 | Finalize Project | `11-gherkin-case-project-finalization-and-first-run.md` | `assets/onboarding.js:3332` `openExecutionModal`, `submitPromptsExecution` |
| TC-ONB-11 | Protocol/Port Strip | `03-gherkin-case-domain-sanitization-and-cleaning.md` | `assets/onboarding.js:68` `obCleanDomain(raw)`, regex stripping auth & ports |
| TC-ONB-12 | Vanity/Fallback TLD | `04-gherkin-case-cctld-geographic-auto-deduction.md` | `assets/onboarding.js:33` `OB_GENERIC_TWO_LETTER_TLDS` (.io, .ai -> US/en) |
| TC-ONB-13 | Duplicate Topic | `08-gherkin-case-custom-topic-injection-and-duplicates.md` | `assets/onboarding.js:3195` `obTopicKey` comparison against existing list |
| TC-ONB-14 | Zero-Bound Weights | `06-gherkin-case-custom-engine-sliders-and-bounds.md` | Sliders dragged to 0, custom preset assigned, no NaN division errors |
| TC-ONB-15 | Polling Timeout | `09-gherkin-case-suggestion-polling-and-idempotency.md` | `assets/onboarding.js:841` `OB_POLL_BUDGET_MS = 300000`, recovery card |
| TC-ONB-16 | Empty Input Gating | `12-gherkin-case-onboarding-gating-and-guardrails.md` | `setOnboardingStep(4)` checks brand & domain, halts with toast error |
| TC-ONB-17 | Poller Resurrection | `09-gherkin-case-suggestion-polling-and-idempotency.md` | `assets/onboarding.js:914` `obResumePollIfStalled()`, batch survival on route swap |
| TC-ONB-18 | Zero Prompts Gating | `12-gherkin-case-onboarding-gating-and-guardrails.md` | Deselect all prompts disables finalize CTA and blocks modal trigger |
