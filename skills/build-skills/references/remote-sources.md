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

## Downloading skills with skill-dl

`skill-dl` is the primary tool for downloading skills from Playbooks URLs.

### Installation check

```bash
skill-dl --version
# Expected: skill-dl v1.1.0+
```

### URL format

Every Playbooks skill URL maps to a GitHub repo:

- `playbooks.com/skills/{owner}/{repo}/{skill}` → `github.com/{owner}/{repo}`

`skill-dl` handles the mapping, cloning, and extraction automatically. It groups URLs by repo so each repo is cloned only once, even when downloading multiple skills from the same repo.

### Single skill

```bash
skill-dl https://playbooks.com/skills/vercel-labs/agent-browser/agent-browser \
  -o ./research-corpus
```

### Batch download from a URL file

Write one URL per line. Comments with `#` are supported.

```bash
cat > urls.txt << 'EOF'
# Agent browser skills — top installs
https://playbooks.com/skills/vercel-labs/agent-browser/agent-browser
https://playbooks.com/skills/vercel-labs/agent-browser/dogfood
https://playbooks.com/skills/vercel-labs/agent-browser/electron
https://playbooks.com/skills/vercel-labs/agent-browser/slack

# Community variants
https://playbooks.com/skills/openclaw/skills/agent-browser
https://playbooks.com/skills/browserbase/agent-browser/agent-browser
https://playbooks.com/skills/am-will/codex-skills/agent-browser
EOF

skill-dl urls.txt -o ./research-corpus --no-auto-category -f
```

### Parallel download for large batches

`skill-dl` already groups by repo internally (one clone per repo), but processes repos sequentially. For large batches (50+ URLs across many repos), split the URL file by repo and run multiple `skill-dl` processes in parallel:

```bash
# Split URLs by unique repo (owner/repo), then download in parallel
split_and_download() {
  local url_file="$1"
  local output_dir="$2"
  local max_parallel="${3:-4}"

  # Extract unique repos and create per-repo URL files
  local tmp_dir=$(mktemp -d)
  while IFS= read -r url; do
    [[ "$url" =~ ^# ]] || [[ -z "$url" ]] && continue
    # Extract owner/repo from URL
    repo_key=$(echo "$url" | sed 's|.*/skills/\([^/]*/[^/]*\)/.*|\1|' | tr '/' '_')
    echo "$url" >> "${tmp_dir}/${repo_key}.txt"
  done < "$url_file"

  # Download each repo group in parallel
  local pids=()
  for repo_file in "${tmp_dir}"/*.txt; do
    skill-dl "$repo_file" -o "$output_dir" --no-auto-category -f &
    pids+=($!)
    # Throttle to max_parallel concurrent processes
    if (( ${#pids[@]} >= max_parallel )); then
      wait "${pids[0]}"
      pids=("${pids[@]:1}")
    fi
  done
  wait
  rm -rf "$tmp_dir"
}

split_and_download urls.txt ./research-corpus 6
```

Alternatively, use `xargs` for a simpler parallel approach when each URL targets a different repo:

```bash
# Each URL as a separate skill-dl call, 6 in parallel
grep -v '^#' urls.txt | grep -v '^$' | \
  xargs -P 6 -I {} skill-dl {} -o ./research-corpus --no-auto-category -f
```

> **Trade-off:** The `xargs` approach re-clones repos that appear multiple times. The split approach avoids this. Use split for large research corpora; use `xargs` for quick grabs with mostly unique repos.

### Useful flags

| Flag | Purpose |
|---|---|
| `-o <dir>` | Output directory (default: `./skills-collection`) |
| `--no-auto-category` | Flat structure — skill folders sit directly in output dir |
| `-c <name>` | Force all skills into a named category subfolder |
| `-f, --force` | Overwrite existing skill directories |
| `--dry-run` | Preview what would be downloaded without writing |
| `-v, --verbose` | Show debug output including search paths and available skills |

### Output structure

`skill-dl` names output folders as `{owner}--{repo}--{skill}`:

```
research-corpus/
  vercel-labs--agent-browser--agent-browser/
    SKILL.md
    references/
      commands.md
      authentication.md
      ...
  openclaw--skills--agent-browser/
    SKILL.md
    ...
```

### Handling failures

Skills that don't exist in the target repo are logged as `[ERR] Not found in repo`. With `-v`, the tool lists available skills in that repo so you can correct the URL. Failures don't stop the batch — all other skills continue downloading.

After a batch run, check the summary:

```
━━━ Summary ━━━
  Total:   91
  Success: 78
  Failed:  13
```

Re-run failed URLs individually with `-v` to diagnose, or drop them if the skill was renamed or removed upstream.

## Skill location heuristics

When `skill-dl` searches a cloned repo, it checks these paths in order:

- `skills/{skill}/SKILL.md`
- `{skill}/SKILL.md`
- `.skills/{skill}/SKILL.md`
- `.claude/skills/{skill}/SKILL.md`
- `.agent/skills/{skill}/SKILL.md`
- `.opencode/skills/{skill}/SKILL.md`
- `.cursor/skills/{skill}/SKILL.md`
- `.agents/skills/{skill}/SKILL.md`
- `src/skills/{skill}/SKILL.md`

If none match, it searches the entire repo for any `SKILL.md` whose parent directory matches the skill name. If the repo root itself contains `SKILL.md`, it is treated as a single-skill repo.

## Download discipline

When using downloaded skills as research evidence:

- preserve the real skill files that explain how the skill works
- keep bundled references, scripts, and assets when they are part of the skill itself
- `skill-dl` already excludes repo metadata (`.git`, `.github`, `node_modules`, `README.md`, `LICENSE`, lockfiles, etc.)
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
- download tool and flags
- how downloaded material should be treated during synthesis
