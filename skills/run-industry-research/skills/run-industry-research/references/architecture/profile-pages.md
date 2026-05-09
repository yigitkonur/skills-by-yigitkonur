# Profile Pages

How to write the standalone `<entity-slug>.md` decision pages at the corpus root.

Read this in **Phase 6** of the run-industry-research workflow.

## What a profile page is

A profile page is the readable, narrative-style decision page for a `core` tier entity. It lives at the corpus root (`<topic>/[entity-slug].md`), one per `core` entity, alongside the entity's evidence-pack folder (`<topic>/[entity-slug]/`).

The profile page is the buyer's first read. It synthesizes the evidence pack into a single document that answers "should I pick this entity, and under what conditions?" — without forcing the reader to navigate 10 subfolders.

The evidence pack is the source. The profile page is the synthesis.

## What a profile page is NOT

| Profile page is | Profile page is not |
|---|---|
| A readable narrative | A file index |
| A synthesis of multiple categories | A duplicate of `00-overview/` |
| The buyer's executive read | A landing-page-style marketing summary |
| 300-700 lines for substantial entities | A two-paragraph summary |
| Linking into the evidence pack for detail | Replacing the evidence pack |
| Opinionated about fit and risk | Vendor-neutral list of features |

If the profile page is shorter than the evidence-pack `00-overview/01-executive-brief.md`, it's not a profile page — it's a duplicate.

## When to write profile pages

| Corpus scale | Profile pages |
|---|---|
| `compact` (1-10 entities) | Optional — small enough that the evidence pack alone may suffice |
| `standard` (10-40 entities) | Default yes for `core` tier |
| `deep` (40-100 entities) | Required for `core` tier |
| `tiered` (100+ entities) | Required for top-tier; secondary tier gets compact profile-only (no full pack) |

If the user explicitly says "I just want the evidence packs, no separate profile pages," skip Phase 6 with a stated reason.

## Section ordering

A strong profile page follows this order. Adapt section names to the vertical, but keep the logic.

```markdown
# [Entity Name]

> One-line positioning statement (what they sell, who for, what makes them distinct).

## Research metadata

- **Capture date:** YYYY-MM-DD
- **Research scale:** [compact/standard/deep/tiered]
- **Source corpus:** [link to evidence pack folder]
- **Confidence:** [high/medium/low] with one-line rationale

## Executive summary

3-5 paragraph synthesis. The buyer who only reads this section should know:
- What the entity is and how it differs from the obvious comparator
- Whether it's a buy candidate for them and under what conditions
- The single biggest risk or unresolved question

## Headline findings

5-10 bullet points of the most important facts/decisions, each linking to the evidence-pack file that backs it.

## Best-fit scenarios

Concrete buyer scenarios where this entity is the right pick, with conditions:
- "If you need X and have Y constraint, this is the right choice because [evidence]"
- "If you can tolerate Z risk, the cost advantage is significant"

## Do-not-choose-if

Concrete scenarios where this entity is the wrong pick:
- "If you need [requirement], this entity does not deliver because [evidence]"
- "If [condition], the lock-in cost outweighs the savings"

## Evidence pack map

Table linking each evidence-pack subfolder to its purpose. This is the navigation aid for readers who want to drill into specific categories.

| Subfolder | What it covers | Files |
|---|---|---|
| `[entity]/00-overview/` | Positioning and taxonomy | [list] |
| `[entity]/01-pricing/` | Public pricing, unit economics, scenario costs | [list] |
| ... | ... | ... |

## Deep profile

Synthesis sections that combine evidence from multiple subfolders. Section names match the vertical's category list from Phase 2. Typical sections for SaaS/vendor research:

### Pricing and unit economics
2-4 paragraphs synthesizing pricing/01-* and pricing/02-*, with link to specific files for unit details.

### Product and platform
Synthesis of platform/02-* files.

### Integrations and ecosystem
Synthesis of integrations/03-* files.

### Operations and reliability
Synthesis of operations/04-* files.

### Security, compliance, legal
Synthesis of security/05-* files.

### Audience and practitioner signal
Synthesis of audience/06-* files. Direct quotes belong in the audience subfolder; the profile page summarizes the sentiment landscape.

### Benchmarks and performance
Synthesis of benchmarks/07-* files.

## Numbers worth memorizing

A short table of the 5-10 quantitative facts that matter most for decisions:

| Number | Source | Caveat |
|---|---|---|
| $X/month entry plan | pricing/01-* | Excludes overage |
| Y minutes free tier | pricing/01-* | Resets daily |
| ... | ... | ... |

## Open gaps

Bullet list of unresolved questions that would change the recommendation, each pointing to the evidence-pack `09-sources/` file.

## Sources

Link to the evidence-pack `09-sources/01-source-map.md` and `09-sources/02-claims-ledger.md`.
```

## Length guidance

- **Compact entity profile** — 200-400 lines (sparse evidence, narrow scope)
- **Standard entity profile** — 400-700 lines (typical core entity in standard corpus)
- **Substantial entity profile** — 700-1000 lines (incumbent or category leader with rich evidence)

Longer than 1000 lines means the profile is duplicating the pack. Shorter than 200 lines means it's not synthesizing — it's summarizing.

For reference, the worked-example cloud-browser corpus has profile pages ranging from 479 lines (Airtop, mid-tier challenger) to 631 lines (Anchor Browser, dominant Reddit-recommended entity).

## Distinguishing profile from `00-overview/`

The most common mistake is making the profile page a copy of `00-overview/01-executive-brief.md`. They are different artifacts:

| `<entity>/00-overview/01-executive-brief.md` | `<entity>.md` (profile) |
|---|---|
| Atomic file inside the evidence pack | Standalone file at corpus root |
| Single concern: positioning | Multi-concern: positioning + pricing + ops + audience + decision |
| 50-100 lines | 300-700 lines |
| Read by researchers entering the pack | Read by buyers as first encounter |
| Cited by the profile page | Synthesizes from multiple pack files |

The brief is a leaf in the pack. The profile is the front door.

## Linking discipline

Inside the profile page, every non-trivial claim should link to an evidence-pack file:

```markdown
The Hobby plan is $39/month with 100 browser-minutes ([pricing details](browserbase/01-pricing/01-public-pricing-and-plan-matrix.md)),
but session timeouts default to 5 minutes ([session lifecycle](browserbase/02-platform/02-session-lifecycle-persistence-auth.md))
which materially affects cost-per-task for long-running agents.
```

This is the "synthesis with links" pattern. The profile carries the narrative; the pack carries the evidence.

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Profile is a copy of `00-overview/` | No synthesis added | Combine 4-7 categories into a narrative |
| Profile is two paragraphs | Not enough to support a decision | Expand to 300+ lines with concrete scenarios |
| Profile has no links into the pack | Loses source traceability | Every claim links to the pack file |
| Profile is opinionated without sources | "Trust me" recommendations | Each opinion ties to specific evidence |
| Profile has a buy/don't-buy verdict at the top | Removes the buyer's agency | Provide best-fit and do-not-choose scenarios; let the buyer match their context |
| Profile has volatile pricing in headline | Stale within months | Move pricing to a body section; headline carries qualitative positioning |
| Profile duplicates Reddit quotes | Audience evidence belongs in the pack | Profile summarizes sentiment; pack carries verbatim quotes |
| Profile is a "vendor pitch" tone | Reads like a marketing brochure | Buyer-first tone: where they win, where they lose, what would change the recommendation |

## Worked example

The cloud-browsers corpus has 12 profile pages (one per `core` entity). Notable patterns:

- **`airtop.md`** (479 lines) — strong "best-fit" and "do-not-choose-if" sections; pricing summarized with link to scenarios; Reddit sentiment one paragraph with link to verbatim comments
- **`anchor-browser.md`** (631 lines) — longest profile because Anchor dominates Reddit migration recommendations and required a substantial audience-evidence synthesis
- **`bright-data-agent-browser.md`** (608 lines) — different vertical positioning (proxy-network-first); profile structure adapts (`05-security/` content elevated to a more prominent profile section)

Read three of these before writing your first profile page to internalize the synthesis-with-links pattern.

## Validation checklist

Before declaring a profile page done:

- [ ] Has a `Research metadata` block with capture date and confidence rating
- [ ] Executive summary is 3-5 paragraphs and is comprehensible standalone
- [ ] Headline findings are linked to evidence-pack files
- [ ] Best-fit scenarios are concrete (with conditions, not generic)
- [ ] Do-not-choose-if scenarios exist and are concrete
- [ ] Evidence-pack map table covers every subfolder in the pack
- [ ] Deep profile sections synthesize from multiple files (not single-file copies)
- [ ] "Numbers worth memorizing" table exists with caveats
- [ ] Open gaps section points to `09-sources/`
- [ ] Length is in the 300-700 line range (or justified outlier)
- [ ] Tone is buyer-first, not vendor-pitch
