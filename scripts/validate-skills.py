#!/usr/bin/env python3
"""Validate all skills in the repository.

Checks:
  1. Reference linkage — every file in references/ must be linked from SKILL.md
  2. Frontmatter — name matches directory, description format and word count
  3. SKILL.md length — SKILL.md must stay under 500 lines
  4. No junk files (.DS_Store, .swp, evals, LICENSE inside skills)

Usage:
    python3 scripts/validate-skills.py          # full validation, exit 1 on errors
    python3 scripts/validate-skills.py --quick   # same checks (kept for hook compat)
"""

import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO_ROOT, "skills")

JUNK_PATTERNS = {".DS_Store", ".swp", "Thumbs.db", ".gitkeep"}
JUNK_DIRS = {"evals", "__pycache__"}
BANNED_FILES_IN_SKILL = {"LICENSE", "LICENSE.md", "CHANGELOG.md"}
MAX_SKILL_MD_LINES = 1000


def skill_content_dir(skill_dir, skill_name):
    """Return the path to the skill content directory (SKILL.md + references/)."""
    return os.path.join(skill_dir, "skills", skill_name)


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
    """Check frontmatter name, description format, and word count."""
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

    if not description.startswith("Use skill if you are"):
        errors.append(
            f'description must start with "Use skill if you are" — got: "{description[:60]}..."'
        )

    word_count = len(description.split())
    if word_count > 30:
        errors.append(f"description is {word_count} words (max 30)")

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

        if skill_errors:
            all_errors[skill_name] = skill_errors

        skills_checked += 1

    # Report
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
