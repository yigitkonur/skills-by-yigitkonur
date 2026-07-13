#!/usr/bin/env python3
"""Generate plugin metadata from the skills/ tree.

Every Claude-compatible skill becomes an individually installable plugin (so
users can `/plugin install <skill>@yigitkonur` and uninstall it just as easily).
Themed bundles group related skills for one-shot installs, and an `everything`
bundle installs every Claude-compatible skill. Codex-only skills remain in the
root `skills/` tree but are excluded from every Claude marketplace allowlist.

All plugins share the single skills/ folder at the repo root via
`source: "./"` + `strict: false` + an explicit `skills` allowlist, so no
skill files are duplicated (see code.claude.com/docs/en/plugin-marketplaces).

Codex currently consumes this repo as one all-pack plugin from the repo root:
`.codex-plugin/plugin.json` points at `./skills/`, and
`.agents/plugins/marketplace.json` exposes the repo root as a Codex plugin.

Run after adding/removing/renaming a skill:
    python3 scripts/gen-marketplace.py            # write plugin metadata
    python3 scripts/gen-marketplace.py --check    # verify metadata is up to date (CI)
"""

import importlib.util
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO_ROOT, "skills")
CLAUDE_OUT_PATH = os.path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")
CODEX_MARKETPLACE_OUT_PATH = os.path.join(REPO_ROOT, ".agents", "plugins", "marketplace.json")
CODEX_MANIFEST_OUT_PATH = os.path.join(REPO_ROOT, ".codex-plugin", "plugin.json")
VERSION_PATH = os.path.join(REPO_ROOT, "VERSION")

MARKETPLACE_NAME = "yigitkonur"
CODEX_PLUGIN_NAME = "skills-by-yigitkonur"

# Runtime-specific skills that ship through the root Codex plugin only. Keep
# these out of Claude's per-skill plugins, themed bundles, and yk-everything.
CODEX_ONLY_SKILLS = {"orchestrate-projects-by-jean"}


def version():
    """Single source of truth for every plugin's version (bumped by CI)."""
    try:
        return open(VERSION_PATH).read().strip()
    except FileNotFoundError:
        return "1.0.0"

# Themed bundles. Every Claude-compatible skill MUST appear in exactly one
# group; Codex-only skills MUST NOT appear in a group (enforced below).
# key -> (category label, human blurb, [skill dirs])
GROUPS = {
    "yk-review": (
        "review",
        "Review & completion — code review, review-feedback triage, done-claim audits, runtime debugging.",
        ["run-review", "run-codex-review-loop", "run-codex-adversarial-loop", "audit-completion", "debug-runtime"],
    ),
    "yk-frontend": (
        "frontend",
        "Frontend rebuild & audit — pixel-faithful URL→Next.js, UI/UX/Laws-of-UX audits.",
        [
            "convert-url-to-nextjs",
            "audit-ux-laws",
            "audit-ui-and-save-files",
            "audit-ux-and-save-files",
        ],
    ),
    "yk-mcp": (
        "mcp",
        "MCP & agent interfaces — build (SDK v1/v2, mcp-use), clean architecture, convert v1→v2, test, and agent-readiness audits for MCP servers and CLIs.",
        [
            "audit-agentic-mcp",
            "audit-agentic-cli",
            "build-clean-mcp-architecture",
            "build-mcp-server-sdk-v1",
            "build-mcp-server-sdk-v2",
            "build-mcp-use-agent",
            "build-mcp-use-client",
            "build-mcp-use-server",
            "convert-mcp-sdk-v1-to-v2",
            "test-by-mcpc-cli",
        ],
    ),
    "yk-build": (
        "build",
        "App & framework builders — Chrome MV3, Cloudflare Email Service, Effect-TS v3, Kernel SDK, LangChain.js, LicenseSeat (macOS/Swift), Raycast, Sentry (macOS/Swift), TinaCMS+Next.js.",
        [
            "build-chrome-extension",
            "build-cloudflare-email-sending",
            "build-effect-ts-v3",
            "build-kernel-ts-sdk",
            "build-langchain-ts-app",
            "build-licenseseat-swift",
            "build-raycast-script-command",
            "build-sentry-macos-swift",
            "build-tinacms-nextjs",
        ],
    ),
    "yk-research": (
        "research",
        "Research & discovery — single-question and wave-based corpus research, GitHub repo scouting, bulk Codex search. Bundles the internet-researcher subagents.",
        ["run-research", "run-deep-research", "run-github-scout", "search-it-bulk-by-codex"],
    ),
    "yk-automation": (
        "automation",
        "Live automation — agent-browser CLI, Android device control, Tailscale Funnel public tunnels.",
        ["run-agent-browser", "mobilerun-control", "run-tailscale-funnel"],
    ),
    "yk-config": (
        "config",
        "Instruction & config files — AGENTS.md/CLAUDE.md/REVIEW.md hierarchies, drift audits, scenario Makefiles.",
        ["init-agent-config", "update-agent-config", "init-makefiles", "init-jean-json"],
    ),
    "yk-ops": (
        "ops",
        "Ops & release — Railway, Coolify Cloud compose deploys, repo cleanup, npm publishing.",
        [
            "run-railway",
            "deploy-coolify-cloud",
            "run-repo-cleanup",
            "publish-npm-package",
        ],
    ),
    "yk-skills": (
        "skills-meta",
        "Skill authoring — research-driven skill creation and derailment stress-testing of existing SKILL.md files.",
        ["build-skill", "audit-skill-by-derailment"],
    ),
    "yk-delivery": (
        "delivery",
        "Aligned delivery — scored multi-round question alignment, a filename-state spec corpus, and waved parallel subagent orchestration for a large or ambiguous initiative.",
        ["run-aligned-delivery"],
    ),
}

# Bundles that also ship the internet-researcher subagents from subagents/claude/.
AGENT_BUNDLES = {"yk-research"}
CLAUDE_AGENTS = ["./subagents/claude/"]


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

    # Coverage invariant: every Claude-compatible skill is in exactly one
    # group, while every declared Codex-only skill exists and is in no group.
    grouped = [s for _c, _b, members in GROUPS.values() for s in members]
    dupes = sorted({s for s in grouped if grouped.count(s) > 1})
    missing = sorted(set(skills) - set(grouped))
    unknown = sorted(set(grouped) - set(repo_skills))
    missing_codex_only = sorted(CODEX_ONLY_SKILLS - set(repo_skills))
    grouped_codex_only = sorted(CODEX_ONLY_SKILLS & set(grouped))
    problems = []
    if dupes:
        problems.append(f"skills in >1 group: {dupes}")
    if missing:
        problems.append(f"skills in NO group: {missing}")
    if unknown:
        problems.append(f"group lists non-existent skills: {unknown}")
    if missing_codex_only:
        problems.append(f"Codex-only skills do not exist: {missing_codex_only}")
    if grouped_codex_only:
        problems.append(f"Codex-only skills appear in Claude groups: {grouped_codex_only}")
    if problems:
        print("marketplace generation failed:\n  " + "\n  ".join(problems), file=sys.stderr)
        sys.exit(2)

    plugins = []
    ver = version()

    # 1) everything bundle
    plugins.append(
        {
            "name": "yk-everything",
            "source": "./",
            "description": "Every Claude-compatible skill — all {} skills plus the internet-researcher agents. Heaviest context cost; prefer a themed bundle or single skill.".format(
                len(skills)
            ),
            "version": ver,
            "category": "bundle",
            "strict": False,
            "skills": [f"./skills/{s}" for s in skills],
            "agents": CLAUDE_AGENTS,
        }
    )

    # 2) agents-only plugin — install just the internet-researcher subagents
    plugins.append(
        {
            "name": "yk-researchers",
            "source": "./",
            "description": "Internet-researcher subagents only (no skills) — api-docs, debug-stuck, tech-choice, shipping-pattern, quick, generic. Fan them out for source-backed answers.",
            "version": ver,
            "category": "bundle",
            "tags": ["agents"],
            "strict": False,
            "skills": [],
            "agents": CLAUDE_AGENTS,
        }
    )

    # 3) themed bundles
    for key, (category, blurb, members) in GROUPS.items():
        entry = {
            "name": key,
            "source": "./",
            "description": blurb,
            "version": ver,
            "category": "bundle",
            "tags": [category],
            "strict": False,
            "skills": [f"./skills/{m}" for m in members],
        }
        if key in AGENT_BUNDLES:
            entry["agents"] = CLAUDE_AGENTS
        plugins.append(entry)

    # 4) one plugin per skill (fine-grained install/uninstall)
    skill_to_cat = {s: cat for _k, (cat, _b, members) in GROUPS.items() for s in members}
    for s in skills:
        plugins.append(
            {
                "name": s,
                "source": "./",
                "description": skill_desc(v, s),
                "version": ver,
                "category": skill_to_cat[s],
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
            "description": "Skills for AI coding agents — review, research, UI/UX audit, MCP & framework builders, browser/device automation, config files, publish. Install the whole pack, a themed bundle, a single skill, or just the researcher agents.",
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


def build_codex_marketplace():
    return {
        "name": MARKETPLACE_NAME,
        "interface": {
            "displayName": "Yigit Konur",
        },
        "plugins": [
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
        ],
    }


def render_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def generated_files():
    return {
        CLAUDE_OUT_PATH: render_json(build_claude_marketplace()),
        CODEX_MARKETPLACE_OUT_PATH: render_json(build_codex_marketplace()),
        CODEX_MANIFEST_OUT_PATH: render_json(build_codex_manifest()),
    }


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
        print("plugin metadata is up to date")
        return

    for path, rendered in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(rendered)
        print(f"wrote {os.path.relpath(path, REPO_ROOT)}")


if __name__ == "__main__":
    main()
