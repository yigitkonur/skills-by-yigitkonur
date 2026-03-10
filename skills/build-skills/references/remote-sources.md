# Remote Sources

## Discovery

### Playbooks search

- URL pattern: `https://playbooks.com/skills?search=<query>&page=<n>`
- Detail page: `https://playbooks.com/skills/{owner}/{repo}/{skill}`

### Parallel discovery

When researching a topic, search multiple query variants simultaneously to maximize coverage:

```bash
# Parallel search — run multiple curl/scrape calls concurrently
queries=("agent browser" "agent-browser" "browser automation" "headless browser")
for q in "${queries[@]}"; do
  curl -s "https://playbooks.com/skills?search=${q// /+}" &
done | sort -u
wait
```

Or via the `skills-as-context` MCP tool (if available):
- Call `search-skills` with multiple query variants in parallel
- Deduplicate results by skill ID before proceeding

### What to collect

For each candidate, capture: title, owner/repo, detail URL, description, install count, and selection rationale.

## Downloading with skill-dl

`skill-dl` is the CLI tool for batch-downloading skills from Playbooks URLs.

### Install / verify

```bash
# Check if installed
skill-dl --version

# Install from source if missing
curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh | bash
```

### Quick start

```bash
# Single skill
skill-dl https://playbooks.com/skills/vercel-labs/agent-browser/agent-browser -o ./corpus

# Batch from file
skill-dl urls.txt -o ./corpus --no-auto-category -f

# Dry run first
skill-dl urls.txt --dry-run
```

### Parallel download for large batches

skill-dl groups URLs by repo internally (one clone per repo), but processes repos sequentially. For 50+ URLs across many repos, parallelize at the repo level:

**Option A — split by repo, then parallel skill-dl** (best: no redundant clones)

```bash
# Extract unique repos, create per-repo URL files, run in parallel
tmp=$(mktemp -d)
while IFS= read -r url; do
  [[ "$url" =~ ^# ]] || [[ -z "$url" ]] && continue
  repo=$(echo "$url" | sed 's|.*/skills/\([^/]*/[^/]*\)/.*|\1|' | tr '/' '_')
  echo "$url" >> "${tmp}/${repo}.txt"
done < urls.txt

ls "${tmp}"/*.txt | xargs -P 6 -I {} skill-dl {} -o ./corpus --no-auto-category -f
rm -rf "$tmp"
```

**Option B — xargs one-URL-per-process** (simple but re-clones shared repos)

```bash
grep -v '^#' urls.txt | grep -v '^$' | xargs -P 6 -I {} skill-dl {} -o ./corpus --no-auto-category -f
```

> Use Option A for large corpora with many skills from the same repo. Use Option B for quick grabs across unique repos.

### Flags reference

| Flag | Purpose |
|---|---|
| `-o <dir>` | Output directory (default: `./skills-collection`) |
| `--no-auto-category` | Flat output, no category subfolders |
| `-c <name>` | Force all into one category folder |
| `-f` | Overwrite existing |
| `--dry-run` | Preview only |
| `-v` | Verbose (shows search paths, available skills) |

### Output naming

Folders: `{owner}--{repo}--{skill}/` containing `SKILL.md` + bundled references.

### Skill search paths

skill-dl checks these locations in order:
`skills/{skill}`, `{skill}`, `.skills/{skill}`, `.claude/skills/{skill}`, `.agent/skills/{skill}`, `.opencode/skills/{skill}`, `.cursor/skills/{skill}`, `.agents/skills/{skill}`, `src/skills/{skill}`.
Fallback: full-repo search for SKILL.md with matching parent dir name, then root-level SKILL.md.

## Troubleshooting

| Problem | Fix |
|---|---|
| `skill-dl: command not found` | Install: `curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh \| bash` |
| `[ERR] Could not clone` | Repo is private, renamed, or deleted. Check URL manually. |
| `[ERR] Not found in repo` | Skill name doesn't match any path in repo. Run with `-v` to see available skills. |
| Slow on many repos | Use parallel download (Option A above). |
| Need to retry failures | Pipe failed URLs from summary into a new file, re-run. |

## Using downloaded skills as evidence

Downloaded skills are evidence for comparison, not templates to clone.

After download:
1. `tree` the corpus
2. Read high-signal skills (by install count or unique approach)
3. Cite relative paths in comparison table
4. Inherit patterns selectively
5. Rewrite the final result to be original and repo-fit
