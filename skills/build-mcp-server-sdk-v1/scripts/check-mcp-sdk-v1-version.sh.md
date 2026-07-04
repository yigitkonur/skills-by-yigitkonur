# check-mcp-sdk-v1-version.sh

## Purpose

Confirm that a Node project is using the stable single-package MCP TypeScript SDK v1 path before applying this skill.

## Usage

```bash
bash scripts/check-mcp-sdk-v1-version.sh [project-dir]
```

`project-dir` defaults to the current directory. The script reads `package.json` with Node.js and does not require `jq`.

## Output

- `OK @modelcontextprotocol/sdk=<range> zod=<range>` when the project is on the v1 SDK package and declares `zod`.
- `FAIL ...` when `@modelcontextprotocol/sdk` is missing, `zod` is missing, a v2 alpha or `next` range is detected, v2 split packages are present, or source files import split packages.

## Skill routing

Use this in `SKILL.md` Step 1/4 when an existing project has `package.json` and the SDK generation must be confirmed before editing code.
