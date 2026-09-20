# Comparison Matrix Schema Specification

The Comparison Matrix Schema provides a strongly typed, deterministic data model for comparing arbitrary entities (software tools, models, frameworks, architectures, products) with dynamic weighting, multi-rule sorting, and filtering.

## 1. Top-Level Entity: `ComparisonMatrixSchema`

```typescript
export interface ComparisonMatrixSchema {
  id: string;               // Unique slug (e.g. "ai-code-assistants")
  title: string;            // Page header title
  description: string;      // 1-2 sentence subtitle
  subjectLabel: string;     // Plural noun describing items (e.g. "Assistants", "Frameworks")
  groups: CriteriaGroup[];
  criteria: CriterionDefinition[];
  items: ComparisonItem[];
  scoring?: {
    algorithm?: 'linear-normalized' | 'weighted-sum';
    defaultWeights?: Record<string, number>;
  };
  metadata?: {
    lastUpdatedAt?: string;
    version?: string;
    curator?: string;
    sourceDocumentCount?: number;
    methodologyUrl?: string;
  };
}
```

---

## 2. Groups: `CriteriaGroup`

Groups establish visual and semantic hierarchy in the comparison matrix:

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Unique slug (e.g. `coreCapabilities`, `performance`) |
| `label` | `string` | Display label rendered in accordion group headers |
| `description` | `string?` | Optional explanatory tooltip |
| `defaultExpanded` | `boolean` | Whether group starts expanded (default: `true`) |
| `parentGroupId` | `string?` | Optional parent ID for multi-level nesting |

---

## 3. Criteria: `CriterionDefinition`

Every criterion defines an atomic evaluation dimension with specific data typing, weighting, and directionality:

| Field | Type | Default | Description |
|---|---|---|---|
| `key` | `string` | Required | Unique camelCase key referenced in `item.values[key]` |
| `label` | `string` | Required | Human-readable title displayed in column/row labels |
| `groupId` | `string` | Required | Must match an existing `groups[].id` |
| `type` | `CriterionType` | Required | Supported: `boolean`, `number`, `price`, `select`, `select-text`, `multiselect`, `text`, `url`, `date`, `computed` |
| `unit` | `string?` | Optional | Suffix label (e.g. `ms`, `MB`, `tokens`, `/mo`) |
| `description` | `string?` | Optional | Methodology note rendered in cell popovers |
| `options` | `CriterionOption[]?`| Optional | Array of `{ value: string; label: string; rank?: number }` for select fields |
| `scoreable` | `boolean` | `true` | When `false`, cell is displayed but excluded from total score |
| `higherIsBetter` | `boolean?` | `undefined` | For numeric/price fields: `true` if higher is better (throughput), `false` if lower is better (cost, latency) |
| `booleanBest` | `boolean?` | `true` | For boolean fields: `true` if `true` is rewarded, `false` if `false` is rewarded |
| `defaultWeight` | `number` | `5` | Integer or half-integer from `0` to `10` |
| `isHardRequirement` | `boolean?` | `false` | If `true`, failing this criterion triggers a disqualification badge |

---

## 4. Items: `ComparisonItem`

The candidate entity being evaluated:

| Field | Type | Description |
|---|---|---|
| `id` | `string` | URL-safe slug (e.g. `cursor`, `copilot`, `windsurf`) |
| `name` | `string` | Display name |
| `website` | `string?` | Canonical URL |
| `accent` | `string` | Hex color code used for fallback avatars and tags |
| `icon` | `string?` | Path to square/squircle icon (e.g. `/matrix/icons/cursor.webp`) |
| `summary` | `string?` | 1-sentence synopsis |
| `tags` | `string[]` | Badges (e.g. `["IDE", "Open Source", "Proprietary"]`) |
| `values` | `Record<string, unknown>` | Maps criterion `key` to its typed value or `CellDetail` object |

### CellDetail Object Format (Optional Rich Cell)
Instead of a primitive value, `values[key]` may contain a structured audit object with confidence tracking, evidence citations, uncertainty flags, and verification audit stamps:
```json
{
  "value": 142,
  "secondary": "p95 latency under 500 QPS load",
  "confidence": {
    "score": 0.92,
    "level": "high",
    "tier": "verified"
  },
  "prediction": {
    "isEstimate": true,
    "range": [120, 160],
    "rationale": "Empirical benchmark on AWS c6i.4xlarge"
  },
  "evidence": {
    "quote": "Average p99 latency observed at 142ms under standard benchmark suite",
    "sourceUrl": "https://example.com/benchmark-run",
    "verifiedAt": "2026-09-18T12:00:00Z",
    "verifierAgent": "verifier-agent-alpha"
  },
  "uncertainty": {
    "isUncertain": false
  },
  "verificationAudit": {
    "status": "confirmed",
    "notes": "Verified against official benchmark repository commit history."
  }
}
```

The `confidence` field also accepts legacy string values (`"verified"`, `"vendor-claimed"`, `"community"`, `"unverified"`) for backwards compatibility, but new data should always use the structured `{ score, level, tier }` object.
