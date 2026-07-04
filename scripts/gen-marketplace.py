#!/usr/bin/env python3
"""Generate .claude-plugin/marketplace.json from the skills/ tree.

Every skill becomes an individually installable plugin (so users can
`/plugin install <skill>@yigitkonur` and uninstall it just as easily).
Themed bundles group related skills for one-shot installs, and an
`everything` bundle installs the whole pack.

All plugins share the single skills/ folder at the repo root via
`source: "./"` + `strict: false` + an explicit `skills` allowlist, so no
skill files are duplicated (see code.claude.com/docs/en/plugin-marketplaces).

Run after adding/removing/renaming a skill:
    python3 scripts/gen-marketplace.py            # write marketplace.json
    python3 scripts/gen-marketplace.py --check    # verify it is up to date (CI)
"""

import importlib.util
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO_ROOT, "skills")
OUT_PATH = os.path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")

MARKETPLACE_NAME = "yigitkonur"

# Themed bundles. Every skill MUST appear in exactly one group (enforced below).
# key -> (category label, human blurb, [skill dirs])
GROUPS = {
    "yk-review": (
        "review",
        "Review & completion — code review, review-feedback triage, done-claim audits, runtime debugging.",
        ["run-review", "run-codex-review-loop", "audit-completion", "debug-runtime"],
    ),
    "yk-frontend": (
        "frontend",
        "Frontend rebuild & audit — pixel-faithful URL→Next.js, design.md extraction, UI/UX/Laws-of-UX audits.",
        [
            "convert-url-to-nextjs",
            "create-design-md",
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
        "App & framework builders — Chrome MV3, Effect-TS v3, Kernel SDK, LangChain.js, macOS SwiftUI, Raycast, TinaCMS+Next.js.",
        [
            "build-chrome-extension",
            "build-effect-ts-v3",
            "build-kernel-ts-sdk",
            "build-langchain-ts-app",
            "build-macos-app",
            "build-raycast-script-command",
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
        ["init-agent-config", "update-agent-config", "init-makefiles"],
    ),
    "yk-ops": (
        "ops",
        "Ops & release — Railway, repo cleanup, autonomous babysitter, Linear CLI, remote offload runs, Vercel prebuild, npm publishing.",
        [
            "run-railway",
            "run-repo-cleanup",
            "run-babysitter",
            "run-linear-cli",
            "offload-run",
            "vercel-local-prebuild",
            "publish-npm-package",
        ],
    ),
    "yk-skills": (
        "skills-meta",
        "Skill authoring — research-driven skill creation and derailment stress-testing of existing SKILL.md files.",
        ["build-skill", "audit-skill-by-derailment"],
    ),
}

# Bundles that also ship the internet-researcher subagents from agents/claude/.
AGENT_BUNDLES = {"yk-research"}
CLAUDE_AGENTS = ["./agents/claude/"]


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


def build():
    v = load_validator()
    skills = all_skills()

    # Coverage invariant: every skill in exactly one group.
    grouped = [s for _c, _b, members in GROUPS.values() for s in members]
    dupes = sorted({s for s in grouped if grouped.count(s) > 1})
    missing = sorted(set(skills) - set(grouped))
    unknown = sorted(set(grouped) - set(skills))
    problems = []
    if dupes:
        problems.append(f"skills in >1 group: {dupes}")
    if missing:
        problems.append(f"skills in NO group: {missing}")
    if unknown:
        problems.append(f"group lists non-existent skills: {unknown}")
    if problems:
        print("marketplace generation failed:\n  " + "\n  ".join(problems), file=sys.stderr)
        sys.exit(2)

    plugins = []

    # 1) everything bundle
    plugins.append(
        {
            "name": "yk-everything",
            "source": "./",
            "description": "The whole pack — all {} skills in one install. Heaviest context cost; prefer a themed bundle or single skill.".format(
                len(skills)
            ),
            "version": "1.0.0",
            "category": "bundle",
            "strict": False,
            "skills": ["./skills/"],
            "agents": CLAUDE_AGENTS,
        }
    )

    # 2) themed bundles
    for key, (category, blurb, members) in GROUPS.items():
        entry = {
            "name": key,
            "source": "./",
            "description": blurb,
            "version": "1.0.0",
            "category": "bundle",
            "tags": [category],
            "strict": False,
            "skills": [f"./skills/{m}" for m in members],
        }
        if key in AGENT_BUNDLES:
            entry["agents"] = CLAUDE_AGENTS
        plugins.append(entry)

    # 3) one plugin per skill (fine-grained install/uninstall)
    skill_to_cat = {s: cat for _k, (cat, _b, members) in GROUPS.items() for s in members}
    for s in skills:
        plugins.append(
            {
                "name": s,
                "source": "./",
                "description": skill_desc(v, s),
                "version": "1.0.0",
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
            "description": "Skills for AI coding agents — review, research, UI/UX audit, MCP & framework builders, browser/device automation, config files, publish. Install the whole pack, a themed bundle, or a single skill.",
            "version": "1.0.0",
        },
        "plugins": plugins,
    }


def main():
    check = "--check" in sys.argv
    data = build()
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"

    if check:
        current = open(OUT_PATH).read() if os.path.isfile(OUT_PATH) else ""
        if current != rendered:
            print(
                "marketplace.json is stale — run: python3 scripts/gen-marketplace.py",
                file=sys.stderr,
            )
            sys.exit(1)
        print("marketplace.json is up to date")
        return

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        f.write(rendered)
    print(f"wrote {os.path.relpath(OUT_PATH, REPO_ROOT)} — {len(data['plugins'])} plugins")


if __name__ == "__main__":
    main()
