#!/usr/bin/env python3
"""Static audit for converting a repo to Vercel local-prebuilt deploys.

This script does not read .env files and does not run Vercel network commands.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


SECRET_ENV_NAMES = {".env", ".env.local", ".env.production", ".env.development"}


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        return {"__error__": str(exc)}


def detect_package_manager(repo: Path, package_json: dict[str, Any]) -> str:
    package_manager = str(package_json.get("packageManager", ""))
    if package_manager.startswith("pnpm@") or (repo / "pnpm-lock.yaml").exists():
        return "pnpm"
    if package_manager.startswith("yarn@") or (repo / "yarn.lock").exists():
        return "yarn"
    if package_manager.startswith("bun@") or (repo / "bun.lockb").exists() or (repo / "bun.lock").exists():
        return "bun"
    if (repo / "package-lock.json").exists() or (repo / "npm-shrinkwrap.json").exists():
        return "npm"
    return "unknown"


def vercel_exec(package_manager: str, has_local_vercel: bool) -> str:
    if package_manager == "pnpm":
        return "pnpm exec vercel" if has_local_vercel else "pnpm dlx vercel"
    if package_manager == "yarn":
        return "yarn vercel" if has_local_vercel else "yarn dlx vercel"
    if package_manager == "bun":
        return "bunx vercel"
    if package_manager == "npm":
        return "npm exec vercel --" if has_local_vercel else "npx vercel"
    return "vercel"


def output_stats(repo: Path) -> dict[str, Any]:
    output = repo / ".vercel" / "output"
    config = output / "config.json"
    if not output.exists():
        return {"exists": False, "config": False}
    total = 0
    files = 0
    for root, _, names in os.walk(output):
        for name in names:
            try:
                total += (Path(root) / name).stat().st_size
                files += 1
            except OSError:
                pass
    return {
        "exists": True,
        "config": config.exists(),
        "bytes": total,
        "megabytes": round(total / 1024 / 1024, 2),
        "files": files,
    }


def audit(repo: Path) -> dict[str, Any]:
    package_json = load_json(repo / "package.json")
    vercel_json = load_json(repo / "vercel.json")
    project_json = load_json(repo / ".vercel" / "project.json")
    package_manager = detect_package_manager(repo, package_json)

    deps = {}
    for key in ("dependencies", "devDependencies"):
        value = package_json.get(key)
        if isinstance(value, dict):
            deps.update(value)
    scripts = package_json.get("scripts") if isinstance(package_json.get("scripts"), dict) else {}
    has_local_vercel = "vercel" in deps
    vc = vercel_exec(package_manager, has_local_vercel)
    git = vercel_json.get("git") if isinstance(vercel_json.get("git"), dict) else {}

    env_files = sorted(p.name for p in repo.iterdir() if p.is_file() and p.name in SECRET_ENV_NAMES)
    risky_scripts = [
        name
        for name, value in scripts.items()
        if isinstance(value, str)
        and "vercel deploy" in value
        and "--prebuilt" not in value
        and "deploy" in name
    ]

    warnings: list[str] = []
    actions: list[str] = []
    if not project_json:
        warnings.append(".vercel/project.json not found; project is not linked in this checkout")
        actions.append(f"{vc} link --scope <team>")
    if not has_local_vercel:
        warnings.append("vercel is not pinned in package dependencies/devDependencies")
        actions.append("add vercel as a dev dependency or document deliberate global CLI fallback")
    if risky_scripts:
        warnings.append("package scripts include Vercel deploy commands without --prebuilt: " + ", ".join(risky_scripts))
    if git.get("deploymentEnabled") is not False:
        warnings.append("vercel.json does not disable Git deployments; decide whether local-prebuilt must be mandatory")
    if output_stats(repo).get("exists") and not output_stats(repo).get("config"):
        warnings.append(".vercel/output exists but config.json is missing; do not deploy it")

    commands = {
        "pullProduction": f"{vc} pull --yes --environment=production --scope <team>",
        "buildProduction": f"{vc} build --prod --yes --scope <team>",
        "deployProductionPrebuilt": f"{vc} deploy --prebuilt --prod --scope <team> --yes --archive=tgz",
        "stageProductionPrebuilt": f"{vc} deploy --prebuilt --prod --skip-domain --scope <team> --yes --archive=tgz",
        "envRunExample": f"{vc} env run --environment=production --scope <team> -- <command>",
    }

    return {
        "repo": str(repo),
        "packageManager": package_manager,
        "hasPackageJson": bool(package_json),
        "hasLocalVercelDependency": has_local_vercel,
        "vercelCommand": vc,
        "linkedProject": bool(project_json),
        "vercelJson": {
            "present": bool(vercel_json),
            "buildCommand": vercel_json.get("buildCommand"),
            "installCommand": vercel_json.get("installCommand"),
            "outputDirectory": vercel_json.get("outputDirectory"),
            "gitDeploymentEnabled": git.get("deploymentEnabled"),
        },
        "envFilesPresentWithoutReading": env_files,
        "output": output_stats(repo),
        "warnings": warnings,
        "recommendedActions": actions,
        "commands": commands,
    }


def print_text(result: dict[str, Any]) -> None:
    print("Vercel local-prebuild audit")
    print(f"repo: {result['repo']}")
    print(f"package manager: {result['packageManager']}")
    print(f"vercel command: {result['vercelCommand']}")
    print(f"linked project: {result['linkedProject']}")
    print(f"local vercel dependency: {result['hasLocalVercelDependency']}")
    print(f"git deployment enabled: {result['vercelJson']['gitDeploymentEnabled']}")
    print(f"env files present (not read): {', '.join(result['envFilesPresentWithoutReading']) or 'none'}")
    print(f"output: {json.dumps(result['output'], sort_keys=True)}")
    if result["warnings"]:
        print("\nwarnings:")
        for warning in result["warnings"]:
            print(f"- {warning}")
    if result["recommendedActions"]:
        print("\nrecommended actions:")
        for action in result["recommendedActions"]:
            print(f"- {action}")
    print("\ncommands:")
    for name, command in result["commands"].items():
        print(f"- {name}: {command}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".", help="Repository root to inspect")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    result = audit(repo)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
