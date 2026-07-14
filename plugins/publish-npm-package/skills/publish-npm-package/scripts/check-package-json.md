# check-package-json.mjs

Inspect a package directory before wiring npm publishing.

## Usage

```bash
node scripts/check-package-json.mjs [package-dir]
node scripts/check-package-json.mjs [package-dir] --json-only
```

## Checks

- parses `package.json`
- validates basic `name`, `version`, `repository`, `publishConfig`, `files`, `exports`, and `types` signals
- detects obvious `src`/`dist` mismatches
- detects `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, and `bun.lockb`
- reports the deterministic install command implied by the lockfile

The script prints human-readable lines followed by JSON. It exits nonzero only for hard errors such as missing `package.json`, invalid JSON, or a likely broken package shape.
