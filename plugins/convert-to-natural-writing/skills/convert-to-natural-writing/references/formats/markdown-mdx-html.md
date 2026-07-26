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
| Inline or fenced code | Exact |
| HTML/JSX tag and attribute name | Exact |
| Attribute value | Exact unless explicitly identified as copy |
| MDX expression or ESM | Exact |
| Comment | Preserve unless removal is in scope |
| Generated region | Do not hand-edit; follow repository generation workflow |

When syntax is ambiguous, protect it and use the consuming parser to identify boundaries.

## Markdown

CommonMark treats fenced code contents as literal. Do not rewrite prose-looking text inside a fence unless the user explicitly asks to edit the code sample.

Protect:

- fence marker, length, indentation, and info string;
- inline code delimiters and contents;
- link and image destinations, titles, and reference identifiers;
- footnote identifiers in dialects that support them;
- heading anchors when generated from exact text and external links depend on them;
- HTML blocks and template syntax passed through the renderer.

Markdown syntax can change meaning with whitespace. List indentation, block quotes, hard breaks, and nested fences require parser-aware review.

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

Protect keys, types, required fields, dates, enum values, slugs, IDs, and delimiters. A prose value such as `title` or `description` may be rewritten only when scope allows it. Quote a rewritten string if YAML punctuation could change parsing.

The bundled audit compares frontmatter keys and values conservatively. The repository's frontmatter parser remains authoritative.

## MDX

MDX combines Markdown with JSX, JavaScript expressions, and ESM. Natural-language-looking text may still be syntax.

Protect:

- `import` and `export` declarations;
- component names and nesting;
- braces and expressions;
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
- embedded `script`, `style`, `pre`, `code`, and template contents.

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
5. Run `audit-rewrite.py` for deterministic drift.
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

Use native tools for those claims.

## Common failures

| Failure | Correction |
| --- | --- |
| Rewriting prose inside code fences | Treat fenced contents as literal unless explicitly in scope. |
| Changing link labels and destinations together | Protect destinations separately. |
| Treating MDX as ordinary Markdown | Preserve JSX, expressions, ESM, and whitespace-sensitive boundaries. |
| Removing `lang` or `dir` as redundant | Preserve internationalization metadata and test rendering. |
| Trusting a regex audit as a compiler | Run the consuming parser/build and observe output. |

## Completion check

- Only authorized prose regions changed.
- Frontmatter keys/types, destinations, code, tags, attributes, and expressions are reconciled.
- Locale and bidi metadata remain intact.
- The deterministic audit and native parser/build passed at the rung claimed.
- Rendered output was observed or clearly reported as unverified.
