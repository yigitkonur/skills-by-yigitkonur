# Fact-Checking Methodology

How to verify claims, validate patterns, and ensure accuracy when building skills from research.

## Why fact-checking matters for skills

Skills are agent instructions. If a skill contains incorrect patterns, outdated API calls, or wrong configuration values, the agent will confidently reproduce those errors at scale. Unlike documentation that humans read critically, skills are consumed literally.

Every claim in a skill should be traceable to a verified source.

## The verification hierarchy

| Level | Verification method | Trust level | When to use |
|---|---|---|---|
| 1 | Official documentation | Highest | API specs, configuration fields, CLI flags |
| 2 | Source code inspection | High | Implementation details, undocumented behavior |
| 3 | Community consensus | Medium | Best practices, patterns, conventions |
| 4 | Single blog post or tutorial | Low | Needs cross-referencing |
| 5 | AI-generated content | Lowest | Must be verified against Level 1-3 |

## Verification workflow

### Step 1: Identify claims that need verification

When reading a source skill or reference material, flag any:

- API method names and signatures
- Configuration field names and valid values
- CLI command syntax and flags
- Version numbers and compatibility ranges
- Performance characteristics or benchmarks
- "Always do X" or "Never do Y" prescriptive statements

### Step 2: Trace each claim to its source

For each flagged claim:

1. **Find the official documentation** — Is this documented by the tool's maintainers?
2. **Check the source code** — Does the implementation match the documentation?
3. **Check the version** — Is this claim true for the current version?
4. **Check the date** — When was this information published?

### Step 3: Cross-reference across sources

A claim is stronger when multiple independent sources agree:

```
Strong:   Official docs + source code + 3 independent tutorials
Medium:   Official docs + 1 tutorial
Weak:     Single blog post only
Invalid:  Contradicted by official docs or source code
```

### Step 4: Document the verification

Show the verification table inline in conversation output:

```markdown
| Claim | Source | Verified | Notes |
|---|---|---|---|
| `name` field max 64 chars | Claude Code docs | ✅ | Confirmed in source code |
| `description` max 1024 chars | Medium article | ⚠️ | Not in official docs, but matches behavior |
| `metadata` field is free-form | Blog post | ❌ | Not supported in current version |
```

## Common verification traps

### Trap 1: Outdated documentation

Documentation frequently lags behind implementation. When docs and code disagree:

- **Prefer the code** for behavior verification
- **Prefer the docs** for API contracts (the code may be a bug)
- **Note the discrepancy** in your research artifact

### Trap 2: Platform-specific behavior

A pattern that works in Claude Code may not work in Cursor or Codex:

- Verify against each target platform separately
- Clearly label platform-specific guidance
- Don't generalize from one platform's behavior

### Trap 3: Version-dependent features

APIs and formats change. Always:

- Record the version you verified against
- Check the changelog for breaking changes
- Use `>=` version constraints rather than exact versions

### Trap 4: Inference from examples

When official docs are sparse, developers often infer behavior from examples:

- An example showing `name: my-skill` doesn't prove `name` is required
- An example without `version` field doesn't prove `version` is unsupported
- Test the boundary cases, don't just reproduce the examples

### Trap 5: AI-generated research

When using AI tools (deep research, LLM scraping) for research:

- AI may hallucinate URLs, function names, and API details
- AI may conflate information from different tools or versions
- Always verify AI-generated claims against Level 1-2 sources
- Treat AI research as a starting point, not a conclusion

## Fact categories and verification approaches

### Verifying API/format specifications

```
Claim: "SKILL.md frontmatter supports an `allowed-tools` field"

Verification steps:
1. Check official docs → code.claude.com/docs/en/skills
2. Check source code → anthropics/claude-code repo
3. Test it → Create a skill with `allowed-tools`, verify it loads
4. Result: ✅ Confirmed in docs and source
```

### Verifying best practices

Best practices are harder to verify because they're prescriptive, not descriptive.

```
Claim: "Keep SKILL.md under 500 lines"

Verification steps:
1. Check official guidance → Does the maintainer recommend this?
2. Check top-rated skills → What line counts do successful skills use?
3. Check technical constraints → Is there a token budget that maps to ~500 lines?
4. Result: ⚠️ Guideline, not hard limit. Based on ~5K token Level 2 budget.
```

### Verifying patterns and anti-patterns

```
Claim: "Never use angle brackets in frontmatter description"

Verification steps:
1. Check docs → "Avoid XML angle brackets as they can inject instructions"
2. Test it → Create a skill with <tags> in description
3. Check parser → Does the YAML parser strip or interpret them?
4. Result: ✅ Confirmed — YAML parser treats them as XML, causes issues
```

## Research source evaluation

When evaluating a source for skill research:

### High-signal sources

| Source type | Trust factors |
|---|---|
| Official docs (vendor site) | Maintained by tool creators, versioned |
| Source code (GitHub) | Ground truth for behavior |
| High-install skills (Playbooks) | Validated by community usage |
| Release notes / changelogs | Authoritative for version changes |

### Medium-signal sources

| Source type | Caveats |
|---|---|
| Blog posts by known authors | May be opinion-heavy, check date |
| Conference talks | Often aspirational, check if features shipped |
| Community forum answers | Practical but may be version-specific |
| Curated skill packs | Quality varies by curator |

### Low-signal sources

| Source type | Caveats |
|---|---|
| AI-generated articles | High hallucination risk for specifics |
| Generic tutorials | Often copy from each other |
| Stack Overflow answers | Check vote count and date |
| Reddit comments | Anecdotal, but good for sentiment |

## Building a verification log

For non-trivial skills, maintain a verification log:

```markdown
## Verification Log

### Frontmatter fields
- `name`: Required (source: official docs, verified 2025-01)
- `description`: Recommended, max 1024 chars (source: official docs + source code)
- `allowed-tools`: Optional, comma-separated (source: official docs, experimental)
- `when_to_use`: UNDOCUMENTED — likely deprecated (source: source code inspection)

### Directory structure
- `references/`: Loaded on demand via Read tool (source: official docs)
- `scripts/`: Executed via Bash, not read into context (source: deep dive blog + source)
- `assets/`: Referenced by path only (source: deep dive blog, unverified officially)

### Token budgets
- Level 1: ~100 tokens per skill (source: medium article, cross-referenced with forum)
- Level 2: ≤5K tokens (source: medium article, consistent with observed behavior)
- Level 3: Unlimited (source: official docs imply no cap)
```

## When to stop verifying

Verification has diminishing returns. Stop when:

1. The claim is confirmed by at least two independent Level 1-3 sources
2. The claim is consistent with observed behavior in testing
3. The claim is low-impact (a wrong convention name won't break anything)
4. Further verification would delay the skill significantly

Focus verification effort on:
- Claims that would cause agent errors if wrong
- API/format specifications that agents consume literally
- Security-relevant guidance
- Platform-specific differences
