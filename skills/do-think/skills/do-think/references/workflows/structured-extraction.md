# Structured Extraction — Mess → Schema

Operation: **Structured Extraction** (`Op: Extraction`).

Extract a *known schema* from an *unknown shape*. The output structure is predictable; the input format is not. Meeting transcript → action items + assignees + deadlines. Invoice PDF → ledger entry. Call recording → CRM fields. Email → database row.

This is **not** Sense-Making. There is no verdict to defend; there is a known set of fields to fill. The thinking discipline is **completeness + fidelity + ambiguity-honesty** — not options analysis.

## Triggers

- "Extract", "Parse", "Pull out", "Get all the X from Y"
- "Tag this with…", "Categorize this into…", "Log to <system>"
- Conversations / docs / files / calls → structured records (rows, JSON, CRM entries, calendar events)

## What this operation does NOT need

- ❌ ≥3 options analysis (there's nothing to compare — there's content to extract)
- ❌ The Sense-Making stress-test trio (Inversion / Ladder / Second-Order) — wrong fit
- ❌ Generation — extraction is *finding*, not creating

## What this operation DOES need

- ✅ Schema specification (every field, every type, every constraint)
- ✅ Sample inputs covering edge cases (empty, ambiguous, malformed, missing-field, multi-value)
- ✅ Per-field provenance ("this value came from line 42 of the source")
- ✅ Honest "unknown" / "ambiguous" flagging instead of confident guesses
- ✅ Completeness check (did we miss any records? any fields?)

## Phase A — Frame

- **A1** (Cynefin): Complicated for known formats (invoices in your standard layout); Complex for novel/varied inputs (free-form transcripts).
- **A2** (Op): Extraction.
- **A3** (Reframe): rare — the schema is usually given.

## Phase B — Calibrate

- **B1** (Tier): driven by **how costly an extraction error is**.
  - Low: throwaway notes for personal use
  - Medium: business records consumed by humans (CRM, calendar)
  - High: financial / legal / billing records (an extracted-wrong invoice posts the wrong amount)
- **B2** (Grounding) — Extraction-specific:
  1. **The schema spec** — every field, type, allowed values, required vs. optional
  2. **Sample inputs covering edges** — at least 3, including: a clean case, a messy case, an edge case (missing fields, ambiguous data, multi-value, malformed)
  3. **Disambiguation rules** — what to do when the source is unclear (default value? flag for human? best-guess with confidence?)

## Phase C — Compare

### C1. Produce filled schema + completeness flag + ambiguity log

Three artifacts, not three options:

1. **Filled schema** — every field populated (with `null` / `unknown` for genuinely missing).
2. **Completeness flag** — does the source contain everything the schema asked for? If not, list what's missing.
3. **Ambiguity log** — for each field where the source was unclear, log: the field, the candidate values, why they're ambiguous, and which one (if any) you chose with what confidence.

### C2. Stress-test (Extraction-specific — NOT the trio)

Three checks, all written:

- **Coverage** — did you extract all *records* the schema implies? (e.g., extracted 4 action items, but the transcript had 7 distinct asks — coverage failure)
- **Edge case scan** — did any of the input's edge cases (empty values, unusual formats, multi-value fields) get silently squashed? List each edge case observed and how you handled it.
- **Schema-fit verification** — does every extracted value satisfy the schema's type and constraint? (`amount: number > 0`, `email: valid email format`, `priority: one of [low, med, high]`). Run the type-check explicitly.

**Phase C exit criterion**: schema filled + completeness flag set + ambiguity log written + 3 checks done.

## Phase D — Commit

- **D1**: hand off the filled schema. If the receiving system needs validation, run that validation now.
- **D2**: verification check — the receiving system accepts the records (no validation errors), AND the ambiguity log was reviewed by a human if it has any entries (any field flagged ambiguous OR low-confidence).

## Output contract

Different from Sense-Making's Minto. Extraction's output is the **filled schema + provenance + flags**:

```
Records extracted: <N>
Records expected: <M> (or "unknown — flag for human review")
Coverage: <complete | N missing — see below>

[Filled schema records here, machine-readable]

Provenance per field (sample): field X → source line Y
Ambiguity log:
- Field A on record 3: candidates were [X, Y]; chose X because <rationale>; confidence: medium
- Field B on record 7: source said both 5 and 7 in different places; flagged for human

Open questions:
- <field> on <records>: source did not contain this — fill default or flag?
```

## Disambiguation discipline

When the source is unclear, the four legitimate moves:

1. **Best-guess with confidence flag** — pick the most likely value, flag confidence as low/medium.
2. **Multi-value record** — if the field genuinely has two answers, record both (if schema allows).
3. **Null / unknown** — if no defensible best guess, leave null and log the ambiguity.
4. **Halt + ask** (Interactive mode only) — fork to the user with the specific ambiguity.

**Forbidden**: confident extraction of an ambiguous value (silent guess presented as fact). This is the worst Extraction failure mode because downstream systems can't tell the value is shaky.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Silently filling unknowable fields with confident-looking guesses | Use null / unknown / flagged. Confidence is *part of the schema*, not noise. |
| Skipping the completeness check ("I extracted what was there") | The check is "what was *expected*?" Extracting 4 of 7 records is half the job. |
| Schema drift — adding fields the schema didn't ask for "because they seemed useful" | Don't. The schema is the contract. Extra fields go in the ambiguity log as "additional observations." |
| Squashing edge cases into a single representative value | Every edge case observed gets logged, even if you chose one canonical value. |
| Treating Extraction like Sense-Making (3 options, stress-test trio) | Wrong tools. Extraction's stress-test is coverage + edge cases + schema fit. |
| Claiming the extraction is "verified" without running the schema validator | Type-check explicitly. Pretty-printing isn't validation. |
