# convert-to-natural-writing

Humanizing or rewriting AI-sounding, robotic, or generic text, Markdown, MDX, or HTML into natural multilingual copy; not translation-only, proofreading-only, or authorship scoring.

**Category:** productivity

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install convert-to-natural-writing@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended & PromptScript-compatible):**
   Installs directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global collisions. Fully compatible with project-scoped tools like PromptScript:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/convert-to-natural-writing -y

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y
   ```

   PromptScript projects can also import directly via `prs`:
   ```bash
   prs skills add github.com/yigitkonur/skills-by-yigitkonur/skills/convert-to-natural-writing/SKILL.md
   ```

2. **Global install (user-level):**
   Installs globally into `~/.agents/skills` for all universal agents (Claude Code, Cursor, Codex, Antigravity, Amp, etc.) cleanly without triggering project-scoped agent warnings:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/convert-to-natural-writing -y -g -a universal

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y -g -a universal
   ```

## What it does

- Diagnoses robotic or templated prose without claiming to identify its author.
- Rewrites toward a warm, natural, casual-professional register while preserving facts and claim strength.
- Handles pasted prose plus Markdown, MDX, and HTML in any language the active model can edit responsibly.
- Protects links, code, frontmatter, markup, names, numbers, attribution, uncertainty, and locale identity.
- Covers partial/long rewrites, templates, generated regions, accessibility copy, localized values, and high-stakes reviewer gates.
- Includes a dependency-free audit helper with explicit-literal options, structured warnings, 35 focused tests, and 16 routed reference guides.

The skill does not promise detector evasion or universal native fluency. For high-stakes multilingual publication, it names when fluent human review is still required.
