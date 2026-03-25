# Target Modes and Path Conventions

Decide the target mode before running any command from this skill. The example paths in the other references are patterns for common repos, not hardcoded requirements.

---

## Non-Negotiable Rules

- The **target root** is the directory that owns the UI you are documenting. It may be the original repo root or a writable working copy of that UI.
- Run commands against the target root and its evidence directories, never against the skills repo.
- Treat sample paths like `src/`, `app/`, `components/`, and `package.json` as placeholders for common layouts. Replace them with the real paths in the target.
- If a framework, package manifest, or config file does not exist in the target, do not infer it. Mark the check `not implemented`, `N/A`, or document the evidence gap explicitly.

---

## Mode 1: Repo-Backed UI

Use this mode when the target has an application structure such as:

- `package.json`
- `src/` or `app/`
- component source files (`.tsx`, `.jsx`, `.vue`, etc.)
- framework or styling config files

In this mode:

- Search the real UI directories, not only `src/` if the repo uses a different layout.
- Use package manifests and config files for stack detection.
- Treat component source files as the primary evidence for variants, states, and composition.

---

## Mode 2: Offline Snapshot / Plain HTML+CSS

Use this mode when the target is a captured UI with files such as:

- `index.html`
- one or more `.css` files
- static assets (`.svg`, `.png`, `.jpg`)
- no package manifest or no component source tree

In this mode:

- Treat the snapshot root itself as the search root.
- Treat CSS files as the source of truth for tokens, layout rules, and state styling.
- Treat repeated DOM fragments plus their matching selectors as component evidence.
- Skip package-manager, framework, and component-library checks unless the snapshot itself contains direct evidence.
- Document only the variants and states that the snapshot actually proves. If coverage is incomplete, say so explicitly rather than inventing missing behavior.

---

## Command Substitution Rules

Reinterpret example commands like this:

| Reference example | What to run instead |
|---|---|
| `grep ... src/` | Search the actual UI directories under the target root |
| `grep ... app/` | Search the app directory only if the target really has one |
| `grep ... package.json` | Run only if a package manifest exists |
| `find src -name "*.stories.tsx"` | Search the real stories directory, or skip if Storybook is absent |
| `grep ... --include="*.tsx"` | In snapshot mode, switch the include set to `*.html`, `*.css`, and asset files as needed |

If a reference shows both `src/` and `.`, prefer the narrowest real path that still covers the UI evidence.

---

## Output Placement

- Write `.design-soul/` at the target root.
- If the original source is read-only, a copied working directory of that target is a valid target root.
- Do not place extraction output inside the skill directory or another unrelated parent folder.
