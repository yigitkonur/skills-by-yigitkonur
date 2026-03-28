#!/usr/bin/env python3
"""Bump the semver version of a skill in both its plugin.json and the root marketplace.json.

Usage: python3 scripts/bump-version.py <skill-name> <patch|minor|major>

Examples:
    python3 scripts/bump-version.py review-pr patch    # 1.0.0 -> 1.0.1
    python3 scripts/bump-version.py review-pr minor    # 1.0.0 -> 1.1.0
    python3 scripts/bump-version.py review-pr major    # 1.0.0 -> 2.0.0
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO_ROOT, "skills")
MARKETPLACE_PATH = os.path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")


def bump_semver(version, bump_type):
    """Apply a semver bump and return the new version string."""
    parts = version.split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    return f"{major}.{minor}.{patch}"


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <skill-name> <patch|minor|major>")
        sys.exit(1)

    skill_name = sys.argv[1]
    bump_type = sys.argv[2]

    if bump_type not in ("patch", "minor", "major"):
        print(f"Error: bump type must be patch, minor, or major (got '{bump_type}')")
        sys.exit(1)

    # --- Validate skill directory exists ---
    skill_dir = os.path.join(SKILLS_DIR, skill_name)
    if not os.path.isdir(skill_dir):
        print(f"Error: skill '{skill_name}' not found at {skill_dir}")
        sys.exit(1)

    # --- Read and bump plugin.json ---
    plugin_path = os.path.join(skill_dir, ".claude-plugin", "plugin.json")
    if not os.path.isfile(plugin_path):
        print(f"Error: plugin.json not found at {plugin_path}")
        sys.exit(1)

    with open(plugin_path, "r") as f:
        plugin_data = json.load(f)

    old_plugin_version = plugin_data["version"]
    new_plugin_version = bump_semver(old_plugin_version, bump_type)
    plugin_data["version"] = new_plugin_version

    with open(plugin_path, "w") as f:
        json.dump(plugin_data, f, indent=2)
        f.write("\n")

    print(f"plugin.json: {old_plugin_version} -> {new_plugin_version}")

    # --- Read and bump marketplace.json ---
    with open(MARKETPLACE_PATH, "r") as f:
        marketplace_data = json.load(f)

    # Bump the matching plugin entry
    found = False
    for plugin in marketplace_data.get("plugins", []):
        if plugin["name"] == skill_name:
            old_market_version = plugin["version"]
            plugin["version"] = new_plugin_version
            print(f"marketplace.json [{skill_name}]: {old_market_version} -> {new_plugin_version}")
            found = True
            break

    if not found:
        print(f"Error: skill '{skill_name}' not found in marketplace.json plugins list")
        sys.exit(1)

    # Always patch-bump the top-level marketplace version
    old_top_version = marketplace_data["version"]
    new_top_version = bump_semver(old_top_version, "patch")
    marketplace_data["version"] = new_top_version
    print(f"marketplace.json [top-level]: {old_top_version} -> {new_top_version}")

    with open(MARKETPLACE_PATH, "w") as f:
        json.dump(marketplace_data, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
