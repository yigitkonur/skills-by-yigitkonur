# Master Skill Checklist

> **Phase routing:** Not every checklist item applies at every stage. Items marked "DRAFT ESSENTIAL" (Phases 0-3) should be checked before sharing any draft. Items marked "FINAL PASS ONLY" (Phases 4+) are for comprehensive quality passes before publishing.
>
> **Quick start for drafts:** Search this file for "DRAFT ESSENTIAL" to find the minimum viable checks.


Comprehensive checklist covering every phase of skill development. 90+ items organized by phase. Every item is binary (yes/no), specific, and verifiable.

Use the full checklist for published skills. Use Phase 0-3 for personal skills. Skip Phase 6-7 for non-published skills.

---

## Phase 0 — ✅ DRAFT ESSENTIAL: Before You Start

Planning and preparation before writing any files.

- [ ] If using the full research path: verified `skill-dl` is installed (`skill-dl --version`) or available via `bash scripts/skill-dl --where`, or documented the fallback method. Install globally with `sudo -v ; curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh | sudo bash`
- [ ] Identified 2-3 concrete use cases with specific user trigger phrases
- [ ] Classified skill type: Document/Asset Creation, Workflow Automation, or MCP Enhancement
- [ ] Listed all tools needed: built-in Claude tools, MCP servers, scripts
- [ ] Defined quantitative success criteria (trigger accuracy, tool call count, token budget)
- [ ] Defined qualitative success criteria (no user corrections, consistent output, first-try success)
- [ ] Reviewed existing skills on the same topic (local workspace first, plus remote search for the full research path)
- [ ] Planned folder structure (flat references vs. subdirectories)
- [ ] Decided on reference file organization strategy
- [ ] Identified target platforms (Claude.ai, Claude Code, API)
- [ ] Assessed MCP dependencies and verified MCP server availability
- [ ] Read the optimization guide or relevant references from this skill
- [ ] If non-trivial: completed research workflow, showed source shortlist inline, and produced the comparison table with inherit/avoid decisions

---

## Phase 1 — ✅ DRAFT ESSENTIAL: Frontmatter Quality

The frontmatter determines whether Claude ever loads your skill.

### File basics
- [ ] File named exactly `SKILL.md` (case-sensitive, not `skill.md` or `SKILL.MD`)
- [ ] `---` delimiter on line 1 (no blank lines before it)
- [ ] Closing `---` delimiter after all frontmatter fields
- [ ] No tabs in frontmatter (spaces only)
- [ ] Valid YAML syntax (no unclosed quotes, no bare colons in values)

### Name field
- [ ] `name` field is present
- [ ] `name` uses kebab-case only (lowercase letters, numbers, hyphens)
- [ ] `name` is ≤64 characters
- [ ] `name` matches the directory name
- [ ] No leading, trailing, or consecutive hyphens
- [ ] Name does not contain "claude" or "anthropic" (reserved by Anthropic)
- [ ] Name follows verb-noun pattern (`build-mcp-server`, `review-pr`)

### Description field
- [ ] `description` field is present
- [ ] Description includes WHAT the skill does (action + outcome)
- [ ] Description includes WHEN to use it (trigger conditions)
- [ ] Description includes key capability keywords
- [ ] Description includes technology/framework/tool names users would say
- [ ] Description includes file types if the skill handles specific formats
- [ ] Description is under 1024 characters
- [ ] No `<` or `>` characters anywhere in frontmatter (XML injection risk)
- [ ] Description specific enough to avoid false triggers on unrelated queries
- [ ] Description broad enough to catch legitimate paraphrased requests
- [ ] Negative triggers added if over-triggering risk exists ("Do NOT use for...")
- [ ] Tested: asked Claude "When would you use [skill-name]?" and answer matches intent

### Optional fields
- [ ] `allowed-tools` is minimal — only tools the skill actually needs
- [ ] Side-effect skills (deploy, delete, publish) use `disable-model-invocation: true`
- [ ] `compatibility` field set if the skill requires specific platforms or dependencies
- [ ] `metadata` includes `author` and `version` for published skills

---

## Phase 2 — ✅ DRAFT ESSENTIAL: Body Structure

The SKILL.md body is the core instruction set.

### Size and format
- [ ] SKILL.md body is under 500 lines
- [ ] SKILL.md is under 5,000 words total
- [ ] Starts with `# Title` matching the human-readable skill name
- [ ] Uses imperative language ("Run...", "Create...", not passive voice)
- [ ] No ambiguous language ("properly", "things", "as needed" without definition)

### Navigation and routing
- [ ] Decision tree or reference routing table is present
- [ ] Decision tree has max 3 levels of depth
- [ ] Decision tree branches are mutually exclusive (no overlapping categories)
- [ ] Most common paths are listed first in the decision tree
- [ ] Every leaf node resolves to a file path or inline section
- [ ] Every file in `references/` is reachable from SKILL.md

### Content sections
- [ ] Quick start section covers the 80% use case without loading references
- [ ] 2-5 key patterns with code examples are included
- [ ] Pitfalls table uses table format with actionable fixes (not prose)
- [ ] Minimal reading sets bundle related references for common scenarios
- [ ] Guardrails section lists explicit "Do not" constraints
- [ ] Critical instructions are at the top, not buried in the middle

### Instructions quality
- [ ] At least one complete input/output example
- [ ] Error handling included for each workflow step
- [ ] No more than 7 essential rules in SKILL.md (extras in reference files)
- [ ] Steps are specific and actionable, not vague
- [ ] Dependencies between steps are explicit

---

## Phase 3 — ✅ DRAFT ESSENTIAL: Reference Files

Reference files provide depth without bloating SKILL.md.

### Routing integrity
- [ ] Every file in `references/` is routed from SKILL.md (decision tree, reading set, or routing table)
- [ ] No orphaned reference files exist
- [ ] No README.md inside the skill folder
- [ ] Cross-references between files use relative paths within the skill

### File quality
- [ ] Each reference file is 100-400 lines (no micro-files under 50, no monoliths over 400)
- [ ] Each reference file covers a single topic (no mixed concerns)
- [ ] Each file starts with `# Title` and a one-line purpose statement
- [ ] 2-4 code examples per reference file
- [ ] Good AND bad examples shown where the distinction matters
- [ ] Troubleshooting section at the end of relevant files

### Organization
- [ ] Max directory depth: `references/category/file.md` (2 levels max)
- [ ] Subdirectories used when reference file count exceeds 6
- [ ] File names are kebab-case, descriptive, and ≤50 characters
- [ ] No version suffixes in file names (`auth.md` not `auth-v2.md`)
- [ ] No circular dependencies between reference files
- [ ] Subdirectory names match decision tree top-level branches

---

## Phase 4 — 🔍 FINAL PASS ONLY: Content Quality

The content must be accurate, current, and synthesized — not copied.

### Accuracy
- [ ] All code examples are tested and working
- [ ] No deprecated API methods, removed CLI flags, or outdated syntax
- [ ] Version context provided for version-dependent features
- [ ] Platform-specific guidance is clearly labeled (Claude.ai vs. Claude Code vs. API)
- [ ] Claims are traceable to verified sources (official docs, source code, community consensus)

### Format
- [ ] Tables used for structured lookups (not paragraph prose)
- [ ] At least one complete input/output example in SKILL.md
- [ ] Consistent terminology throughout all files
- [ ] Markdown formatting is clean and renders correctly

### Safety
- [ ] No secrets, credentials, API keys, or personal data in any file
- [ ] No packaging artifacts (node_modules, build configs, CI pipelines)
- [ ] Rollback instructions included for destructive operations
- [ ] No `<` or `>` characters in any frontmatter field

### Originality
- [ ] Content is synthesized from evidence, not copied from a single source
- [ ] If research was done, comparison table exists showing inherit/avoid decisions
- [ ] No copied source skill with only superficial renaming
- [ ] Patterns are adapted to the target repo's conventions

---

## Phase 5 — 🔍 FINAL PASS ONLY: Testing

Testing validates that the skill works correctly in practice.

### Triggering tests
- [ ] Live trigger coverage completed in the active runtime, OR the installation block is documented and live trigger coverage is explicitly excluded
- [ ] For new skills: installed the draft into the active runtime's skill directory before live trigger testing, or documented why installation was blocked
- [ ] 5+ queries that SHOULD trigger the skill prepared and executed live when installation was possible
- [ ] 5+ queries that should NOT trigger the skill prepared and executed live when installation was possible
- [ ] 3+ paraphrased variants tested live when installation was possible
- [ ] Asked Claude "When would you use [skill-name]?" — answer matches intent
- [ ] No conflicts with other enabled skills on the same queries

### Functional tests
- [ ] Primary workflow completes without error
- [ ] Error handling works for at least one failure case
- [ ] Edge cases covered (empty input, large input, special characters)
- [ ] MCP calls succeed if skill uses MCP (tested independently first)
- [ ] Results are consistent across 3+ consecutive runs

### Performance tests
- [ ] Token consumption is reasonable for the task (compared to no-skill baseline)
- [ ] Tool call count is equal or lower than no-skill baseline
- [ ] Workflow completes without user correction in 3+ runs
- [ ] No degraded response quality from context overload

---

## Phase 6 — 🔍 FINAL PASS ONLY: Publishing

Preparing the skill for public distribution.

### Naming consistency
- [ ] Directory name matches frontmatter `name` exactly
- [ ] SKILL.md `# Title` is a human-readable version of the name
- [ ] Cross-skill references use the target skill's frontmatter `name`

### Repository quality
- [ ] LICENSE file exists in the repo (MIT or Apache-2.0 recommended)
- [ ] Repo-level README with installation instructions
- [ ] README includes usage examples and screenshots
- [ ] Repository topics/tags include relevant keywords
- [ ] No .git, node_modules, or temp files in distribution package
- [ ] Clean git history (no accidental commits, no credential leaks)

### Distribution
- [ ] Version tracked in frontmatter `metadata` field
- [ ] Git tag created for the release version
- [ ] Installation guide covers both Claude.ai (upload) and Claude Code (directory placement)
- [ ] Quick-start example in README works out of the box

---

## Phase 7 — 🔍 FINAL PASS ONLY: Post-Ship Monitoring

Ongoing maintenance after the skill is live.

### Triggering health
- [ ] Monitoring for under-triggering (users manually invoking)
- [ ] Monitoring for over-triggering (loading for unrelated queries)
- [ ] Description updated when trigger behavior drifts

### Quality health
- [ ] Collecting user feedback on output quality
- [ ] Tracking failed API/MCP calls per workflow
- [ ] Watching for user corrections during skill execution

### Maintenance
- [ ] Monthly check for outdated API references or deprecated patterns
- [ ] Quarterly review of usage patterns and metrics
- [ ] Version bump in metadata on each meaningful change
- [ ] Examples re-verified after dependency updates
- [ ] Deprecation notice added if skill is being retired

---

## Quick Reference: Minimum Viable Checks

For rapid validation when time is short, verify at minimum:

- [ ] File is `SKILL.md`, frontmatter has `---` delimiters on line 1
- [ ] `name` is kebab-case, matches directory
- [ ] `description` has what + when + trigger phrases
- [ ] No `<` or `>` in frontmatter
- [ ] Body under 500 lines
- [ ] All reference files are routed from SKILL.md
- [ ] At least one working example
- [ ] Tested 3 trigger queries and 3 non-trigger queries
