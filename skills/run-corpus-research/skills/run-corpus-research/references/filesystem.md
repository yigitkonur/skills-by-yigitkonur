# Filesystem Contract

The directory structure, MAX-N caps, file naming, and context-sharing
rules. Read this in **Phase 3** before architecture lockdown, and in
every wave brief to verify the agent's owned scope.

## The 4-layer corpus structure

Every corpus has four layers:

1. **Root entry** — `README.md` linking into the corpus and a profile
   page (`<entity-slug>.md`) per `core` entity.
2. **`_meta/`** — orchestrator's working artifacts (charter, entities
   list, axes list, templates, file budget, dispatch log, master
   summary).
3. **`<entity-slug>/`** — per-entity evidence packs, one folder per
   `core` entity.
4. **`_cross/`** — per-axis cross-entity comparisons, one folder per
   axis.

## Concrete tree (domain-independent)

```
<corpus-root>/
├── README.md                                       (entry point)
├── _meta/                                           (MAX 8 files)
│   ├── 00-master-summary.md                        (Phase 7)
│   ├── 01-charter.md                               (Phase 0; Wave 1 resolves)
│   ├── 02-entities.md                              (Wave 1A output)
│   ├── 03-axes.md                                  (Wave 1B output)
│   ├── 04-product-template.md                      (Phase 2)
│   ├── 05-axis-templates.md                        (Phase 2; can split per axis)
│   ├── 06-file-budget.md                           (Phase 3)
│   └── 07-dispatch-log.md                          (running log across waves)
├── <entity-slug>/                                   (one per core entity; MAX 15 files)
│   ├── 00-overview.md
│   ├── 01-<axis-1-slug>.md
│   ├── 02-<axis-2-slug>.md
│   ├── ...
│   └── 09-sources.md                               (claims ledger)
├── <entity-slug>.md                                 (profile page at root for core entities)
└── _cross/                                          (one folder per axis)
    ├── <axis-1-slug>/                              (MAX 12 files)
    │   ├── 00-overall-comparison.md
    │   ├── 01-<scenario>.md
    │   └── ...
    ├── <axis-2-slug>/                              (MAX 12 files)
    │   └── ...
    └── ...
```

Numbered prefixes (`00-` through `09-` or beyond) sort scan order.
Slugs are kebab-case, descriptive, agent-chosen within the
orchestrator's numbering scheme.

## MAX-N caps with rationale

| Folder | MAX-N | Rationale |
|---|---|---|
| `<entity-slug>/` | 15 files | Enough for ~10 axes plus overview, sources, edge cases. Below ceiling normal. |
| `_cross/<axis-slug>/` | 12 files | One overall-comparison plus up to 11 scenario / contradiction / decision-flipper files. |
| `_meta/` | 8 files | The 8 listed in the tree. Beyond means scope creep. |
| Discovery list size | 50 entities | Tier the long tail to `discovered-only`. |
| Subagents per wave | 8 | Coordination overhead exceeds parallelism savings beyond 8. |
| Waves per session | 4 | Default 3; optional 4. Beyond 4 means upstream charter is wrong. |
| Search rounds per subagent | 4 | Per run-research discipline. |
| Retries per failed agent | 2 | If second attempt fails, log gap and escalate. |

**Why ceilings, not floors.** A minimum of 20 searches means the
agent will pad with garbage queries if the question was answered in
8. A minimum word count produces filler. A minimum file count
produces stub files.

Ceilings work because they signal: this is deep work, depth is
budgeted, find the natural stopping point. The agent reads the
ceiling as permission to be thorough and the room-below-ceiling as
permission to be efficient.

When a researcher hits the cap, the right move is rarely to create
the next file. It is one of:

- **Split** the folder (`pricing-and-billing/` → `pricing/` plus
  `billing-and-overages/`).
- **Merge** two thin files into one with H2 sections.
- **Accept** that the entity warrants the full ceiling and stop
  adding files.

## File naming

The pattern: `<NN>-<topic-slug>.md`

- `<NN>` is a two-digit prefix (typically `00-` through `09-`) for
  scan order. **The orchestrator decides NN.**
- `<topic-slug>` is kebab-case, descriptive of the file's content.
  **The agent decides the slug** based on the evidence they found.

Two researcher subagents may legitimately land different filenames
inside the same numbered subfolder, because their evidence shapes
differ. That is correct.

The orchestrator's Phase 2 templates list *sections* (axis names,
required questions per section) and *expected NN ranges* (e.g.,
"01-09 for axis content; reserve 00 for overview and the highest
NN for sources"). They never prescribe filenames.

Examples of valid naming (slug differences are correct):

```
acme-corp/01-pricing-tiers.md
beta-inc/01-billing-and-overages.md
gamma-co/01-cost-economics.md
```

All three are the same axis (cost), expressed per the entity's
specific evidence shape.

## Filesystem as context channel between waves

Subagents do not see the orchestrator's conversation. They cannot
pass results to other subagents through context. **The filesystem
is the only context channel between waves.**

This is why each wave's brief includes:

- **Read scope** — the exact paths to read (Wave 2 reads
  `_meta/01-charter.md`, `_meta/03-axes.md`,
  `_meta/04-product-template.md`).
- **Write scope** — the exact paths the agent owns (Wave 2 owns
  `<entity-slug>/`).
- **Do-not-touch scope** — paths the agent must not modify (no
  other entity's folder, no `_meta/`, no `_cross/`).

Disjoint write scopes prevent merge conflicts. Explicit read scopes
prevent context bloat from "I read everything before writing".

The orchestrator merges via file reads. After every wave, the gate
procedure is:

1. Read every file the wave's subagents wrote.
2. Cross-reference against the brief's DoD.
3. Flag any silent gap-skips (sections in
   `_meta/04-product-template.md` not addressed in the entity's
   pack).
4. Update `_meta/07-dispatch-log.md`.
5. Decide: next wave, retry, or escalate.

## Insufficient-evidence handling

No stub files. A section with sparse evidence becomes a one-paragraph
"insufficient evidence" entry inside an existing file in the same
subfolder, with the specific data gap named.

Example:

```markdown
## Compliance and audit posture

**Insufficient evidence.** Vendor docs do not name compliance
regimes (no SOC 2, ISO 27001, HIPAA, or sector-specific
certifications listed on `/security` page). No third-party audit
reports surfaced via Reddit or HN search. The data gap: vendor's
public compliance posture is not documented; if the decider needs
compliance evidence, request a vendor-supplied attestation.
```

Skipping silently is a failure. Creating a stub file (e.g.,
`05-compliance.md` with a single line "TBD") is also a failure —
it pollutes the corpus and cannot be distinguished from a
forgotten section.

## Absolute rules

- **No placeholder text.** Zero `TODO`, `TBD`, `fill later`,
  `<placeholder>`, `???` strings in core or cross files. The Phase 7
  verification gate fails on these.
- **No empty files.** Every file has content. If a section's
  evidence is insufficient, fold it into an existing file as an
  "insufficient evidence" note.
- **No same-name files in the same folder.** Standard filesystem
  rule, surfaced because numbered prefixes can collide if the
  orchestrator and agent both default to `01-`.
- **No hidden files.** No `.DS_Store`, `Thumbs.db`, `.tmp`, `.bak`
  in any corpus folder. Phase 7 verification grep fails on these.

## Token-efficient context sharing

The filesystem-as-channel pattern is also a token-efficiency lever.
Every brief tells the agent to read only the specific files they
need, not the whole corpus.

Wave 2 example (per-entity researcher reads):

- `_meta/01-charter.md` — context (decider use case, freshness).
- `_meta/03-axes.md` — the axis catalog (their pack's section
  structure).
- `_meta/04-product-template.md` — the template (what each axis
  section must address).
- Their own `<entity-slug>/` folder — initially empty; they fill
  it.

That's three meta files plus their own folder. They do NOT read
other entities' folders, `_cross/`, or each other's outputs. Token
cost ≈ 3-5K tokens of input regardless of how big the corpus
grows.

Wave 3 example (per-axis cross-synthesis researcher reads):

- `_meta/01-charter.md` — context.
- `_meta/05-axis-templates.md` (or the specific axis template) —
  comparison axes mandated.
- `<entity-slug>/<NN>-<their-axis>.md` for every `core` entity —
  the per-entity evidence on their assigned axis.
- Optionally each entity's `09-sources.md` for citation
  resolution.

That's one meta file plus N axis-specific files (one per `core`
entity). Token cost scales with N entities × evidence-per-axis,
not with the whole corpus.

The contract: **subagents read only their assigned scope. The
orchestrator merges via file reads. Cross-talk happens only through
the filesystem.**

## Tree before research

The orchestrator may pre-create empty folders before Wave 2
dispatches:

```bash
mkdir -p "$CORPUS"/_meta "$CORPUS"/_cross
for entity in <core-entity-slugs-from-_meta/02-entities.md>; do
  mkdir -p "$CORPUS"/"$entity"
done
for axis in <axis-slugs-from-_meta/03-axes.md>; do
  mkdir -p "$CORPUS"/_cross/"$axis"
done
```

This is optional but useful: pre-creating folders means agents see
the tree shape they are expected to fill. Empty folders serve as
commitments during the session.

## Verification commands (for the Phase 7 completion gate)

Concrete bash commands to run before declaring done:

```bash
CORPUS=<corpus-root-absolute-path>

# Total file count (informational, not capped)
find "$CORPUS" -type f -name '*.md' | wc -l

# No hidden junk
find "$CORPUS" \( -name '.DS_Store' -o -name 'Thumbs.db' \
                -o -name '*.tmp' -o -name '*.bak' \)

# MAX 15 per entity folder
for entity in "$CORPUS"/*/; do
  base=$(basename "$entity")
  case "$base" in _meta|_cross) continue;; esac
  count=$(find "$entity" -maxdepth 1 -type f -name '*.md' | wc -l)
  test "$count" -gt 15 && echo "OVER: $base has $count files"
done

# MAX 12 per cross-axis folder
for axis in "$CORPUS"/_cross/*/; do
  count=$(find "$axis" -maxdepth 1 -type f -name '*.md' | wc -l)
  test "$count" -gt 12 && echo "OVER: _cross/$(basename "$axis") has $count"
done

# MAX 8 per meta
count=$(find "$CORPUS"/_meta -maxdepth 1 -type f -name '*.md' | wc -l)
test "$count" -gt 8 && echo "OVER: _meta has $count files"

# No placeholder text
grep -rEn '\b(TODO|TBD|fill later|<placeholder>)\b' "$CORPUS"

# Master summary present
test -f "$CORPUS/_meta/00-master-summary.md" && echo "master summary OK"
```

## Domain-independent: why this structure works for any research

The structure works for any research domain because:

- **Entities × axes is universal** — every comparison-research
  question has both.
- **Per-entity packs are decision-grade reads** — the decider opens
  one when comparing finalists.
- **Per-axis cross folders enable scenario thinking** — the decider
  compares finalists per axis.
- **Profile pages bridge depth and brevity** — the decider reads
  one profile, navigates into the pack only when needed.
- **Master summary is the recommendation** — the decider reads it
  first.

This shape is independent of whether the entities are products,
candidates, locations, services, organizations, or papers. The
domain-specific work happens in: (a) what the axes are named, (b)
what evidence sources are authoritative, (c) what practitioner
channels matter. The structure itself is constant.
