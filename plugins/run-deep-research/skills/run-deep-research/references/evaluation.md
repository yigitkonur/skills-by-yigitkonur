# Deep-Dive Evaluation & Quality Audit

The authoritative evaluation rubric and audit guide for deep-research corpora.
Use this reference in **Phase 7** or during **Between-Wave Gates** to evaluate the
depth, authenticity, and decision-grade rigor of the entire research corpus.

---

## 1. The Deep-Dive Evaluation Rubric

Every deep-dive deliverable must be evaluated along **6 core dimensions**. A corpus is
only ready for the decider when all six dimensions achieve **Level 3 (Decision-Grade)**.

| Dimension | Level 1: Shallow (Reject / Re-dispatch) | Level 2: Marginal (Needs Revision) | Level 3: Decision-Grade (Pass) |
|---|---|---|---|
| **1. Structural Discipline** | Unstructured dumps; folder caps violated (>15/entity, >12/cross); placeholder files (`TODO`, `TBD`, stubs). | Inconsistent naming; missing index or charter; minor directory clutter. | Clean tree structure; strict MAX-N compliance; zero stubs; every file is indexed and linked. |
| **2. Axis Coverage & Gaps** | Key charter axes skipped; unaddressed sections; silent omissions of difficult questions. | Generic "insufficient evidence" or "TBD" notes with no diagnostic context. | **100% axis coverage**: every core entity addresses all charter axes with evidence OR a specific data-gap diagnosis. |
| **3. Evidentiary Rigor** | Claims cite search snippets, AI impressions, or unverified memory; zero verbatim quotes. | URLs present but quotes missing; marketing claims accepted as objective truth. | **Verified citations**: every numeric, priced, or versioned claim includes a verbatim scraped quote, URL, and capture date. |
| **4. Community & Sentiment** | "Reddit/HN consensus says X" with no attribution, post links, or quotes. | Paraphrased sentiment; single anecdotal comment treated as market truth. | **Attributed practitioner evidence**: quotes cite author/handle, date, score/upvotes, permalink, and bias profile. |
| **5. Cross-Entity Synthesis** | Side-by-side concatenation; empty matrix cells; flat "X is best" without conditions. | Basic feature checklist; contradictions smoothed over in prose. | **Conditional comparative synthesis**: complete matrices; scenario rankings; explicit contradictions and trade-offs surfaced. |
| **6. Decider Actionability** | Diffuse summaries; no clear recommendation; illegible to a fresh reader. | Generic advice ("evaluate your needs"); missing trade-off analysis. | **Fresh-context legible**: 7 required master sections; cited load-bearing findings; clear conditional recommendation. |

---

## 2. The 6-Step Evaluation Workflow

The orchestrator executes this 6-step evaluation before declaring any deep-dive corpus complete.

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│  Step 1: Structural &   │ ──► │  Step 2: Template &     │ ──► │  Step 3: Citation &     │
│  Budget Verification    │     │  Axis Coverage Audit    │     │  Evidence Verification  │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
             │                                                               │
             ▼                                                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│  Step 6: Decider Fresh- │ ◄── │  Step 5: Cross-Axis     │ ◄── │  Step 4: Practitioner & │
│  Context Read & Memo    │     │  Synthesis Audit        │     │  Attribution Audit      │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

### Step 1: Structural & Budget Verification
- **Automated file scan**:
  - Entity folders contain ≤15 `.md` files.
  - Cross-axis folders contain ≤12 `.md` files.
  - Meta folder contains ≤8 `.md` files.
- **Zero placeholder text**: run a regex sweep for `\b(TODO|TBD|fill later|<placeholder>|\?\?\?)\b`. Any match is a failure.
- **Link integrity**: verify all relative links `[label](path)` resolve to existing files on disk.

### Step 2: Template & Axis Coverage Audit (The 100% Rule)
- Extract the list of locked axes from `_meta/03-axes.md`.
- Extract the list of `core` entities from `_meta/02-entities.md`.
- For each `(entity, axis)` pair, verify that the entity folder contains:
  1. A dedicated content file covering that axis, **OR**
  2. A distinct section or high-specificity "insufficient evidence" entry in another file.
- **Audit Insufficient-Evidence Notes**: Ensure every gap entry explains:
  - Exactly what information was searched for.
  - Which primary sources were checked.
  - Why the data was unavailable (e.g., paywall, enterprise sales gating, unreleased feature).
  - What resolution path could settle the uncertainty (e.g., direct POC test, vendor sales inquiry).

### Step 3: Citation & Evidentiary Rigor Audit
- **Direct Quoting Standard**: Check numeric, performance, pricing, and versioned assertions.
  - *Pass*: `> "Pro tier is $49/seat/month billed annually with a 5-seat minimum." — vendor.com/pricing (captured 2026-09-12)`
  - *Fail*: `Pro tier costs around $50/mo.` (unquoted, unsourced, unverified).
- **Source Credibility Hierarchy**:
  1. Primary official sources (docs, changelogs, API specs, security whitepapers, postmortems).
  2. Public codebase / repository evidence (GitHub commits, issues, PRs, release tags).
  3. Authoritative third-party benchmarks with disclosed test methodologies.
  4. Real practitioner commentary with verified context (Reddit, HN, engineering blogs).
  5. Vendor marketing claims (must be flagged as vendor-asserted, not established fact).

### Step 4: Practitioner & Community Evidence Audit
- Community sentiment must never be presented as uniform "consensus."
- Audit each sentiment claim to confirm:
  - Source channel specified (e.g., `r/devops`, `r/selfhosted`, Hacker News).
  - Author and timestamp preserved (e.g., `u/eng_lead_99 (2026-04)`).
  - Upvote/score context included when available (e.g., `+84 upvotes`).
  - Dissenting views documented alongside dominant opinions.

### Step 5: Cross-Axis Comparative Synthesis Audit
- Open each `_cross/<axis-slug>/00-overall-comparison.md` file and audit:
  - **Matrix Completeness**: No blank cells. Every `(entity, column)` cell has a verified value or an explicit `[No public data]` note.
  - **Conditional Rankings**: Does the comparison answer *"Who wins under Scenario A vs Scenario B?"* (e.g., small team vs enterprise compliance, low-latency vs low-cost).
  - **Contradiction Surfacing**: When Entity A's documentation contradicts Entity B's performance claims, or when user reports disagree with marketing docs, both sides are cited with their respective credibility weights.

### Step 6: Decider Fresh-Context Read
- Read `_meta/00-master-summary.md` completely without relying on conversation context.
- Verify the **7 Essential Sections**:
  1. `## Document index` — navigable file map with one-line descriptions.
  2. `## Critical findings` — 3-7 high-conviction insights with citations into corpus files.
  3. `## Cross-domain insights` — emergent systemic findings spanning multiple entities.
  4. `## Action items` — prioritized, practical next steps for the decider.
  5. `## Coverage scope` — explicit boundaries (what was analyzed vs deliberately excluded).
  6. `## Open gaps` — unresolved data gaps with specific resolution recommendations.
  7. `## Recommendation` — unambiguous choice with confidence score and decision-flipping triggers.

---

## 3. Deep-Dive Evaluation Checklist

Print or evaluate this checklist during the final gate:

```markdown
### Deep-Dive Quality Gate Checklist

#### A. Architecture & Scaffolding
- [ ] Folder tree matches the selected framing (Domain-Agnostic or Industry).
- [ ] All `core` entities have dedicated `<entity-slug>/` directories.
- [ ] MAX-N limits respected (≤15 files/entity, ≤12 files/cross, ≤8 files/meta).
- [ ] No temporary files, `.DS_Store`, or empty stub files.

#### B. Coverage & Depth
- [ ] 100% of charter axes addressed across all core entities.
- [ ] Zero unaddressed sections or silent skips.
- [ ] All "insufficient evidence" entries name the specific data gap and reason.
- [ ] Source ledgers (`09-sources.md`) exist for every core entity.

#### C. Source Grounding & Quotes
- [ ] Every numeric, versioned, or pricing claim cites a verbatim quote.
- [ ] Zero citations derived from unverified search snippets.
- [ ] Captures include URL and timestamp.
- [ ] Vendor claims are separated from independent practitioner verification.

#### D. Comparative Synthesis
- [ ] Cross-axis matrices have no blank cells.
- [ ] Rankings are conditional and name decision-flipping variables.
- [ ] Contradictions between sources are surfaced and analyzed.
- [ ] Profile pages (`<entity-slug>.md`) synthesize rather than duplicate raw pack files.

#### E. Master Summary & Decider Usability
- [ ] Contains all 7 required master summary sections.
- [ ] Standalone legible to a reader with zero prior context.
- [ ] Decision recommendation is clear, justified, and actionable.
```

---

## 4. Remediation & Triage Protocols

When an evaluation check fails, execute the corresponding remediation protocol:

| Check Failure | Root Cause | Remediation Protocol |
|---|---|---|
| **Coverage Gap** (Axis missing in entity pack) | Subagent overlooked axis or search yielded no immediate hits. | Dispatch a focused subagent with a narrow brief targeting only the missing axis and specific primary source URLs. Max 2 retries. |
| **Unquoted Numeric Claim** | Subagent paraphrased or synthesized from memory. | Instruct subagent to locate the primary page and extract the exact verbatim sentence with URL and scrape date. |
| **Vague Consensus Claim** | Subagent summarized sentiment without capturing specific comments. | Require specific Reddit / HN thread extraction with post permalinks, usernames, and direct quotes. |
| **Flat / Unconditional Ranking** | Synthesizer picked a "winner" without factoring in decider constraints. | Re-synthesize the cross-comparison matrix along 2-3 realistic operational scenarios (e.g., high vs low throughput, self-hosted vs managed). |
| **MAX-N Cap Exceeded** | Folder contains too many granular or redundant files. | Merge thin one-page notes into cohesive multi-section files or split the axis into two distinct sub-axes. |
