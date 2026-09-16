# Target ES5 Deprecation & Modern Target Selection

## Overview

TypeScript 7.0 removes the `ES5` and `ES3` emit targets. Emitting downlevel ES5 code with complex prototype chains, `var` hoisting, and polyfill helpers is no longer supported within the native TypeScript compiler.

## Target Selection Strategy

| Project Archetype | Recommended Target | Recommended Lib |
| :--- | :--- | :--- |
| **Next.js 14+ / React 18+** | `"target": "ESNext"` or `"ES2022"` | `["DOM", "DOM.Iterable", "ESNext"]` |
| **Vite / SPA Frontend** | `"target": "ES2022"` | `["DOM", "DOM.Iterable", "ESNext"]` |
| **Node.js 20+ Backend / Cloudflare Workers** | `"target": "ES2022"` | `["ESNext"]` |
| **Cross-Platform Library / CLI** | `"target": "ES2020"` | `["ES2020"]` |

## Why Was ES5 Removed?

1. **Native JavaScript Engines**: All modern browsers and runtimes (Chrome, Safari, Firefox, Edge, Node.js 18+, Bun, Deno, Cloudflare Workers) natively support ES2020+ features:
   * Classes and class fields
   * Async/await
   * Optional chaining (`?.`) and nullish coalescing (`??`)
   * BigInt and Promise APIs
2. **Compiler Performance**: Eliminating downlevel ES5 AST transformation allowed the native Go compiler to stream output ASTs directly to bytecode/transpilation targets with 10x throughput.
3. **Specialized Downleveling**: If legacy browser support (e.g. IE11 or ancient WebViews) is strictly necessary, downstream tools like Babel, SWC, or browserslist-configured bundlers handle downleveling much more effectively.

## Updating `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["DOM", "DOM.Iterable", "ESNext"],
    "useDefineForClassFields": true
  }
}
```
