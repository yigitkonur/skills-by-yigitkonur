# F-01 — ESM Module Requirement (P0, S1)

## Observation

The SDK's `package.json` has `"type": "module"` and only ships ESM exports.
When a project's `package.json` lacks `"type": "module"`, imports fail:

```
Error [ERR_PACKAGE_PATH_NOT_EXPORTED]: No "exports" main defined in
.../node_modules/@github/copilot-sdk/package.json
```

## Why P0

This blocks the very first step. No code runs until this is fixed.

## Root cause

S1 — Missing prerequisite. The skill assumes ESM-compatible project config
but never states this requirement.

## Fix applied

Added to SKILL.md Quick start:
1. `npm init -y` to create package.json
2. `npm pkg set type=module` with comment "SDK is ESM-only"
3. Callout: `> **ESM required.** The SDK only ships ESM exports.`
