# Discovery Prompt Scaffolds

Reusable scaffolds for AGENTS-first discovery waves and writer dispatches. Use these only after the main agent has inspected the repo, built the folder map, and filled the placeholders with repo evidence.

## Contents

- [Wave 1 Broad Architecture](#wave-1-broad-architecture)
- [Wave 2 Folder Deep Dive](#wave-2-folder-deep-dive)
- [Writer Agent](#writer-agent)

## Wave 1 Broad Architecture

Use a 500-2500 word prompt built from this scaffold:

```text
You are Wave 1 of an AGENTS-first repo-instruction discovery pass.

Mission:
Map the repository at a broad architectural level so the main agent can design an AGENTS.md hierarchy before any writing begins.

Repository:
- Root: <repo path>
- Current tree snapshot: <paste `tree -dL 2 .` or equivalent>
- Existing instruction surfaces: <list any AGENTS.md, CLAUDE.md, .claude, Copilot, Cursor, Gemini, README, CONTRIBUTING files already found>

What you must discover:
1. The repo's real command sources and which commands are verified versus missing.
2. The top-level architecture, major folders, and which areas appear to have distinct workflows or risks.
3. Existing agent-instruction files, duplicated guidance, stale guidance, or CLAUDE-first anti-patterns.
4. Which folders are strong candidates for local AGENTS.md files, especially under `src/`, `apps/`, `packages/`, `services/`, or similar roots.
5. What a future folder-level writer would need to know before drafting local instructions.
6. Which review-critical areas should later shape `REVIEW.md` if review context is in scope.

How to work:
- Read only enough repo evidence to support claims.
- Separate documented facts from inference.
- Cite exact file paths for every important claim.
- Call out conflicts between files.
- Do not write AGENTS.md yet.
- Do not propose generic best practices.
- Focus on information that prevents mistakes.

Deliverable:
Produce a concise architecture brief with:
- verified commands and their sources
- repo-wide boundaries
- candidate AGENTS.md folders
- candidate review-critical areas
- missing information that must be resolved in Wave 2
- risks if the main agent writes before deeper folder exploration
```

## Wave 2 Folder Deep Dive

Use a 500-2500 word prompt built from this scaffold:

```text
You are Wave 2 of an AGENTS-first repo-instruction discovery pass.

Mission:
Investigate one subtree deeply enough that the main agent can write a local AGENTS.md for that folder without guessing.

Assigned subtree:
- Folder: <folder path>
- Parent/root context: <one paragraph from Wave 1 summary>
- Tree excerpt: <paste relevant lines from `tree -d .` or `tree -dL 2 .`>

What you must answer for this folder:
1. What does a coder working in this folder need to know before making changes here?
2. Which commands, entry points, or test workflows are local to this folder?
3. Which patterns are non-obvious and would cause mistakes if omitted?
4. Which rules belong in the parent AGENTS.md instead of this folder file?
5. Which changes in this folder deserve special scrutiny in review?
6. Should this folder also receive a sibling `CLAUDE.md` symlink or any extra native agent files?

How to work:
- Read only files that materially improve the folder brief.
- Ground every rule in repo evidence.
- Prefer local conventions over generic advice.
- Distinguish facts from inference.
- Avoid repeating parent-level instructions unless the folder overrides them.
- Do not write the final AGENTS.md file. Hand the main agent the evidence needed to write it.

Deliverable:
Return a folder brief with:
- the folder's purpose
- local commands and boundaries
- non-obvious patterns plus WHY
- content that must appear in this folder's AGENTS.md
- content that must stay in the parent file
- content that should later shape review context if needed
- unresolved unknowns that still block writing
```

## Writer Agent

Expand this scaffold with repo-specific findings, up to 5000 words:

```text
You are the writer for one folder in an AGENTS-first instruction hierarchy.

Ownership:
- Target file: <path/to/AGENTS.md>
- Folder scope: <folder>
- Parent instruction file: <parent AGENTS path>
- Companion entrypoint policy: create `CLAUDE.md` as a symlink to this AGENTS.md after the content is finalized

Context you must use:
- Repo summary from Wave 1: <insert synthesized summary>
- Folder brief from Wave 2: <insert subtree findings>
- Existing files to preserve or tighten: <list>
- Verified commands and paths: <list>

Writing objective:
Produce the smallest high-signal AGENTS.md that tells a coder working in this folder exactly what they need to know here and nothing they already know from the parent file.

Requirements:
- Keep only folder-local instructions.
- Preserve valid warnings and boundary rules.
- Ground every rule in evidence.
- Include commands only if they are verified and local to this folder.
- Do not duplicate parent instructions.
- Prefer imperative, measurable language.
- Call out non-obvious WHY context where it prevents mistakes.
- If the folder truly has minimal unique guidance, write a short local AGENTS.md rather than skipping the file.

Deliverable:
Return the final AGENTS.md content plus any notes the main agent needs before creating the companion `CLAUDE.md` symlink.
```
