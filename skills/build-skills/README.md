# build-skills

Creating or substantially revising a Claude skill and need workspace-first evidence, remote comparison, and repo-fit synthesis before writing SKILL.md.

**Category:** productivity

## Install

Install this skill individually:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-skills
```

Or install the full pack:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

## Remote Skill Search Helper

`build-skills` uses `skill-dl` for remote discovery and download during the
full research path.

Install `skill-dl` globally:

```bash
sudo -v ; curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh | sudo bash
```

Use it after installation:

```bash
skill-dl --version
skill-dl search typescript mcp server --top 20
skill-dl urls.txt -o ./research-corpus --no-auto-category -f
```

The skill also bundles helper scripts under
`skills/build-skills/skills/build-skills/scripts/`:

```bash
cd skills/build-skills/skills/build-skills
bash scripts/skill-dl --help
bash scripts/skill-research.sh --help
```

On macOS Apple Silicon, `bash scripts/skill-dl ...` can fall back to the
bundled `scripts/skill-dl-darwin-arm64` binary when `skill-dl` is not already
installed in `PATH`.
