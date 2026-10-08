#!/usr/bin/env python3
"""Generate marketplace metadata and self-contained Codex plugins from skills/.

Every Claude-compatible skill becomes an individually installable plugin (so
users can `/plugin install <skill>@yigitkonur` and uninstall it just as easily).
One `yk-everything` plugin installs every Claude-compatible skill. Codex-only skills remain in the
root `skills/` tree but are excluded from every Claude marketplace allowlist.

All plugins share the single skills/ folder at the repo root via
`source: "./"` + `strict: false` + an explicit `skills` allowlist, so no
skill files are duplicated (see code.claude.com/docs/en/plugin-marketplaces).

Codex gets the same fine-grained install surface through generated plugin
packages in `plugins/<skill>/`. Each package copies one canonical skill under
its own `skills/` directory, which Codex requires for plugin discovery. The
root `skills-by-yigitkonur` entry remains the backwards-compatible all-pack
plugin.

Run after adding/removing/renaming a skill:
    python3 scripts/gen-marketplace.py            # write plugin metadata
    python3 scripts/gen-marketplace.py --check    # verify metadata is up to date (CI)
"""

import importlib.util
import json
import os
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO_ROOT, "skills")
CLAUDE_OUT_PATH = os.path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")
CODEX_MARKETPLACE_OUT_PATH = os.path.join(REPO_ROOT, ".agents", "plugins", "marketplace.json")
CODEX_MANIFEST_OUT_PATH = os.path.join(REPO_ROOT, ".codex-plugin", "plugin.json")
CODEX_PLUGINS_DIR = os.path.join(REPO_ROOT, "plugins")
VERSION_PATH = os.path.join(REPO_ROOT, "VERSION")

MARKETPLACE_NAME = "yigitkonur"
CODEX_PLUGIN_NAME = "skills-by-yigitkonur"

# Runtime-specific skills that ship through the root Codex plugin only. Keep
# these out of Claude's per-skill plugins and yk-everything.
CODEX_ONLY_SKILLS = set()


def version():
    """Single source of truth for every plugin's version (bumped by CI)."""
    try:
        return open(VERSION_PATH).read().strip()
    except FileNotFoundError:
        return "1.0.0"

def load_validator():
    spec = importlib.util.spec_from_file_location(
        "v", os.path.join(REPO_ROOT, "scripts", "validate-skills.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def skill_desc(v, skill):
    _name, desc = v.parse_frontmatter(os.path.join(SKILLS_DIR, skill, "SKILL.md"))
    return desc or f"{skill} skill."


def all_skills():
    return sorted(
        s for s in os.listdir(SKILLS_DIR) if os.path.isdir(os.path.join(SKILLS_DIR, s))
    )


def build_claude_marketplace():
    v = load_validator()
    repo_skills = all_skills()
    skills = sorted(set(repo_skills) - CODEX_ONLY_SKILLS)

    missing_codex_only = sorted(CODEX_ONLY_SKILLS - set(repo_skills))
    if missing_codex_only:
        print(f"marketplace generation failed:\n  Codex-only skills do not exist: {missing_codex_only}", file=sys.stderr)
        sys.exit(2)

    plugins = []
    ver = version()

    # 1) all-pack plugin
    plugins.append(
        {
            "name": "yk-everything",
            "source": "./",
            "description": "Every Claude-compatible skill — all {} skills. Every skill is manual-only (invoked by name).".format(
                len(skills)
            ),
            "version": ver,
            "category": "skills",
            "strict": False,
            "skills": [f"./skills/{s}" for s in skills],
        }
    )

    # 2) one plugin per skill (fine-grained install/uninstall)
    for s in skills:
        plugins.append(
            {
                "name": s,
                "source": "./",
                "description": skill_desc(v, s),
                "version": ver,
                "category": "skills",
                "strict": False,
                "skills": [f"./skills/{s}"],
            }
        )

    return {
        "name": MARKETPLACE_NAME,
        "owner": {
            "name": "Yigit Konur",
            "url": "https://github.com/yigitkonur",
        },
        "metadata": {
            "description": "Skills for AI coding agents — review, research, UI/UX audit, MCP & framework builders, browser/device automation, config files, publish. Install the whole pack or a single skill.",
            "version": version(),
        },
        "plugins": plugins,
    }


def build_codex_manifest():
    ver = version()
    return {
        "name": CODEX_PLUGIN_NAME,
        "version": ver,
        "description": "Yigit Konur's curated skills pack for AI coding agents.",
        "author": {
            "name": "Yigit Konur",
            "url": "https://github.com/yigitkonur",
        },
        "homepage": "https://github.com/yigitkonur/skills-by-yigitkonur",
        "repository": "https://github.com/yigitkonur/skills-by-yigitkonur",
        "license": "MIT",
        "keywords": [
            "agent-skills",
            "codex",
            "claude-code",
            "mcp",
            "research",
            "review",
        ],
        "skills": "./skills/",
        "interface": {
            "displayName": "Skills by Yigit Konur",
            "shortDescription": "A curated skills pack for AI coding agents.",
            "longDescription": "Install review, research, UI/UX audit, MCP, framework, automation, configuration, and release skills as one Codex plugin.",
            "developerName": "Yigit Konur",
            "category": "Productivity",
            "capabilities": ["Read", "Write", "Interactive"],
            "websiteURL": "https://github.com/yigitkonur/skills-by-yigitkonur",
            "defaultPrompt": [
                "Use a relevant skill for this task.",
                "List the installed skills in this pack.",
                "Use the research skills for this question.",
            ],
            "brandColor": "#10A37F",
        },
    }


def build_codex_skill_manifest(v, skill):
    """Build a standalone Codex manifest for one canonical skill directory."""
    description = skill_desc(v, skill)
    return {
        "name": skill,
        "version": version(),
        "description": description,
        "author": {
            "name": "Yigit Konur",
            "url": "https://github.com/yigitkonur",
        },
        "homepage": "https://github.com/yigitkonur/skills-by-yigitkonur",
        "repository": "https://github.com/yigitkonur/skills-by-yigitkonur",
        "license": "MIT",
        "keywords": ["agent-skills", "codex", skill],
        "skills": "./skills/",
        "interface": {
            "displayName": skill,
            "shortDescription": description,
            "longDescription": f"Install only the {skill} workflow from Yigit Konur's curated skills pack.",
            "developerName": "Yigit Konur",
            "category": "Productivity",
            "capabilities": ["Read", "Write", "Interactive"],
            "websiteURL": "https://github.com/yigitkonur/skills-by-yigitkonur",
            "defaultPrompt": [f"Use the {skill} skill for this task."],
            "brandColor": "#10A37F",
        },
    }


def build_codex_marketplace():
    v = load_validator()
    skills = all_skills()
    plugins = [
        {
            "name": CODEX_PLUGIN_NAME,
            "source": {
                "source": "local",
                "path": "./",
            },
            "policy": {
                "installation": "AVAILABLE",
                "authentication": "ON_INSTALL",
            },
            "category": "Productivity",
        }
    ]
    plugins.extend(
        {
            "name": skill,
            "source": {
                "source": "local",
                "path": f"./plugins/{skill}",
            },
            "policy": {
                "installation": "AVAILABLE",
                "authentication": "ON_INSTALL",
            },
            "category": "Productivity",
        }
        for skill in skills
    )
    return {
        "name": MARKETPLACE_NAME,
        "interface": {
            "displayName": "Yigit Konur",
        },
        "plugins": plugins,
    }


def render_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def generated_files():
    return {
        CLAUDE_OUT_PATH: render_json(build_claude_marketplace()),
        CODEX_MARKETPLACE_OUT_PATH: render_json(build_codex_marketplace()),
        CODEX_MANIFEST_OUT_PATH: render_json(build_codex_manifest()),
    }


def codex_plugin_path(skill):
    return os.path.join(CODEX_PLUGINS_DIR, skill)


def copied_skill_path(skill):
    return os.path.join(codex_plugin_path(skill), "skills", skill)


def files_match(left, right):
    """Return whether two regular files have identical contents and mode bits."""
    try:
        return (
            os.path.isfile(left)
            and os.path.isfile(right)
            and os.stat(left).st_mode & 0o777 == os.stat(right).st_mode & 0o777
            and open(left, "rb").read() == open(right, "rb").read()
        )
    except OSError:
        return False


def skill_tree_matches(skill):
    """Verify that one generated Codex package exactly mirrors its source skill."""
    source_root = os.path.join(SKILLS_DIR, skill)
    target_root = copied_skill_path(skill)
    if not os.path.isdir(target_root):
        return False

    for root, dirs, files in os.walk(source_root):
        relative = os.path.relpath(root, source_root)
        target_dir = os.path.join(target_root, relative)
        if not os.path.isdir(target_dir):
            return False
        if sorted(dirs) != sorted(
            entry
            for entry in os.listdir(target_dir)
            if os.path.isdir(os.path.join(target_dir, entry))
        ):
            return False
        if sorted(files) != sorted(
            entry
            for entry in os.listdir(target_dir)
            if os.path.isfile(os.path.join(target_dir, entry))
        ):
            return False
        for filename in files:
            if not files_match(os.path.join(root, filename), os.path.join(target_dir, filename)):
                return False
    return True


def codex_plugin_packages_are_current():
    """Check every generated one-skill package without modifying the worktree."""
    v = load_validator()
    skills = all_skills()
    if not os.path.isdir(CODEX_PLUGINS_DIR):
        return False
    expected_dirs = set(skills)
    actual_dirs = {
        entry
        for entry in os.listdir(CODEX_PLUGINS_DIR)
        if os.path.isdir(os.path.join(CODEX_PLUGINS_DIR, entry))
    }
    if actual_dirs != expected_dirs:
        return False
    for skill in skills:
        manifest_path = os.path.join(codex_plugin_path(skill), ".codex-plugin", "plugin.json")
        if not os.path.isfile(manifest_path):
            return False
        if open(manifest_path).read() != render_json(build_codex_skill_manifest(v, skill)):
            return False
        if not skill_tree_matches(skill):
            return False
    return True


def write_codex_plugin_packages():
    """Regenerate each standalone Codex plugin from the canonical skills tree."""
    v = load_validator()
    skills = all_skills()
    os.makedirs(CODEX_PLUGINS_DIR, exist_ok=True)
    expected_dirs = set(skills)
    for entry in os.listdir(CODEX_PLUGINS_DIR):
        path = os.path.join(CODEX_PLUGINS_DIR, entry)
        if entry not in expected_dirs and os.path.isdir(path):
            shutil.rmtree(path)
    for skill in skills:
        plugin_root = codex_plugin_path(skill)
        if os.path.isdir(plugin_root):
            shutil.rmtree(plugin_root)
        os.makedirs(os.path.join(plugin_root, ".codex-plugin"))
        with open(os.path.join(plugin_root, ".codex-plugin", "plugin.json"), "w") as f:
            f.write(render_json(build_codex_skill_manifest(v, skill)))
        shutil.copytree(
            os.path.join(SKILLS_DIR, skill),
            copied_skill_path(skill),
            copy_function=shutil.copy2,
        )
    print(f"wrote {os.path.relpath(CODEX_PLUGINS_DIR, REPO_ROOT)}/ ({len(skills)} Codex plugins)")


def main():
    check = "--check" in sys.argv
    files = generated_files()

    if check:
        stale = []
        for path, rendered in files.items():
            current = open(path).read() if os.path.isfile(path) else ""
            if current != rendered:
                stale.append(os.path.relpath(path, REPO_ROOT))
        if stale:
            print("plugin metadata is stale — run: python3 scripts/gen-marketplace.py", file=sys.stderr)
            for path in stale:
                print(f"  stale: {path}", file=sys.stderr)
            sys.exit(1)
        if not codex_plugin_packages_are_current():
            print("Codex plugin packages are stale — run: python3 scripts/gen-marketplace.py", file=sys.stderr)
            sys.exit(1)
        print("plugin metadata is up to date")
        return

    for path, rendered in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(rendered)
        print(f"wrote {os.path.relpath(path, REPO_ROOT)}")
    write_codex_plugin_packages()


if __name__ == "__main__":
    main()
