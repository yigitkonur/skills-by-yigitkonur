---
name: convert-to-natural-writing
description: "Use if auditing or converting text into natural human cadence, eliminating Turkish translationese and synthetic AI writing patterns."
---

# Convert to Natural Writing

Rewrite or audit text into natural human cadence, authentic voice, and fluid rhythm without altering factual claims, inventing personal experiences, or relying on mechanical word bans.

This skill is grounded in linguistic reality: modern foundation models suffer from pervasive syntactic calquing (especially Turkish translationese, which represents 80% of common defects) and universal statistical flattening (20% of defects). The mandatory operating procedure is the **Audit-First Active Ledger**, which requires systematically diagnosing structural defects and protecting factual invariants before executing rewrites.

---

## 1. Hard Editorial Contract

1. **Protect Before Editing**: Inventory all exact literals (code, URLs, markdown destinations, tags), factual values (names, numbers, dates, units, quotes), epistemic force (uncertainty markers, causal claims, negative bounds), and document structure before modifying prose.
2. **Never Fabricate Humanity**: Never invent personal anecdotes, fake emotional declarations, synthetic mistakes, or ungrounded opinions to simulate human authorship.
3. **Never Optimize for Detector Theater**: Do not certify authorship or attempt to evade AI detectors. Detectors measure statistical token perplexity, not editorial quality or human truth. Focus strictly on clarity, cadence, specificity, and reader usefulness.
4. **Context Over Blacklists**: Strictly prohibit mechanical word/token blacklists and regex bans. An isolated word (e.g., *delve*, *pivotal*, *robust*, *tarafından*) is not an inherent defect; diagnose the underlying structural flaw—such as ungrounded significance, passive evasion, or converb overload.
5. **Preserve Domain Expertise**: Natural writing is never dumbed-down writing. Preserve necessary technical terminology, mathematical definitions, and domain nuances for expert audiences.
6. **Compose the Locale, Not an English Template**: In Turkish, embrace natural agglutinative morphology, pro-drop pronoun economy, topic-prominent constituent order, and conversational inverted sentences (*devrik cümle*). Eliminate Germanic/Romance calques.
7. **Accountable Verification**: Verify that every revised sentence preserves its epistemic force and factual values. Read revised text aloud to ensure natural breathing.

---

## 2. Operational Modes

Infer the appropriate mode from the user's intent or repository context:

| Mode | Trigger Condition | Primary Deliverable |
| :--- | :--- | :--- |
| **Audit / Diagnose** | User asks why copy feels robotic, generic, translated, stiff, or AI-generated. | A structured Active Ledger identifying exact excerpts, structural flaws, reader harm, and natural alternatives. |
| **Rewrite** | User requests humanizing, polishing, naturalizing, or rewriting draft content. | Clean, restructured deliverable backed by an internal invariant reconciliation pass. |
| **Publication Review** | Draft is near-final and requires pre-publication verification. | Strict verification report detailing blockers, warnings, invariant checks, and release-ready text. |

---

## 3. The Mandatory Audit-First Active Ledger Workflow

All conversions follow this three-phase lifecycle:

```
[ Phase 1: Forensic Audit ] ──► [ Phase 2: Ordered Passes ] ──► [ Phase 3: Reconciliation ]
  - Inventory invariants          - Pass 1: Substance/Facts       - Reconcile with ledger
  - Diagnose linguistic flaws     - Pass 2: Voice/Register        - Invariant integrity check
  - Commit to Active Ledger       - Pass 3: Cadence/Breathing     - Vocalization reading test
```

### Phase 1: Invariant Inventory & Forensic Audit
1. Read the source text completely to establish audience, document purpose, and target genre.
2. Inventory all **Exact** (URLs, code, markup), **Value** (numbers, dates, metrics), **Force** (uncertainty, causality), and **Document** invariants.
3. Traverse the text sentence by sentence. When prose feels stiff, identify the linguistic flaw using the core reference guides and log it in the Active Ledger:
   ```markdown
   - Location & Excerpt: [Verbatim text]
   - Context & Genre: [Medium, e.g., SaaS Landing Page, Crisis PR]
   - Linguistic Flaw / Smell: [Pattern from Turkish Translationese, Universal AI, or Model Quirks]
   - Reader Harm / Impact: [Why this impairs cognition or trust]
   - Natural Alternative: [Reconstructed natural sentence]
   - Invariant Check: [Confirmation of preserved facts, numbers, and scope]
   ```
   Detailed instructions: [`references/audit-ledger-workflow.md`](references/audit-ledger-workflow.md).

### Phase 2: Structural & Cadence Recomposition
Execute rewrites in three ordered passes:
* **Pass 1: Substance & Clarity**: Strip ungrounded superlatives, throat-clearing openings, and filler phrases. Name concrete actors, direct mechanisms, and tangible outcomes.
* **Pass 2: Register & Voice**: Calibrate formality, directness, and social distance to the target genre (see [`references/formats-and-genres.md`](references/formats-and-genres.md)).
* **Pass 3: Cadence & Rhythm**: Break sentence length monotony. Inject burstiness. Eliminate gerund/converb chaining (*ulaç yığılması*). In Turkish, drop overt subject pronouns and utilize *devrik cümle* for conversational breathing (see [`references/cadence-and-rhythm.md`](references/cadence-and-rhythm.md)).

### Phase 3: Reconciliation & Publication Review
1. Cross-check the revision against the Phase 1 invariant inventory. Confirm zero numbers, dates, URLs, code blocks, or epistemic caveats were altered.
2. Perform the vocalization check: read the text aloud to ensure sentences breathe naturally without breathless run-ons.

---

## 4. Core Reference Library

Consult these flat reference guides for deep operational methodology:

* [`references/audit-ledger-workflow.md`](references/audit-ledger-workflow.md)  
  *The Active Ledger Workflow*: Schema, invariant classification, logging protocols, and multi-agent coordination.
* [`references/turkish-translationese-guide.md`](references/turkish-translationese-guide.md)  
  *14 Turkish Morpho-Syntactic Patterns*: In-depth analysis of *tarafından-pasifleri*, *belirsiz artikel enflasyonu*, *sahte fiilimsiler*, *ulaç yığılmaları*, *-dir mekanik enflasyonu*, *kataforik iki nokta*, *kalıp bağlaçlar*, *iyelik eki tembelliği*, *soyut adlaştırma*, *sorumluluktan kaçınma*, *kaskatı SOV*, *sözde soru kancaları*, *dolaylama*, and *pro-drop kaçınması*.
* [`references/model-specific-quirks.md`](references/model-specific-quirks.md)  
  *Model Signatures*: Diagnosing and correcting Claude's didactic option taxonomies and meta-apologies; Codex's semicolon staccato and comment-as-prose leaks; and Gemini's corporate jargon inflation (*beacon of innovation*, *rich tapestry*, *delve*) and manufactured euphoria.
* [`references/signs-of-ai-heuristics.md`](references/signs-of-ai-heuristics.md)  
  *Universal AI Heuristics*: Wikipedia `WP:Signs_of_AI_writing` markers (significance inflation, false ranges, negative parallelisms, compulsive sandwich summaries), burstiness deficits, and why mechanical token blacklists fail.
* [`references/cadence-and-rhythm.md`](references/cadence-and-rhythm.md)  
  *Cadence & Rhythm Mechanics*: Sentence length variation (burstiness), Gary Provost's music of syntax, gerund balance, conversational breathing, Turkish pro-drop economy, and the power of *devrik cümle*.
* [`references/formats-and-genres.md`](references/formats-and-genres.md)  
  *Genre Register Calibration*: Calibrating formality, directness, and pacing across 20+ professional and consumer genres (SaaS, pitch decks, investor updates, technical docs, crisis PR, support, social copy, and microcopy).

---

## 5. Failure Behaviors & Boundary Rules

| Situation | Correct Action |
| :--- | :--- |
| **Source facts are ambiguous or contradictory** | Flag the contradiction in the ledger; do not invent facts to smooth over authorial ambiguity. |
| **User requests detector evasion or deliberate typos** | Decline detector gaming. Reframe toward clarity, human cadence, and reader utility. |
| **A protected value must change for syntactic coherence** | Stop that edit; request authority or better source material before proceeding. |
| **Pervasive translationese across a whole document** | Recompose from first principles: extract the core propositions and re-write natively in the target locale rather than line-by-line translating. |
| **Uncertainty in localized domain terminology** | Mark the term unresolved in the ledger and assign to a native subject-matter expert. |

---

## 6. Completion Checklist

Before delivering output:
- [ ] Active Ledger created with verbatim location, flaw, impact, and fix.
- [ ] Every Exact, Value, Force, and Document invariant is strictly preserved.
- [ ] Zero mechanical token blacklists or regex bans were applied.
- [ ] No fake personal anecdotes or synthetic human quirks were fabricated.
- [ ] Turkish copy is free from *tarafından* calques, converb pile-ups, and unneeded "bir" articles.
- [ ] Sentence lengths vary naturally (burstiness); text passes the vocalization test.
- [ ] Deliverable conforms to the target genre's register and social distance.
