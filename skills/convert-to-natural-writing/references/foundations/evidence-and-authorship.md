# Evidence and Authorship

Use this reference to separate observable editorial problems from claims about whether a human or an AI produced the text.

## The core distinction

Authorship and quality are different questions:

- **Authorship** asks who or what produced the text. Style alone rarely establishes this reliably.
- **Quality** asks whether the text is accurate, clear, specific, coherent, useful, appropriate, and publication-ready.

This skill answers the second question. It may describe textual features, but it must not turn those features into an authorship verdict.

## Evidence ladder

Rank observations by what they actually prove:

| Level | Evidence | Supports | Does not support |
| --- | --- | --- | --- |
| 1 | Broken placeholders, prompt chatter, malformed markup | A production or editing defect | Who authored the draft |
| 2 | Repetition, vague actors, unsupported significance, generic transitions | A contextual editorial concern | AI generation by itself |
| 3 | Metadata, revision history, provenance records | A claim about process within the record's limits | Universal certainty if records are incomplete |
| 4 | Detector output or vocabulary heuristics | At most, a model-specific statistical signal | Reliable individual authorship classification |

When provenance matters, request provenance evidence. Do not substitute punctuation or vocabulary folklore.

## Why detector optimization is the wrong target

Detector-facing edits create three problems:

1. They optimize for an opaque model rather than the reader.
2. They encourage arbitrary changes such as removing precise words, punctuation, or grammatical consistency.
3. They can disproportionately flag multilingual writers and writers using conventional academic or professional registers.

Published evaluations have found substantial false positives and poor generalization across domains and languages. The exact rate depends on the detector, dataset, threshold, and language; never universalize one study's result.

## Safe reframe

When a user asks for “undetectable,” “0% AI,” or “definitely human,” reply briefly:

> I can improve the writing for clarity, specificity, voice, and reader fit, but I can't guarantee detector results or certify human authorship.

Then continue with the legitimate editorial task. Do not lecture, score the text, or provide detector-specific tactics.

## Descriptive signs are not rules

Collections such as Wikipedia's *Signs of AI writing* are valuable when treated as diagnostic prompts. Their own framing matters: the signs are descriptive rather than prescriptive, and they are potential signs of a problem rather than the problem itself.

Use a listed pattern only after answering:

1. Does it occur in this exact text?
2. Does it create reader harm in this genre and locale?
3. Does it cluster with other evidence?
4. Can the underlying issue be named without mentioning AI?
5. Would the same edit improve confirmed human writing?

If the answer to the last question is no, the edit is probably detector theater.

## Strong and weak diagnoses

Weak:

> “Moreover” sounds AI-generated. Replace it.

Strong:

> Three consecutive paragraphs begin with additive transitions even though the relationship changes from evidence to limitation. Remove the first two transitions and name the limitation directly.

Weak:

> The em dashes make this look machine-written.

Strong:

> This sentence nests two asides inside the main claim, so the evidence and qualification are hard to follow. Split the qualification into a second sentence.

The strong diagnoses describe function and reader impact. They remain valid regardless of authorship.

## Do not manufacture counter-signals

Never add or preserve an error merely to appear human. Do not invent:

- a first-person memory;
- emotion or preference;
- a customer conversation or interview;
- a metric, example, name, or date;
- regional slang or inconsistent spelling;
- deliberate typos, fragments, or contradictions;
- unsupported criticism or contrarianism.

Real voice comes from accountable choices and concrete source material, not simulated imperfection.

## Attribution discipline

Keep the source of every claim visible:

| Source state | Editorial treatment |
| --- | --- |
| Supplied first-hand statement from an identified speaker | May retain first person and personal perspective. |
| Approved organizational claim | May use “we” only if the organization is the speaker. |
| External source | Preserve attribution and citation; do not absorb it into the narrator's voice. |
| Unattributed draft claim | Keep qualified or flag for evidence; do not strengthen. |
| Generated suggestion with no source | Treat as unverified, not fact. |

## Reporting uncertainty

Be precise about the confidence available:

- “This draft contains unresolved placeholder text” is observable.
- “This paragraph uses repetitive framing that weakens the argument” is an editorial judgment with evidence.
- “This was written by AI” is an authorship claim the text does not establish.
- “A detector scored it 82%” is a report about a detector, not the author.

If a user genuinely needs academic-integrity or compliance review, recommend process evidence and human review. Do not disguise an editorial rewrite as forensic analysis.

## Common failures

| Failure | Correction |
| --- | --- |
| Treating a long sign list as a forbidden-word list | Convert each item into a contextual reader-impact question. |
| Quoting one false-positive statistic as universal | State dataset, languages, tool class, and scope. |
| Refusing the whole rewrite after an evasion request | Reframe once, then complete the quality-focused edit. |
| Claiming a rewrite “passes” because one detector score fell | Exclude detector scores from completion criteria. |
| Using polished fluency as proof of AI | Evaluate genre and reader fit; many humans write polished prose. |

## Completion check

- Every diagnosis names observable text and reader impact.
- No style feature is treated as proof of authorship.
- Detector limitations are stated without overclaiming one study.
- The rewrite contains no fabricated biography, evidence, or “human” mistakes.
- Provenance-sensitive questions are routed to provenance evidence and accountable review.
