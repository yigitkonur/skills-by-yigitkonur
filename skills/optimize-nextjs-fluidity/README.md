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

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/optimize-nextjs-fluidity
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```
