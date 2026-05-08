# Source Verification

How to evaluate skill quality, select candidates for synthesis, and identify trust signals.

## Evaluating skill quality

When researching existing skills for patterns to inherit or adapt, not all skills are equal. Use these signals to separate high-quality from low-quality sources.

### Trust signal matrix

| Signal | High quality | Medium quality | Low quality |
|---|---|---|---|
| Install count | >1000 | 100-1000 | <100 |
| Reference file count | 5-30 (organized) | 2-5 | 0-1 or >50 (sprawl) |
| SKILL.md structure | Decision tree + reading sets | Workflow steps + references | Flat prose, no routing |
| Description quality | Specific trigger phrases | Adequate action + outcome | Vague or missing |
| Last updated | Within 6 months | 6-12 months | >12 months |
| Repo stars | >50 | 10-50 | <10 |
| Author activity | Active maintainer | Occasional commits | Abandoned |

### Structural quality indicators

A well-structured skill shows these patterns:

```
✅ High quality:
├── Clear decision tree in SKILL.md
├── Every reference file routed from SKILL.md
├── Reference files are 100-400 lines each
├── No orphaned files
├── Consistent naming conventions
├── Minimal reading sets for common scenarios
└── Pitfalls table with actionable fixes

⚠️ Medium quality:
├── Workflow steps but no decision tree
├── Some reference files not routed
├── Reference files vary wildly in size
└── Missing pitfalls or reading sets

❌ Low quality:
├── No routing from SKILL.md to references
├── Monolithic SKILL.md (>500 lines)
├── Or: Empty SKILL.md with all content in references
├── Orphaned files nobody references
├── Inconsistent naming
└── No examples
```

## Candidate selection workflow

### Phase 1: Broad search

Search for skills related to your topic using multiple query variants:

```bash
# Example: researching skills for browser automation
queries=(
  "browser automation"
  "playwright testing"
  "headless browser"
  "web scraping agent"
)
```

Collect candidates with: skill name, source URL, keyword match count, brief description.

### Phase 2: Triage

Sort candidates into tiers:

| Tier | Criteria | Action |
|---|---|---|
| Must-read | High installs + good structure + relevant topic | Download and read fully |
| Worth checking | Medium installs or unique approach | Download, scan SKILL.md |
| Skip | Low installs + poor structure + peripheral topic | Record but don't download |

### Phase 3: Deep inspection

For must-read candidates:

1. Read the full SKILL.md
2. Check the decision tree (if present) for routing patterns
3. Read 2-3 reference files to assess depth
4. Note what the skill does well and what it does poorly
5. Identify specific patterns worth inheriting

### Phase 4: Document findings

Record findings inline in conversation output before synthesis, using this format for each candidate:

```markdown
## Candidate: build-copilot-sdk-app

**Source**: skills-by-yigitkonur
**Install count**: N/A (local pack)
**Quality tier**: Must-read

### Strengths
- Comprehensive decision tree (80+ leaf nodes)
- Well-organized reference subdirectories (10 categories)
- Effective minimal reading sets (7 scenarios)
- Strong pitfalls table (10 entries with fixes)

### Weaknesses
- Some reference files are placeholder-thin
- No scripts/ directory

### Inherit
- Decision tree structure and arrow-alignment pattern
- Minimal reading set concept
- Pitfalls table format

### Avoid
- 80+ leaf nodes is too large for most skills
- Don't copy the specific technology content
```

## Comparing multiple sources

When multiple skills cover similar ground, build a comparison table before synthesis.

### Required comparison columns

| Column | What to record |
|---|---|
| Source | Skill name and origin |
| Focus | What aspect of the topic it covers |
| Strengths | What this source does better than others |
| Gaps | What this source misses or handles poorly |
| Relevant sections | Specific files or sections worth reading |
| Inherit / avoid | Decision for each major pattern |

### Example comparison table

| Source | Focus | Strengths | Gaps | Inherit / avoid |
|---|---|---|---|---|
| copilot-sdk skill | SDK reference | Excellent decision tree, typed patterns | No research methodology | Inherit tree structure, avoid SDK-specific content |
| do-review skill | PR review | Strong workflow discipline | No reference organization guidance | Inherit phase-based routing |
| init-agent-config | Config files | Good file-format coverage | Thin on decision-making | Inherit config spec format |

### Decision language

End each row with a clear decision:

- "Inherit the comparison discipline, avoid the extra packaging"
- "Inherit the trigger language pattern, avoid the bulky body"
- "Inherit the reference routing, avoid duplicate guidance"

Vague conclusions like "interesting approach" are not useful.

## Identifying patterns to inherit

When evaluating what to take from a source:

### Worth inheriting

- **Structural patterns**: How the decision tree is organized
- **Routing patterns**: How SKILL.md connects to reference files
- **Content density**: How much detail per reference file
- **Quality signals**: Tables, examples, actionable pitfalls
- **Progressive disclosure**: How content is layered across levels

### Not worth inheriting

- **Technology-specific content**: API details, code examples for a different tool
- **Over-engineering**: Scoring systems, review loops, factory patterns
- **Packaging artifacts**: README badges, CI configs, install scripts
- **Duplicate guidance**: Same advice repeated in SKILL.md and references

## Verifying before inheriting

Before adopting a pattern from another skill:

1. **Does it solve a real problem?** Don't inherit patterns just because they look sophisticated
2. **Does it fit the target skill's complexity?** A micro-skill doesn't need a 50-node decision tree
3. **Does it follow current best practices?** Old skills may use deprecated patterns
4. **Can you simplify it?** Inherited patterns often carry unnecessary complexity

## Trust signals for specific platforms

### skills.sh / Playbooks

| Signal | Where to find | What it means |
|---|---|---|
| Install count | Search results | Community validation of usefulness |
| Detail page description | Skill detail URL | Quality of documentation |
| Repo activity | Linked GitHub repo | Maintenance status |
| Multiple skills in repo | Repo structure | Author has skill-building experience |

### GitHub repositories

| Signal | Where to find | What it means |
|---|---|---|
| Stars and forks | Repo page | Community interest |
| Issue activity | Issues tab | Active community and maintenance |
| Commit frequency | Commits page | Ongoing development |
| License | LICENSE file | Redistribution clarity |
| CI/CD status | Actions tab | Quality discipline |

### Community sources (Reddit, forums, blogs)

| Signal | Where to find | What it means |
|---|---|---|
| Upvotes / engagement | Post metrics | Community agreement |
| Concrete examples | Post content | Practical, tested advice |
| Date published | Post metadata | Recency and relevance |
| Author background | Profile | Expertise level |
| Follow-up corrections | Comments | Community-validated accuracy |

## Red flags

When evaluating any source, watch for:

| Red flag | Why it matters |
|---|---|
| No examples, only theory | Author may not have tested the patterns |
| Claims without version context | May be outdated |
| Copy-pasted from AI output | High hallucination risk |
| "Always" and "never" without justification | Over-generalized |
| Excessive complexity | May be solving problems that don't exist |
| No mention of trade-offs | One-sided view |
| Broken links or missing files | Unmaintained |
| Conflicting advice within the same source | Incoherent |


---

## Quick quality rubric

Use this rubric for rapid assessment of downloaded skills. Score each criterion 0-2:

| Criterion | 0 (Poor) | 1 (Acceptable) | 2 (Good) |
|---|---|---|---|
| **Structure** | No references/, everything in SKILL.md | Has references/ but poorly organized | Clean references/ with logical grouping |
| **Size** | SKILL.md > 500 lines | 300-500 lines | Under 300 lines |
| **Routing** | No routing table | File list without context | "Read when" routing with context |
| **Frontmatter** | Missing or invalid | Present but incomplete | Complete with valid name + description |
| **Decomposition** | Single monolithic file | Some splitting, inconsistent | Well-decomposed, no file > 500 lines |
| **Actionability** | Vague instructions | Some concrete steps | Clear, testable instructions |

**Scoring:**
- **10-12:** Tier 1 - Production-ready reference
- **6-9:** Tier 2 - Useful but flawed, extract ideas carefully
- **0-5:** Tier 3 - Anti-pattern source, use only as negative example

**Quick assessment command sequence:**
```bash
# Run these 4 commands for any downloaded skill:
wc -l SKILL.md
ls references/ 2>/dev/null | wc -l
head -5 SKILL.md  # Check frontmatter
grep -c '### ' SKILL.md  # Count routing sections
```

**Assessment output template:**
```
Skill: [name]
SKILL.md lines: [n]
Reference files: [n]
Frontmatter: [valid/invalid]
Routing sections: [n]
Score: [0-12]
Tier: [1/2/3]
Decision: [inherit/adapt/avoid]
```
