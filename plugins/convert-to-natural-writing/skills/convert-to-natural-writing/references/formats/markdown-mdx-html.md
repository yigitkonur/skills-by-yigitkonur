# Markdown, MDX, and HTML

Use this reference to rewrite prose inside structured content without breaking syntax, metadata, code, components, links, language information, or renderer behavior.

## Treat prose and structure differently

Classify every region before editing:

| Region | Default treatment |
| --- | --- |
| Prose paragraph or heading | Editable within the editorial contract |
| Frontmatter key | Exact |
| Frontmatter prose value | Editable only if authorized; preserve type and quoting needs |
| Link/image label | Usually editable |
| Link/image destination | Exact |
| Inline, fenced, or indented code | Exact |
| Reference/footnote identifier | Exact; definition prose may be editable |
| HTML/JSX tag and attribute name | Exact |
| Attribute value | Exact unless explicitly identified as copy |
| MDX expression or ESM | Exact |
| Template directive | Exact |
| HTML comment, entity, or raw-text body | Exact unless explicitly authorized |
| Comment | Preserve unless removal is in scope |
| Generated region | Do not hand-edit; follow repository generation workflow |

When syntax is ambiguous, protect it and use the consuming parser to identify boundaries.

## Markdown

CommonMark treats fenced code contents as literal. Do not rewrite prose-looking text inside a fence unless the user explicitly asks to edit the code sample.

Protect:

- fence marker, length, indentation, and info string;
- four-space/tab-indented code blocks and their internal blank lines;
- inline code delimiters and contents;
- inline and reference link destinations, including relative paths and nested parentheses;
- reference-definition, collapsed/shortcut-reference, and footnote identifiers;
- footnote identifiers in dialects that support them;
- heading anchors when generated from exact text and external links depend on them;
- HTML blocks and template syntax passed through the renderer.

Visible link labels, image alt text, reference titles, and footnote prose may be edited when the contract allows it. The structural identifier or destination may not. Markdown syntax can change meaning with whitespace. List indentation, block quotes, hard breaks, nested fences, and extension directives require parser-aware review.

## Frontmatter

Frontmatter is data, not decoration:

```yaml
---
title: "A clearer title"
date: 2026-07-26
draft: false
tags:
  - editing
slug: natural-writing
---
```

Protect keys, types, required fields, dates, enum values, slugs, IDs, sequences, and delimiters. A named prose value such as `title`, `description`, `summary`, or `excerpt` may be rewritten only when scope allows it. Preserve block-scalar shape, and quote a rewritten string if YAML punctuation could change parsing.

The bundled audit compares non-copy scalars and sequences conservatively while allowing common copy-field values to change. It is not a YAML implementation: anchors, aliases, merge keys, tags, duplicate keys, complex keys, and schema-specific types still require the repository's frontmatter parser.

## MDX

MDX combines Markdown with JSX, JavaScript expressions, and ESM. Natural-language-looking text may still be syntax.

Protect:

- `import` and `export` declarations;
- component names and nesting;
- braces and expressions;
- template directives such as `{{…}}`, `{%…%}`, and `${…}` when another engine shares the file;
- prop names and protected prop values;
- spread props and comments;
- code blocks containing JSX examples;
- blank lines and delimiters that determine parsing.

Editable copy may appear as children or selected props:

```mdx
<Callout tone="warning" title="Review before publishing">
  This value still needs a source.
</Callout>
```

Unless authorized, edit only the title and child prose. Preserve `Callout`, `tone`, and `warning` exactly.

## HTML

Protect structural and internationalization semantics:

- element names, nesting, IDs, classes used by scripts/styles, and data attributes;
- form names, values, methods, and destinations;
- URLs and resource paths;
- ARIA names and relationships unless accessibility copy is explicitly in scope;
- `lang`, `dir`, and bidi isolation;
- entities and whitespace where preformatted behavior matters;
- comments and character-reference spelling when exact source representation matters;
- embedded `script`, `style`, `textarea`, `pre`, `code`, and template contents.

Visible text nodes and human-facing attributes such as `alt`, `title`, `placeholder`, and `aria-label` may be copy, but changes must preserve function and accessibility.

## Language and direction

W3C internationalization guidance makes language metadata operational:

- keep the document's default language declaration;
- mark inline language changes when pronunciation, fonts, quotation, or assistive technology depend on them;
- preserve right-to-left direction and bidi isolation for mixed-direction content;
- do not reorder bidirectional strings by eye;
- test visible output with the target scripts and fonts.

Changing prose must not strip or homogenize language boundaries.

## Safe editing workflow

1. Identify file type and actual renderer.
2. Read repository instructions and generation boundaries.
3. Inventory frontmatter, destinations, code, tags, attributes, expressions, and language metadata.
4. Edit only confirmed prose regions.
5. Run `audit-rewrite.py` for deterministic drift; add `--protect` or `--protect-from` for project-specific exact literals.
6. Run formatter/parser/compiler for the file type.
7. Run the narrowest consuming build or content validation.
8. Inspect rendered output and links when available.

Never edit a generated copy when the canonical source and generator are available.

## Audit limitations

The helper intentionally does not implement full CommonMark, YAML, MDX, JSX, or HTML parsers. It inventories common protected tokens and flags suspicious drift. It cannot determine:

- whether JSX nesting is valid;
- whether a changed title breaks generated anchors;
- whether HTML semantics or accessibility improved;
- whether a frontmatter value has the correct domain type;
- whether a template or CMS accepts the file;
- whether visible output matches the source.
- whether equal tag inventories retain the same nesting and order;
- whether a dialect-specific construct was classified correctly;
- whether Unicode-normalized or visually equivalent values are operationally equivalent.

Use native tools for those claims.

## Common failures

| Failure | Correction |
| --- | --- |
| Rewriting prose inside code fences | Treat fenced contents as literal unless explicitly in scope. |
| Changing link labels and destinations together | Protect destinations separately. |
| Treating MDX as ordinary Markdown | Preserve JSX, expressions, ESM, and whitespace-sensitive boundaries. |
| Treating a template variable as placeholder residue | Confirm the renderer; protect required directives and render representative data. |
| Editing `script`, `style`, comments, or entities as visible copy | Treat raw-text and source-control regions as exact unless separately authorized. |
| Removing `lang` or `dir` as redundant | Preserve internationalization metadata and test rendering. |
| Trusting a regex audit as a compiler | Run the consuming parser/build and observe output. |

## Completion check

- Only authorized prose regions changed.
- Frontmatter keys/types, destinations, code, tags, attributes, and expressions are reconciled.
- Locale and bidi metadata remain intact.
- The deterministic audit and native parser/build passed at the rung claimed.
- Rendered output was observed or clearly reported as unverified.
