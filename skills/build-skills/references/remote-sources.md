# Remote Sources

## Discovery

### skill-dl search

`skill-dl search` is the primary discovery method. It queries Playbooks and returns a prioritized markdown table directly to stdout.

Tool home: https://github.com/yigitkonur/cli-skill-downloader

```bash
# Basic search — pass 3–20 keywords
skill-dl search "agent browser" "headless automation" "browser testing"

# Broader coverage — more keywords surface different result clusters
skill-dl search "typescript" "type safety" "strict mode" "ts config" "compilation"

# Minimum required: at least 3 keywords
# Maximum: 20 keywords per invocation
```

**Output format:** a markdown table with columns: rank, skill name, owner/repo, keywords matched, match count, URL. Skills are ranked by how many of your keywords they matched — cross-keyword overlap is the primary signal.

**Usage pattern:**

1. Run `skill-dl search` with 3–20 keywords covering the topic from multiple angles
2. **Triage**: if results exceed 50 rows, use `--min-match 2` to focus on cross-keyword hits, or `--top 20` to cap output. For niche topics where the max match count is ≤2, broaden keyword variety or manually curate from the full list
3. Review the table — higher keyword match count = higher priority
4. Run a second search with different phrasing if the first result set looks narrow
5. Deduplicate by URL across multiple search runs before building the URL file

### Playbooks URL pattern

- Detail page: `https://playbooks.com/skills/{owner}/{repo}/{skill}`

### What to collect

For each candidate, capture: skill name, owner/repo, detail URL, keywords matched, match count, and selection rationale.

## Prerequisites

Before using any remote source tools, verify availability:

```bash
# Primary tool
skill-dl --version 2>/dev/null && echo "skill-dl ready" || echo "NOT AVAILABLE"

# MCP fallback
# skills-as-context-search-skills — available if skills.sh MCP server is configured
# skills-as-context-get-skill-details — available if skills.sh MCP server is configured
```

**Fallback chain:**
1. `skill-dl` (preferred) — CLI tool for searching and downloading skills
2. `skills-as-context-search-skills` + `skills-as-context-get-skill-details` (MCP) — requires skills.sh MCP server
3. Manual GitHub search — search for repositories containing SKILL.md files

Use the first available option. Document which method you used in your research summary.


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
| `[ERR] Not found in repo` | Skill name doesn't match any path in repo. Run with `-v` to see available skills. The skill may use a non-standard directory layout. |
| Slow on many repos | Use parallel download (Option A above). |
| Need to retry failures | Pipe failed URLs from summary into a new file, re-run. |

## Using downloaded skills as evidence

Downloaded skills are evidence for comparison, not templates to clone.

After download:
1. `tree` the corpus
2. Read high-signal skills (by keyword match count or unique approach)
3. Cite relative paths in comparison table
4. Inherit patterns selectively
5. Rewrite the final result to be original and repo-fit

---

## Search usage examples

### skill-dl search patterns
```bash
# Broad discovery
skill-dl search typescript mcp server --top 20

# Narrow by domain
skill-dl search react testing component --top 10

# Framework-specific
skill-dl search nextjs app-router authentication --top 15
```

### MCP tool patterns
When using `skills-as-context-search-skills`:
- Use specific, descriptive queries (not single keywords)
- Request enough results to compare: aim for 10-20 results
- Follow up with `skills-as-context-get-skill-details` for the most promising candidates

### Manual GitHub search patterns
When both skill-dl and MCP tools are unavailable:
- Search: `filename:SKILL.md [topic keywords]`
- Filter by recently updated repositories
- Look for repos with a `references/` directory structure
- Prefer repos with multiple files (indicates decomposed content)

## Quality assessment checklist

For each downloaded skill, quickly assess:

| Check | Command/Method | Pass criteria |
|---|---|---|
| SKILL.md size | `wc -l SKILL.md` | Under 500 lines |
| Has references | `ls references/ 2>/dev/null` | Directory exists with files |
| Frontmatter valid | Check first 5 lines | Has name + description |
| Description length | Count characters | Under 1024 chars |
| No angle brackets | `grep '[<>]' SKILL.md` | No matches in frontmatter |
| Routing table | `grep '### ' SKILL.md` | Has section-based routing |

Skills failing 3+ checks are Tier 3 — use only as anti-pattern examples.
