# Preventing Rehype/Remark AST Bottlenecks During Large Builds

> **Context:** Content Layer & Collections | **Impact:** Critical | **Target:** Astro 5 / Astro 7

## 1. Why We Do This

In high-throughput static builds (e.g. 3,800+ routes), Markdown and HTML Abstract Syntax Tree (AST) transformations are executed for every document. Naive remark or rehype plugins with quadratic traversal algorithms, unmemoized regular expressions, repeated string serializations, or synchronous I/O operations will severely bottleneck the build pipeline. Plugins must be designed as single-pass AST visitors (using `unist-util-visit`), avoiding mutating ancestor trees or re-parsing serialized HTML chunks. Furthermore, critical transformations (such as glossary autolinking or code line merging) should leverage compiled Rust processors or linear token streams.

## 2. How It Differs From Classic React / Next.js

In Next.js, remark and rehype plugins are often configured in `next.config.mjs` and re-evaluated per page request in dev mode or during static exports, with minimal inspection into AST traversal costs. Astro exposes fine-grained control over Markdown and Content Layer plugins via `config/markdown.mjs`, enabling pipeline order isolation, selective collection execution, and integration with Sätteri Rust primitives.

## 3. Common Mistakes & Anti-Patterns

- Running nested loops or O(N^2) scans over all AST nodes.
- Re-parsing HTML strings into DOM trees inside an AST visitor instead of operating directly on HAST nodes.
- Doing synchronous filesystem reads or network calls inside remark/rehype visitor callbacks.

### ❌ Bad Practice / Anti-Pattern

```js
// ❌ Inefficient regex replacement over full HTML string inside rehype plugin
import { visit } from 'unist-util-visit'

export function slowGlossaryPlugin() {
  return (tree) => {
    // Bad: Serializes nodes, runs heavy regex replacements, and re-parses repeatedly
    visit(tree, 'element', (node) => {
      if (node.tagName === 'p') {
        const text = JSON.stringify(node)
        terms.forEach((term) => {
          // O(T * N) regex execution per paragraph!
          text.replace(new RegExp(term, 'gi'), `<a href="...">$&</a>`)
        })
      }
    })
  }
}
```

### ✅ Best Practice / Idiomatic

```js
// ✅ Linear AST walker targeting text nodes with ancestor guards
import { visit, SKIP } from 'unist-util-visit'

export function fastGlossaryPlugin(termsMap) {
  return (tree) => {
    visit(tree, 'element', (node) => {
      // Guard: Immediately skip anchors, pre, code, and headings
      if (['a', 'pre', 'code', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(node.tagName)) {
        return SKIP
      }
    })

    // Linear text node traversal with precompiled single-regex alternation
    visit(tree, 'text', (node, index, parent) => {
      // Direct HAST node splice without string serialization
    })
  }
}
```

## 4. Verification & Audit

Audit Markdown pipeline plugins for performance bottlenecks and unist visitor efficiency:

```bash
git grep -n "unist-util-visit" config/markdown-plugins/
git grep -n "SKIP" config/markdown-plugins/
```

Profile Markdown compilation timing across content collections:

```bash
pnpm vitest run tests/int/markdown-pipeline-parity.test.ts
```
