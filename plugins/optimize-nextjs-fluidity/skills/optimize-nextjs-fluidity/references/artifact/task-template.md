# Task file template

One markdown file per task under `nextjs-enhancement/tasks/`. This is the unit the fix
agents execute and the unit a human reviews. Filename: `NN-<verb-object-slug>.md`, where
`NN` encodes **dependency order** (not discovery order) and the slug is verb-first
(`remove-edge-runtime-exports`, `migrate-priority-to-fetchpriority`).

```markdown
# Task NN: <Verb-object title>

**Status:** pending
**Domain:** <one of the 14 domain slugs>
**Severity:** critical | major | minor
**Reversibility:** fully-reversible | component-level-revert | migration-required
**Auto-apply:** yes | no — <reason if no>
**Depends on:** [Task 0X](0X-slug.md) — or `none`
**Blocks:** [Task 0Z](0Z-slug.md) — or `none`
**Composition step:** <1-14 from references/gating/composition-recipe.md>

## Why this matters

One or two sentences. What breaks, costs, or degrades if this stays as-is. Present tense,
specific to this repo. No generic performance rhetoric.

## Evidence

- `src/path/file.tsx:142` — `<literal matched text>`
- `src/path/other.tsx:88` — `<literal matched text>`

Source finding: [`../findings/<domain>/NN-slug.md`](../findings/<domain>/NN-slug.md)

## Applicability

Installed Next.js `<version>`; capability probe: `<key> → present|absent|unresolved`.
State why this task is valid on *this* install. If the fix uses a version-gated API, name
the floor and confirm the probe cleared it.

## Recipe

`references/fix/<domain>.md` § `<exact recipe H2 name>`

## Exact change

```diff
- <before>
+ <after>
```

For multi-file changes, one diff block per file with a `# path` comment above it. If the
change is structural rather than line-level, describe it as an ordered list of concrete
edits — never as prose intent.

## Verification command

```bash
<exact reproducible command>
```

**Expected:** <what a pass looks like — specific output, header, panel state, or metric>
**Rung:** static | type/lint | build | runtime | measured
(see `references/workflow/verification-playbook.md`)

## Rollback

<The literal inverse operation: which line, prop, import, or file to restore.>

## Cost / risk note

<One line when the change touches billing primitives or a conflict family. Cite
`references/gating/cost-model.md` or `references/gating/conflicts.md`. Otherwise: `none`.>

## Fix tracking

- [ ] Applied by agent #<N>
- Commit: `<sha>`
- Verification: `<pass | fail>` — `<output excerpt>`
- Notes: `<anything the next reader needs>`
```

## For `migration-required` tasks

Add before `## Fix tracking`:

```markdown
## Pre-flight checklist (human decision required)

Status is `blocked-needs-human`. This change is a one-way door: <named exit cost>.

- [ ] <checklist items, copied from references/gating/lockin-reversibility.md>
```

Never set `Auto-apply: yes` on one of these.

## Rules

1. **One task, one coherent change.** Twelve call sites of one deprecated prop is one task.
   A change spanning more than ~10 files must be split.
2. **Evidence is copied, not summarised.** `file:line` plus the literal matched text.
3. **No task without a verification command.** If none exists, the task stays `pending`
   with a note — do not invent a check.
4. **Ordinals reflect dependencies.** A task must never be ordinaled before something it
   depends on.
5. **`Blocks` is the reverse edge of `Depends on`** — keep both in sync at Phase 4.
6. **Status vocabulary is fixed:** `pending` · `in-progress` · `done` · `blocked` ·
   `blocked-needs-human` · `wontfix`. Nothing else parses.

## Worked example

```markdown
# Task 03: Migrate deprecated `priority` prop to `fetchPriority`

**Status:** pending
**Domain:** image-optimization
**Severity:** minor
**Reversibility:** fully-reversible
**Auto-apply:** yes
**Depends on:** none
**Blocks:** none
**Composition step:** 2

## Why this matters

`priority` is deprecated as of Next.js 16.0 and will be removed in a future major. It
still works on the installed 16.2.9, so nothing is broken today — but every new call site
adds migration debt, and the successor props express intent more precisely.

## Evidence

- `src/components/project-image.tsx:128` — `priority?: boolean`
- `src/components/project-image.tsx:232` — `priority={priority}`

Source finding: [`../findings/image-optimization/02-deprecated-priority-prop.md`](../findings/image-optimization/02-deprecated-priority-prop.md)

## Applicability

Installed Next.js 16.2.9 — at/above the 16.0 deprecation, below any removal. Both
successor props (`fetchPriority` 13.3+, `loading` core) exist. All six call sites route
through this one wrapper, so the wrapper is the only edit point.

## Recipe

`references/fix/image-optimization.md` § `priority → successor migration`

## Exact change

```diff
# src/components/project-image.tsx
-          priority={priority}
+          fetchPriority={priority ? 'high' : undefined}
+          loading={priority ? 'eager' : loading || 'lazy'}
```

## Verification command

```bash
rg -n 'priority=\{' src/components/project-image.tsx; npx tsc --noEmit
```

**Expected:** no `priority={` remains in the wrapper; typecheck passes.
**Rung:** type/lint

## Rollback

Restore `priority={priority}` and remove the two successor props.

## Cost / risk note

none

## Fix tracking

- [ ] Applied by agent #<N>
- Commit: `<sha>`
- Verification: `<pass | fail>` — `<output excerpt>`
```
