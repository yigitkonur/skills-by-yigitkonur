# Conventional Commits (+ Gitmoji)

Subject line format:

```
<emoji> <type>(<scope>): <imperative subject>

<body>

<footer>
```

## Type registry

Use the narrowest fitting type. If two fit, split the commit.

| Type | Emoji | When |
|---|---|---|
| `feat` | ✨ | New user-visible capability. |
| `fix` | 🐛 | Bug fix that changes observable behavior. |
| `docs` | 📝 | Documentation only (README, AGENTS.md, JSDoc, comments-as-contract). |
| `refactor` | ♻️ | Same behavior, different shape. Split from `feat`/`fix`. |
| `test` | ✅ | Test-only changes (adds, fixes, renames, restructures). |
| `chore` | 🔧 | Tooling, deps, build config that doesn't fit `build`/`ci`. |
| `perf` | ⚡ | Observable speed/memory/bundle-size improvement. |
| `build` | 📦 | Changes to build system, compiler, bundler, package manager. |
| `ci` | 👷 | CI pipelines, GitHub Actions, pre-commit hooks. |
| `revert` | ⏪ | `git revert`-style undo of a prior commit. |
| `style` | 🎨 | Formatting, whitespace, semicolons. Avoid if `format-on-save` handles it. |

Use one of these. Don't invent new types for one-off commits.

## Scope rules

The scope is a short label for the affected area. Rules:

1. **One scope per commit.** Two scopes = two commits.
2. **Name the thing touched**, not the action. `feat(auth)` not `feat(add-login)`.
3. **Short** — 1–3 kebab-case words max.
4. **Use the ecosystem's own name** when the project already has one (`feat(router)` if the code calls it "router", not "routing").
5. **Omit when truly cross-cutting** (e.g. `chore: upgrade pnpm` with no single scope).

Examples, good:
- `feat(onboarding): replace interests with marketing set`
- `fix(chat-input): hide model selector behind action-bar filter`
- `docs(wope): document lockdown layer in AGENTS.md`

Examples, bad:
- `feat: new stuff` — no scope, no specificity
- `feat(src/features/ChatInput/ActionBar/Model/index.tsx): ...` — full path is not a scope
- `fix(various): multiple small fixes` — should be N commits

## Subject rules

- **Imperative mood.** "add", not "added" or "adds". The reader completes the sentence "If applied, this commit will <subject>".
- **≤50 characters** (soft cap) including emoji + type + scope.
- **No trailing period.**
- **No issue/PR references** in the subject — put those in the footer.

## Body rules

- Blank line between subject and body.
- Wrap at ~72 chars.
- Explain the **why**, not the **what** (the diff already shows the what).
- One paragraph per concern. Bullet lists for enumerations.
- Reference architecture decisions, previous related commits (by short SHA), or incident IDs when relevant.

## Footer rules

- Blank line between body and footer.
- `BREAKING CHANGE: <description>` when the public API/behavior changes. Required for SemVer major bumps.
- Issue/PR references: `Refs: #123`, `Closes: #456`, `Reverts: <short-sha>`.
- Co-authored-by: line if the change came out of a pair/mob session.

## Full example

```
✨ feat(wope-lockdown): brand + behavior lockdown layer

Pins the product to a single hardcoded OpenAI-compatible provider,
hides configuration UI, rebrands the loader + theme label, reorients
onboarding for a marketing audience, and auto-seeds the default MCP
for every user.

Ten items in one layer:

1. Disable react-scan overlay in src/initialize.ts.
2. Skip ProSettings onboarding step via src/features/Onboarding/Classic.
...

Refs: #42
BREAKING CHANGE: /settings/provider/* routes are removed; deep links
now redirect to /.
```

## Breaking changes

Two notations, use either:

- **Footer:** `BREAKING CHANGE: <what breaks, how to migrate>`
- **Bang:** `feat(api)!: remove v1 endpoints` — `!` after the scope.

Using both is fine and traditional. Either alone is sufficient for SemVer tooling.

## Revert pattern

When reverting:

```
⏪ revert: "<original commit subject>"

This reverts commit <full SHA>.

<why the revert is needed, what would be a correct alternative>
```

`git revert <sha> --no-edit` produces a usable skeleton; add the "why" paragraph.

## Why gitmoji

Purely visual scanning aid for long commit histories. The emoji is decorative — the type is what tools (release-please, semantic-release, commitlint) actually parse. Don't let a reviewer fight over emoji choice; pick the one closest from the table above and move on.

If a repo's `AGENTS.md` or CI forbids emoji in commit messages, drop them. Conventional Commits stands alone.

## Don't

- Don't use `fix` for behavior changes — that's `feat` or `refactor`.
- Don't use `chore` as a catch-all. If it fits `build`/`ci`/`test`, use the narrower type.
- Don't prefix with a ticket ID (`[JIRA-123] feat: ...`). Put the reference in the footer.
- Don't write subjects longer than 50 chars. If you need that much, your commit is doing too much.
- Don't squash unrelated commits to "clean up" — granular history is evidence.

## Tool hints

- `commitlint --from <base> --to HEAD` validates Conventional Commits across a range. Run before pushing.
- `git log --oneline --no-merges <base>..HEAD` is the fastest way to scan your upcoming PR's commits.
- `git log --format='%s' <base>..HEAD | head -20` feeds straight into a PR body draft.

---

Repo-local overrides win. If the target repo's `CONTRIBUTING.md` says "no emoji" or "type only, no scope" or "use our bespoke format", follow that. This doc is the fallback when the repo is silent.
