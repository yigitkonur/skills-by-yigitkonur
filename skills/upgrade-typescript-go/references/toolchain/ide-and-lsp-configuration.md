# IDE & Language Server Protocol (LSP) Configuration

## Overview

TypeScript 7.0 includes a high-performance native Language Server daemon written in Go, replacing the legacy Node.js `tsserver.js`.

The native language service provides instantaneous auto-completion, hover definitions, rename refactorings, and diagnostics with near-zero memory footprint.

## VS Code & Cursor Configuration

### 1. Workspace Settings (`.vscode/settings.json`)

To configure VS Code or Cursor to use the workspace's native TypeScript binary:

```json
{
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,
  "typescript.preferences.includePackageJsonAutoImports": "auto",
  "typescript.suggest.autoImports": true
}
```

### 2. Native Language Server Options

If using the native preview LSP extension:
```json
{
  "typescript.native.enabled": true,
  "typescript.native.maxMemoryMB": 1024
}
```

## Neovim / Helix / Zed Configuration

In Neovim (using `nvim-lspconfig` or Mason):
- Point `vtsls` or `ts_ls` to the workspace native binary.
- Or use the `tsgo` LSP binary directly as the language server.

## Troubleshooting IDE Drift

If the IDE shows outdated type errors while CLI `tsc --noEmit` passes:
1. Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`).
2. Run **`TypeScript: Restart TS Server`**.
3. Run **`TypeScript: Select TypeScript Version...`** → Select **`Use Workspace Version`**.
