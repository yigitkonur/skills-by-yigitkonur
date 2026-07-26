# Protected-Content Ledger

Use this reference to inventory what must survive a rewrite exactly, semantically, rhetorically, and structurally.

## Why the ledger comes first

Fluent rewrites can be wrong. They often drift by changing a number's referent, strengthening uncertainty, dropping attribution, altering a link, or “cleaning up” structured syntax. A protected-content ledger makes those risks explicit before prose changes begin.

The ledger may remain internal. Its purpose is control, not extra output.

## Four protection classes

| Class | Protects | Examples |
| --- | --- | --- |
| Exact | Byte-sensitive or identity-sensitive material | URLs, code, IDs, slugs, link destinations, tag and attribute names |
| Value | Facts whose wording may change but value and referent may not | Names, dates, numbers, units, quotations, pricing, product behavior |
| Force | The strength and boundary of a claim | “may,” attribution, causality, comparison set, exclusions, limitations |
| Document | The role and processing contract of the file | Locale, genre, frontmatter purpose, heading job, CTA, reading order |

Record authorization separately. An approved change is not a preservation failure, but it must remain visible during reconciliation.

## Exact inventory

Capture exact items before editing:

- absolute and relative URLs;
- Markdown link/image destinations, reference-definition labels, shortcut/collapsed identifiers, and footnote identifiers;
- email addresses, handles, and phone numbers;
- inline, fenced, and indented code blocks, including fence language;
- component, variable, API, command, file, and package names;
- HTML and JSX tag names, attribute names, protected values, comments, entities, and raw-text bodies;
- frontmatter keys, slugs, IDs, enum values, and required field types;
- MDX expressions/ESM and template directives such as `{{…}}`, `{%…%}`, and `${…}`;
- citation identifiers, footnote labels, and anchors;
- `lang`, `dir`, bidi isolation, and locale routing markers.

Visible link labels may change when allowed. Destinations stay exact unless the user authorizes a link change.

## Value inventory

For each value, record its referent:

```text
12.5% → share of sampled pages, not all pages
2025 → review year, not publication year
€49/month → starter plan, billed monthly
three retries → total attempts after the initial request? verify wording
```

A script can confirm that `12.5%` remains present. Only semantic review can confirm that it still describes sampled pages.

Include:

- quantities, percentages, currency, ranges, thresholds, and units;
- calendar and relative dates;
- proper names, titles, organizations, and places;
- quoted material and its speaker;
- feature capabilities and limitations;
- CTA commitments, eligibility, timing, and conditions;
- comparisons and their baselines.

Record locale-specific spelling, placement, digits, separators, and spacing as part of the value. `€49`, `49 EUR`, `100 zł`, `₺1.250,50`, and `١٢٫٥ د.إ` are not interchangeable surface variants without locale and product authority.

For exact phrases the generic audit cannot infer—legal wording, approved quotations, product names, UI labels, or defined terms—add repeatable `--protect` literals or a reviewed `--protect-from` file. Treat the supplied list as project evidence, not as permission to skip semantic reconciliation.

## Force inventory

Small words can carry the document's integrity:

| Source force | Drift to prevent |
| --- | --- |
| “may reduce” | “reduces” |
| “was associated with” | “caused” |
| “in our sample” | “in all cases” |
| “the report states” | narrator-owned fact |
| “one factor” | “the reason” |
| “up to 20%” | “20%” |
| “not shown” | “does not exist” |

Record negation, modality, attribution, causal language, scope, exceptions, comparison sets, and evidence status. Reconcile them sentence by sentence.

## Document inventory

Protect document-level intent:

- language and locale variety;
- target reader and expertise;
- page or section purpose;
- search intent and canonical topic;
- heading hierarchy and section jobs;
- metadata semantics and field boundaries;
- component order and reading order;
- CTA destination and promise;
- required boilerplate or legal text;
- content that must remain unchanged by explicit instruction.

“Make it warmer” does not authorize changing a policy, schema, or CTA.

## Structured ledger template

```markdown
### Exact
- `https://example.com/method` — Markdown destination
- `RetryPolicy` — component name
- `lang="tr"` — locale attribute

### Value
- `12.5%` — sampled pages requiring review
- `2025` — review period
- “Ayşe Yılmaz” — quoted analyst

### Force
- “may” — uncertainty must remain
- result is correlation, not causation
- applies only to authenticated requests

### Document
- Turkish professional register
- keep frontmatter keys and JSX order
- CTA remains “Raporu indir” and keeps destination

### Authorized changes
- heading may be shortened
```

## Reconciliation method

After each rewrite pass:

1. Compare exact inventories mechanically where possible.
2. Locate every value in the revision and confirm its referent.
3. Compare every changed claim's force with the source.
4. Confirm the document still performs the same job.
5. Record authorized differences and unresolved drift.
6. Re-run the repository's parser or renderer for structured files.

For a partial rewrite, compare equivalent scopes or reconstruct the complete revised document before running whole-file reconciliation. For a long document edited in chunks, run both section-level checks and a final full-document check.

Do not postpone all reconciliation until the end of a large document. Check section by section to keep drift local and recoverable.

## Contradictions

If the draft says `12%` and its linked source says `21%`:

- do not choose the more plausible value;
- record both and their sources;
- rank authority if the repository defines it;
- flag the conflict for resolution;
- rewrite surrounding prose without hiding the discrepancy.

The ledger is allowed to contain unresolved items. That is more honest than a clean but invented result.

## Common failures

| Failure | Correction |
| --- | --- |
| Inventorying values without referents | Record what each number, date, or name describes. |
| Protecting facts but not uncertainty | Add a force section for modality, attribution, scope, and causality. |
| Treating frontmatter as ordinary prose | Protect keys, types, and required values; edit only authorized strings. |
| Assuming unchanged tokens mean unchanged meaning | Re-read the sentence and paragraph role. |
| Hiding authorized changes from the audit | Record the authorization and expected difference. |

## Completion check

- Exact, value, force, and document protections are all represented.
- Numbers and dates retain their referents, not just their glyphs.
- Attribution, uncertainty, negation, scope, and causality do not drift.
- Structured syntax and locale metadata remain intact.
- Every difference is either reconciled, explicitly authorized, or unresolved with an owner.
