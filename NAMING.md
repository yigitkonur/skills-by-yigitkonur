# Naming Standard

Every skill in this pack follows `verb-object` in `kebab-case`. The verb is what you'd say when reaching for the skill — *"I want to ___ ___"*. If the natural verb is not in the registry, the skill is named wrong.

Memory beats taxonomy. A small verb set is easier to recall than a precise one.

## The Twelve Verbs

| Verb | Use it when | Don't use it when | Example |
|---|---|---|---|
| `build-` | Write application code with a framework / SDK / library; produce a runnable project or component | The output is config / instructions for another tool (`init-`), or you're refreshing existing code (`update-`) | `build-chrome-extension`, `build-macos-app`, `build-mcp-server-sdk-v2`, `build-skill` |
| `init-` | Generate config / instruction files that another tool will consume (AGENTS.md hierarchies, Makefiles, Greptile rules, Copilot prompts) | The output is application code (`build-`) | `init-agent-config`, `init-makefiles` |
| `update-` | Refresh stale claims, counts, or references in an artifact that already exists and has drifted | Audit-only with no edits (`audit-`); writing from scratch (`build-` / `init-`) | `update-agent-config` |
| `convert-` | Transform an artifact from format A to format B; input and output shapes differ structurally | Producing documentation from existing code without a buildable output (`extract-`) | `convert-mcp-sdk-v1-to-v2`, `convert-url-to-nextjs` |
| `extract-` | Pull data, design tokens, or assets out of existing artifacts — output is documentation / structured data, not a runnable project | The output is a buildable project (`convert-`) | `extract-saas-design` |
| `run-` | Drive an external CLI / API / browser / tool for the user's current task during the session | The skill produces static config (`init-`) or writes app code (`build-`) | `run-railway`, `run-codex-2`, `run-linear-cli`, `run-research`, `run-agent-browser` |
| `audit-` | Read-only inspection; produce findings, no fixes | The skill also applies fixes (`update-`); the output is pass / fail (`test-`) | `audit-agentic-cli`, `audit-completion`, `audit-ui`, `audit-skill-by-derailment` |
| `review-` | Evaluate a code change for merge-readiness; produce reviewer feedback | Triaging *received* review feedback as input (that's `review-feedback` — distinct object); driving the review tool (`run-`) | `review-pr`, `review-self`, `review-feedback` |
| `test-` | Verify functional behavior with binary pass / fail evidence | The output is qualitative findings (`audit-` or `review-`); chasing a bug (`debug-`) | `test-by-mcpc-cli` |
| `debug-` | Chase a reproducible runtime bug or intermittent failure; methodology over inspection | Inspecting code statically (`audit-`); reviewing a diff (`review-`) | `debug-runtime` |
| `publish-` | Set up automated release / CI / packaging for a registry | Authoring the code being released (`build-`); single-shot ad-hoc deploy (`run-`) | `publish-npm-package` |
| `plan-` | Frame a decision, compare options, or apply a named decision methodology; produce a recommendation, not code | The output is a runnable artifact (`build-` / `init-`) | `plan-tradeoff` |

## The Intent Verb Test

Complete *"I want to ___ ___"*. If the natural verb isn't in the registry, the skill is misfiled.

- *"I want to **build** a Chrome extension"* → `build-chrome-extension` ✓
- *"I want to **audit** my agentic CLI"* → `audit-agentic-cli` ✓
- *"I want to **update** my AGENTS.md after the refactor"* → `update-agent-config` ✓
- *"I want to **run** Railway commands"* → `run-railway` ✓
- *"I want to **review** this PR"* → `review-pr` ✓
- *"I want to **debug** a runtime bug"* → `debug-runtime` ✓
- *"I want to **plan** between three architectural options"* → `plan-tradeoff` ✓

## Object Rules

1. **Name the thing acted on**, not the technique. `build-chrome-extension`, not `build-with-manifest-v3`.
2. **Preserve distinctive methodology names** in the object when the technique IS the value: `audit-skill-by-derailment`, `convert-url-to-nextjs`. Strip generic methodology names (`-with-X`, `-using-Y`).
3. **Use the ecosystem's own name** — `mcp-sdk-v2`, `langchain-ts`, `effect-ts-v3`.
4. **Keep it short** — 2-3 words max after the verb.
5. **No generic suffixes** — no `-guide`, `-helper`, `-util`, `-tool`.
6. **Version suffixes only when versions are genuinely different things** — `-sdk-v1` vs `-sdk-v2` (different APIs); not `-v2` as decoration.

## Disambiguation (frequent overlaps)

| Overlap | Rule |
|---|---|
| `audit-` vs `review-` | Audit produces a report. Review produces feedback **on a change** (PR, branch, diff). `audit-completion` (check claims), `review-pr` (judge a diff). |
| `audit-` vs `test-` | Audit produces narrative findings. Test produces binary pass / fail. `audit-ui` (visual findings), `test-by-mcpc-cli` (does it work? yes / no). |
| `update-` vs `audit-` | Update applies fixes. Audit only reports. `update-agent-config` does both phases — when in doubt, the action verb wins. |
| `run-` vs `build-` | Run drives a live tool during the session. Build produces an artifact. `run-railway` (drive Railway CLI), `build-tinacms-nextjs` (write TinaCMS code). |
| `init-` vs `build-` | Init outputs config for another tool. Build outputs runnable code. `init-makefiles` (configure Make), `build-mcp-use-server` (write a server). |
| `convert-` vs `extract-` | Convert produces a usable B from an existing A. Extract produces documentation / structured data. `convert-url-to-nextjs` (buildable project), `extract-saas-design` (documentation). |
| `plan-` vs `debug-` | Plan frames a decision without code. Debug chases a bug at runtime. `plan-tradeoff` (architectural decisions), `debug-runtime` (active bug hunt). |

## Canonical Rules

1. **Directory name** — `kebab-case`, starts with a registry verb, install-path-friendly
2. **Frontmatter `name`** — must exactly match the directory name (per agentskills.io spec)
3. **Per-skill `INSTALL.md` heading** — must exactly match directory name
4. **Cross-skill references** — always use canonical repo-local names
5. **Description** — starts with `Use skill if you are`, 30 words or fewer, describes when to trigger

## Anti-Patterns

| Anti-pattern | Fix |
|---|---|
| No verb prefix (`agent-browser`) | `run-agent-browser` |
| Verb not in registry (`orchestrate-codex`, `synthesize-skills`) | Pick from the 12: `run-codex-*`, `build-skill` |
| Generic suffix (`mcp-guide`, `claude-helper`) | Specific object: `build-mcp-server-sdk-v2` |
| `claude` or `anthropic` in skill name | Forbidden — agent-agnostic |
| `do-` or other generic verbs | Use the specific verb from the 12 |
| Multiple verbs (`build-and-publish-x`) | Two skills, or rename to the dominant verb |
| Version-as-decoration (`-v2`, `-final`) | Drop unless the version IS the point (`-sdk-v1` / `-sdk-v2`) |

## Migration History

The verb registry was rewritten on 2026-05-17. Renames applied in the same commit:

| Old | New | Reason |
|---|---|---|
| `apply-clean-mcp-architecture` | `build-clean-mcp-architecture` | `apply-` dropped; refactor IS code-writing → `build-` |
| `ask-review` | `review-self` | `ask-` dropped; opening a self-review IS a review |
| `check-completion` | `audit-completion` | `check-` dropped; read-only verification → `audit-` |
| `convert-mcp-server-sdk-v1-to-v2` | `convert-mcp-sdk-v1-to-v2` | Shorten object |
| `do-debug` | `debug-runtime` | `do-` dropped; `debug-` is the verb |
| `do-review` | `review-pr` | `do-` dropped; `review-` is the verb |
| `do-think` | `plan-tradeoff` | `do-` dropped; `plan-` is the verb |
| `do-ui-audit` | `audit-ui` | `do-` dropped; `audit-` is the verb |
| `enhance-agent-config` | `update-agent-config` | `enhance-` dropped; `update-` covers stale-ref refresh |
| `enhance-skill-by-derailment` | `audit-skill-by-derailment` | `enhance-` dropped; the skill tests for friction → `audit-` |
| `evaluate-code-review` | `review-feedback` | `evaluate-` dropped; triaging received feedback → `review-` |
| `optimize-agentic-cli` | `audit-agentic-cli` | `optimize-` dropped; audit-then-tune → `audit-` |
| `optimize-agentic-mcp` | `audit-agentic-mcp` | Same |
| `orchestrate-codex` | `run-codex-1` | `orchestrate-` dropped; numbered alias with `use-codex` (test-and-decide period) |
| `synthesize-skills` | `build-skill` | `synthesize-` dropped; output IS a SKILL.md artifact |
| `use-codex` | `run-codex-2` | `use-` dropped → `run-`; numbered alias with `orchestrate-codex` |
| `use-linear-cli` | `run-linear-cli` | `use-` → `run-` |
| `use-railway` | `run-railway` | `use-` → `run-` |

## Dropped Verbs (and why)

| Verb | Why dropped | What to use instead |
|---|---|---|
| `do-` | Too generic — every concrete intent fits a specific verb | The specific verb (`debug-`, `plan-`, `review-`, `audit-`) |
| `apply-` | Single-use; overlaps with `init-` (apply config) and `build-` (apply patterns to code) | `init-` or `build-` |
| `ask-` | Single-use; folded into the receiving verb | `review-self`, `request-` if needed |
| `check-` | Overlaps with `audit-` and `test-` | `audit-` for read-only; `test-` for pass / fail |
| `evaluate-` | Overlaps with `audit-` and `review-` | `audit-` when read-only; `review-` when feedback-producing |
| `enhance-` | Overlaps with `update-` | `update-` for stale refresh |
| `optimize-` | Overlaps with `update-` and `audit-` | `update-` for changes; `audit-` for report-only |
| `use-` | Overlaps with `run-` | `run-` is the active-execution verb |
| `develop-` | Overlaps with `build-` | `build-` always |
| `orchestrate-` | One skill; verb is too narrow | `run-` (drive the tool, the orchestration is the object) |
| `synthesize-` | One skill; the output is a buildable artifact | `build-` |

## Adding a New Skill

1. Test the verb: *"I want to ___ ___"*. If the natural fit isn't one of the 12, **don't propose the new skill** — re-frame to use an existing verb. If you genuinely can't, propose a new verb in a PR with rationale and ≥3 candidate skills using it.
2. Pick the object per the Object Rules.
3. Create `skills/<name>/SKILL.md` and `skills/<name>/INSTALL.md`. Use `references/` and `scripts/` as siblings if needed (agentskills.io spec).
4. Add a row to the root `README.md` table in alphabetical order.
5. Run `python3 scripts/validate-skills.py` — must pass.

## See also

- `CONTRIBUTING.md` — full quality checklist and skill structure rules
- `agentskills.io/specification` — canonical SKILL.md format and directory layout
