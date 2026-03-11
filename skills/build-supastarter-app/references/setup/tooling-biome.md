# Tooling: Biome

> Biome linting and formatting configuration. Consult this when getting lint errors, adding lint rules, or understanding code style enforcement.

## Configuration

From `biome.json` at the project root:

```json
{
  "$schema": "https://biomejs.dev/schemas/2.0.0-beta.1/schema.json",
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "defaultBranch": "main",
    "useIgnoreFile": true
  },
  "organizeImports": {
    "enabled": true
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "tab",
    "lineWidth": 80
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "complexity": {
        "noExcessiveCognitiveComplexity": "off"
      },
      "correctness": {
        "noUnusedImports": {
          "level": "error",
          "fix": "safe"
        }
      },
      "style": {
        "noParameterAssign": "error",
        "useAsConstAssertion": "error",
        "noNonNullAssertion": "off",
        "useNodejsImportProtocol": "off"
      },
      "suspicious": {
        "noExplicitAny": "off"
      }
    }
  },
  "css": {
    "linter": {
      "enabled": false
    }
  }
}
```

## Key Rules

| Rule | Level | Behavior |
|------|-------|----------|
| `noUnusedImports` | error | Auto-fixable — Biome removes unused imports on format |
| `noParameterAssign` | error | Cannot reassign function parameters |
| `useAsConstAssertion` | error | Must use `as const` for constant objects/arrays |
| `noExplicitAny` | off | `any` is allowed (project uses it sparingly) |
| `noNonNullAssertion` | off | Non-null assertions (`!`) are allowed |
| `noExcessiveCognitiveComplexity` | off | Complex functions are allowed |

## Formatting Rules

- **Indent style:** Tabs (not spaces)
- **Line width:** 80 characters
- **Import organization:** Enabled (auto-sorts imports)
- **CSS linting:** Disabled (Tailwind v4 handles CSS)

## CLI Commands

```bash
# Lint all files
pnpm lint

# Format all files
pnpm format

# Check without fixing (CI mode)
pnpm lint --no-fix

# Fix specific file
pnpx biome check --write path/to/file.ts
```

## IDE Integration

Biome has VS Code and JetBrains extensions. The configuration in `biome.json` is automatically picked up.

## VCS Integration

```json
"vcs": {
  "enabled": true,
  "clientKind": "git",
  "useIgnoreFile": true
}
```

Biome respects `.gitignore` — files ignored by git are also ignored by the linter/formatter.

---

**Related references:**
- `references/conventions/typescript-patterns.md` — TypeScript patterns that complement Biome
- `references/conventions/code-review-checklist.md` — Pre-commit quality checks
- `references/cheatsheets/commands.md` — CLI commands
