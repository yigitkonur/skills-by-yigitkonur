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
| `default.png` | **Mandatory.** Initial screen render with populated content. | Visual hierarchy, typographic scale, spacing tokens, layout symmetry, WCAG 2.2 AA contrast floors (4.5:1 / 3:1), APCA Lightness Contrast ($L_c \ge 90$ body, $L_c \ge 75$ standard), and dark-mode retinal halation / irradiation (avoid `#FFFFFF` on `#000000`). |
| `hover.png` | Cursor placed over primary CTA, card, or navigation link. | Pointer cursor presence, hover color shifts, transition smoothness, tooltip visibility. |
| `active.png` | Input focused with keyboard cursor, or button actively held pressed. | Focus Appearance Indicators (WCAG 2.2 SC 2.4.11 AAA, SC 2.4.12 AA, SC 2.4.13 AAA): 2px stroke / perimeter area, 3:1 dual contrast against component & background, `outline-offset` $\ge 2\text{px}$, non-obscuration; button depression depth. |
| `empty-state.png` | Screen viewed with 0 items (new workspace, empty cart, no search results). | Helpful illustration, clear explanation, call to action guiding user to create first item. |
| `error-state.png` | Invalid form submission or simulated network failure. | Clear error messaging, proximity to faulty field, non-color redundant indicator (icon + text). |
| `loading.png` | Capture during network latency or mock 500ms delay. | Skeleton loading quality, layout stability (zero Cumulative Layout Shift), progress clarity. |
| `modal-open.png` | Dialog, drawer, or dropdown overlay open. | Backdrop scrim contrast, modal centering, mobile sheet height, visual focus containment, non-trapping escape hatch. |

### Visual Focus Appearance Checklist (`active.png`)
When auditing `active.png`, evaluators specifically grade against WCAG 2.2 Focus Appearance standards:
1. **Indicator Presence:** An unambiguous visual focus ring or border change must appear on keyboard focus. If `outline: none` removes the indicator without a custom replacement: **Catastrophe/Critical (WCAG 2.4.7 AA)**.
2. **Minimum Area (SC 2.4.11 AAA):** Focus indicator must enclose at least an unbroken 1px border around the entire component perimeter ($A \ge 1\text{px} \times \text{perimeter}$) or 2px line along the shortest side. Preferred standard: solid **2px** outline.
3. **Dual-Contrast Requirement:** Indicator must achieve at least **3.0:1** contrast against both the unfocused component surface AND the surrounding background canvas.
4. **Offset Clearance:** An `outline-offset` of $\ge 2\text{px}$ is recommended so the focus ring does not visually fuse with existing element borders.
5. **Non-Obscuration (SC 2.4.12 AA / SC 2.4.13 AAA):** The focused component must not be clipped or covered by sticky headers, sticky footers, or floating drawers.

---

## 3. Canonical Viewport Specifications & Multi-Density Conventions

### Canonical Modern Viewports
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

### Multi-Density Display Conventions (`@1x`, `@2x`, `@3x`)
- **CSS Logical Pixels vs. Physical Device Pixels:** A mobile viewport of $390\times 844$ CSS points captured at `@3x` resolution produces a raw image of $1170\times 2532$ physical pixels.
- **Coordinate Invariance:** All findings in `AUDIT-REPORT.md` must be recorded using **Normalized Percentage Coordinates** (`top%`, `left%`, `width%`, `height%`). This guarantees that spatial bounding boxes remain 100% deterministic and invariant regardless of whether assets are captured at `@1x`, `@2x`, or `@3x` pixel densities.
- **File Naming Suffixes:** Canonical filenames without density suffixes (e.g. `default.png`, `active.png`) are standard. Where capture pipelines output density-tagged variants (e.g. `default@2x.png`, `default@3x.png`), the validation gate treats them as valid state assets for their base state.

---

## 4. Pre-Evaluation Gate Check

Before the orchestrator invokes evaluation agents, it must execute the capture validation gate:

```bash
bash skills/audit-ui-ux/scripts/validate-capture-gate.sh audit-artifacts/<YYYY-MM-DD>/
```

The validation gate script verifies:
1. **Directory Integrity:** Handles spaces and special characters in paths safely.
2. **Mandatory Baseline:** Every screen folder contains at least `default.png` (or supported density variant `default@2x.png`).
3. **File Integrity:** All `.png` files have non-zero byte size and match genuine PNG magic byte signatures (`0x89504E470D0A1A0A`), failing corrupt or truncated partial transfers.
4. **State Inventory & CLI Feedback:** Logs state completeness and outputs actionable remediation instructions if mandatory states are missing.
5. **Exit Status:** Returns exit code `0` on success, blocking phase advancement on failure.
