# Skills over MCP (SEP-2640)

*Authoritative guide for serving reusable agent skills from mcp-use v2 servers.*

Official documentation:
- [Skills over MCP](https://docs.mcp-use.com/v2/typescript/server/skills)

---

## 1. What are Skills over MCP?

Skills let an MCP server ship reusable operating workflows alongside its tools. Prefer a Skill when a task requires a repeatable multi-step workflow, policies, templates, or scripts that would otherwise bloat tool descriptions.

Do not replace executable capabilities with prose:
- **Tools**: perform actions.
- **Resources**: expose discoverable content.
- **Prompts**: return model-ready messages.
- **Skills**: teach an agent how to combine them safely.

---

## 2. Directory Convention

Create a conventional `skills/` directory beside your server entry:

```text
skills/
  process-refund/
    SKILL.md
    references/
      policy.md
    templates/
      confirmation.md
```

Every skill needs a directory-matching `SKILL.md` with trigger frontmatter:

```md
---
name: process-refund
description: Check refund eligibility and process approved customer refunds
---

# Process refunds

Read `references/policy.md` before deciding eligibility.
Use `templates/confirmation.md` after a successful refund.
```

Keep `SKILL.md` procedural and small. Put detailed policies in `references/`, deterministic logic in `scripts/`, and output templates in `templates/`.

---

## 3. Server Configuration

By default, the presence of the `skills/` directory automatically enables discovery. You can configure it explicitly on `MCPServer`:

```ts
new MCPServer({ name: "shop", version: "1.0.0", skills: true }); // requires conventional directory
new MCPServer({ name: "shop", version: "1.0.0", skills: false }); // disables skills discovery
new MCPServer({
  name: "shop",
  version: "1.0.0",
  skills: { directory: "custom-skills" }, // custom relative path
});
```

---

## 4. Discovery & Protocol Surface

The server advertises the Skills over MCP extension:
- `skills/list`: Client discovers all registered skills with descriptions.
- `skills/get`: Client retrieves the full `SKILL.md` instruction content and referenced files.
