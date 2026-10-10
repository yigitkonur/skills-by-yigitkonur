# Filesystem Contract

The directory structure, MAX-N caps, file naming, and context-sharing
rules. Read this in **Phase 3** before architecture lockdown, and in
every wave brief to verify the agent's owned scope.

## The Dual-Layer Corpus Model

Traditional deep research suffered from the "500-file micro-fragmentation trap":
splitting each entity into 10-15 granular files created token thrashing, fragmented
context, and made automated aggregation impossible.

This skill implements a **Dual-Layer Architecture**:

1. **Human Layer (Consolidated Dossiers)**:
   - `<entity-slug>/dossier.md`: Single comprehensive document covering all charter axes.
   - `<entity-slug>/sources.md`: Verified claims ledger with verbatim quotations and locators.
   - `_cross/<axis-slug>/synthesis.md`: Cross-entity comparison starting with an **Executive Digest**.
2. **Machine Layer (Structured Metadata & Ledger)**:
   - **YAML Frontmatter** on each `dossier.md`: Machine-extractable scores, pricing tiers, and tags.
   - `_meta/manifest.json`: Unified entity registry, status tracking, and metadata index.
   - `_meta/claims.jsonl`: Line-by-line machine ledger of every verified claim and quotation.

## Concrete tree (domain-independent)

```
<corpus-root>/
├── README.md                                       (entry point & navigation map)
├── _meta/                                           (MAX 8 files)
│   ├── manifest.json                               (Machine catalog & entity registry)
│   ├── claims.jsonl                                (Machine-readable claims ledger)
│   ├── 00-master-summary.md                        (Phase 7 master rollup)
│   ├── 01-charter.md                               (Phase 0; Wave 1 resolves)
│   ├── 02-entities.md                              (Wave 1A output)
│   ├── 03-axes.md                                  (Wave 1B output)
│   ├── 04-product-template.md                      (Phase 2 dossier schema)
│   ├── 05-axis-templates.md                        (Phase 2 comparison schema)
│   ├── 06-file-budget.md                           (Phase 3)
│   └── 07-dispatch-log.md                          (running log across waves)
├── <entity-slug>/                                   (one per core entity; MAX 3 files)
│   ├── dossier.md                                  (Consolidated evidence dossier + frontmatter)
│   └── sources.md                                  (Claims ledger & citations)
├── <entity-slug>.md                                 (optional profile page at root for core entities)
└── _cross/                                          (one folder per axis; MAX 3 files each)
    └── <axis-slug>/
        ├── synthesis.md                            (Executive Digest + comparative matrix + rankings)
        └── scenarios.md                            (optional scenario / edge-case deep-dives)
```

## MAX-N caps with rationale

| Folder | MAX-N | Rationale |
|---|---|---|
| `<entity-slug>/` | 3 files | Consolidated `dossier.md` + `sources.md` + optional deep dive. Prevents file fragmentation. |
| `_cross/<axis-slug>/` | 3 files | Consolidated `synthesis.md` (with Executive Digest) + optional scenarios. |
| `_meta/` | 8 files | The 8 standard metadata artifacts. Beyond means scope creep. |
| Discovery list size | 50 entities | Tier the long tail to `discovered-only` in `manifest.json`. |
| Subagents per wave | 8 | Coordination overhead exceeds parallelism savings beyond 8. |
| Waves per session | 4 | Default 3; optional 4. Beyond 4 means upstream charter is wrong. |
| Search rounds per subagent | 4 | Per run-research discipline. |
| Retries per failed agent | 2 | If second attempt fails, log gap and escalate. |

**Why consolidated dossiers.** A 500-file corpus destroys LLM context windows during Phase 7 synthesis. By consolidating an entity's evidence into `dossier.md` with structured YAML frontmatter, the orchestrator and downstream tools can read or query the entire corpus efficiently without token thrashing.

## Machine Layer: YAML Frontmatter Schema

Every `<entity-slug>/dossier.md` must begin with valid YAML frontmatter:

```yaml
---
entity: "Acme Platform"
slug: "acme-platform"
tier: "core"
capture_date: "2026-10-10"
pricing:
  model: "usage-based"
  starting_price_usd_monthly: 49
  free_tier: true
compliance:
  - "SOC2-Type-II"
  - "HIPAA"
  - "ISO-27001"
scores:
  cost: 8
  performance: 9
  developer_experience: 7
---
```

## Machine Layer: `_meta/manifest.json`

The machine catalog provides an instant queryable view across the entire corpus:

```json
{
  "topic": "ai-native-cloud-browsers",
  "version": "1.0.0",
  "updated_at": "2026-10-10T12:00:00Z",
  "entities": {
    "browserbase": {
      "name": "Browserbase",
      "tier": "core",
      "dossier": "browserbase/dossier.md",
      "sources": "browserbase/sources.md",
      "status": "complete"
    }
  },
  "axes": ["architecture", "cost-pricing", "performance-anti-detect"],
  "cross_axes": ["architecture", "cost-pricing", "performance-anti-detect"]
}
```

## Filesystem as Context Channel Between Waves

Subagents do not see the orchestrator's conversation. They cannot
pass results to other subagents through context. **The filesystem
is the only context channel between waves.**

This is why each wave's brief includes:

- **Read scope** — the exact paths to read (Wave 2 reads
  `_meta/01-charter.md`, `_meta/03-axes.md`, `_meta/04-product-template.md`).
- **Write scope** — the exact paths the agent owns (Wave 2 owns
  `<entity-slug>/`).
- **Do-not-touch scope** — paths the agent must not modify (no
  other entity's folder, no `_meta/`, no `_cross/`).

Disjoint write scopes prevent merge conflicts. Explicit read scopes
prevent context bloat.

## Insufficient-Evidence Handling

No stub files. A section with sparse evidence becomes a one-paragraph
"insufficient evidence" entry inside `dossier.md`, with the specific data gap named.

Example:

```markdown
## Compliance and audit posture

**Insufficient evidence.** Vendor docs do not name compliance
regimes (no SOC 2, ISO 27001, HIPAA, or sector-specific
certifications listed on `/security` page). No third-party audit
reports surfaced via Reddit or community search. The data gap: vendor's
public compliance posture is not documented; if the decider needs
compliance evidence, request a vendor-supplied attestation.
```

Skipping silently is a failure. Creating a stub file (e.g.,
`compliance.md` with a single line "TBD") is strictly forbidden.

## Absolute Rules

- **No placeholder text.** Zero `TODO`, `TBD`, `fill later`,
  `<placeholder>`, `???` strings in any file. The Phase 7 verification gate fails on these.
- **No empty files.** Every file has content.
- **No hidden files.** No `.DS_Store`, `Thumbs.db`, `.tmp`, `.bak`
  in any corpus folder.
- **MAX 3 files per entity folder.** (`dossier.md`, `sources.md`, optional deep dive).
- **MAX 3 files per cross folder.** (`synthesis.md`, optional `scenarios.md`).
- **MAX 8 markdown files in `_meta/`.**

## Token-Efficient Context Sharing

Wave 2 example (per-entity researcher reads):
- `_meta/01-charter.md` — context (decider use case, freshness).
- `_meta/03-axes.md` — the axis catalog.
- `_meta/04-product-template.md` — the template.
- Writes only to `<entity-slug>/dossier.md` and `<entity-slug>/sources.md`.

Wave 3 example (per-axis cross-synthesis researcher reads):
- `_meta/01-charter.md` — context.
- `_meta/05-axis-templates.md` — comparison template.
- `<entity-slug>/dossier.md` for every `core` entity — reads the consolidated dossier.
- `<entity-slug>/sources.md` — for citation resolution.
- Writes only to `_cross/<axis-slug>/synthesis.md`.

The contract: **subagents read only their assigned scope. The
orchestrator merges via file reads. Cross-talk happens only through
the filesystem.**

## Verification Commands

Run the automated verification script:

```bash
# Intermediate wave verification:
bash scripts/verify-corpus.sh <corpus-root-path>

# Phase 7 final completion gate:
bash scripts/verify-corpus.sh --final <corpus-root-path>
```
