# Screen & State Directory Architecture

## 1. Directory Structure Schema

Before launching vision evaluation, screenshot assets must be organized into a deterministic file hierarchy rooted under `audit-artifacts/`:

```
audit-artifacts/
  [YYYY-MM-DD]/                              # Canonical audit date (e.g. 2026-10-10)
    AUDIT-REPORT.md                          # Consolidated audit report
    [screen-slug]/                           # Kebab-case name of the screen/flow
      default.png                            # Mandatory: Base loaded screen state
      hover.png                              # Hover micro-interaction state
      active.png                             # Active input/focused/pressed state
      empty-state.png                        # Zero-data or blank-state rendering
      error-state.png                        # Form error / alert / toast feedback
      loading.png                            # Skeleton / spinner / pending state
      modal-open.png                         # Dialog / bottom-sheet / drawer open
```

---

## 2. Standard State Catalog & Evaluation Intent

Every digital interface exists in multiple interactive states. Auditing only the pristine "default" state blinds the audit to broken error handling, jarring layout shifts, and missing focus rings.

| State Filename | Trigger & Context | What the Vision Evaluator Inspects |
|---|---|---|
| `default.png` | **Mandatory.** Initial screen render with populated content. | Visual hierarchy, typographic scale, spacing tokens, layout symmetry, initial contrast. |
| `hover.png` | Cursor placed over primary CTA, card, or navigation link. | Pointer cursor presence, hover color shifts, transition smoothness, tooltip visibility. |
| `active.png` | Input focused with cursor, or button actively held pressed. | Focus ring visibility and color contrast (WCAG 2.4.7/2.4.11), active depression depth. |
| `empty-state.png` | Screen viewed with 0 items (new workspace, empty cart, no search results). | Helpful illustration, clear explanation, call to action guiding user to create first item. |
| `error-state.png` | Invalid form submission or simulated network failure. | Clear error messaging, proximity to faulty field, non-color redundant indicator (icon + text). |
| `loading.png` | Capture during network latency or mock 500ms delay. | Skeleton loading quality, layout stability (zero Cumulative Layout Shift), progress clarity. |
| `modal-open.png` | Dialog, drawer, or dropdown overlay open. | Backdrop scrim contrast, modal centering, mobile sheet height, visual focus containment. |

---

## 3. Canonical Viewport Specifications

When capturing web screens, test against authoritative modern viewports:

| Device Category | Viewport Dimensions | Target Description |
|---|---|---|
| **Mobile Standard (iOS)** | **390 × 844 pt** | iPhone 13, iPhone 14 base standard (1170×2532 px @ 3x) |
| **Mobile Modern (Dynamic Island)** | **393 × 852 pt** | iPhone 14 Pro, 15, 16 baseline |
| **Mobile Standard (Android)** | **360 × 800 dp** | Standard modern Android baseline (or 412×915 dp for Pixel) |
| **Tablet** | **768 × 1024 pt** | iPad portrait; tests navigation collapse and multi-column grids |
| **Desktop Baseline** | **1440 × 900 px** | Standard design system desktop target |
| **Desktop Compact** | **1280 × 800 px** | Laptops; tests 12-column grid scaling and table squishing |
| **Desktop Ultra-Wide** | **1920 × 1080 px** | High-res monitors; tests maximum container width constraints |

---

## 4. Pre-Evaluation Gate Check

Before the orchestrator invokes evaluation agents, it must execute:

```bash
bash skills/audit-ui-ux/scripts/validate-capture-gate.sh audit-artifacts/<YYYY-MM-DD>/
```

The script verifies:
1. Every screen folder contains at least `default.png`.
2. All `.png` files have valid non-empty byte counts and correct PNG header signatures (`0x89504E470D0A1A0A`).
3. State completeness is logged and confirmed.
