# Review Context

How to create `REVIEW.md` without turning it into a duplicate `AGENTS.md` file.

## Contents

- [Purpose](#purpose)
- [When To Create It](#when-to-create-it)
- [Root Review File](#root-review-file)
- [Scoped Review Files](#scoped-review-files)
- [Writing Rules](#writing-rules)
- [Relationship To Native Adapters](#relationship-to-native-adapters)

## Purpose

`REVIEW.md` standardizes what changes should be flagged, protected, or held to a higher bar during review.

Use it to capture:
- repo-specific diff risks
- high-risk architectural boundaries
- security, data, API, schema, or migration changes that need scrutiny
- review ignore rules for generated or irrelevant files
- testing expectations that reviewers should require for risky changes

Do not use it for:
- agent workflow instructions
- generic coding advice
- rules already enforced by lint, format, typecheck, or deterministic tests
- platform-native syntax for Copilot, Devin, or Greptile
- a second copy of `AGENTS.md`

## When To Create It

Default to a root `REVIEW.md` when the run is standardizing repository review context or when discovery finds review-critical risks worth encoding.

Document an explicit exception instead of creating `REVIEW.md` when:
- the user requested only AGENTS migration or companion entrypoints
- the repo has no shared review standard or risk model to encode yet
- an existing repository policy already provides the same review context and duplicating it would create drift

If you skip `REVIEW.md`, say why in the final response.

## Root Review File

The root file should answer:

`What kinds of changes should be flagged or scrutinized because they break this repo's intended standards or risk boundaries?`

Suggested section order:
- `## Critical Areas`
- `## Security`
- `## Conventions`
- `## Performance`
- `## Patterns`
- `## Ignore`
- `## Testing`

Only include sections backed by repo evidence. Prefer 5-10 strong review rules over a long checklist.

## Scoped Review Files

Use scoped `REVIEW.md` files only when a subtree has review risks that would bloat or contradict the root.

Good scoped triggers:
- a package owns public contracts or schemas
- a service has distinct auth, data, migration, or deployment risks
- a docs or skills subtree has standards that differ from application code
- generated code needs special ignore or regeneration review rules

Do not create scoped review files just because a folder has a local `AGENTS.md`. Most local `AGENTS.md` files do not need a matching `REVIEW.md`.

## Writing Rules

- Ground every rule in repo evidence.
- Make each rule specific, measurable, actionable, and semantic.
- Put highest-risk rules first.
- Skip anything already enforced by tooling unless reviewers need to verify the tooling was run.
- Keep operating instructions in `AGENTS.md`; keep diff scrutiny in `REVIEW.md`.
- If review drafting exposes a missing work boundary, update the relevant `AGENTS.md` instead of stuffing workflow guidance into `REVIEW.md`.
- Preserve existing review warnings unless the repo proves they are stale.
- Keep unresolved unknowns in the response, not in the file.

## Relationship To Native Adapters

Native review adapters are translations of completed review context, not independent policy files.

| Platform | Native files | Relationship to `REVIEW.md` |
|----------|--------------|-----------------------------|
| Copilot | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` | Translate root and scoped review criteria into Copilot-compatible files |
| Devin | `REVIEW.md`, optional scoped `REVIEW.md` | Treat `REVIEW.md` as the main Bug Catcher review surface |
| Greptile | `.greptile/config.json`, optional `rules.md`, `files.json` | Translate review criteria into config plus prose/context files |

Ask about native adapters only after the AGENTS hierarchy and review-context decision are complete.
