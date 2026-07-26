# Non-Signals

Use this reference to avoid false diagnoses based on isolated words, punctuation, formatting, dialect, fluency, or detector scores.

## Default rule

No isolated feature proves poor writing or AI authorship. A feature becomes an editorial issue only when its use harms meaning, flow, accessibility, credibility, genre fit, locale fit, or renderer behavior.

## Surface features that are not defects by themselves

| Feature | Legitimate uses | Investigate only when |
| --- | --- | --- |
| Em dash | Interruption, apposition, emphasis | Nesting or frequency obscures the main clause. |
| Colon | Explanation, list, amplification | The promised relationship is missing. |
| Semicolon | Closely related independent clauses | It conflicts with house style or overloads the sentence. |
| Three-item list | Genuine parallel grouping | Items are padded, overlapping, or mechanically repeated. |
| Bold text | Scanning and emphasis | Nearly everything is emphasized or markup is broken. |
| Headings | Navigation and hierarchy | Every paragraph gets a heading or hierarchy is incoherent. |
| Table | Exact comparisons and mappings | Cells contain essays or accessibility suffers. |
| Formal register | Policy, research, legal, executive contexts | It hides action, exceeds the audience, or conflicts with channel. |
| Contractions | Conversational professional voice | Legal meaning, localization, or house style requires expansion. |
| Long sentence | Necessary qualification or relationship | Working memory collapses before the main claim resolves. |
| Short sentence | Emphasis, instruction, rhythm | A whole document becomes choppy or simplistic. |

## Vocabulary is contextual

Words sometimes associated with model output may be precise domain language:

- “robust” is appropriate when describing statistical robustness or fault tolerance with a defined condition;
- “landscape” may be the accepted term for a competitive or regulatory overview;
- “delve” can be ordinary in some regions and genres;
- “leverage” has a specific meaning in finance and mechanics;
- “seamless” may be an approved product claim if the experience and evidence support it.

The question is not “Is this on a list?” It is “What exact meaning does it carry here, and is that meaning earned?”

## Correctness is not suspicious

Do not damage text because it is:

- grammatically consistent;
- well organized;
- correctly punctuated;
- free of spelling errors;
- balanced in tone;
- explicit about structure;
- concise or comprehensive;
- fluent in a second language.

Humans use editors, templates, style guides, accessibility tools, and professional conventions. Quality is not evidence of automation.

## Dialect and multilingual variation

The following are not defects unless the declared locale requires something else:

- British, American, Canadian, Australian, Indian, Nigerian, Singaporean, or other English conventions;
- regional vocabulary and punctuation;
- code-switching appropriate to audience and channel;
- non-native but intelligible constructions;
- gendered or ungendered grammatical forms required by the language;
- local politeness, honorific, and pronoun systems;
- deliberate retention of source terms where translation would lose precision.

Never “correct” a valid language variety into the editor's preferred one without a locale contract.

## Genre conventions

Features that look repetitive in one genre may be required in another:

| Genre | Convention to preserve when useful |
| --- | --- |
| API documentation | Repeated imperative steps and stable terminology |
| Safety instruction | Explicit warnings and controlled redundancy |
| Academic writing | Qualification, attribution, and domain terminology |
| Policy | Defined terms, scope clauses, and consistent formulae |
| SEO page | Search intent and scannable headings without keyword stuffing |
| Legal copy | Exact force, defined references, and conservative wording |
| Support article | Repeated UI labels and predictable step structure |

Natural writing is not synonymous with conversational writing.

## Detector scores are non-signals for editing

A detector score may be recorded if the user supplies it, but it must not determine edits. Scores vary with model, threshold, language, length, genre, and post-processing. A lower score after rewriting does not establish improved quality, and a higher score does not establish worse quality.

Use reader-centered measures instead:

- Can the reader identify the actor and action?
- Are claims supported and correctly qualified?
- Does each section advance the purpose?
- Is terminology stable and appropriate?
- Does the locale sound natural to a qualified reader?
- Does the document parse and render correctly?

## Paired examples

Keep:

> The service retries the request three times—once immediately, then twice with backoff—before returning `429`.

The dashes clarify a bounded sequence and code is exact.

Change:

> The service—which is robust and, importantly, scalable—retries the request—which may fail—for improved outcomes.

The nested interruptions hide the actual behavior and replace it with evaluation.

Keep:

> Moreover, the proof applies only when the function is continuous.

Here “moreover” adds a logically related condition in a formal mathematical discussion.

Change:

> Moreover, our platform is fast. Furthermore, it is flexible. In addition, it is easy to use.

The transitions mask three unsupported promotional claims.

## Bias check before changing a feature

Ask:

1. Is this valid in the declared language variety?
2. Is it conventional for the genre?
3. Does it carry necessary technical or legal meaning?
4. Is the concern based on actual reader harm or a stereotype about AI writing?
5. Would I make the same edit if trusted provenance showed a human wrote it?

If the concern fails questions 4 or 5, do not edit for that reason.

## Common failures

| Failure | Correction |
| --- | --- |
| Removing every em dash | Repair only dashes that obscure structure or violate style. |
| Replacing every flagged word | Diagnose the claim and context first. |
| Adding typos or unevenness | Preserve correctness; improve accountable voice and specificity. |
| Penalizing formal multilingual prose | Validate locale and genre with qualified review. |
| Treating templates as inherently bad | Keep templates that help readers; remove empty or mismatched repetition. |

## Completion check

- No isolated feature is called proof of authorship.
- Valid dialect, genre, and domain conventions remain intact.
- Changes are justified by reader impact or document contracts.
- Detector scores do not appear in the rewrite objective.
- Correctness is preserved rather than intentionally degraded.
