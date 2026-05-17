# Grounded Q&A — Question + Corpus → Cited Answer

Operation: **Grounded Q&A** (`Op: GroundedQA`).

Answer in plain English using a **bounded private corpus**, not the model's training. HR policy questions over Confluence. Codebase questions over the repo. Support FAQ over docs. Engineering questions over SharePoint.

This is **not** Sense-Making (no verdict; just an answer the corpus already contains). The thinking discipline is **citation honesty + scope boundary + retrieval-not-training**.

## Triggers

- "What does our X say about Y?" / "Per our policy…"
- "Where is X used in the codebase?" / "How do we handle Z?"
- "Search the docs for…" / "Look up the SOP for…"
- The user has a *bounded private corpus* and the answer should come from it, not from training data

## What this operation needs

- ✅ **Corpus boundary spec** — what is "in" and "out" of the source of truth (only the docs in `/policy/`? only the README? the whole repo? Slack history too?)
- ✅ **Retrieval before answer** — pull the relevant text, then answer FROM the text
- ✅ **Citation per claim** — every assertion ties back to a corpus location
- ✅ **Honest "I don't know in our corpus"** when the answer isn't there

## What this operation does NOT need

- ❌ ≥3 candidate verdicts (there's an answer in the corpus, or there isn't)
- ❌ The Sense-Making stress-test trio
- ❌ Generation beyond what the corpus supports

## Phase A — Frame

- **A1** (Cynefin): usually Clear (standard answer in the corpus) or Complicated (answer requires synthesizing multiple corpus sources).
- **A2** (Op): GroundedQA.
- **A3** (Reframe): rare — the user's question is usually well-formed for a Q&A.

## Phase B — Calibrate

- **B1** (Tier): driven by **cost of a wrong answer**.
  - Low: internal lookup, easily corrected
  - Medium: customer-facing answer
  - High: regulatory / legal / compliance answer where wrong = liability
- **B2** (Grounding) — Q&A-specific:
  1. **Confirm the corpus boundary** — what's in, what's out
  2. **Retrieve relevant passages** — use search / grep / vector retrieval to pull the *exact text* that should support the answer
  3. **Note retrieval coverage** — did you find direct answers, or did you have to infer? If inference, flag it.

## Phase C — Compare

### C1. Retrieved evidence + scope confirmation

Two artifacts:

1. **Retrieved passages** — the exact text from the corpus that supports the answer, with source location (file path, page, doc ID, line number).
2. **Scope confirmation** — does the retrieved evidence *directly* answer the question, or does it require inference / synthesis? If the latter, flag.

### C2. Stress-test (Q&A-specific — NOT the Sense-Making trio)

Three checks:

- **Hallucination scan** — for each claim in the answer, does the retrieved passage actually say that? Re-read the passage, not the answer. If you can't underline the claim in the source, the claim is hallucinated. **Cut it or flag it as inference.**
- **Citation completeness** — does every assertion have a citation? Generic "the docs say" is not a citation. `policy.md:42-47` is.
- **Out-of-scope flag** — is any part of the answer derived from training data rather than the corpus? If yes, mark it explicitly: "Per general best practice (NOT in our docs): …"

**Phase C exit criterion**: retrieved evidence shown + 3 checks done.

## Phase D — Commit

- **D1**: produce the answer with citations (or "I don't see this in our corpus" honesty).
- **D2**: verification check — the user can navigate to the cited locations and confirm the claims. The answer is auditable.

## Output contract

Distinct from Sense-Making. The output is **answer + citations + scope honesty**:

```
Answer: <plain-English answer>

Sourced from:
- <file/doc location 1>: "<the exact passage that supports the claim>"
- <file/doc location 2>: "<...>"

Scope: <"directly answered by corpus" | "synthesized across multiple corpus sources" | "partially in corpus + partially inferred">

Inference (NOT from corpus):
- <any claim that goes beyond what the corpus says, flagged explicitly>

Not found in corpus:
- <any part of the question the corpus didn't address>
```

## "I don't know in our corpus" is a valid answer

The single most important Q&A discipline: **honesty about absence**.

If the corpus doesn't have the answer:
- Don't invent
- Don't fall back silently to training data
- Say so: "Our corpus does not directly address X. The closest mention is <citation>, which says <quote>. Per general practice (NOT in our corpus), the typical answer is …"

This honesty is what separates a Grounded Q&A agent from a generic chatbot. Users can trust an agent that admits the gap; they cannot trust one that hallucinates.

## When Grounded Q&A composes with other operations

Many real tasks layer Q&A under other operations:

- **Composition + Q&A**: "Draft the policy update" → first run Q&A on the existing policy (the corpus), then compose the update.
- **Sense-Making + Q&A**: "Should we change our refund policy?" → first run Q&A to surface what the current policy is, then run Sense-Making on the change.
- **Extraction + Q&A**: "What are all the SLAs we've committed to in customer contracts?" → Extraction over the contract corpus, Q&A wrapper to answer the meta-question.

Re-classify when the layer changes. Q&A is often the grounding step for a downstream operation.

## Anti-patterns

| Anti-pattern | Counter |
|---|---|
| Answering from training when the corpus exists | The whole point is corpus-grounding. If the corpus doesn't have it, say so — don't substitute training data silently. |
| "The docs say…" without a specific citation | Citations are file:line / doc-id / URL. Generic gestures don't survive an audit. |
| Confidently synthesizing across corpus + training without flagging which is which | Mark each claim's source. Mixing is fine; mixing silently is not. |
| Treating "no direct answer in corpus" as a failure | Honesty about absence is the value-add. Inventing is the failure. |
| Running the Sense-Making stress-test trio | Wrong tools. Q&A's stress-test is hallucination + citation + out-of-scope. |
| Skipping retrieval and answering from memory | The Q&A discipline is *retrieval first*, then answer from retrieved text. Memory-based answers are training-grounded, not corpus-grounded. |
| Citing a passage that doesn't actually support the claim | Re-read the passage. If it doesn't say what you claim, the claim is hallucinated. Cut or rephrase. |
