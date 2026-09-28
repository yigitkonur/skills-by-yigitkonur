# Test Suite 03: Theme Engine, Language Localization, Profile & Product Tour

## 1. Module Overview & Architectural Grounding

The **Shell Preferences, Localization, Identity & Guidance** subsystem (`assets/ui-shell.js`, `assets/radar.js` lines 1858–1940, 3848–3873, 5350–5396, 6580–6740, `assets/radar.css`) governs theme mode management (`light`, `dark`, `system`), bilingual internationalization (`en`, `tr`), feature announcements ("What's New"), interactive spotlight guidance ("Product Tour"), user profile settings, and system metadata popovers.

### Subsystem Topology & Seams
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        SHELL PREFERENCES & CONTROLS TOPOLOGY                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ SIDEBAR FOOTER (.side-foot)                                                            │
│ ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ [☼/☾] Theme Toggle (.foot-btn[data-action="theme-toggle"])                          │ │
│ │ [🎁]  What's New (.foot-btn[data-action="whats-new"])                              │ │
│ │ [EN]  Language Toggle (.foot-btn.lang-btn[data-action="lang-toggle"])               │ │
│ │ [?]   About Popover (.foot-btn[data-action="info-pop"])                             │ │
│ │ [◧]   Collapse Sidebar (.foot-btn[data-action="side-collapse"])                     │ │
│ └────────────────────────────────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ PROFILE TRIGGER (.profile-trigger[data-action="profile-menu"])                     │ │
│ │  ├─ Avatar Initials ("AS")                                                         │ │
│ │  ├─ User Name ("Alex Smith")                                                       │ │
│ │  └─ Email ("[USER_EMAIL]")                                                 │ │
│ └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                        │
│ FLOATING FLYOUT CONTAINERS                                                             │
│ ├─ #profileMenuHolder  ──► .profile-popover (Workspace, Account, Settings, Theme Sub) │
│ ├─ #modalHolder        ──► .modal.whatsnew-modal (Feature Announcements)              │
│ ├─ #productTourHolder  ──► svg.tour-mask-svg + .tour-tooltip-card (Interactive Walk)  │
│ └─ #infoPop            ──► .info-pop (Snapshot & Data Source Metadata)                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Core State Invariants
- `state.theme`: `"light"`, `"dark"`, or `"system"`. CSS token class `.dark` applied to `document.body` when dark mode is active.
- `state.lang`: `"en"` or `"tr"`. Document attribute `document.documentElement.lang` bound reactively.
- `state.tour`: `{ isActive: boolean, currentStep: number, totalSteps: 4 }`.
- `state.profileMenuOpen`: Boolean flag controlling `#profileMenuHolder`.

---

## 2. Directory Structure & Test Cases

This directory contains 12 focused, modular Gherkin QA test cases:

| File Name | Case ID | Title / Purpose | Original Coverage |
|:---|:---|:---|:---|
| `01-gherkin-case-theme-toggle-light-dark-modes.md` | TC-PREF-01 | Dual Surface Theme Inversion (Light/Dark) via Sidebar Foot and Topbar | E2E-PREF-01 |
| `02-gherkin-case-theme-selection-profile-submenu.md` | TC-PREF-02 | Explicit Tri-Mode Theme Selection (Light/Dark/System) via Profile Popover | E2E-PREF-02 |
| `03-gherkin-case-bilingual-language-switch-and-toasts.md` | TC-PREF-03 | Bilingual Language Toggling (EN <-> TR), HTML Lang Attribute & Toast Lifecycle | E2E-PREF-03 |
| `04-gherkin-case-whats-new-feature-announcements.md` | TC-PREF-04 | What's New Feature Announcement Modal Content Schema and Feature List | E2E-PREF-04 |
| `05-gherkin-case-product-tour-complete-walkthrough.md` | TC-PREF-05 | Interactive 4-Step Product Tour Walkthrough, Spotlight Cutout Rings & Stepper | E2E-PREF-05 |
| `06-gherkin-case-profile-flyout-navigation-links.md` | TC-PREF-06 | User Profile Popover Identity Display, Account & Settings Deep Navigation | E2E-PREF-06 |
| `07-gherkin-case-about-radar-metadata-inspection.md` | TC-PREF-07 | About Zeo Radar Metadata Popover, Engine Coverage & Snapshot Verification | E2E-PREF-07 |
| `08-gherkin-case-theme-storage-resilience-and-system-media.md` | TC-PREF-08 | Storage-Resilient Theme Fallback & Dynamic OS `prefers-color-scheme` Binding | E2E-PREF-08 |
| `09-gherkin-case-turkish-diacritics-and-toast-settlement.md` | TC-PREF-09 | Turkish Diacritic Invariance (İ/ı/ş/ğ/ü/ö/ç) and Toast Queue Sequence Settlement | E2E-PREF-09 |
| `10-gherkin-case-whats-new-triple-dismissal-parity.md` | TC-PREF-10 | What's New Modal Triple-Dismissal Parity (Close Button, Backdrop, Escape) | E2E-PREF-10 |
| `11-gherkin-case-product-tour-abort-and-route-escape.md` | TC-PREF-11 | Product Tour Mid-Flight Abort (Mask, Close, Skip) and Route Navigation Escape | E2E-PREF-11 |
| `12-gherkin-case-profile-flyout-dismissal-and-workspace-nav.md` | TC-PREF-12 | Profile Flyout Outside-Click Dismissal & Home Workspace Catalog Navigation | E2E-PREF-12 |

---

## 3. Parameter Vocabulary & Test Placeholders

Test scenarios in this suite use standardized, bracketed placeholders:

| Placeholder | Meaning & System Mapping | Where & How to Set | Representative Test Variants |
|:---|:---|:---|:---|
| `[APP_URL]` | Base origin URL of the running web application | Base URL parameter in `openOrReuseTab` | `https://zeoradar.endpoints.lol` |
| `[DOMAIN]` | Monitored target brand domain under test | Target brand website | `daikin.com.tr` |
| `[COUNTRY]` | ISO 3166-1 alpha-2 country code targeting locale evaluation | Selected country dropdown or detected domain ccTLD | `US`, `TR`, `UK` |
| `[LANGUAGE]` | IETF language code for UI localization | App shell language toggle or `state.lang` | `en` (English), `tr` (Turkish) |
| `[THEME_MODE]` | Active visual appearance mode | Stored in `state.theme` and `zeo_theme` in localStorage | `light`, `dark`, `system` |
| `[TOUR_STEP]` | Current sequential step in product spotlight walk | Stored in `state.tour.currentStep` | `0` (Step 1), `1` (Step 2), `2` (Step 3), `3` (Step 4) |
| `[TOAST_TYPE]` | Semantic toast visual notification category | Call to `showToast({ type })` | `info`, `success`, `error`, `warn` |
| `[DISMISSAL_METHOD]`| Method used to close modal or tour dialog | User action | `button-close`, `backdrop-click`, `keyboard-escape` |

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
     const task = await useOrCreateTaskSpace('e2e-pref-suite');
     const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/overview', { wait: true });
     // ... execute semantic actions & assertions
     await completeTaskSpace('e2e-pref-suite', { keep: false });
   EOF"
   ```
2. **MacBook Screenshot Capture**: Screenshots are captured directly on the MacBook display to `/tmp/ego-shots/pref/` or `~/Desktop/shots/`.
3. **Evidence Download via SCP**: Upon scenario completion, the test runner downloads screenshots and network captures to the designated result directory:
   ```bash
   scp macbook:/tmp/ego-shots/pref/case-01-*.png ./01-gherkin-result-case-theme-toggle-light-dark-modes/screenshots/
   ```
4. **Result Directory Specification**:
   - Each Gherkin case corresponds to an execution result directory named `0X-gherkin-result-case-<slug>/`.
   - Result directories are **NEVER created as empty placeholders**. They are instantiated only by the test execution runner upon executing the suite.

---

## 5. Traceability & Code Coverage Matrix

| Original Scenario ID | Original Title | New Modular Gherkin Case | Real Code Reference & Invariant Hardening |
|:---|:---|:---|:---|
| E2E-PREF-01 | Theme Mode Switching (Light / Dark) | `01-gherkin-case-theme-toggle-light-dark-modes.md` | `assets/ui-shell.js:627-632` (`applyTheme`), `document.body.classList.toggle("dark")` |
| E2E-PREF-02 | Theme Selection via Profile Submenu | `02-gherkin-case-theme-selection-profile-submenu.md` | `assets/radar.js:5360-5385` (`.theme-opt[data-theme]`, checkmark reflection) |
| E2E-PREF-03 | Bilingual Language Switch (EN <-> TR) | `03-gherkin-case-bilingual-language-switch-and-toasts.md` | `assets/ui-shell.js:95-110` (`applyLang`), `t()`, `document.documentElement.lang` |
| E2E-PREF-04 | "What's New" Modal Open & Dismiss | `04-gherkin-case-whats-new-feature-announcements.md` | `assets/radar.js:3848-3873` (4 capabilities: link, calendar, bookmark, sparkle) |
| E2E-PREF-05 | Complete 4-Step Product Tour Journey | `05-gherkin-case-product-tour-complete-walkthrough.md` | `assets/radar.js:6580-6740` (`startProductTour()`, SVG spotlight cutout mask) |
| E2E-PREF-06 | Profile Popover & Route Links | `06-gherkin-case-profile-flyout-navigation-links.md` | `assets/radar.js:5350-5365` (User identity Alex Smith, Account & Settings links) |
| E2E-PREF-07 | About Info Popover Inspection | `07-gherkin-case-about-radar-metadata-inspection.md` | `assets/radar.js:5390-5415` (`#infoPop`, measurement date, assets count, engines) |
| E2E-PREF-08 | Storage-Resilient Theme & Live Media | `08-gherkin-case-theme-storage-resilience-and-system-media.md` | `assets/ui-shell.js:84-90` (try/catch storage), `window.matchMedia` change listener |
| E2E-PREF-09 | Turkish Diacritics & Toast Settlement | `09-gherkin-case-turkish-diacritics-and-toast-settlement.md` | `assets/ui-shell.js:148-150` (`t()`), `assets/ui-shell.js:698-703` (2800ms seq settle) |
| E2E-PREF-10 | What's New Modal Triple-Dismissal Parity | `10-gherkin-case-whats-new-triple-dismissal-parity.md` | `assets/ui-shell.js:620-625` (`closeModal()`, `#modalHolder.innerHTML = ""`) |
| E2E-PREF-11 | Product Tour Mid-Flight Abort | `11-gherkin-case-product-tour-abort-and-route-escape.md` | `assets/radar.js:6620-6635` (`endProductTour()`, mask click, close button, route sync) |
| E2E-PREF-12 | Profile Flyout Outside-Click & Catalog | `12-gherkin-case-profile-flyout-dismissal-and-workspace-nav.md` | `assets/radar.js:5205-5210` (Outside click dismissal), `assets/radar.js:5362` (goto-home) |
