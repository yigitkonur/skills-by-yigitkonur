# Editorial Contract

Use this reference to establish what the document must do, who it serves, and which constraints outrank stylistic preferences.

## Start with the reader's job

Natural writing is contextual. A sentence can be excellent in a field manual and wrong in a welcome email. Before rewriting, capture the smallest useful contract:

| Dimension | Question | If unknown |
| --- | --- | --- |
| Reader | Who will use this, and what do they already know? | Infer from the channel and terminology; mark the inference. |
| Purpose | What should the reader understand, decide, or do? | Use the document's CTA, title, or surrounding page. |
| Genre | Is this documentation, analysis, marketing, policy, email, or something else? | Preserve the current genre unless the user requests a change. |
| Locale | Which language variety, register, and cultural context apply? | Preserve the source locale; do not silently normalize it to US English. |
| Authority | Which facts and source materials are approved? | Treat unsupported claims as unresolved, not raw material to embellish. |
| Voice | Is there a house guide or approved sample? | Use the warm casual-professional default only when no stronger guide exists. |
| Format | Plain text, Markdown, MDX, HTML, CMS field, or another container? | Inspect the file extension and syntax before editing. |
| Scope | May headings, links, metadata, CTA, order, and length change? | Protect them until authorized. |

## Rank competing instructions

When instructions conflict, use this order:

1. Verified facts, quotations, legal commitments, and explicit user constraints.
2. Repository or publication contracts, including schema and renderer rules.
3. Approved voice guide and current representative samples.
4. Document-specific audience and purpose.
5. This skill's default voice.
6. Personal taste.

An old published page is evidence of intent, but not automatically a voice oracle. Prefer a current guide or a sample the user explicitly identifies as successful.

## Define the allowed transformation

Choose the narrowest transformation that meets the request:

| Transformation | Allowed | Not implied |
| --- | --- | --- |
| Copy edit | Clarity, grammar, flow, local repetition | New arguments or research |
| Structural edit | Reordering, new headings, merging or splitting sections | New factual substance |
| Transcreation | Recompose for the target locale and reader | Literal translation or cultural invention |
| Publication review | Identify blockers and produce ready copy where supported | Legal, medical, or factual certification |
| Format-preserving rewrite | Change prose inside structured files | Schema, component, or destination changes |

If the user says “keep the structure,” preserve heading count, order, component placement, and field boundaries. If the user says “content only,” do not modify layout code or structured payloads.

## Work from positive evidence

Useful evidence includes:

- a house style guide;
- two or three approved samples from the same channel;
- reader research or a clear audience description;
- terminology lists and source material;
- explicit examples of phrases the organization uses or avoids;
- the document's actual rendering context.

A blacklist of supposed “AI words” is not a voice guide. It cannot explain when a term is precise, necessary, conventional, or wrong for a particular reader.

## Set voice coordinates

Describe voice with operational coordinates, not adjectives alone:

| Coordinate | Low end | High end | Decision signal |
| --- | --- | --- | --- |
| Formality | Conversational | Ceremonial | Stakes, relationship, genre |
| Warmth | Neutral | Personally supportive | Reader state and channel |
| Density | Guided | Expert-compressed | Reader knowledge and task urgency |
| Assertiveness | Exploratory | Directive | Evidence strength and required action |
| Personality | Institutional | Distinctive | Accountable speaker and brand permission |

“Warm but professional” often means moderate warmth, direct sentences, contractions where natural, concrete help, and no forced intimacy. It does not mean jokes, slang, or first-person stories.

## Stop conditions

Pause the affected part of the rewrite when:

- two approved sources contradict each other;
- a claim cannot be preserved without becoming broader or more certain;
- the target locale is unclear and the variants would materially differ;
- a legal, safety, pricing, or policy commitment appears unsupported;
- a structured field's editing boundary is unknown;
- the requested tone depends on an invented speaker identity.

Continue with unaffected material. Name the exact gap rather than turning one uncertainty into a full-document block.

## Contract record

Keep a compact internal note:

```text
Mode: Rewrite
Reader: Technical buyer comparing two approaches
Purpose: Explain tradeoffs and support a decision
Locale: Turkish, professional conversational register
Authority: Supplied report and linked documentation
Voice: Direct, knowledgeable, warm; no first-person experience
Format: MDX; preserve frontmatter, JSX, links, and code
Scope: Headings may tighten; CTA and claims may not change
```

Do not include this note in the final response unless the user requests a rationale, the contract required a consequential inference, or a blocker remains.

## Common failures

| Failure | Correction |
| --- | --- |
| “Make it human” becomes permission to invent a persona | Separate voice from biography; use supported detail only. |
| A marketing page is rewritten like a chat message | Re-anchor to channel, stakes, and reader decision. |
| Expert terminology is removed as “too formal” | Keep terms that carry domain meaning; explain them only when the reader needs it. |
| A target language inherits English syntax and section shapes | Recompose for the locale instead of translating sentence by sentence. |
| Every ambiguity becomes a clarifying question | Infer reversible details; ask only when the answer changes facts, locale, authority, or scope. |

## Completion check

- Reader, purpose, genre, locale, authority, voice, format, and scope are known or explicitly inferred.
- Higher-authority constraints outrank the default style.
- The allowed transformation is no broader than the request.
- Stop conditions have owners instead of being silently polished away.
- The final prose can be judged against reader usefulness, not an abstract “human” score.
