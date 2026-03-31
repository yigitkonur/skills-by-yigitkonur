#!/usr/bin/env python3
"""Validate all skills in the repository.

Checks:
  1. Reference linkage — every file in references/ must be linked from SKILL.md
  2. Frontmatter — name matches directory, description format and word count
  3. Marketplace consistency — every skill has plugin.json and marketplace entry
  4. No junk files (.DS_Store, .swp, evals, LICENSE inside skills)

Usage:
    python3 scripts/validate-skills.py          # full validation, exit 1 on errors
    python3 scripts/validate-skills.py --quick   # skip marketplace check (for pre-push)
"""

import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO_ROOT, "skills")

JUNK_PATTERNS = {".DS_Store", ".swp", "Thumbs.db", ".gitkeep"}
JUNK_DIRS = {"evals", "__pycache__"}
BANNED_FILES_IN_SKILL = {"LICENSE", "LICENSE.md", "README.md", "CHANGELOG.md"}


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


def check_references(skill_name, skill_dir):
    """Check that every reference file is linked from SKILL.md and vice versa."""
    errors = []
    refs_dir = os.path.join(skill_dir, "references")
    skill_md = os.path.join(skill_dir, "SKILL.md")

    if not os.path.isdir(refs_dir) or not os.path.isfile(skill_md):
        return errors

    # Collect all .md files on disk
    on_disk = set()
    for root, _dirs, files in os.walk(refs_dir):
        for f in files:
            if f.endswith(".md"):
                rel = os.path.relpath(os.path.join(root, f), skill_dir)
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
    skill_md = os.path.join(skill_dir, "SKILL.md")

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
                # Only at skill root level
                if root == skill_dir:
                    errors.append(f"banned file in skill root: {f}")

    return errors


def check_marketplace():
    """Check marketplace.json and plugin.json consistency."""
    errors = []

    mp_path = os.path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")
    if not os.path.isfile(mp_path):
        errors.append("REPO: .claude-plugin/marketplace.json not found")
        return errors

    with open(mp_path) as f:
        marketplace = json.load(f)

    plugin_names = {p["name"] for p in marketplace["plugins"]}

    # Check every skill directory has a marketplace entry and plugin.json
    for skill_name in sorted(os.listdir(SKILLS_DIR)):
        skill_dir = os.path.join(SKILLS_DIR, skill_name)
        if not os.path.isdir(skill_dir):
            continue
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue

        if skill_name not in plugin_names:
            errors.append(f"{skill_name}: missing from marketplace.json")

        pj_path = os.path.join(skill_dir, ".claude-plugin", "plugin.json")
        if not os.path.isfile(pj_path):
            errors.append(f"{skill_name}: missing .claude-plugin/plugin.json")
            continue

        with open(pj_path) as f:
            pj = json.load(f)

        if pj.get("name") != skill_name:
            errors.append(
                f'{skill_name}: plugin.json name "{pj.get("name")}" != directory name'
            )
        if not pj.get("version"):
            errors.append(f"{skill_name}: plugin.json missing version")

    # Check marketplace entries point to existing skills
    for plugin in marketplace["plugins"]:
        pname = plugin["name"]
        if not os.path.isdir(os.path.join(SKILLS_DIR, pname)):
            errors.append(f"MARKETPLACE: entry '{pname}' has no matching skill directory")

    return errors


def main():
    quick = "--quick" in sys.argv

    all_errors = {}
    skills_checked = 0

    for skill_name in sorted(os.listdir(SKILLS_DIR)):
        skill_dir = os.path.join(SKILLS_DIR, skill_name)
        if not os.path.isdir(skill_dir):
            continue

        skill_errors = []
        skill_errors.extend(check_frontmatter(skill_name, skill_dir))
        skill_errors.extend(check_references(skill_name, skill_dir))
        skill_errors.extend(check_junk(skill_name, skill_dir))

        if skill_errors:
            all_errors[skill_name] = skill_errors

        skills_checked += 1

    # Marketplace check (skip in --quick mode)
    marketplace_errors = []
    if not quick:
        marketplace_errors = check_marketplace()

    # Report
    print(f"Validated {skills_checked} skills")

    total_errors = sum(len(e) for e in all_errors.values()) + len(marketplace_errors)

    if total_errors == 0:
        print("\n✅ All validations passed")
        sys.exit(0)

    print(f"\n❌ {total_errors} error(s) found:\n")

    for skill_name, errs in sorted(all_errors.items()):
        for e in errs:
            print(f"  {skill_name}: {e}")

    for e in marketplace_errors:
        print(f"  {e}")

    print(
        "\n"
        "Fix these issues before pushing. Run:\n"
        "  python3 scripts/validate-skills.py\n"
    )

    sys.exit(1)


if __name__ == "__main__":
    main()
