# Edge-Case Playbook

Use this reference when a rewrite is partial, generated, unusually long, high-stakes, template-heavy, accessibility-sensitive, or difficult to validate with the bundled deterministic audit.

## First decision: what is the editable boundary?

| Situation | Editable boundary | Required protection | Proof after editing |
| --- | --- | --- | --- |
| One paragraph in a plain document | The named paragraph | Nearby facts, force, terminology, and section job | Re-read in full-document context |
| One field in frontmatter or a CMS record | Only the authorized copy field | Keys, types, sibling fields, IDs, locale, and delimiters | Actual schema/frontmatter parser |
| Visible copy in MDX or HTML | Confirmed text nodes and approved copy attributes | Components, expressions, ESM, tags, non-copy attributes, comments, raw-text bodies | Native compiler/build plus render |
| Generated region | Canonical source, never the generated output | Generator inputs, ownership marker, generated boundaries | Regenerate and check freshness/diff |
| Template-backed page | Only literal reader-facing copy | `{{…}}`, `{%…%}`, `${…}`, filters, variables, branches, and whitespace controls | Template engine with representative data |
| Legal, medical, financial, safety, or policy copy | Wording authorized by the accountable reviewer | Defined terms, conditions, negation, scope, modality, citations, version/date | Qualified domain approval |

If the boundary is unclear, protect the ambiguous region. Do not infer that prose-looking text is editable merely because it renders as words.

## Partial rewrites

A full original file and a revised fragment are not comparable inputs. Choose one of these approaches:

1. Compare the complete original and complete revised document after reinserting the fragment.
2. Extract the same bounded region from both versions and compare those two regions.
3. If neither is possible, use an explicit ledger and report that whole-document drift was not checked.

Include one paragraph or structural boundary on either side when meaning depends on context. Recheck headings, references, list numbering, transitions, repeated definitions, and CTA flow in the complete document.

For several fragments, reconcile after every fragment and then run one whole-document pass. Chunk-level green results do not detect omissions between chunks.

## Exact project invariants

The built-in inventory cannot infer every product name, UI label, legal phrase, quotation, or domain term. Add exact literals:

```bash
python3 {baseDir}/scripts/audit-rewrite.py \
  --protect "Exact Product Name" \
  --protect "Offer is void where prohibited." \
  original.mdx revised.mdx
```

For a reusable newline-delimited list:

```text
# Lines beginning with # and blank lines are ignored.
Exact Product Name
Offer is void where prohibited.
Settings > Billing
```

```bash
python3 {baseDir}/scripts/audit-rewrite.py \
  --protect-from protected-literals.txt \
  --json original.mdx revised.mdx
```

Both options are repeatable and may be combined. Duplicate inputs are deduplicated, but repeated occurrences inside the document are counted. A blank literal, a comments-only protection file, an unreadable file, or a literal absent from the original is a usage error with exit code `2`. Use `--protect` rather than a file for a literal that intentionally begins with `#`.

Exact matching is Unicode- and whitespace-sensitive. Non-breaking space, narrow non-breaking space, composed and decomposed accents, smart punctuation, and line endings may look alike but differ. Do not normalize them silently; decide whether the difference is authorized and test the consuming system.

## Markdown and dialect extensions

Protect more than inline links:

- reference-definition labels and destinations;
- explicit, collapsed, and shortcut reference identifiers;
- footnote identifiers and their definitions;
- fenced and indented code, including prose-looking examples;
- relative destinations with nested parentheses;
- raw HTML, template directives, and extension syntax;
- heading text when generated anchors are part of the public contract.

Reference titles, link labels, image alt text, and footnote prose may be editable copy. Their identifiers and destinations remain structural. GitHub Flavored Markdown, footnote plugins, custom directives, and CMS shortcodes exceed CommonMark; use the exact parser configured by the repository.

## Frontmatter and data-shaped copy

The helper allows common copy fields such as `title`, `description`, `summary`, `excerpt`, and common SEO/meta variants to change. It protects other scalar and sequence content conservatively.

Still verify with a YAML/frontmatter parser because the helper does not fully resolve:

- anchors, aliases, tags, directives, duplicate keys, merge keys, or multi-document streams;
- implicit types and schema-specific enums;
- flow collections or complex keys in every legal form;
- whether a named copy field is actually copy in this repository;
- whether a rewritten colon, hash, quote, or line break changes scalar parsing.

For TOML, JSON, JSON5, or another metadata format, treat the helper as plain-text support only and use that format's parser.

## MDX, JSX, HTML, and templates

The helper separately inventories common MDX brace expressions and ESM, template directives, HTML comments and entities, and `script`, `style`, and `textarea` bodies. This avoids treating CSS braces or JSON-LD as editable prose.

Mixed syntaxes remain the highest-risk case:

- a JSX prop can contain nested JavaScript, a template directive, or serialized data;
- `<script>` can contain a string that resembles `</script>`;
- HTML parsing rules can repair malformed source into an unexpected DOM;
- a sanitizer can remove valid-looking elements or attributes;
- template whitespace controls can change visible spacing;
- component children may be data rather than reader-facing copy.

Preserve syntax first, then run the native MDX compiler, template renderer, HTML validator, sanitizer path, or application build. Inspect the resulting DOM or rendered page when the publication claim depends on it.

## Accessibility copy

`alt`, `title`, `placeholder`, `aria-label`, and `aria-description` can contain editable copy, but authorization to edit them is not proof that the result is accessible.

Before changing an accessibility string:

1. Identify the element's role and the accessible-name source.
2. Check whether visible text already supplies the name.
3. Preserve references such as `aria-labelledby`, `aria-describedby`, `for`, IDs, and target relationships exactly.
4. Keep required UI labels consistent with the actual interface and locale.
5. Test the accessibility tree or the repository's accessibility checks.

Do not “warm up” error messages, consent text, or instructions until clarity, action, and consequence remain unambiguous.

## Locale-sensitive values

Currency and units can appear before or after a number, use a symbol or ISO code, and contain ordinary, non-breaking, or narrow non-breaking spacing. Decimal and grouping marks vary by locale and script.

Protect the full written form and its referent:

```text
€49
49 EUR
100 zł
₺1.250,50
١٢٫٥ د.إ
```

Do not normalize punctuation, spacing, symbol placement, digits, currency, or units toward an English convention. The helper recognizes common forms, not the entire CLDR data model. Use the product's locale formatter and render with the target locale for publication proof.

## Long documents and constrained context

1. Build a document-level ledger before chunking.
2. Split on stable semantic boundaries, not arbitrary token counts.
3. Carry names, terms, force, locale, voice, and cross-reference state into every chunk.
4. Keep a running list of introduced terminology and unresolved evidence.
5. Reassemble without summarizing omitted sections.
6. Run the deterministic audit on the full files.
7. Search for duplicated transitions, dropped definitions, broken references, heading drift, and inconsistent CTA language.
8. Run the native parser/build and a whole-document publication review.

If context is too small for full reconciliation, stop with an explicit incomplete state. Do not call independent chunk quality whole-document quality.

## Generated and vendored content

When markers, repository instructions, or build files identify generated content:

- find the canonical source and generator;
- edit the source only;
- regenerate through the documented command;
- compare the generated diff with the expected scope;
- run freshness or reproducibility checks;
- never hand-correct generated output to make the audit pass.

For vendored or upstream-controlled content, request authority before rewriting. Local style preference does not override ownership or updateability.

## High-stakes language

The default casual-professional register yields to legal precision, clinical clarity, financial disclosure, safety instructions, policy authority, and crisis communication.

Protect exact terms when their wording has approved meaning. Track every modal (`must`, `may`, `should`), negation, condition, exception, jurisdiction, effective date, actor, and source. A warmer sentence that changes an obligation or risk boundary is a failure even if every number and URL survives.

Require an accountable reviewer. The skill and helper can prepare reviewable copy; neither can grant legal, medical, financial, safety, or policy approval.

## Audit outcomes

| Outcome | Meaning | Next action |
| --- | --- | --- |
| Exit `0`, `pass: true` | No inventoried mismatch or newly introduced artifact | Complete semantic, locale, native-format, and publication review |
| Exit `1`, `pass: false` | Exact inventory changed or a new artifact appeared | Restore, authorize, or explain every difference; rerun |
| Exit `2` | Input, file, or protected-literal usage is invalid | Correct the invocation; no editorial conclusion is available |
| Warning only | Confidence is low because input is empty, inventory is sparse, revision is empty, or size changed sharply | Inspect scope and content; warnings are not proof or failure by themselves |
| Existing artifact | The original already contained the same residue | Report separately; do not call it newly introduced or silently bless it |

An authorized difference should remain visible in the report or change ledger. Do not weaken a category globally to accommodate one expected change.

## What the helper cannot prove

The helper uses conservative inventories, not complete ASTs. It may miss a legal syntax form, and multiset equality does not prove nesting, order, reference correctness, semantic equivalence, accessibility, factual truth, or rendered behavior. A pass also says nothing about authorship or detector outcomes.

If the native parser is unavailable:

1. run the deterministic audit;
2. manually inspect the structured diff;
3. state exactly which parser/build/render proof is missing;
4. avoid a ready-to-publish claim for structured or high-stakes content;
5. hand off the command and expected evidence to the owner who can run it.

## Recovery checklist

- Compare equivalent scopes.
- Protect project-specific literals explicitly.
- Keep template, code, generated, and raw-text regions out of prose editing.
- Preserve locale-sensitive values byte-for-byte unless authorized.
- Treat warnings as review prompts, not scores.
- Run the native parser/build for every structured format.
- Require fluent and domain review at the stakes actually present.
- Report the exact unverified rung instead of converting uncertainty into confidence.
