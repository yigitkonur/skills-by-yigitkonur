---
name: convert-to-natural-writing
description: Use skill if you are humanizing or rewriting AI-sounding, robotic, or generic text, Markdown, MDX, or HTML into natural multilingual copy; not translation-only, proofreading-only, or authorship scoring.
---

# Convert to Natural Writing

Rewrite supplied content into warm, natural, casual-professional prose without changing what the writer can honestly claim. Optimize for the reader, locale, genre, and document contract—not for a performance of humanity or a detector score.

## Hard contract

1. **Protect before editing.** Inventory facts, names, numbers, dates, quotations, links, code, markup, attribution, uncertainty, scope, and document structure before changing prose.
2. **Never fabricate humanity.** Do not add personal experience, opinions, feelings, anecdotes, interviews, sources, metrics, mistakes, dialect markers, or quirks that the input does not support.
3. **Never certify authorship.** Style patterns and detector scores cannot prove who or what wrote text. Do not return an AI probability, a human-written guarantee, or detector-evasion tactics.
4. **Diagnose in context.** A word, punctuation mark, sentence length, list, or rhetorical device is not a defect by itself. Explain the reader harm before changing it.
5. **Preserve expertise.** Natural does not mean simplistic. Keep necessary terminology, qualification, detail, and genre conventions for expert readers.
6. **Compose the locale, not an English template.** Use the source language's syntax, register, terminology, punctuation, and cultural expectations. Surface low confidence or the need for fluent review.
7. **Keep publication accountable.** A deterministic audit catches token and markup drift, not factual truth, semantic equivalence, native fluency, or publication fitness.

If the user asks to make text “undetectable,” “bypass a detector,” or look “definitely human,” state the reframe in one sentence and continue toward clarity, specificity, voice, integrity, and reader usefulness. Do not optimize against a detector.

## Choose the mode

Infer the mode and proceed. Ask only when an unknown audience, locale, source authority, or change boundary would materially alter the result and cannot be found in the supplied content or repository.

| Mode | Use when | Return |
| --- | --- | --- |
| **Diagnose** | The user asks why text feels robotic, generic, templated, translated, or AI-sounding. | Exact excerpt, quality problem, reader impact, evidence level, and smallest useful change. No authorship verdict. |
| **Rewrite** | The user asks to humanize, naturalize, deslopify, warm up, de-template, or rewrite existing content. | Clean revised content by default; add unresolved risks only when material. |
| **Publication review** | The draft is near-final or the user asks whether it is ready to publish. | Blockers, warnings, unresolved evidence, and ready copy—or a clear not-ready verdict. |

Proofreading-only, translation-only, writing from a blank page, research without a supplied draft, and AI-authorship classification are outside this skill. A rewrite may include grammar fixes, transcreation, or fact checks when they support the editorial job.

## Quick start

For an ordinary rewrite:

1. Read `references/foundations/editorial-contract.md`, `references/workflow/protected-content-ledger.md`, and `references/workflow/rewrite-passes.md`.
2. Add `references/voice/warm-casual-professional.md` for the default register.
3. Add `references/voice/multilingual-editing.md` when the content is not in the editor's strongest language or contains multiple locales.
4. Build the ledger, run the three passes, reconcile the revision, and return clean copy.

Example:

```text
Source: In our 2025 review, 12.5% of sampled pages may need another check. See [the method](https://example.com/method).
Internal ledger: 2025; 12.5%; sampled pages; “may”; https://example.com/method
Return: Our 2025 review found that 12.5% of the sampled pages may need another check. See [the method](https://example.com/method).
```

The ledger stays internal unless requested or needed to explain a blocker.

## Minimal reading sets

Choose one mode base, then add only the modifiers needed for the current phase. Keep the initial load to five references.

### Mode bases

| Mode | Read |
| --- | --- |
| **Rewrite** | `references/foundations/editorial-contract.md`, `references/workflow/protected-content-ledger.md`, `references/workflow/rewrite-passes.md` |
| **Diagnose** | `references/foundations/evidence-and-authorship.md`, `references/diagnosis/editorial-signals.md`, `references/diagnosis/non-signals.md` |
| **Publication review** | `references/workflow/publication-review.md`, `references/foundations/editorial-contract.md`, `references/workflow/protected-content-ledger.md` |

### Modifiers

1. **Default voice:** add `references/voice/warm-casual-professional.md` when no stronger house voice or supplied sample exists.
2. **Multilingual:** add `references/voice/multilingual-editing.md` for non-English, mixed-language, localized, or culturally sensitive content.
3. **People and identity:** add `references/voice/inclusive-language.md` when editing descriptions of people, communities, identities, disability, age, gender, race, ethnicity, or socioeconomic status.
4. **File format:** add `references/formats/markdown-mdx-html.md` for `.md`, `.mdx`, `.html`, frontmatter, JSX, embedded code, or repository-backed content.
5. **Production residue:** add `references/diagnosis/production-artifacts.md` for placeholders, assistant chatter, malformed citations, broken fences, or renderer mismatches.
6. **Worked model:** add `references/examples/multilingual-before-after.md` only when a concrete transformation pattern is needed.
7. **Source verification:** add `references/sources/annotated-bibliography.md` when a rule, detector claim, or external standard needs provenance.
8. **Skill verification:** use `references/testing/trigger-and-functional-tests.md` when installing, testing, or revising this skill.

## Workflow

### 1. Establish the editorial contract

Identify or infer:

- mode, source locale, target locale if adaptation is in scope, audience, knowledge level, and genre;
- reader job, document purpose, intended decision, and publication channel;
- approved facts, sources, terminology, quotations, and genuine first-hand material;
- desired voice, formality, warmth, and supplied positive or negative samples;
- format and renderer: plain text, Markdown, MDX, HTML, CMS field, email, report, or another container;
- scope boundaries for headings, metadata, links, CTA, structure, length, legal language, and SEO intent.

Use `references/foundations/editorial-contract.md`. Existing copy is evidence of intent, not automatically a quality oracle. A house guide or current approved sample outranks the default register.

### 2. Build the protected-content ledger

Record four protection classes:

| Class | Examples | Rule |
| --- | --- | --- |
| **Exact** | URLs, link destinations, code, citations, IDs, slugs, component names, HTML/JSX attributes | Preserve byte-for-byte unless a change is explicitly authorized. |
| **Value** | Names, numbers, dates, units, quotations, CTA commitments, factual propositions | Preserve the value and its referent; wording may change without semantic drift. |
| **Force** | Uncertainty, attribution, causality, comparison set, scope, limitations, negative claims | Never make a claim more certain, broader, more causal, or more favorable. |
| **Document** | Locale identity, genre, heading job, metadata purpose, search intent, reading order | Preserve the document contract even when prose is restructured. |

Follow `references/workflow/protected-content-ledger.md`. Mark contradictions or unsupported material unresolved; do not polish uncertainty into certainty.

### 3. Diagnose by evidence level

Sort every observation into one bucket:

1. **Objective production defects:** prompt residue, placeholders, malformed citation tokens, broken markup, changed protected values, or renderer mismatch.
2. **Contextual editorial signals:** vague actors, unsupported significance, generic promotion, shallow analysis, repetitive syntax, templated section shapes, empty summaries, or model-associated vocabulary clusters.
3. **Non-signals:** an isolated word, em dash, bold span, list, table, title case, formal register, correct grammar, dialect feature, or detector score.

Use `references/diagnosis/editorial-signals.md`, `references/diagnosis/non-signals.md`, and, when relevant, `references/diagnosis/production-artifacts.md`. Diagnose the text's reader-facing quality, never its author.

### 4. Rewrite in ordered passes

Run these passes in order. If a later pass changes meaning, return to the earliest affected pass.

1. **Substance and clarity**
   - Lead with what the reader needs.
   - Name concrete actors, actions, mechanisms, evidence, limits, and decisions.
   - Remove empty promotion, fake comprehensiveness, duplicate commentary, and unsupported significance.
   - Keep one stable domain term per concept.
2. **Voice, audience, and locale**
   - Match the supplied or house voice; otherwise use the warm casual-professional default.
   - Adapt tone to reader state, genre, stakes, culture, and expertise.
   - Use first person only for a verified speaker and second person only for a real reader action.
   - Compose naturally in the declared locale; do not translate syntax, tell lists, or jokes mechanically.
3. **Rhythm and surface**
   - Vary structure when meaning and cadence benefit, not to satisfy a pattern quota.
   - Simplify transitions, repair accidental repetition, and stop at the last useful sentence.
   - Keep rhetoric, fragments, lists, headings, and punctuation when they do real work.

Use `references/workflow/rewrite-passes.md` and the exact voice references selected above.

### 5. Verify integrity

Compare the revision with the ledger claim by claim and value by value. Re-read each changed sentence in its paragraph and each paragraph in its document role.

When original and revised files are available, run:

```bash
python3 {baseDir}/scripts/audit-rewrite.py path/to/original.mdx path/to/revised.mdx
```

Use `--json` for machine-readable output. The audit checks deterministic token, code, link, frontmatter, and markup inventories plus common production residue. It does not prove factual truth, semantic equivalence, style quality, native fluency, or authorship. Resolve or report every failure; review a clean result semantically.

For Markdown, MDX, or HTML, also follow `references/formats/markdown-mdx-html.md` and run the consuming repository's parser, formatter, build, or renderer when available.

### 6. Return the mode-specific result

- **Rewrite:** return clean content with no preamble by default. Add `Unresolved` only for material facts, sources, locale confidence, format risks, or approvals.
- **Diagnose:** use `Excerpt → issue → reader impact → evidence level → smallest useful change`.
- **Publication review:** separate `Blockers`, `Warnings`, `Unresolved evidence`, and `Ready copy`.

When the user requests a change ledger, group it by substance, voice/locale, surface, and protected-item verification. Do not narrate every synonym change.

## Failure behavior

| Situation | Action |
| --- | --- |
| Approved facts or source text are missing | Improve only supported material; name the exact evidence gap and block affected claims. |
| The draft and source conflict | Show the conflict, rank source authority, and preserve neither silently. |
| The user asks for invented specificity or personality | Refuse the invention inside the deliverable; use only supplied, attributable detail. |
| The user asks for detector optimization | Reframe to editorial quality and proceed without detector-facing transformations or scores. |
| A protected value must change for coherence | Stop that edit and request authority or better source evidence. |
| Locale competence is uncertain | Preserve meaning conservatively, flag confidence, and require fluent review for high-stakes publication. |
| The audit passes but meaning drifted | Treat it as failure; semantic review outranks token equality. |
| The audit flags an authorized change | Record the authorization and keep the expected difference visible. |

## Pitfalls

| Pitfall | Correction |
| --- | --- |
| Replacing “AI words” with synonyms | Fix the underlying vagueness, repetition, or unsupported claim—or keep the precise word. |
| Adding an anecdote, opinion, or mistake for warmth | Use only genuine material supplied by an accountable speaker. |
| Removing every dash, list, heading, bold span, or formal phrase | Judge function, genre, locale, and renderer rather than a tell list. |
| Making every sentence short and conversational | Match cognitive load and expertise; preserve technical precision. |
| Making every language sound like translated US English | Recompose for local syntax, register, terminology, and culture. |
| Trusting a detector or “human score” | Ignore the score as an editorial target; assess clarity, specificity, fidelity, and usefulness. |
| Declaring success because the script passes | Run semantic, locale, format, and publication review too. |

## Reference catalog

Every reference is a direct leaf. Load it only for the stated decision.

| File | Read when |
| --- | --- |
| `references/foundations/editorial-contract.md` | Establishing mode, audience, purpose, source authority, voice, scope, and stop conditions. |
| `references/foundations/evidence-and-authorship.md` | Separating editorial evidence, authorship claims, detector limits, and safe reframing. |
| `references/diagnosis/editorial-signals.md` | Diagnosing clustered, transferable quality problems without using a blacklist. |
| `references/diagnosis/non-signals.md` | Preventing false positives based on punctuation, vocabulary, dialect, format, register, or scores. |
| `references/diagnosis/production-artifacts.md` | Finding placeholders, prompt residue, malformed citations, broken markup, and renderer defects. |
| `references/workflow/protected-content-ledger.md` | Capturing exact, value, force, document, locale, and structured-content invariants. |
| `references/workflow/rewrite-passes.md` | Running substance, voice/locale, and rhythm/surface passes with regression checks. |
| `references/workflow/publication-review.md` | Deciding blockers, warnings, evidence gaps, reviewer ownership, and ready state. |
| `references/voice/warm-casual-professional.md` | Applying the default warm, natural, knowledgeable register without forced intimacy. |
| `references/voice/multilingual-editing.md` | Editing non-English, mixed-language, localized, low-resource, or culturally sensitive content. |
| `references/voice/inclusive-language.md` | Editing references to people and identity accurately, specifically, and without imposed labels. |
| `references/formats/markdown-mdx-html.md` | Preserving Markdown, frontmatter, JSX, ESM, HTML tags/attributes, code, links, and language metadata. |
| `references/examples/multilingual-before-after.md` | Studying ledger-backed English, Turkish, Spanish, and mixed-format transformations. |
| `references/sources/annotated-bibliography.md` | Verifying research authority, dates, quotes, scope, conflicts, and source-derived rules. |
| `references/testing/trigger-and-functional-tests.md` | Testing activation boundaries, primary workflows, failure cases, and audit-helper fixtures. |

## Completion check

- Every protected item is preserved or explicitly authorized.
- Every changed claim keeps its attribution, uncertainty, scope, and causal strength.
- No fact, source, experience, emotion, metric, quote, identity label, or dialect feature was invented.
- The locale reads naturally at the confidence level claimed; high-risk gaps have reviewer ownership.
- Structure, links, code, metadata, CTA, and renderer contracts remain intact.
- Diagnostics describe reader-facing defects, never inferred authorship.
- The result is useful and specific without forced casualness, fake imperfection, or detector theater.
