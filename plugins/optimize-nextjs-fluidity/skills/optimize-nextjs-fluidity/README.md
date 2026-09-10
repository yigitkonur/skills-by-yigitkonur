# optimize-nextjs-fluidity

Auditing and optimizing a Next.js App Router repo for performance and fluidity, producing a version-gated task plan the agent then executes.

**Category:** development

## What it does

Profiles an unknown Next.js repo, gates every best practice against what the **installed**
package actually supports, fans out parallel audit agents, writes a dependency-ordered plan
as one markdown file per task under `nextjs-enhancement/`, then executes the safely
reversible tasks and verifies each one. One-way doors (enabling Cache Components, changing
URL policy) are prepared with a pre-flight checklist and left for a human.

Knowledge baseline: Next.js 16.3.0 / React 19.2, verified 2026-08-05 — distilled from a
163-file source-verified research corpus. The skill never assumes the target repo is on
that version; the capability probe reads `node_modules` and withholds anything the install
does not accept.

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install optimize-nextjs-fluidity@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended):**
   Omitting the `-g` flag installs the skill directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global agent conflicts.

   ```bash
   # This skill only
   npx -y skills add -y yigitkonur/skills-by-yigitkonur/skills/optimize-nextjs-fluidity

   # Or the full pack
   npx -y skills add -y yigitkonur/skills-by-yigitkonur
   ```

2. **Global install (user-level):**
   Installs across all supported global agents (`~/.agents/skills`).

   ```bash
   # This skill only
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/optimize-nextjs-fluidity

   # Or the full pack
   npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
   ```

   > [!NOTE]
   > If global installation reports `PromptScript does not support global skill installation`, you can safely ignore it. PromptScript is project-scoped by design; the skill is already installed for all other agents. To avoid this warning completely, run the project-level command above without `-g`.
