# Detect template — every domain audit file follows this shape

Use this exact structure for every file under `references/detect/`. The point is uniform
output: a domain audit agent can switch domains just by switching files, not by changing
how it thinks.

```markdown
# Detect: <domain>

**Corpus lineage:** <pack>/00-...md, <pack>/03-...md (or 02), <pack>/07-...md, <pack>/08-...md

## Applicability gate

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| `<exact API / flag name>` | `<X.Y.Z or legacy>` | `<prerequisite flag / runtime / package>` | `<X.Y.Z or n/a>` | NOT APPLICABLE if repo support is absent; BLOCKED if prerequisite missing; REMOVE if repo has a dead surface at a version where it is gone. |

(One row per gated feature in this domain, sourced from `references/gating/version-matrix.md`.)

## Detection commands

Read-only only. Prefer `rg`; fall back to `grep -rn` if needed. Every command must map 1:1 to a gate row or a pitfall signature.

```bash
# one-line purpose
rg -n '<pattern>' --glob '<glob>' <target-repo-root>
```

## Domain severity rubric

- **critical** — removed API/flag in live use; architectural precondition violated; user-visible breakage likely or build/runtime failure likely
- **major** — P0-tier practice absent or misconfigured for this archetype; likely measurable CWV/UX harm
- **minor** — stable opt-in not adopted; deprecated-but-still-functional surface; quality gap without current breakage
- **informational** — intentional divergence, wrapper indirection, or a note a fixer should know, but not a task by itself

Add 2–4 domain-specific examples under each level.

## False-positive filters

List domain-specific exclusions. Typical examples:
- comments/docstrings do not count as live usage
- test files are excluded
- known non-page render contexts (RSS routes, `api/og`, Satori) are exempt from page-HTML/image rules
- wrapper components collapse many call sites into one shared finding
- deliberate config divergence with an adjacent explanatory comment is informational unless the corpus says it is unsafe

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under `findings/<domain>/` must include:
- `file:line` (exact)
- literal matched text (copied from rg/grep output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (verbatim or near-verbatim from the corpus-derived prose below)
- suggested fix recipe section name from `references/fix/<domain>.md`

## Pitfall signatures

Table: `Failure signature | Cause | Fix direction | Recipe section`

Lift these from the pack's 07-file. Keep the cause→fix mapping terse and reproducible.

## Cross-domain interactions

1–3 short bullets naming dependencies or suppressions. Example: “If `cacheComponents`
is absent, skip every Partial Prefetching recommendation and downgrade related findings to
NOT APPLICABLE.”

## Reference pointer

Fix recipes for this domain live in `references/fix/<domain>.md`.
```

## Non-negotiable rules

1. **Use the installed package as the arbiter.** A gate row must say "probe first" if the
   surface is known to differ across nearby minors (`experimental.viewTransition` is the
   canonical example).
2. **Commands must be copy-pastable.** A subagent should be able to run each command
   verbatim against the target repo root.
3. **Every domain gets a false-positive section.** The zeo recon proved this is not
   optional (`export const dynamic` inside a comment, RSS routes containing `<img>`, etc.).
4. **Zero findings is valid.** If the repo already conforms, the subagent writes nothing.
