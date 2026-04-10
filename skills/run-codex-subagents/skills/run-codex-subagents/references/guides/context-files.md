# Context Files

The `context_files` parameter on `spawn-task` prepends file contents into the agent's context before the prompt. Use it to give the agent immediate access to critical reference material without requiring file reads.

## Format

```json
{
  "context_files": [
    { "path": "/absolute/path/to/file.md", "description": "Migration plan v3" },
    { "path": "/project/src/types.ts", "description": "Core type definitions" },
    { "path": "/project/schema.prisma" }
  ]
}
```

Each entry:
- `path` (required) — Absolute filesystem path. Must exist and be readable.
- `description` (optional) — Short explanation of why this file is included. Appears as a label before the file content in the agent's context.

## How It Works

Before the agent sees your prompt, the server reads each file and prepends its content:

```
--- Context file: /project/src/types.ts (Core type definitions) ---
[full file contents here]
--- End context file ---

--- Context file: /project/schema.prisma ---
[full file contents here]
--- End context file ---

[your prompt follows]
```

The agent sees these files as part of its initial context. It doesn't need to read them with tools — they're already loaded.

## When to Use

### Good use cases

| Scenario | Example file | Why prepend |
|---|---|---|
| Implementation plan | `WAVE-5-PLAN.md` | Agent needs to follow specific steps |
| API schema | `openapi.yaml` | Agent needs exact endpoint shapes |
| Type definitions | `src/types.ts` | Agent must match existing types |
| Architecture spec | `ARCHITECTURE.md` | Agent needs system context |
| Migration guide | `MIGRATION.md` | Agent must follow migration steps |
| Test fixtures | `fixtures/sample.json` | Agent needs exact test data format |

### Bad use cases

| Scenario | Why not | Better approach |
|---|---|---|
| Entire source directory | Way too many tokens | Let agent `find` and `cat` what it needs |
| Large generated files | Wastes context budget | Agent reads the specific section it needs |
| Files the agent might not need | Speculative loading wastes tokens | Only prepend must-have files |
| Binary files | Can't be serialized as text | Reference by path in prompt |
| Files >500 lines | Consumes too much budget | Excerpt the relevant section into a temp file |

## Budget Guidelines

Context files consume input tokens on every reasoning turn. A 200-line TypeScript file is roughly 2-3K tokens.

| Configuration | Estimated tokens | Risk level |
|---|---|---|
| 1 small file (50 lines) | ~500-800 | Negligible |
| 3 medium files (150 lines each) | ~3-5K | Safe |
| 5 files (300 lines each) | ~10-15K | Monitor total usage |
| 10+ files or >500 lines each | ~20K+ | Likely harmful to task performance |

**Rule of thumb:** Max 5 files, each under 500 lines. If you need more, the agent should read files itself.

## Description Best Practices

The `description` field helps the agent understand why the file is relevant:

```json
// Good — tells the agent how to use this file
{ "path": "/project/PLAN.md", "description": "Implementation plan — follow steps in order" }
{ "path": "/project/types.ts", "description": "Type definitions — new code must conform to these" }

// Bad — description doesn't add value
{ "path": "/project/PLAN.md", "description": "A file" }
{ "path": "/project/types.ts", "description": "TypeScript file" }

// Fine — omitting description when the filename is self-explanatory
{ "path": "/project/schema.prisma" }
```

## Combining with Prompts

Reference context files explicitly in your prompt:

```
"Read the migration plan provided in context. Execute steps 3-7.
For each step, create the file specified, following the type
definitions also provided in context. Do not modify any existing files."
```

This tells the agent to look at the prepended content rather than searching the filesystem.

## Path Requirements

- Paths must be absolute (`/Users/me/project/file.ts`, not `./file.ts`)
- Paths must exist on disk at spawn time (server reads them synchronously)
- Paths must be readable by the MCP server process
- Symlinks are followed
- If a path doesn't exist, the spawn-task call fails with an error

## Interaction with Other Parameters

| Parameter | Interaction |
|---|---|
| `prompt` | Context files appear before the prompt in agent's view |
| `developer_instructions` | System instructions appear separately; context files are in user context |
| `cwd` | Context file paths are independent of cwd — always absolute |
| `depends_on` | Context files are read at spawn time, not when dependency resolves |

## Anti-patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Prepending 20 files | Consumes 30%+ of token budget before agent starts | Limit to 5 essential files |
| Prepending files agent won't reference | Wasted tokens, confuses agent | Only include must-have references |
| Using relative paths | Server can't resolve them | Always use absolute paths |
| Prepending frequently-changing files | Content is snapshot at spawn time | Agent should read live if freshness matters |
| Duplicating prompt content in files | Same info twice wastes tokens | Put it in one place |
