# Multilingual Editing

Use this reference for non-English, mixed-language, localized, transcreated, low-resource, or culturally sensitive content.

## First principle

Edit the target language as a language in its own right. Do not use English syntax, punctuation, rhetoric, paragraph templates, or informality as a universal definition of natural writing.

## Establish the locale

Language code alone is not enough. Record:

- language and regional variety;
- audience location and community;
- formal or informal address;
- channel and genre;
- domain terminology and approved glossary;
- source and target languages if adaptation is involved;
- script, direction, and mixed-language requirements;
- editor confidence and required reviewer expertise.

Examples: `pt-BR` and `pt-PT`, `es-MX` and `es-ES`, or formal and informal Turkish may require different vocabulary, address, punctuation, and expectations.

## Meaning before naturalness

Resolve the source proposition before recomposing:

1. Identify facts, relationships, uncertainty, attribution, and purpose.
2. Separate fixed terminology and names from adaptable prose.
3. Note idioms, metaphors, humor, or cultural references that cannot transfer literally.
4. Recompose the idea in target-language syntax and register.
5. Compare the target version with the protected-content ledger.

Word-for-word fidelity can produce meaning drift. Free adaptation can invent meaning. The ledger controls both risks.

## Locale dimensions

| Dimension | Questions |
| --- | --- |
| Syntax | Does clause order follow target-language information flow? |
| Register | Do pronouns, honorifics, and verb forms match the relationship? |
| Terminology | Is the term used by practitioners in this locale and domain? |
| Punctuation | Are quotation, decimal, date, spacing, and capitalization conventions local? |
| Rhetoric | Does the culture prefer direct requests, contextual setup, or another pattern here? |
| Examples | Are names, units, scenarios, and references meaningful without fabrication? |
| Accessibility | Are plain-language and reading-level choices appropriate in this language? |
| Internationalization | Are `lang`, `dir`, bidi, encoding, and font behavior preserved? |

## Turkish example

Translated-template feel:

> Günümüzün hızla gelişen dijital dünyasında, işletmelerin başarıya ulaşmak için yenilikçi çözümleri benimsemeleri her zamankinden daha önemlidir.

Natural revision when the supported point is workflow speed:

> Ekipler, onaylanan değişiklikleri sistemler arasında elle taşımak yerine inceleme ve yayınlama adımlarını tek akışta birleştirebilir.

The revision removes generic scene-setting and states the actual action. It does not add slang, spelling variation, or a fictional speaker.

## Spanish example

Literal source-shaped version:

> En orden para completar el proceso, los usuarios deben primero realizar la verificación de su dirección de correo electrónico.

Natural professional version:

> Para completar el proceso, verifica primero tu correo electrónico.

This direct form is appropriate only if the product consistently uses informal singular address. A formal or regional contract may require another form.

## Mixed-language content

For code, product names, borrowed terms, or quotations:

- preserve protected code and identifiers exactly;
- use the approved localized product term when one exists;
- do not translate a trademark or UI label unless the actual interface does;
- mark local language changes with `lang` in HTML when needed;
- isolate bidirectional segments correctly;
- keep glossary choices stable across the document;
- avoid adding parenthetical translations to every borrowed term unless readers need them.

## Low-resource and non-Latin languages

Multilingual quality evaluation requires language-specific calibration. Broad model confidence is not enough, especially for low-resource, morphologically rich, non-Latin, or bidirectional languages.

Use a conservative policy:

- preserve source meaning and structure more closely at low confidence;
- avoid dialect imitation or colloquial invention;
- flag uncertain terminology explicitly;
- seek a fluent target-locale reviewer for publication;
- require domain expertise for legal, medical, financial, safety, or policy content;
- test actual fonts, line breaking, input, and rendering where relevant.

## Back-translation

Back-translation can reveal missing facts, reversed relations, or changed force. It cannot prove:

- natural local phrasing;
- cultural appropriateness;
- terminology accepted by practitioners;
- inclusive or respectful identity language;
- publication readiness.

Use it as a diagnostic probe, not a final quality gate.

## Fluent-review gate

Require fluent review when any of these apply:

- the editor's confidence is moderate or low;
- the content affects rights, safety, health, finance, law, or public policy;
- dialect or community identity matters;
- humor, idiom, persuasion, or emotional support carries the message;
- the target language is low-resource for the available tools;
- a source and target term have no one-to-one correspondence;
- the content will be highly visible or difficult to correct.

Name the required reviewer: fluent locale editor, subject expert, legal reviewer, or community representative.

## Common failures

| Failure | Correction |
| --- | --- |
| Translating sentence by sentence | Resolve meaning, then recompose clauses and paragraphs. |
| Making every locale sound like casual US English | Follow local register and relationship conventions. |
| Treating dialect as error | Confirm the declared variety and audience. |
| Translating code, product names, or UI labels | Preserve the actual system's terms. |
| Claiming native quality from back-translation | Use fluent target-locale review. |

## Completion check

- Locale includes variety, register, audience, and channel.
- Target prose follows local syntax and rhetorical expectations.
- Protected facts, force, terms, code, and internationalization metadata remain intact.
- Confidence is explicit and proportional.
- High-stakes or low-confidence content has a qualified review owner.
