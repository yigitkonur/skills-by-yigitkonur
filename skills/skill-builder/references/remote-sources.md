# Remote Sources

Use this file when the task requires outside skill examples.

## Primary source pattern

Start with remote skill directories that expose repeatable listing pages and stable detail URLs.

For the current workflow, the main pattern is Playbooks-style discovery:

- listing root: `https://playbooks.com/skills`
- search page: `https://playbooks.com/skills?search=<query>`
- paginated search page: `https://playbooks.com/skills?search=<query>&page=<n>`
- detail page: `https://playbooks.com/skills/{owner}/{repo}/{skill}`

## What to collect from listings

Capture fields that support later comparison, not just download automation.

Useful fields include:

- skill title
- owner or repo label
- detail URL
- short description
- popularity signal when present
- verified signal when present
- pagination coverage so the reader knows how broad the search was

Keep enough detail to explain why a source was selected, not just that it existed.

## Downloader mapping assumptions

A Playbooks detail URL usually maps to a GitHub repo in this shape:

- `playbooks.com/skills/{owner}/{repo}/{skill}`
- `github.com/{owner}/{repo}`

The skill may live inside that repo in more than one layout. Common locations include:

- `skills/{skill}`
- `{skill}`
- `.skills/{skill}`
- `.claude/skills/{skill}`
- `.agent/skills/{skill}`
- `.opencode/skills/{skill}`
- `.cursor/skills/{skill}`
- `.agents/skills/{skill}`
- `src/skills/{skill}`

If the repo root itself contains `SKILL.md`, treat it as a root-level skill repo.

## Download discipline

When copying remote examples:

- preserve the real skill files that explain how the skill works
- keep bundled references, scripts, and assets when they are part of the skill itself
- exclude obvious repo metadata and packaging noise
- treat downloaded examples as temporary evidence unless the user explicitly wants them shipped

## How to use downloaded examples

Downloaded skills are evidence, not templates to clone.

After download:

1. run `tree` on the downloaded corpus
2. read the relevant files
3. cite relative paths in your comparison table
4. inherit patterns selectively
5. rewrite the final result so it is original and repo-fit

## Expansion rule

If you later support more remote ecosystems, document each one with the same structure:

- listing URL pattern
- detail URL pattern
- fields available from listings
- repo or archive mapping assumptions
- parser caveats
- how downloaded material should be treated during synthesis
