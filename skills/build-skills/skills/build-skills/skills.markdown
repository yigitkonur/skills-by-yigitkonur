# build-skills revision research

## Scope

Revise `build-skills` so its remote research workflow has complete `skill-dl`
installation guidance, a proper `scripts/` directory, a bundled macOS arm64
binary fallback, and script usage that matches the current Agent Skills
guidance for bundled scripts.

## Local evidence

### Workspace scan

- `skills/build-skills/README.md`
- `skills/build-skills/skills/build-skills/SKILL.md`
- `skills/build-skills/skills/build-skills/references/remote-sources.md`
- `skills/build-skills/skills/build-skills/references/research-workflow.md`
- `skills/build-skills/skills/build-skills/references/research/search-strategies.md`
- `skills/build-skills/skills/build-skills/references/iteration/troubleshooting.md`
- `skills/build-skills/skills/build-skills/references/checklists/master-checklist.md`
- `skills/build-skills/skills/build-skills/references/distribution/publishing.md`
- `skills/build-skills/skills/build-skills/references/examples/anti-patterns.md`
- existing helper script originally at `references/skill-research.sh`

### Local gaps

- The skill referenced `skill-dl`, but the install command still used
  `curl ... | bash` instead of the current privileged installer flow.
- Search and download docs did not explain how to use `skill-dl` after
  installation.
- The helper script lived under `references/` instead of `scripts/`, which
  conflicts with the current Agent Skills guidance for executable helpers.
- There was no bundled fallback for macOS arm64 despite the user requesting one.

## Remote sources

### Agent Skills docs

1. `https://agentskills.io/skill-creation/using-scripts`
2. `https://agentskills.io/client-implementation/adding-skills-support`

## Source notes

### Current local build-skills skill

- Strengths:
  - strong research-first workflow
  - good routing to references
  - already treats `skill-dl` as the preferred research tool
- Gaps:
  - outdated install guidance
  - scripts not surfaced as first-class resources
  - no script help contract
- Relevant paths:
  - `SKILL.md`
  - `references/remote-sources.md`
  - `references/research-workflow.md`
  - `references/skill-research.sh` (before move)
- Decision:
  - inherit the workflow; avoid keeping executable helpers under `references/`

### Agent Skills: Using scripts

- Strengths:
  - explicit rule that scripts belong in `scripts/`
  - requires listing scripts in `SKILL.md`
  - says script paths are relative to the skill directory root
  - strong guidance on `--help`, noninteractive behavior, useful errors, and
    stdout/stderr discipline
- Gaps:
  - does not prescribe a packaging strategy for compiled binaries
- Relevant sections:
  - bundled `scripts/` usage
  - relative path references from `SKILL.md`
  - `--help` and noninteractive guidance
- Decision:
  - inherit the `scripts/` structure, relative-path routing, and `--help`
    requirement

### Agent Skills: Adding skills support

- Strengths:
  - reinforces progressive disclosure
  - clarifies that scripts/resources should be exposed but not eagerly read
  - clarifies that relative paths resolve from the skill directory root
- Gaps:
  - aimed at client implementors, not skill authors
- Relevant sections:
  - catalog / instructions / resources tiers
  - bundled resource listing
  - location/base-directory path handling
- Decision:
  - inherit the explicit script listing and relative-path assumptions in
    `SKILL.md`; avoid overloading the main skill file with binary details

## Comparison table

| Source | Focus | Strengths | Gaps | Relevant paths or sections | Inherit / avoid |
|---|---|---|---|---|---|
| Local `build-skills` | Research workflow for skill creation | Strong workflow, good routing, clear guardrails | Old installer command, scripts misplaced, no bundled fallback | `SKILL.md`, `references/remote-sources.md`, old `references/skill-research.sh` | Inherit workflow and references; avoid keeping executable helpers under `references/` |
| Agent Skills: Using scripts | Script packaging and agent-facing interfaces | Clear `scripts/` rule, relative paths, `--help`, noninteractive guidance | No binary packaging advice | `Using scripts`, `Referencing scripts from SKILL.md`, `Document usage with --help` | Inherit script layout and help/error conventions |
| Agent Skills: Adding skills support | Progressive disclosure and resource exposure | Clear resource-tier model and path resolution | Client-side, not author-side | progressive disclosure tiers, bundled resources, base directory handling | Inherit explicit script listing and root-relative execution; avoid client-only detail in main workflow |

## Synthesis decisions

- Move the executable helper from `references/skill-research.sh` to
  `scripts/skill-research.sh`.
- Add `scripts/skill-dl` as the stable entrypoint for all `skill-dl` usage in
  this skill.
- Bundle `scripts/skill-dl-darwin-arm64` as the macOS arm64 fallback binary.
- Update all search/download/install guidance to use the current installer:
  `sudo -v ; curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh | sudo bash`
- Tell users how to use the tool after installation, not just how to install it.
- Keep direct `skill-dl` examples for globally installed usage, but prefer
  `bash scripts/skill-dl ...` inside the skill's own instructions.

## Next-use note

If this skill is revised again, re-check:

1. the bundled binary still matches the published `skill-dl` interface
2. the global installer command still points to the current release path
3. `scripts/skill-research.sh` still uses only root-relative script paths
