#!/usr/bin/env python3
"""Validate all skills in the repository.

Checks:
  1. Reference linkage — every file in references/ must be linked from SKILL.md
  2. Frontmatter — name matches directory, description format and length
  3. SKILL.md length — SKILL.md must stay under 500 lines
  4. No junk files (.DS_Store, .swp, evals, LICENSE inside skills)
  5. Research surfaces (skills + subagents, source and generated installs) stay
     on the current Research Powerpack v9 four-tool contract

Usage:
    python3 scripts/validate-skills.py          # full validation, exit 1 on errors
    python3 scripts/validate-skills.py --quick   # same checks (kept for hook compat)
"""

import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO_ROOT, "skills")
SUBAGENTS_DIR = os.path.join(REPO_ROOT, "subagents")

JUNK_PATTERNS = {".DS_Store", ".swp", "Thumbs.db", ".gitkeep"}
JUNK_DIRS = {"evals", "__pycache__"}
BANNED_FILES_IN_SKILL = {"LICENSE", "LICENSE.md", "CHANGELOG.md"}
MAX_SKILL_MD_LINES = 1000

# Research Powerpack v9 exposes exactly four public tools. Anything that teaches
# an agent to call a retired name sends it at a tool the server no longer has,
# so every research surface in this repo is scanned for the old vocabulary.
RESEARCH_TOOL_NAMES = (
    "plan-research",
    "web-search",
    "extract-evidence",
    "review-research",
)
RESEARCH_REMOVED_TOOL_NAMES = (
    "get-research-consultancy",
    "scrape-link",
    "start-research",
    "raw-web-search",
    "smart-web-search",
    "raw-scrape-links",
    "smart-scrape-links",
    "web-search-links",
    "scrape-links",
    "get-reddit-post",
    "search-reddit",
)
# The old MCP namespace was hard-coded from a server alias that no longer
# matches how these agents are installed; canonical tool names travel better.
RESEARCH_REMOVED_NAMESPACES = ("mcp__research-powerpack__",)
RESEARCH_REMOVED_PARAMETER_MARKERS = (
    "`goal`",
    "`keywords`",
    "`extract`",
    "`include_playbook`",
    "`research_id`",
    '"goal":',
    '"keywords":',
    '"extract":',
    '"include_playbook":',
    '"scope":',
    '"progress":',
    '"research_id":',
)
# Skills whose Markdown must be free of the retired call vocabulary. Each entry
# also has its generated Codex package checked, so a stale mirror cannot ship.
RESEARCH_GUARDED_SKILLS = (
    "run-research",
    "run-deep-research",
    "run-github-scout",
    "test-by-mcpc-cli",
)
# Parameter-name guarding is narrower than tool-name guarding: `keywords` and
# `extract` are ordinary English elsewhere, so only the skills that actually
# call the research server are held to the strict marker list.
RESEARCH_PARAMETER_GUARDED_SKILLS = ("run-research", "run-deep-research")
RUN_RESEARCH_REQUIRED_MARKERS_BY_FILE = (
    (
        "SKILL.md",
        (
            "| `plan-research` | `objective: string` |",
            "| `web-search` | `queries: string[]` |",
            "| `extract-evidence` | `urls: string[]`, `evidence_requirements: string[]` |",
            "| `review-research` | no arguments |",
            "Known-URL work must not pay planning or search overhead.",
            'schema_version: "2"',
            "`continuation.required`",
            "`continuation.next_call`",
            "`resume_available`",
            "in-process-only",
        ),
    ),
    (
        os.path.join("references", "resumable-extraction.md"),
        (
            "continuation: {",
            "resume_available: boolean;",
            "cache_ttl_seconds: 3600;",
            "pending_sources: Array<{",
            'tool: "extract-evidence";',
            "evidence_requirements: string[];",
            "isError: false",
            "zero-based",
            "smaller URL batches",
            "sparse block projection",
            "originating ordered requirements",
            "reports omitted ranges",
        ),
    ),
)
RUN_RESEARCH_REQUIREMENT_STATUSES = (
    "answered",
    "partial",
    "not-found",
    "conflicting",
)


def skill_content_dir(skill_dir, skill_name):
    """Return the path to the skill content directory (SKILL.md + references/).

    Per agentskills.io/specification the layout is flat: the skill directory
    itself contains SKILL.md (parent dir name = skill name = frontmatter name).
    """
    return skill_dir


def parse_frontmatter(skill_md_path):
    """Extract name and description from SKILL.md YAML frontmatter."""
    with open(skill_md_path) as f:
        content = f.read()

    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return None, None

    block = m.group(1)

    name_match = re.search(r"^name:\s*(.+)", block, re.MULTILINE)
    name = name_match.group(1).strip().strip("\"'") if name_match else None

    desc_match = re.search(
        r"^description:\s*>-\s*\n(.*?)(?=\n\w|\n---|\Z)", block, re.MULTILINE | re.DOTALL
    )
    if desc_match:
        description = " ".join(
            line.strip() for line in desc_match.group(1).splitlines() if line.strip()
        )
    else:
        desc_match = re.search(r'^description:\s*"?(.+?)"?\s*$', block, re.MULTILINE)
        description = desc_match.group(1).strip() if desc_match else None

    return name, description


def check_structure(skill_name, skill_dir):
    """Verify SKILL.md is in the correct subdirectory for Claude Code discovery."""
    errors = []
    expected = os.path.join(skill_content_dir(skill_dir, skill_name), "SKILL.md")
    if not os.path.isfile(expected):
        errors.append(f"SKILL.md not found at expected path: skills/{skill_name}/SKILL.md")
    return errors


def check_references(skill_name, skill_dir):
    """Check that every reference file is linked from SKILL.md and vice versa."""
    errors = []
    content_dir = skill_content_dir(skill_dir, skill_name)
    refs_dir = os.path.join(content_dir, "references")
    skill_md = os.path.join(content_dir, "SKILL.md")

    if not os.path.isdir(refs_dir) or not os.path.isfile(skill_md):
        return errors

    # Collect all .md files on disk
    on_disk = set()
    for root, _dirs, files in os.walk(refs_dir):
        for f in files:
            if f.endswith(".md"):
                rel = os.path.relpath(os.path.join(root, f), content_dir)
                on_disk.add(rel)

    if not on_disk:
        return errors

    with open(skill_md) as fh:
        content = fh.read()

    # Find all references/*.md paths mentioned in SKILL.md
    raw_matches = re.findall(r"(?:skills/[^/]+/)?(references/[^\s|)\x60\]\"'>]+\.md)", content)

    # Identify cross-skill references to exclude
    cross_skill = set()
    for m_str in re.findall(r"skills/([^/]+/references/[^\s|)\x60\]\"'>]+\.md)", content):
        parts = m_str.split("/", 1)
        if parts[0] != skill_name:
            cross_skill.add(parts[1] if len(parts) > 1 else m_str)

    referenced = set()
    for r in raw_matches:
        if "*" in r:
            # Glob patterns — expand to check against on_disk
            import fnmatch

            pattern = r
            matched = {f for f in on_disk if fnmatch.fnmatch(f, pattern)}
            referenced.update(matched)
            if not matched:
                errors.append(f"SKILL.md glob pattern `{r}` matches no files on disk")
            continue
        if r in cross_skill:
            continue
        referenced.add(r)

    orphaned = on_disk - referenced
    missing = referenced - on_disk

    for o in sorted(orphaned):
        errors.append(f"orphaned reference not linked from SKILL.md: {o}")
    for m_str in sorted(missing):
        errors.append(f"SKILL.md references non-existent file: {m_str}")

    return errors


def check_frontmatter(skill_name, skill_dir):
    """Check frontmatter name, description format, and length."""
    errors = []
    skill_md = os.path.join(skill_content_dir(skill_dir, skill_name), "SKILL.md")

    if not os.path.isfile(skill_md):
        errors.append("missing SKILL.md")
        return errors

    name, description = parse_frontmatter(skill_md)

    if not name:
        errors.append("SKILL.md has no parseable frontmatter or missing name")
        return errors

    if name != skill_name:
        errors.append(f'frontmatter name "{name}" does not match directory "{skill_name}"')

    if not description:
        errors.append("frontmatter missing description")
        return errors

    accepted_prefixes = ("Use skill if you are ", "Use if ")
    if not description.startswith(accepted_prefixes):
        errors.append(
            'description must start with "Use skill if you are " '
            f'(legacy "Use if " is also accepted) — got: "{description[:60]}..."'
        )

    if len(description.split()) > 30:
        errors.append(f"description is {len(description.split())} words (max 30)")

    return errors


def check_junk(skill_name, skill_dir):
    """Check for junk files, eval dirs, and banned files inside a skill."""
    errors = []

    for root, dirs, files in os.walk(skill_dir):
        # Check for banned directories
        for d in dirs:
            if d in JUNK_DIRS:
                rel = os.path.relpath(os.path.join(root, d), skill_dir)
                errors.append(f"banned directory: {rel}/")

        for f in files:
            if f in JUNK_PATTERNS:
                rel = os.path.relpath(os.path.join(root, f), skill_dir)
                errors.append(f"junk file: {rel}")
            if f in BANNED_FILES_IN_SKILL:
                # At skill root level or skill content dir root
                if root == skill_dir or root == skill_content_dir(skill_dir, skill_name):
                    errors.append(f"banned file in skill root: {f}")

    return errors


def check_skill_length(skill_name, skill_dir):
    """Check that SKILL.md remains under the line budget."""
    errors = []
    skill_md = os.path.join(skill_content_dir(skill_dir, skill_name), "SKILL.md")
    if not os.path.isfile(skill_md):
        return errors

    with open(skill_md) as fh:
        line_count = sum(1 for _ in fh)

    if line_count > MAX_SKILL_MD_LINES:
        errors.append(
            f"SKILL.md is {line_count} lines (max {MAX_SKILL_MD_LINES})"
        )

    return errors


def scan_markdown_for_retired_research_vocabulary(
    label, root_dir, *, check_parameters
):
    """Report retired tool names, namespaces, and call shapes under root_dir."""
    errors = []
    for root, _dirs, files in os.walk(root_dir):
        for filename in sorted(files):
            if not filename.endswith(".md"):
                continue
            path = os.path.join(root, filename)
            with open(path) as fh:
                content = fh.read()
            rel = os.path.relpath(path, root_dir)
            for removed in RESEARCH_REMOVED_TOOL_NAMES:
                if removed in content:
                    errors.append(f"{label}/{rel} contains removed tool name: {removed}")
            for namespace in RESEARCH_REMOVED_NAMESPACES:
                if namespace in content:
                    errors.append(
                        f"{label}/{rel} contains removed MCP namespace: {namespace}"
                    )
            if check_parameters:
                for marker in RESEARCH_REMOVED_PARAMETER_MARKERS:
                    if marker in content:
                        errors.append(
                            f"{label}/{rel} contains removed parameter marker: {marker}"
                        )
    return errors


def check_research_v9_vocabulary(skill_name, skill_dir):
    """Hold research skills and their generated mirrors to the v9 vocabulary."""
    if skill_name not in RESEARCH_GUARDED_SKILLS:
        return []

    check_parameters = skill_name in RESEARCH_PARAMETER_GUARDED_SKILLS
    errors = []
    for install_label, install_dir in research_install_dirs(skill_name, skill_dir):
        if not os.path.isdir(install_dir):
            errors.append(f"{install_label} install is missing: {install_dir}")
            continue
        errors.extend(
            scan_markdown_for_retired_research_vocabulary(
                install_label, install_dir, check_parameters=check_parameters
            )
        )
    return errors


def research_install_dirs(skill_name, skill_dir):
    """Source skill directory plus its generated Codex plugin mirror."""
    return (
        ("source", skill_dir),
        (
            "generated plugin",
            os.path.join(REPO_ROOT, "plugins", skill_name, "skills", skill_name),
        ),
    )


def check_run_research_v9_contract(skill_name, skill_dir):
    """Keep source and freshly generated installs on the current v9 protocol."""
    if skill_name != "run-research":
        return []

    errors = []
    for install_label, install_dir in research_install_dirs(skill_name, skill_dir):
        if not os.path.isdir(install_dir):
            continue

        for relative_path, required_markers in RUN_RESEARCH_REQUIRED_MARKERS_BY_FILE:
            required_path = os.path.join(install_dir, relative_path)
            if not os.path.isfile(required_path):
                errors.append(
                    f"{install_label} install is missing contract file: {relative_path}"
                )
                continue
            with open(required_path) as fh:
                required_content = fh.read()
            for marker in required_markers:
                if marker not in required_content:
                    errors.append(
                        f"{install_label}/{relative_path} is missing contract marker: {marker}"
                    )

        synthesis_path = os.path.join(install_dir, "references", "synthesis.md")
        if not os.path.isfile(synthesis_path):
            errors.append(
                f"{install_label} install is missing contract file: references/synthesis.md"
            )
            continue

        with open(synthesis_path) as fh:
            synthesis = fh.read()
        requirement_section = re.search(
            r"^## Interpret requirement statuses\s*$\n(.*?)(?=^## |\Z)",
            synthesis,
            re.MULTILINE | re.DOTALL,
        )
        if requirement_section is None:
            errors.append(
                f"{install_label}/references/synthesis.md is missing the requirement-status section"
            )
        else:
            documented_statuses = tuple(re.findall(
                r"^- `([^`]+)`: ",
                requirement_section.group(1),
                re.MULTILINE,
            ))
            if documented_statuses != RUN_RESEARCH_REQUIREMENT_STATUSES:
                expected = ", ".join(RUN_RESEARCH_REQUIREMENT_STATUSES)
                actual = ", ".join(documented_statuses) or "none"
                errors.append(
                    f"{install_label}/references/synthesis.md requirement statuses "
                    f"must be exactly [{expected}], got [{actual}]"
                )

        pending_section = re.search(
            r"^## Interpret pending source work\s*$\n(.*?)(?=^## |\Z)",
            synthesis,
            re.MULTILINE | re.DOTALL,
        )
        normalized_pending = "" if pending_section is None else " ".join(
            pending_section.group(1).split()
        )
        pending_markers = (
            "source-level `retrieval_status` or `extraction_status`",
            "never a requirement status",
            "exact same-session continuation",
        )
        if any(marker not in normalized_pending for marker in pending_markers):
            errors.append(
                f"{install_label}/references/synthesis.md must document pending only as source-level unfinished work"
            )

    return errors


def check_subagent_research_contract():
    """Researcher subagents must teach the same four-tool protocol as the skills."""
    if not os.path.isdir(SUBAGENTS_DIR):
        return []

    errors = scan_markdown_for_retired_research_vocabulary(
        "subagents", SUBAGENTS_DIR, check_parameters=False
    )

    for runtime in ("claude", "codex"):
        runtime_dir = os.path.join(SUBAGENTS_DIR, runtime)
        if not os.path.isdir(runtime_dir):
            errors.append(f"subagents/{runtime} directory is missing")
            continue
        for filename in sorted(os.listdir(runtime_dir)):
            if not filename.startswith("internet-researcher") or not filename.endswith(".md"):
                continue
            with open(os.path.join(runtime_dir, filename)) as fh:
                content = fh.read()
            missing = [tool for tool in RESEARCH_TOOL_NAMES if tool not in content]
            if missing:
                errors.append(
                    f"subagents/{runtime}/{filename} never mentions: {', '.join(missing)}"
                )

    return errors


def main():
    all_errors = {}
    skills_checked = 0

    for skill_name in sorted(os.listdir(SKILLS_DIR)):
        skill_dir = os.path.join(SKILLS_DIR, skill_name)
        if not os.path.isdir(skill_dir):
            continue

        skill_errors = []
        skill_errors.extend(check_structure(skill_name, skill_dir))
        skill_errors.extend(check_frontmatter(skill_name, skill_dir))
        skill_errors.extend(check_skill_length(skill_name, skill_dir))
        skill_errors.extend(check_references(skill_name, skill_dir))
        skill_errors.extend(check_junk(skill_name, skill_dir))
        skill_errors.extend(check_research_v9_vocabulary(skill_name, skill_dir))
        skill_errors.extend(check_run_research_v9_contract(skill_name, skill_dir))

        if skill_errors:
            all_errors[skill_name] = skill_errors

        skills_checked += 1

    # Report
    subagent_errors = check_subagent_research_contract()
    if subagent_errors:
        all_errors["subagents"] = subagent_errors

    print(f"Validated {skills_checked} skills")

    total_errors = sum(len(e) for e in all_errors.values())

    if total_errors == 0:
        print("\n✅ All validations passed")
        sys.exit(0)

    print(f"\n❌ {total_errors} error(s) found:\n")

    for skill_name, errs in sorted(all_errors.items()):
        for e in errs:
            print(f"  {skill_name}: {e}")

    flattened_errors = [e for errs in all_errors.values() for e in errs]
    has_reference_errors = any(
        "orphaned reference not linked from SKILL.md" in e
        or "references non-existent file" in e
        or "glob pattern" in e
        for e in flattened_errors
    )
    has_length_errors = any("SKILL.md is" in e and "lines (max" in e for e in flattened_errors)

    if has_reference_errors or has_length_errors:
        print("\nHow to fix:")
        if has_reference_errors:
            print("  • Reference linkage:")
            print("      - Every file under references/ must be explicitly mentioned in SKILL.md.")
            print("      - Remove stale links to files that no longer exist.")
        if has_length_errors:
            print(f"  • SKILL.md length (max {MAX_SKILL_MD_LINES} lines):")
            print("      - Move deep detail into references/ files (nested folders are encouraged).")
            print("      - Keep SKILL.md focused on trigger logic, workflow, decision rules, and routing.")
            print("      - Link every newly added references/*.md file from SKILL.md to preserve context.")

    print(
        "\n"
        "Fix these issues before pushing. Run:\n"
        "  python3 scripts/validate-skills.py\n"
    )

    sys.exit(1)


if __name__ == "__main__":
    main()
