# The Audit-First Active Ledger Workflow

The Audit-First Active Ledger workflow is the foundational operating procedure of natural writing conversion. High-end human editing never begins with hasty line-by-line rewriting or blind synonym substitution. It begins with a disciplined, systematic audit that inventories invariant facts, diagnoses linguistic defects in context, and commits proposed improvements to an explicit ledger before modifying a single word of prose.

---

## 1. Why Audit-First?

When automated agents or novice writers rewrite synthetic text directly, three catastrophic failures consistently occur:

1. **Hallucinatory Factual Drift**: In the pursuit of "flowing" prose, numbers, dates, technical constraints, product names, URLs, or negative conditions are subtly distorted, omitted, or exaggerated.
2. **Superficial Synonym Swapping**: Rather than diagnosing the structural root cause of stiffness (such as rigid word order, gerund overload, or passive evasion), the editor merely swaps out typical "AI words" for synonyms, creating text that feels equally artificial and erratic.
3. **Loss of Accountability & Traceability**: The author or reviewer cannot tell why a change was made, whether the change accurately preserves the original intent, or whether the new register matches the target genre.

The Active Ledger prevents these failures by creating an explicit bridge between diagnosis and execution. Every revision must be justified by an identifiable linguistic flaw, evaluated against reader impact, and checked against protected invariants.

---

## 2. Invariant Protection Classes

Before auditing or editing, categorize every element of the source document into one of four immutable protection classes:

| Protection Class | Target Elements | Operational Rule |
| :--- | :--- | :--- |
| **Exact (Literal)** | URLs, markdown destinations, API identifiers, code snippets, citation tokens, HTML/JSX tags and attributes, product model numbers, CLI commands. | **Preserve byte-for-byte.** Zero alteration, whitespace drift, or reformatting unless explicitly authorized. |
| **Value (Factual)** | Names of people and entities, statistics, percentages, dates, currency amounts, physical units, direct quotes, legal commitments. | **Preserve numerical and semantic value.** Formatting may adapt to target locale standards (e.g., "$10,000" to "10.000 dolar"), but the referent and quantity must remain strictly identical. |
| **Force (Epistemic)** | Attribution, degrees of uncertainty ("may", "likely", "estimated"), causal scope, negative boundaries ("does not support"), limitations. | **Preserve epistemic force.** Never polish uncertainty into certainty. Never broaden a narrow claim or make a tentative finding sound definitive. |
| **Document (Structural)** | Heading hierarchy, table column semantics, metadata keys, search intent, call-to-action (CTA) objectives, reading sequence. | **Preserve document contract.** Reorganize internal sentence rhythm, but do not drop sections or alter the macro-level purpose. |

---

## 3. The Active Ledger Schema

During the audit phase, document findings in a structured Markdown ledger. Each entry isolates a discrete sentence or clause and captures five dimensions:

```markdown
### Ledger Item #{N}
- **Location & Excerpt**: [Exact paragraph, heading, or verbatim source sentence]
- **Context & Genre**: [Target medium, e.g., SaaS Landing Page, Incident Post-Mortem, Twitter Thread]
- **Linguistic Flaw / Smell**: [Specific pattern from Turkish Translationese, Universal AI Heuristics, or Model Quirks]
- **Reader Harm / Impact**: [Why this impairs cognition, engagement, trust, or clarity]
- **Natural Human Alternative**: [Proposed reconstruction respecting natural cadence and voice]
- **Invariant Audit**: [Verification that Exact, Value, Force, and Document invariants remain intact]
```

### Example Ledger Entry

```markdown
### Ledger Item #04
- **Location & Excerpt**: Section 2.1 — "Yeni analiz modülü, yapay zekâ mühendislerimiz tarafından titizlikle geliştirilmiştir."
- **Context & Genre**: SaaS Feature Announcement (Turkish B2B)
- **Linguistic Flaw / Smell**: Pattern 1 (Tarafından-pasifi) & Pattern 5 (-dir mekanik enflasyonu). English agentive passive calque ("was developed by our engineers") combined with officialese suffix.
- **Reader Harm / Impact**: Creates cold, bureaucratic distance; obscures team ownership behind passive grammar; sounds like a translated corporate press release.
- **Natural Human Alternative**: "Yeni analiz modülünü yapay zekâ mühendislerimiz geliştirdi."
- **Invariant Audit**: Preserved actor ("yapay zekâ mühendislerimiz"), subject ("yeni analiz modülü"), and completed action ("geliştirdi"). No factual drift.
```

---

## 4. The Three-Phase Execution Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: INVARIANT INVENTORY & FORENSIC AUDIT               │
│ - Parse document structure and isolate protected invariants │
│ - Conduct contextual sentence-by-sentence evaluation        │
│ - Populate the Active Ledger with verbatim smells & fixes   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: STRUCTURAL & CADENCE RECOMPOSITION                 │
│ - Pass 1: Substance, clarity, and factual alignment         │
│ - Pass 2: Register, voice, and genre calibration            │
│ - Pass 3: Cadence, burstiness, and conversational breathing │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: RECONCILIATION & PUBLICATION REVIEW                │
│ - Claim-by-claim verification against the ledger            │
│ - Invariant integrity check (zero drift in numbers/code/URLs│
│ - Final human rhythm reading aloud check                    │
└─────────────────────────────────────────────────────────────┘
```

### Phase 1: Invariant Inventory & Forensic Audit
1. Read the entire text without editing to understand its primary communicative purpose, genre, and intended reader.
2. Extract all Exact and Value invariants into an internal protection list.
3. Traverse the text sentence by sentence. When prose feels stiff, generic, or unnatural, identify the precise structural mechanism (referencing `references/turkish-translationese-guide.md`, `references/signs-of-ai-heuristics.md`, and `references/model-specific-quirks.md`).
4. Record every finding in the Active Ledger before executing rewrites.

### Phase 2: Structural & Cadence Recomposition
Execute rewrites in three ordered passes. If a later pass modifies meaning, return to Pass 1:

* **Pass 1: Substance & Clarity**: Strip filler words, empty promotional adjectives, and unearned significance. State the actor, mechanism, and outcome directly. Ensure domain terminology remains accurate and stable.
* **Pass 2: Register & Genre**: Align tone with the specific medium (referencing `references/formats-and-genres.md`). Calibrate formality: warm and conversational for onboarding; crisp and empathetic for customer support; direct and quantified for executive updates.
* **Pass 3: Cadence & Rhythm**: Break monotonic sentence lengths (referencing `references/cadence-and-rhythm.md`). Inject burstiness. Eliminate converb chaining (*ulaç yığılması*). In Turkish, leverage natural pro-drop and inverted sentences (*devrik cümle*) to create human conversational breathing.

### Phase 3: Reconciliation & Publication Review
1. Re-read the revised text against the original invariant inventory. Confirm that zero URLs, dates, numbers, code snippets, or epistemic qualifications were lost or modified.
2. Read the text aloud (or simulate vocalization). If a sentence requires pausing for breath in the middle of a clause, re-punctuate or break it into two thoughts.
3. Produce the final clean deliverable. If working in a collaborative team, append the Active Ledger as the transparent justification log.

---

## 5. Escalation & Stop Conditions

Stop editing immediately and escalate to the author or domain owner if:

1. **Source Fact Ambiguity**: The source text makes contradictory claims or asserts metrics that lack logical foundation. Never invent details to resolve an authorial gap.
2. **Epistemic Overreach**: The original text expresses heavy qualification ("initial tests indicate potential feasibility"), but the user requests making it punchy or definitive. State that epistemic integrity outranks marketing punchiness.
3. **Detector-Bypassing Requests**: If asked to "beat an AI detector" or insert deliberate typos, quirks, or slang, explicitly decline the adversarial evasion. Reframe the objective to clarity, authentic voice, rhythm, and reader utility.
4. **Locale Competence Boundaries**: If editing in a language or specialized dialect where cultural idioms or technical terminology cannot be verified with certainty, flag the items in the ledger for review by a native domain expert.
