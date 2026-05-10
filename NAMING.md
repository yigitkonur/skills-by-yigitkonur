# Naming Standard

Every skill name in this pack follows **`verb-object`** in `kebab-case`. The verb is the most important word — users scan by what they want to *do*.

## The Intent Verb Test

The verb in a skill name must be the verb you'd say out loud when reaching for it. Test by completing: *"I want to ___ ___"*. If the natural verb isn't in the name, rename.

Memory beats taxonomy. The right verb is the one that pops into your head when you need the skill — not the one a maintainer files it under.

## Verb Set

Anchor on this set of plain-English intent verbs:

| Verb | Use when | Example |
|---|---|---|
| `build` | Write app code with a framework or SDK | `build-chrome-extension`, `build-macos-app`, `build-mcp-server-sdk-v1` |
| `do` | Generic "let me do this" entry-point skill | `do-debug`, `do-think`, `do-review` |
| `apply` | Apply a methodology or standard to a codebase | `apply-clean-mcp-architecture` |
| `ask` | Hand off / request something | `ask-review` |
| `run` | Drive a CLI, tool, or workflow | `run-agent-browser`, `run-research` |
| `convert` | Transform A to B | `convert-url-to-nextjs` |
| `check` | Audit for completeness | `check-completion` |
| `evaluate` | Triage existing feedback or input | `evaluate-code-review` |
| `extract` | Pull data, design, or assets from existing artifacts | `extract-saas-design` |
| `init` | Generate config or instruction files | `init-agent-config` |
| `enhance` | Improve a prompt, skill, or instruction | `enhance-skill-by-derailment` |
| `orchestrate` | Coordinate N parallel agents under one policy and one observability surface | `orchestrate-codex` |
| `optimize` | Tune for a constraint (e.g. agentic) | `optimize-agentic-cli` |
| `develop` | Apply language-level patterns and standards | _(reserved — no current skill uses this verb)_ |
| `publish` | Release to a registry | `publish-npm-package` |
| `test` | Verify with pass/fail | `test-by-mcpc-cli` |
| `use` | Drive a CLI utility for ongoing operations | `use-railway` |

If none of these fit, propose a new verb in a PR alongside the new skill.

## Object Rules

1. **Name the thing acted on** — not the technique. `build-chrome-extension`, not `build-with-manifest-v3`.
2. **Preserve distinctive methodology names** in the object. `enhance-skill-by-derailment` keeps "derailment". `test-by-mcpc-cli` keeps "mcpc". `convert-url-to-nextjs` keeps "to-nextjs". Strip only the generic verb category — never the named technique.
3. **Use the ecosystem's own name** — `mcpc`, `liquid-glass`, `daisyui`.
4. **Keep it short** — 2-3 words max after the verb.
5. **No generic suffixes** — no `-guide`, `-helper`, `-util`.
6. **No version suffixes** unless the version is the point. `-sdk-v1` is OK because v1 and v2 are genuinely different SDKs.

## Disambiguation

When two skills overlap, use distinct verbs:

- `do-review` (do a PR review) vs `ask-review` (ask for a review on your branch)
- `do-debug` (entry-level systematic debug) vs `do-think` (deep reasoning framework)
- `run-research` (answer a technical research question) vs `run-industry-research` (build a full market/category research corpus)
- `optimize-agentic-cli` handles CLI-only audits and command-contract design

## Canonical Rules

1. **Directory name** — `kebab-case`, starts with an intent verb, install-path-friendly
2. **Frontmatter `name`** — must exactly match the directory name
3. **README label** — must exactly match directory name and frontmatter `name`
4. **Cross-skill references** — always use canonical repo-local names
5. **Description** — starts with `Use skill if you are`, 30 words or fewer, describes when to trigger

## Anti-Patterns

| Anti-pattern | Fix |
|---|---|
| No verb prefix (`agent-browser`) | `run-agent-browser` |
| Awkward verb (`do-X` when a better verb fits) | Use the better verb (`extract-saas-design`, not `do-extract-design`) |
| Stripping a distinctive method (`enhance-skill` instead of `enhance-skill-by-derailment`) | Keep the method, normalize the verb only |
| Generic noun-only object (`build-app`) | Specific noun (`build-chrome-extension`) |
| Mismatched names | Directory = frontmatter `name` = README label, all identical |
| Version suffix as decoration (`-v2`, `-final`) | Drop unless the version is the point (`-sdk-v1`) |
| Marketing name as primary ID (`soul`, `powerpack`) | Use `verb-object` for the directory; marketing name in SKILL.md title only |
| `claude` or `anthropic` in skill name | Forbidden — use a different name |

## Migration Rule

When renaming a published skill:

1. Rename outer directory: `git mv skills/old skills/new`
2. Rename inner content directory: `git mv skills/new/skills/old skills/new/skills/new`
3. Update frontmatter `name:` field
4. Update per-skill README heading and install paths
5. Update root `README.md` table row
6. Update `NAMING.md` canonical list
7. Search cross-skill references and update each
8. Run `python3 scripts/validate-skills.py`

## Current Canonical Skill Names

The canonical name is the directory name. List live skills with `ls skills/` rather than maintaining a hard-coded roster here.
