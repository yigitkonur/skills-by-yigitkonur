# build-skill

Creating or substantially revising a Claude skill and need workspace-first evidence, remote comparison, and repo-fit synthesis before writing SKILL.md.

**Category:** productivity

## Install

Install this skill individually:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-skill
```

Or install the full pack:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

## Remote Skill Search Helper

`build-skill` ships a **pure-bash** `skill-dl` for remote discovery and
download during the full research path. No install step, no proxy keys —
just `bash`, `git`, `curl`, and `npx` (Node.js).

```bash
cd skills/build-skill/skills/build-skill
bash scripts/skill-dl --help
bash scripts/skill-dl search typescript mcp server --top 20
bash scripts/skill-dl urls.txt -o ./research-corpus --no-auto-category -f
bash scripts/skill-research.sh --help
```

### Search channels

- **Primary** — `npx skills find <kw>` (no API key, covers the `skills.sh`
  registry).
- **Optional** — Serper Google API. Set `SERPER_API_KEY` to layer
  `playbooks.com` results on top:

  ```bash
  export SERPER_API_KEY=your_serper_key
  bash scripts/skill-dl search typescript mcp server --top 20
  ```

  Get a key at https://serper.dev. Without it, search runs npx-only and
  still works.

Scrapedo is **not used** and not required.
