# Data Types and Scoring Rubric

The comparison matrix translates heterogeneous candidate attributes into comparable numeric scores (0–100 per cell, scaled by user-adjustable weights 0–10).

---

## 1. Supported Criterion Types & Evaluation Rules

### `boolean`
- Values: `true | false | null`
- Scoring:
  - If `booleanBest === true` (default): `true` = 100 points, `false` = 0 points.
  - If `booleanBest === false` (e.g. `requiresSignup`, `telemetryTracking`): `false` = 100 points, `true` = 0 points.
  - `null` / `undefined`: neutral baseline (50 points or 0 points depending on strictness).

### `number`
- Values: `number | null`
- Parameters: `unit` (e.g. `MB`, `ms`, `k-tokens`), `higherIsBetter` (`true` or `false`).
- Scoring: Min-Max Normalization across active candidate items:
  - When `higherIsBetter === true`:
    $$\text{Score} = \frac{\text{value} - \text{min}}{\text{max} - \text{min}} \times 100$$
  - When `higherIsBetter === false`:
    $$\text{Score} = \frac{\text{max} - \text{value}}{\text{max} - \text{min}} \times 100$$

### `price`
- Values: `number | null` (e.g. `0`, `20`, `99`)
- Handled as numeric with `higherIsBetter: false` and special formatting:
  - `value === 0` displays as `Free` in highlighted green (`#16804a` or `#63cda0`).
  - `value > 0` formats as `$XX/mo` or `$XX`.

### `select`
- Values: `string` matching one of `options[].value`.
- Scoring: If `options[].rank` is defined (scale 0–10 or 1–5), score is mapped proportionally to 0–100:
  $$\text{Score} = \frac{\text{rank}}{\text{maxRank}} \times 100$$

### `multiselect`
- Values: `string[]` matching subset of `options[].value`.
- Scoring: Ratio of supported options relative to the full option pool:
  $$\text{Score} = \frac{|\text{selected}|}{|\text{availableOptions}|} \times 100$$

### `text` & `url` & `date`
- Values: descriptive strings.
- Non-scoreable by default (`scoreable: false`). Renders with interactive popup for detailed reading.

### `select-text`
- Values: `string` — a free-form text value displayed as-is in the cell.
- Behaves like `select` visually but allows arbitrary text values that don't need to match a predefined option list.
- Scoring: Non-scoreable by default (`scoreable: false`). If scoring is needed, define `options` with `rank` values and treat like `select`.

### `computed`
- Values: derived at render time from other criteria (e.g. composite scores, ratios).
- Non-scoreable (`scoreable: false`). The compute logic lives in the frontend model layer, not in the JSON dataset.

---

## 2. Dynamic Weighting Formula

Every criterion has an active weight $W_k \in [0, 10]$ (default $5$):

$$\text{Total Score}_i = \frac{\sum_{k \in \text{criteria}} W_k \times S_{i,k}}{\sum_{k \in \text{criteria}} W_k}$$

Where:
- $S_{i,k} \in [0, 100]$ is candidate $i$'s normalized score for criterion $k$.
- $W_k$ is the weight slider value set by the user or preset.
- Adjusting any weight immediately updates the weighted sum and triggers a smooth re-ranking transition.
