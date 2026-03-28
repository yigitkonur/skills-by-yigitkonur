#!/usr/bin/env python3
"""Generate marketplace.json and per-skill plugin.json from SKILL.md frontmatter.

Idempotent — running twice produces the same output.
Usage: python3 scripts/generate-marketplace.py
"""

import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO_ROOT, "skills")

CATEGORIES = {
    "build-chrome-extension": "development",
    "build-copilot-sdk-app": "development",
    "build-daisyui-mcp": "development",
    "build-hcom-systems": "orchestration",
    "build-langchain-ts-app": "development",
    "build-mcp-use-agent": "development",
    "build-mcp-use-apps-widgets": "development",
    "build-mcp-use-client": "development",
    "build-mcp-use-server": "development",
    "build-openclaw-plugin": "platform",
    "build-openclaw-skill": "platform",
    "build-openclaw-workflow": "platform",
    "build-raycast-script-command": "development",
    "build-skills": "productivity",
    "build-supastarter-app": "development",
    "convert-snapshot-nextjs": "design",
    "convert-vue-nextjs": "development",
    "debug-tauri-devtools": "development",
    "develop-clean-architecture": "development",
    "develop-macos-liquid-glass": "development",
    "develop-typebox-fastify": "development",
    "develop-typescript": "development",
    "enhance-skill-by-derailment": "productivity",
    "extract-saas-design": "design",
    "init-agent-config": "configuration",
    "init-copilot-review": "productivity",
    "init-devin-review": "productivity",
    "init-greptile-review": "productivity",
    "init-openclaw-agent": "platform",
    "optimize-mcp-server": "development",
    "plan-issue-tree": "productivity",
    "plan-prd": "productivity",
    "plan-work": "productivity",
    "publish-npm-package": "development",
    "review-pr": "productivity",
    "run-agent-browser": "testing",
    "run-hcom-agents": "orchestration",
    "run-issue-plan": "productivity",
    "run-openclaw-agents": "platform",
    "run-openclaw-deploy": "platform",
    "run-playwright": "testing",
    "run-research": "productivity",
    "run-seo-analysis": "marketing",
    "test-by-mcpc-cli": "development",
    "use-skill-dl-util": "productivity",
}


def parse_frontmatter(skill_md_path):
    """Extract name and description from SKILL.md YAML frontmatter.

    Uses regex to handle edge cases like unquoted colons and multiline >- syntax.
    """
    with open(skill_md_path) as f:
        content = f.read()

    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return None, None

    block = m.group(1)

    # Extract name
    name_match = re.search(r"^name:\s*(.+)", block, re.MULTILINE)
    name = name_match.group(1).strip().strip("\"'") if name_match else None

    # Extract description — handle both single-line and multiline >- syntax
    desc_match = re.search(r"^description:\s*>-\s*\n(.*?)(?=\n\w|\n---|\Z)", block, re.MULTILINE | re.DOTALL)
    if desc_match:
        # Multiline >- : join continuation lines
        description = " ".join(line.strip() for line in desc_match.group(1).splitlines() if line.strip())
    else:
        desc_match = re.search(r'^description:\s*"?(.+?)"?\s*$', block, re.MULTILINE)
        description = desc_match.group(1).strip() if desc_match else None

    return name, description


def to_user_description(trigger_desc):
    """Strip 'Use skill if you are' / 'Use this skill if you are' prefix."""
    desc = re.sub(r"^Use (?:this )?skill if you are\s+", "", trigger_desc)
    # Capitalize first letter
    if desc:
        desc = desc[0].upper() + desc[1:]
    # Remove trailing period if present, we'll add consistently
    desc = desc.rstrip(".")
    return desc


def generate():
    plugins = []
    warnings = []

    for skill_name in sorted(os.listdir(SKILLS_DIR)):
        skill_dir = os.path.join(SKILLS_DIR, skill_name)
        skill_md = os.path.join(skill_dir, "SKILL.md")

        if not os.path.isdir(skill_dir) or not os.path.isfile(skill_md):
            continue

        name, description = parse_frontmatter(skill_md)

        if not name:
            warnings.append(f"  SKIP {skill_name}: no parseable frontmatter")
            continue

        if name != skill_name:
            warnings.append(f"  WARN {skill_name}: frontmatter name '{name}' != directory name")

        if skill_name not in CATEGORIES:
            warnings.append(f"  WARN {skill_name}: no category mapping, defaulting to 'development'")

        user_desc = to_user_description(description) if description else name
        category = CATEGORIES.get(skill_name, "development")

        # Generate per-skill plugin.json
        plugin_conf_dir = os.path.join(skill_dir, ".claude-plugin")
        os.makedirs(plugin_conf_dir, exist_ok=True)

        plugin_json = {
            "name": name,
            "description": user_desc,
            "version": "1.0.0",
            "author": {"name": "Yigit Konur"},
        }

        plugin_json_path = os.path.join(plugin_conf_dir, "plugin.json")
        with open(plugin_json_path, "w") as f:
            json.dump(plugin_json, f, indent=2, ensure_ascii=False)
            f.write("\n")

        # Add to marketplace plugins list
        plugins.append(
            {
                "name": name,
                "description": user_desc,
                "version": "1.0.0",
                "author": {"name": "Yigit Konur"},
                "source": f"./skills/{skill_name}",
                "category": category,
            }
        )

    # Generate root marketplace.json
    marketplace_dir = os.path.join(REPO_ROOT, ".claude-plugin")
    os.makedirs(marketplace_dir, exist_ok=True)

    marketplace = {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": "yigitkonur-skills",
        "version": "1.0.0",
        "description": f"{len(plugins)} skills for AI coding agents.",
        "owner": {"name": "Yigit Konur", "url": "https://github.com/yigitkonur"},
        "plugins": plugins,
    }

    marketplace_json_path = os.path.join(marketplace_dir, "marketplace.json")
    with open(marketplace_json_path, "w") as f:
        json.dump(marketplace, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Summary
    if warnings:
        print("\n".join(warnings))
        print()

    print(f"Generated .claude-plugin/marketplace.json with {len(plugins)} plugins")
    print(f"Generated {len(plugins)} plugin.json files in skills/*/.claude-plugin/")

    # Validate completeness
    skill_dirs = {
        d
        for d in os.listdir(SKILLS_DIR)
        if os.path.isdir(os.path.join(SKILLS_DIR, d))
        and os.path.isfile(os.path.join(SKILLS_DIR, d, "SKILL.md"))
    }
    plugin_names = {p["name"] for p in plugins}
    missing = skill_dirs - plugin_names
    if missing:
        print(f"\nERROR: {len(missing)} skills missing from marketplace: {', '.join(sorted(missing))}")
        sys.exit(1)

    return len(plugins)


if __name__ == "__main__":
    count = generate()
    sys.exit(0)
