# AGENTS.md — skills-by-yigitkonur

A pack of agent skills. The source is `skills/`; people install it with the `skills` CLI (`npx skills add yigitkonur/skills-by-yigitkonur --skill <name>`). There is no plugin or marketplace layer, no generated copy of any skill, and no version file. Keep it that way.

## Layout

```
skills/<verb-object>/
├── SKILL.md              required, hand-written
├── agents/openai.yaml    required: policy.allow_implicit_invocation: false
├── references/           optional, nested folders allowed
├── scripts/              optional helpers
└── assets/               optional templates and fixtures
scripts/validate-skills.py
tests/                    tests for individual skills
.githooks/                pre-commit and pre-push run the validator
README.md                 one section per skill, with its install command
```

## Rules the validator enforces

Run `python3 scripts/validate-skills.py` before every push. CI runs it too.

- Frontmatter `name` equals the directory name. `description` is at most 30 words.
- Every skill is manual-only: `disable-model-invocation: true` in the `SKILL.md` frontmatter (Claude Code, Cursor, VS Code) and `agents/openai.yaml` with `allow_implicit_invocation: false` (Codex ignores the frontmatter key).
- Every file under `references/` is linked from `SKILL.md`. Links to files that do not exist fail.
- `SKILL.md` stays short: aim for 500 lines, the validator fails above 1000. Put detail in `references/`.
- No junk (`.DS_Store`, `.swp`), no `evals/` or `__pycache__/` directories, no `LICENSE` or `CHANGELOG.md` inside a skill.
- `run-research` follows the Research Powerpack v9 tool names; the validator rejects the retired ones.

## Naming

`verb-object` in kebab-case, where the verb is the one you would say out loud when reaching for the skill.

- `build` write code with a framework or SDK, `run` drive a CLI or tool, `audit` check against evidence, `convert` turn A into B, `init` create config or instruction files, `publish` release to a registry, `test` verify with pass/fail, `deploy` ship a service, `upgrade` move to a newer version, `use` ongoing tool use.
- Name the thing acted on, in the ecosystem's own words (`mcpc`, `tsgo`). Keep a distinctive method in the name (`-by-derailment`, `-to-nextjs`, `-sdk-v1`).
- Two or three words after the verb. No `-guide`, `-helper`, `-util`. No version suffix unless the versions are different products.
- Never put "claude" or "anthropic" in a skill name. Keep `<` and `>` out of frontmatter values. The validator does not check these two.
- Two names predate this pattern and stay for install-path compatibility: `herdr` (upstream's name, invoked as `/herdr`) and `ci-cd-optimize`. New skills do not copy them.

## Writing a skill

- `SKILL.md` is for the agent: direct and operational ("Do X", "Never Y"), a workflow or a router to `references/`. No hype, no duplicated blocks.
- The description says when to use the skill, not what the body contains.
- Cross-skill references use the directory name of the other skill.
- Research before writing a non-trivial skill. Distill, do not copy another skill.

## Adding, renaming or removing a skill

1. Create or change `skills/<name>/`, then validate.
2. Add, rename or remove its section in `README.md` (alphabetical): one line and the install block `npx skills add yigitkonur/skills-by-yigitkonur --skill <name>`.
3. On rename, also update every `skills/*` file that mentions the old name.

## Setup

```bash
git config core.hooksPath .githooks   # once: validator runs on commit and push
```
