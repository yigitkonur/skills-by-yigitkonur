# Linters & AST Static Analysis Tools

## Overview

Linters parse source files into Abstract Syntax Trees (ASTs) to enforce code standards. With the Strada JS Compiler API removed in TypeScript 7.0, linter configurations must be verified to ensure they do not depend on the deprecated Node.js `typescript` API exports.

## Linter Compatibility Matrix

| Linter / Tool | Compatibility Status | Recommended Version |
| :--- | :--- | :--- |
| **ESLint + `@typescript-eslint`** |  **Fully Compatible** | v8.0.0+ (Uses TSESTree parser independent of Strada) |
| **Biome** |  **Fully Native** | v1.8.0+ (Rust-based, zero TS runtime dependency) |
| **Oxlint** |  **Fully Native** | Latest (Rust-based AST parser) |
| **Prettier** |  **Fully Compatible** | v3.0.0+ (Uses internal Babel/TS parser) |
| **Knip** |  **Fully Compatible** | v5.0.0+ (Native graph resolution) |
| **`ts-morph`** | ⚠️ **Requires Bridge** | Requires `@typescript/typescript6` |
| **Custom ESLint rules using `ts.*`** | ⚠️ **Requires Bridge** | Requires `@typescript/typescript6` |

## Updating ESLint Configurations

### ESLint Flat Config (`eslint.config.mjs`):
```js
import tsParser from '@typescript-eslint/parser';
import tsPlugin from '@typescript-eslint/eslint-plugin';

export default [
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        projectService: true, // Uses native project service (fastest)
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      ...tsPlugin.configs.recommended.rules,
    },
  },
];
```

## Migrating Custom AST Rules

If your repository contains custom scripts inspecting TypeScript ASTs:
```ts
// Legacy (Broken in TS 7.0)
import ts from 'typescript';
const program = ts.createProgram([...]);

// Migrated with Bridge
import ts from '@typescript/typescript6';
const program = ts.createProgram([...]);
```
