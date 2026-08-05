# Fix-file contract — every domain recipe file follows this shape

Use this exact structure for every file under `references/fix/`. A fix subagent reads one
of these plus its task file and must be able to make the change without further research.

```markdown
# Fix: <domain>

**Corpus lineage:** <pack>/04-...md, <pack>/05-...md, <pack>/08-...md
**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs. Confirm any
config key against the installed package first — see `references/gating/capability-probe.md`.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| <H2 name> | `<version floor / flag / package>` | fully-reversible \| component-level-revert \| migration-required | <detect finding it answers> |

## <Recipe name> — requires Next.js ≥X.Y.Z<, flag Z>

**When to apply:** one line naming the detect finding that triggers this.

```tsx
// <file path pattern> — Next.js X.Y.Z
<code>
```

**Why each non-obvious line exists:** bullets. Keep the reasoning that explains a
non-obvious prop or ordering; drop citation apparatus.

**Verify after applying:** an exact, reproducible check — a command, a DevTools panel and
what to look for, a specific Lighthouse audit name, or an observable HTML/network change.
Never "looks fine".

**Lock-in / reversibility:** one line, matching `references/gating/lockin-reversibility.md`.
If `migration-required`, name the exit cost here, not just a pointer.

**Rollback:** the literal inverse operation — which line, prop, or import to restore.

## Ordering within this domain

Numbered list when recipes have a required order (e.g. remove Edge exports before
enabling Cache Components). Cross-reference `references/gating/composition-recipe.md`.

## Conflicts to watch

Rows lifted from `references/gating/conflicts.md` that touch this domain.
```

## Non-negotiable rules

1. **Version-annotate every heading.** `— requires Next.js ≥16.3.0` in the H2 itself, so a
   recipe can be skipped by reading its title alone.
2. **Every recipe carries both `Verify after applying` and `Rollback`.** A change the
   executor cannot verify or undo must not ship as a recipe.
3. **Custom-implementation variants.** Where the standard recipe assumes a library
   (`next-themes`, `next-intl`), add a sibling variant for repos that rolled their own —
   the audit verdict `APPLICABLE-CUSTOM` routes here. Frame it as "adapt this mechanism",
   never "replace your implementation with the library".
4. **No invented APIs.** Every prop, key, and import must appear in the corpus pack this
   file distills. If the corpus does not show it, it does not go in.
5. **Keep code runnable.** TS/TSX, complete imports, file-path comment on line 1.
