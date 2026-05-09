# Version Discipline

Use this reference before changing package-sensitive LangChain.js examples, install commands, imports, deployment commands, or provider feature claims.

## Contents

- Tested package matrix
- Refresh workflow
- `@latest` policy
- Mixed-version handling
- Research-date rules

## Tested package matrix

Checked against the npm registry with `npm view <package> version` on 2026-05-09:

| Package | Registry version |
|---|---:|
| `langchain` | `1.4.0` |
| `@langchain/core` | `1.1.45` |
| `@langchain/langgraph` | `1.3.0` |
| `@langchain/openai` | `1.4.5` |
| `@langchain/openrouter` | `0.2.4` |
| `@langchain/langgraph-sdk` | `1.9.1` |
| `@langchain/langgraph-cli` | `1.2.1` |
| `@langchain/textsplitters` | `1.0.1` |
| `@langchain/mcp-adapters` | `1.1.3` |
| `langsmith` | `0.6.3` |
| `openevals` | `0.2.0` |
| `zod` | `4.4.3` |

Treat this as the current tested matrix for this skill, not as a guarantee about the user's project. Existing apps may intentionally pin older compatible versions.

## Refresh workflow

1. Run the bundled checker in the user repo when present: `bash <skill>/scripts/check-langchain-versions.sh`.
2. Re-check package versions from npm before editing dated examples:
   ```bash
   npm view langchain version
   npm view @langchain/core version
   npm view @langchain/langgraph version
   npm view @langchain/openai version
   npm view @langchain/langgraph-sdk version
   npm view @langchain/langgraph-cli version
   ```
3. Update this matrix only when the skill's examples or package guidance need the new versions.
4. Record the check date beside any API-sensitive or pricing-sensitive claim.

## `@latest` policy

Use `@latest` only for exploratory refresh commands where the goal is to install the newest package intentionally:

```bash
npm install langchain@latest @langchain/core@latest
```

Do not write `@latest` as the documented tested state. A skill reference should name either a dated tested matrix or tell the agent to inspect the user's installed packages.

## Mixed-version handling

LangChain packages do not all share the same version number. A healthy app can combine `langchain@1.x`, `@langchain/core@1.1.x`, `@langchain/langgraph@1.3.x`, and provider packages on their own tracks.

Flag these as risks before debugging behavior:

- Two installed major versions for the same `langchain` or `@langchain/*` package.
- `langchain@0.x` mixed with v1 examples.
- Provider package versions older than the core APIs used by examples.
- Lockfile and `package.json` disagreeing after a package update.

Prefer upgrading the smallest compatible package set for the selected path. Do not blanket-upgrade unrelated providers in an existing app unless the task is dependency maintenance.

## Research-date rules

For API-sensitive claims, include the date and source class in the edited reference:

- Package versions: npm registry, date checked.
- LangSmith or deployment pricing: official pricing page, date checked, or a warning to verify current pricing before quoting.
- MCP protocol/version behavior: official MCP spec or package release notes, date checked.
- Provider feature support: provider or LangChain docs, date checked.

When current pricing or ecosystem status is not verified during the task, replace exact numbers with "verify current pricing before quoting" instead of preserving stale dated amounts.
