# `tsgo` Native Binary & CLI Architecture

## Overview

`tsgo` is the native Go executable created during the TypeScript Native project (Project Corsa). In preview releases, it is distributed via `@typescript/native-preview`. In TypeScript 7.0+, the native binary replaces the default `tsc` executable.

## Installation & Distribution

### 1. Standalone / Preview Mode
```bash
# Install the native preview package
pnpm add -D @typescript/native-preview
```
This adds the `tsgo` binary to `node_modules/.bin/tsgo`.

### 2. Full TypeScript 7.0 Mode
```bash
# Install official TypeScript 7.0+
pnpm add -D typescript@latest
```
This installs the native Go compiler directly as the `tsc` binary.

## CLI Options & Compatibility

`tsgo` (and native `tsc`) supports all standard type-checking flags:

```bash
# Type check without emitting files
tsgo --noEmit

# Type check a composite monorepo
tsgo --build

# Watch mode (uses native OS file system events)
tsgo --watch

# Specific tsconfig
tsgo --project ./packages/core/tsconfig.json
```

## Performance Benchmark Characteristics

| Engine | Cold Run (Single Thread) | Cold Run (80 Cores) | Peak RAM Usage |
| :--- | :--- | :--- | :--- |
| **Legacy `tsc` (Node.js/V8)** | ~180-240s | ~180-240s (No multi-threading) | 3.5 - 4.2 GB |
| **Native `tsgo` / `tsc` (Go)** | ~60s | **~15-40s** (Full parallel AST check) | **200 - 600 MB** |

## Key Differences from Legacy `tsc`
1. **Garbage Collection**: Uses Go's concurrent garbage collector; zero risk of V8 `JavaScript heap out of memory` crashes.
2. **True Multithreading**: Scales automatically with available CPU cores (`GOMAXPROCS`).
3. **Instant Startup**: No Node.js runtime initialization delay.
