# Production Artifacts

Use this reference to find objective residue from drafting, prompting, content generation, copying, or rendering before publication.

## What makes an artifact objective

An objective production artifact is observable without guessing authorship. It is broken, unresolved, unintended for readers, or incompatible with the target renderer.

Examples include:

- unresolved placeholders such as `TODO`, `TBD`, `[insert source]`, or `{{company_name}}`;
- assistant chatter such as “Here is the revised version” inside publishable copy, including equivalent preambles in the document's language;
- prompt instructions or role text embedded in the output;
- malformed citation tokens such as `[1]` with no reference or `cite...` residue;
- broken Markdown fences, links, tags, entities, or frontmatter;
- copied navigation, cookie notices, or search snippets that do not belong to the document;
- comments or draft annotations exposed to readers;
- mixed renderer syntax, such as JSX in a Markdown-only pipeline.
- unclosed fences, comments, raw-text elements, frontmatter, or template directives introduced by the rewrite.

## Detection order

1. Identify the intended renderer and publication surface.
2. Scan for unresolved production tokens.
3. Parse structured regions with the repository's real tools when available.
4. Compare source and revision for changed protected items.
5. Render or build the narrowest affected document.
6. Review the visible output, not only source text.

The bundled audit helper detects common residue conservatively. A clean scan does not prove the file renders.

## Placeholder families

Inspect case-insensitively for context-dependent forms:

```text
TODO
TBD
FIXME
XXX
[insert ...]
[add ... here]
<placeholder>
{{variable}}
${VARIABLE}
lorem ipsum
example.com when not intentional
```

Do not blindly delete matches. `TODO` may be a documented code symbol; template braces may be required runtime syntax. Confirm whether the token belongs to the publication contract. In template-backed files, directive preservation belongs in the protected inventory and is not automatically a residue finding.

## Assistant and prompt residue

Common patterns include:

- “Certainly,” “Of course,” or “I hope this helps” before or after the actual deliverable;
- “Here is a more human version” as a publishable heading;
- instructions such as “Maintain a professional tone” left in body copy;
- analysis labels such as “Draft,” “Rationale,” or “Suggested CTA” accidentally pasted into final content;
- meta-claims such as “This paragraph avoids AI-sounding language.”

Search in the source language and publication context, not only English. Equivalent residue includes localized “here is the rewritten version” preambles and model-role disclaimers such as Turkish “bir yapay zekâ dil modeli olarak,” Spanish “como modelo de lenguaje de IA,” French “en tant que modèle de langage d’IA,” German “als KI-Sprachmodell,” and comparable forms. These phrases are still contextual: an article quoting or analyzing one is not automatically defective.

Compare source and revision. Newly introduced residue is a rewrite failure. Residue already present in the source remains reportable debt, but it must not be misrepresented as newly introduced by the editor.

These are defects when the channel expects only the document. They may be legitimate in an editorial report, so interpret them in context.

## Citation residue

Check for:

- numeric markers without a bibliography;
- bibliography entries never cited;
- copied search-result snippets presented as sources;
- citation syntax from another tool or renderer;
- links whose visible claim exceeds the linked source;
- placeholder domains, invented DOIs, or incomplete publication details;
- footnote definitions whose identifiers changed during editing.

Do not “repair” a citation by inventing metadata. Retain the claim as unresolved until a real source is available.

## Markup defects

| Format | Typical artifacts | Verification |
| --- | --- | --- |
| Markdown | Unclosed fences, broken destinations, skipped heading levels | CommonMark-compatible parser and link check |
| MDX | Unbalanced JSX, brace errors, invalid ESM, changed expressions, prose interpreted as JSX | Project's MDX compiler or build |
| HTML | Unclosed comments/tags/raw-text bodies, changed entities, invalid nesting, duplicated IDs, missing `lang` | HTML validator plus browser render |
| Frontmatter | Duplicate keys, changed key types, broken delimiters | Actual YAML/frontmatter parser |
| Templates | Unclosed or changed directives, filters, variables, branches, or whitespace controls | Actual template engine with representative data |
| CMS rich text | Unsupported nodes, missing required fields, leaked editor comments | CMS validation and preview |

## Renderer mismatch

A file can be syntactically plausible and still target the wrong system:

- GitHub-flavored tables sent to a strict CommonMark renderer;
- raw HTML stripped by a sanitizer;
- MDX components unavailable in the consuming project;
- template braces interpreted by a static-site engine;
- smart punctuation changing command or code examples;
- `dir`, `lang`, or bidi isolation removed from multilingual HTML.

Preserve the existing renderer contract and run its native check.

## Safe repair behavior

| Artifact | Repair |
| --- | --- |
| Clearly unintended preamble | Remove it from ready copy. |
| Placeholder with known approved value | Insert the approved value and record the source. |
| Placeholder without value | Block the affected sentence or retain a visible editorial marker outside ready copy. |
| Broken citation | Restore from source history or request the source; never fabricate. |
| Broken markup caused by rewrite | Restore exact protected syntax, then re-run parser. |
| Pre-existing renderer defect | Report separately unless the user authorized broader repair. |

## Example review

Source fragment:

```md
## Results

Here is a polished version:

The rollout improved conversion by [insert percentage]. citeturn0search1
```

Publication review:

```text
Blocker: [insert percentage] has no approved value.
Blocker: the citation token is not valid for this renderer and has no recoverable source metadata.
Artifact: “Here is a polished version” is assistant chatter, not article content.
Ready action: remove the chatter; hold the claim until the metric and source are supplied.
```

## Common failures

| Failure | Correction |
| --- | --- |
| Deleting every placeholder-like token | Distinguish content residue from required code and template syntax. |
| Converting a broken citation into a plausible link | Recover an actual source or block the claim. |
| Trusting a regex as parser proof | Run the consuming parser, build, or preview. |
| Fixing prose but leaving assistant preambles | Review the complete publishable boundary. |
| Removing language or bidi attributes as “noise” | Preserve internationalization structure exactly. |
| Flagging every `{{…}}` or `${…}` as leaked prompting | Determine whether it is required template syntax and audit it as structure. |
| Scanning only English assistant phrases | Review localized preambles, role disclaimers, prompt residue, and the target publication boundary. |

## Completion check

- No unresolved production artifact is silently presented as ready copy.
- Every citation points to a real, recoverable source in the target format.
- Structured content passes the consuming parser or is explicitly marked unverified.
- Template and code syntax are distinguished from placeholders.
- Visible rendering has been checked when the publication surface is available.
