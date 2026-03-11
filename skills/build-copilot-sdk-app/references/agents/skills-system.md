# Skills System — Reference

Skills are reusable prompt modules loaded from directories at session creation. Each skill is a named subdirectory containing a `SKILL.md` file. When loaded, the skill's markdown body is injected into the session context, extending the model's behavior for that session.

---

## `skillDirectories` in SessionConfig

Pass an array of absolute or relative directory paths. Each path is a **parent directory** that contains skill subdirectories — not the skill directory itself.

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient();
await client.start();

const session = await client.createSession({
    onPermissionRequest: async () => ({ kind: "approved" }),
    skillDirectories: [
        "./skills/security",
        "./skills/testing",
        "/shared/org-skills",
    ],
});
```

The CLI discovers all immediate subdirectories of each listed path and looks for a `SKILL.md` file inside each one. Discovery is not recursive — only one level deep.

Expected directory layout:
```
./skills/
├── security/
│   ├── owasp-audit/
│   │   └── SKILL.md       ← discovered
│   └── secrets-scan/
│       └── SKILL.md       ← discovered
└── testing/
    └── coverage-check/
        └── SKILL.md       ← discovered
```

---

## `disabledSkills` — Excluding Skills by Name

Exclude specific skills while keeping all others in the loaded directories active.

```typescript
const session = await client.createSession({
    onPermissionRequest: async () => ({ kind: "approved" }),
    skillDirectories: ["./skills"],
    disabledSkills: ["experimental-feature", "deprecated-tool"],
});
```

Values in `disabledSkills` match against the `name` field in a skill's YAML frontmatter. If no frontmatter `name` is present, the directory name is used as the skill's identifier.

---

## SKILL.md Format

A `SKILL.md` is a markdown file with optional YAML frontmatter at the top. The frontmatter defines metadata; the markdown body is the instruction content injected into the session.

```markdown
---
name: security-audit
description: OWASP Top 10 security review guidelines
---

# Security Audit Instructions

When reviewing code for security issues, always check for:

1. **A01 Broken Access Control** — verify authorization checks on every endpoint
2. **A02 Cryptographic Failures** — flag plaintext secrets, weak hashing, unencrypted PII
3. **A03 Injection** — check for SQL injection, XSS, command injection in all user inputs
4. **A07 Identity and Auth Failures** — verify session management and token lifetimes

Always reference the OWASP category code (e.g., A03:2021) in your findings.
Produce a severity-ranked list: critical > high > medium > low.
```

Frontmatter fields:

| Field | Required | Description |
|---|---|---|
| `name` | No | Skill identifier used with `disabledSkills`. Falls back to directory name if omitted. |
| `description` | No | Human-readable description of what the skill does. |

The YAML frontmatter delimiter is `---` on its own line. Any standard YAML is valid in the block; only `name` and `description` are consumed by the runtime.

---

## How Skills Are Discovered and Loaded

1. At `client.createSession()`, the SDK passes `skillDirectories` to the CLI.
2. The CLI scans each listed directory for immediate subdirectories.
3. For each subdirectory, it checks for a `SKILL.md` file.
4. If found, it parses the YAML frontmatter to extract `name` and `description`.
5. Any skill whose `name` (or directory name) appears in `disabledSkills` is excluded.
6. The remaining skills' markdown bodies are injected into the session context as additional instructions.
7. All skill content is active from the first prompt sent to the session.

Skills are loaded once at session creation. Modifying skill files after the session starts has no effect on the running session.

---

## Skill Trigger Matching Behavior

Skills do not use explicit trigger conditions or keyword matching. Their content is injected unconditionally into the session context and applies to every turn. The model decides when to apply skill instructions based on the prompt context.

Implication: avoid loading skills that conflict with each other. If two skills give contradictory instructions, the model will attempt to reconcile them — results are unpredictable. Use `disabledSkills` or separate `skillDirectories` per session to prevent conflicts.

Design skills to be composable: each skill should address one specific domain without assuming or contradicting other skills.

---

## Skills vs Agents vs MCP Servers — When to Use Which

| Capability | Skills | Custom Agents | MCP Servers |
|---|---|---|---|
| Adds domain instructions | Yes | Yes (via `prompt`) | No |
| Restricts available tools | No | Yes (via `tools`) | No |
| Adds new tools | No | No | Yes |
| Scoped to specific tasks | No (always active) | Yes (selected per prompt) | No (always active) |
| Requires external process | No | No | Yes |
| Reusable across projects | Yes (file-based) | No (code-based) | Yes (if remote) |

Use skills when:
- You want to inject persistent domain expertise without restricting tool access.
- You need portable, file-based instructions shared across multiple codebases.
- The behavior should apply to every interaction in the session, not just delegated sub-tasks.

Use custom agents when:
- You need tool restrictions (principle of least privilege).
- You want intent-based delegation to specialized personas.
- Different phases of a task require different behavioral contracts.

Use MCP servers when:
- You need to expose new tools from external systems (databases, APIs, browsers).
- The capability requires executing code or making network requests.

---

## Dynamic Skill Loading Patterns

### Environment-based skill selection

```typescript
const skillDirs: string[] = ["./skills/base"];

if (process.env.NODE_ENV === "production") {
    skillDirs.push("./skills/prod-safety");
}
if (process.env.ENABLE_EXPERIMENTAL === "true") {
    // load experimental skills but disable known-unstable ones
}

const session = await client.createSession({
    onPermissionRequest: async () => ({ kind: "approved" }),
    skillDirectories: skillDirs,
    disabledSkills: process.env.DISABLED_SKILLS?.split(",") ?? [],
});
```

### Per-user or per-project skills

```typescript
import * as path from "path";
import * as os from "os";

const session = await client.createSession({
    onPermissionRequest: async () => ({ kind: "approved" }),
    skillDirectories: [
        path.join(process.cwd(), ".copilot/skills"),        // project-level
        path.join(os.homedir(), ".copilot/skills"),         // user-level
        "/etc/copilot/org-skills",                          // org-level
    ],
});
```

Skills from multiple directories are merged. If two directories contain skills with the same `name`, both are loaded — avoid name collisions by using namespace prefixes in skill names.

### Combining skills with custom agents

Skills and agents compose cleanly. Skills inject ambient context; agents scope tool access and persona.

```typescript
const session = await client.createSession({
    onPermissionRequest: async () => ({ kind: "approved" }),
    skillDirectories: ["./skills/security"],         // security audit skill always active
    customAgents: [
        {
            name: "security-auditor",
            description: "Security-focused code reviewer",
            tools: ["view", "grep", "glob"],         // read-only
            prompt: "Focus exclusively on OWASP Top 10 vulnerabilities.",
        },
    ],
});
```

### Combining skills with MCP servers

Skills can document how to use MCP tools, improving model behavior:

```typescript
// ./skills/database/SKILL.md
// ---
// name: database-guidelines
// ---
// When querying the database:
// - Always use parameterized queries via the postgres/query tool
// - Never SELECT * — always name columns explicitly
// - Limit results to 100 rows unless the user requests otherwise

const session = await client.createSession({
    onPermissionRequest: async () => ({ kind: "approved" }),
    skillDirectories: ["./skills/database"],
    mcpServers: {
        postgres: {
            command: "npx",
            args: ["-y", "@modelcontextprotocol/server-postgres", process.env.DATABASE_URL!],
            tools: ["*"],
        },
    },
});
```

---

## Troubleshooting Skills Not Loading

1. Verify the path in `skillDirectories` is the **parent** directory, not the skill subdirectory itself.
2. Confirm each subdirectory contains a file named exactly `SKILL.md` (case-sensitive on Linux).
3. Validate YAML frontmatter syntax — malformed YAML causes the skill to be skipped silently.
4. Enable debug logging: `new CopilotClient({ logLevel: "debug" })` — the CLI logs skill discovery.
5. Use absolute paths to rule out working-directory issues:

```typescript
import * as path from "path";
skillDirectories: [path.resolve("./skills")]
```

6. Confirm the `disabledSkills` values match the `name` field in frontmatter exactly (case-sensitive string match).
