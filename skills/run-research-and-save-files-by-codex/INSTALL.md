# run-research-and-save-files-by-codex

Orchestrate a multi-file research corpus where Claude designs the waves,
folder tree, file names, and effort plan, but every web-research task is
delegated to a parallel `codex exec` subprocess. Same corpus shape and
filesystem-as-context-channel discipline as `run-research-and-save-files`;
codex becomes the executor of the search.

The skill itself lives at `skills/run-research-and-save-files-by-codex/SKILL.md`.

**Category:** productivity

## Install

Install this skill individually:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-research-and-save-files-by-codex
```

Or install the full pack:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```
