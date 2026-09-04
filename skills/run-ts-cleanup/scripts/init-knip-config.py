#!/usr/bin/env python3
"""Initialize an optimal, production-grade Knip configuration file.

Scans the target project directory for modern frameworks, testing tools,
code quality linters, and monorepo configurations. Generates a strictly-typed,
framework-tuned knip.jsonc or knip.json configuration avoiding broad ignores
while enabling targeted rules and automated plugins.

Supported Frameworks & Tooling:
    - Web Frameworks: Next.js, Remix, Vite, Astro, Nuxt, SvelteKit, NestJS, Express
    - Testing Frameworks: Vitest, Jest, Cypress, Playwright, Storybook
    - Linters & Styling: Tailwind CSS, ESLint, Prettier
    - Monorepo Engines: pnpm-workspace.yaml, package.json workspaces, lerna.json, turbo.json, nx.json

Usage:
    python3 init-knip-config.py
    python3 init-knip-config.py --target /path/to/project
    python3 init-knip-config.py --format json --force
    python3 init-knip-config.py --dry-run

Exit codes:
    0  Successfully generated configuration (or dry-run printed)
    1  Target file already exists (and --force was not specified) or invalid target
    2  CLI syntax error
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Knip publishes two schemas per major version: schema.json for knip.json and
# schema-jsonc.json for knip.jsonc. Resolve the major from the installed knip so
# the emitted $schema matches the toolchain that will actually read the config;
# fall back to DEFAULT_KNIP_MAJOR when knip is not resolvable.
DEFAULT_KNIP_MAJOR = "6"


def detect_knip_major(cwd: Path) -> str:
    """Return the installed knip major version, or DEFAULT_KNIP_MAJOR if unknown."""
    try:
        proc = subprocess.run(
            ["npx", "--no-install", "knip", "--version"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return DEFAULT_KNIP_MAJOR
    if proc.returncode != 0:
        return DEFAULT_KNIP_MAJOR
    major = proc.stdout.strip().lstrip("v").split(".")[0]
    return major if major.isdigit() else DEFAULT_KNIP_MAJOR


def knip_schema_url(major: str, fmt: str) -> str:
    """Return the $schema URL for a knip major version and config format."""
    filename = "schema-jsonc.json" if fmt == "jsonc" else "schema.json"
    return f"https://unpkg.com/knip@{major}/{filename}"

DEFAULT_STRICT_RULES: dict[str, str] = {
    "files": "error",
    "dependencies": "error",
    "devDependencies": "error",
    "unlisted": "error",
    "binaries": "error",
    "unresolved": "error",
    "exports": "error",
    "types": "error",
    "nsExports": "error",
    "nsTypes": "error",
    "duplicateExports": "error",
    "enumMembers": "warn",
    "classMembers": "off",
}

DEFAULT_TARGETED_IGNORES: dict[str, Any] = {
    "ignoreExportsUsedInFile": {
        "interface": True,
        "type": True,
    },
    "ignoreDependencies": [
        "@types/*",
    ],
    "ignoreBinaries": [
        "docker",
        "docker-compose",
        "git",
    ],
}


@dataclass
class ScanResult:
    """Discovered project characteristics and indicators."""

    target_dir: Path
    package_json: dict[str, Any] = field(default_factory=dict)
    all_dependencies: set[str] = field(default_factory=set)
    frameworks: set[str] = field(default_factory=set)
    is_monorepo: bool = False
    monorepo_type: str | None = None
    workspace_patterns: list[str] = field(default_factory=list)
    has_typescript: bool = False
    existing_config_file: Path | None = None


class ProjectScanner:
    """Scans repository files and package manifests for frameworks and monorepos."""

    def __init__(self, target_dir: Path) -> None:
        self.target_dir = target_dir.resolve()

    def scan(self) -> ScanResult:
        """Perform comprehensive scan of the target directory."""
        if not self.target_dir.is_dir():
            raise ValueError(f"Target path does not exist or is not a directory: {self.target_dir}")

        result = ScanResult(target_dir=self.target_dir)

        # 1. Inspect package.json
        pkg_path = self.target_dir / "package.json"
        if pkg_path.is_file():
            try:
                with open(pkg_path, "r", encoding="utf-8") as f:
                    result.package_json = json.load(f)
            except Exception as e:
                print(f"[WARN] Failed to parse package.json: {e}", file=sys.stderr)

        deps = set()
        for field_name in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            section = result.package_json.get(field_name, {})
            if isinstance(section, dict):
                deps.update(section.keys())
        result.all_dependencies = deps

        # 2. Check TypeScript
        result.has_typescript = (
            "typescript" in deps
            or (self.target_dir / "tsconfig.json").is_file()
            or bool(list(self.target_dir.glob("*.ts")))
            or bool(list(self.target_dir.glob("src/**/*.ts")))
        )

        # 3. Detect Monorepos
        self._detect_monorepo(result)

        # 4. Detect Frameworks & Tooling
        self._detect_frameworks(result)

        # 5. Check for existing Knip configs
        for candidate in (
            "knip.json",
            "knip.jsonc",
            ".knip.json",
            ".knip.jsonc",
            "knip.ts",
            "knip.js",
            "knip.config.ts",
            "knip.config.js",
        ):
            candidate_path = self.target_dir / candidate
            if candidate_path.is_file():
                result.existing_config_file = candidate_path
                break

        return result

    def _detect_monorepo(self, result: ScanResult) -> None:
        """Identify monorepo orchestrators and workspace definitions."""
        # Check pnpm-workspace.yaml
        pnpm_workspace = self.target_dir / "pnpm-workspace.yaml"
        if pnpm_workspace.is_file():
            result.is_monorepo = True
            result.monorepo_type = "pnpm"
            patterns = self._extract_yaml_packages(pnpm_workspace)
            if patterns:
                result.workspace_patterns = patterns
            else:
                result.workspace_patterns = ["packages/*"]

        # Check package.json workspaces
        workspaces = result.package_json.get("workspaces")
        if workspaces:
            result.is_monorepo = True
            result.monorepo_type = result.monorepo_type or "npm/yarn"
            if isinstance(workspaces, list):
                result.workspace_patterns.extend([w for w in workspaces if isinstance(w, str)])
            elif isinstance(workspaces, dict) and "packages" in workspaces:
                pkgs = workspaces.get("packages")
                if isinstance(pkgs, list):
                    result.workspace_patterns.extend([p for p in pkgs if isinstance(p, str)])

        # Check lerna.json
        lerna_json = self.target_dir / "lerna.json"
        if lerna_json.is_file():
            result.is_monorepo = True
            result.monorepo_type = result.monorepo_type or "lerna"
            try:
                with open(lerna_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                pkgs = data.get("packages")
                if isinstance(pkgs, list):
                    result.workspace_patterns.extend([p for p in pkgs if isinstance(p, str)])
            except Exception:
                pass

        # Check turbo.json
        if (self.target_dir / "turbo.json").is_file() or "turbo" in result.all_dependencies:
            result.frameworks.add("turbo")
            if not result.is_monorepo and not result.workspace_patterns:
                result.is_monorepo = True
                result.monorepo_type = "turborepo"
                result.workspace_patterns = ["apps/*", "packages/*"]

        # Check nx.json
        if (self.target_dir / "nx.json").is_file() or "nx" in result.all_dependencies:
            result.frameworks.add("nx")
            if not result.is_monorepo and not result.workspace_patterns:
                result.is_monorepo = True
                result.monorepo_type = "nx"
                result.workspace_patterns = ["apps/*", "libs/*"]

        # Deduplicate patterns
        if result.workspace_patterns:
            result.workspace_patterns = sorted(list(set(result.workspace_patterns)))

    def _extract_yaml_packages(self, yaml_path: Path) -> list[str]:
        """Simple, zero-dependency parser to extract package globs from pnpm-workspace.yaml."""
        patterns: list[str] = []
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            in_packages = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("packages:"):
                    in_packages = True
                    continue
                if in_packages:
                    if stripped.startswith("-"):
                        match = re.search(r"['\"]?([^'\"#\n]+)['\"]?", stripped[1:].strip())
                        if match:
                            pkg_glob = match.group(1).strip()
                            if pkg_glob:
                                patterns.append(pkg_glob)
                    elif stripped and not stripped.startswith("#") and not line.startswith(" "):
                        break
        except Exception:
            pass
        return patterns

    def _has_file(self, pattern: str) -> bool:
        """Check if any file in root matches the glob pattern."""
        try:
            return bool(list(self.target_dir.glob(pattern)))
        except Exception:
            return False

    def _detect_frameworks(self, result: ScanResult) -> None:
        """Scan project for each required framework indicator."""
        deps = result.all_dependencies

        # 1. Next.js
        if "next" in deps or self._has_file("next.config.*") or (self.target_dir / "next-env.d.ts").is_file():
            result.frameworks.add("next")

        # 2. Remix
        if any(d.startswith("@remix-run/") for d in deps) or self._has_file("remix.config.*"):
            result.frameworks.add("remix")

        # 3. Vite
        if "vite" in deps or self._has_file("vite.config.*"):
            result.frameworks.add("vite")

        # 4. Astro
        if "astro" in deps or self._has_file("astro.config.*"):
            result.frameworks.add("astro")

        # 5. Nuxt
        if "nuxt" in deps or self._has_file("nuxt.config.*"):
            result.frameworks.add("nuxt")

        # 6. SvelteKit
        if "@sveltejs/kit" in deps or "svelte" in deps or self._has_file("svelte.config.*"):
            result.frameworks.add("sveltekit")

        # 7. NestJS
        if "@nestjs/core" in deps or (self.target_dir / "nest-cli.json").is_file():
            result.frameworks.add("nest")

        # 8. Express
        if "express" in deps or (self.target_dir / "src/server.ts").is_file() or (self.target_dir / "src/app.ts").is_file():
            result.frameworks.add("express")

        # 9. Storybook
        if (
            any(d.startswith("@storybook/") for d in deps)
            or (self.target_dir / ".storybook").is_dir()
            or self._has_file(".storybook/main.*")
        ):
            result.frameworks.add("storybook")

        # 10. Vitest
        if "vitest" in deps or self._has_file("vitest.config.*"):
            result.frameworks.add("vitest")

        # 11. Jest
        if "jest" in deps or "jest" in result.package_json or self._has_file("jest.config.*"):
            result.frameworks.add("jest")

        # 12. Cypress
        if "cypress" in deps or (self.target_dir / "cypress").is_dir() or self._has_file("cypress.config.*"):
            result.frameworks.add("cypress")

        # 13. Playwright
        if "@playwright/test" in deps or "playwright" in deps or self._has_file("playwright.config.*"):
            result.frameworks.add("playwright")

        # 14. Tailwind CSS
        if "tailwindcss" in deps or any(d.startswith("@tailwindcss/") for d in deps) or self._has_file("tailwind.config.*"):
            result.frameworks.add("tailwind")

        # 15. ESLint
        if (
            "eslint" in deps
            or "eslintConfig" in result.package_json
            or self._has_file("eslint.config.*")
            or self._has_file(".eslintrc*")
        ):
            result.frameworks.add("eslint")

        # 16. Prettier
        if (
            "prettier" in deps
            or "prettier" in result.package_json
            or self._has_file(".prettierrc*")
            or self._has_file("prettier.config.*")
        ):
            result.frameworks.add("prettier")


class ConfigGenerator:
    """Builds optimal Knip configuration tailored to discovered frameworks."""

    def __init__(self, scan: ScanResult, schema_url: str = "") -> None:
        self.scan = scan
        self.schema_url = schema_url or knip_schema_url(DEFAULT_KNIP_MAJOR, "jsonc")

    def build_config(self) -> dict[str, Any]:
        """Construct the configuration dictionary."""
        config: dict[str, Any] = {
            "$schema": self.schema_url,
        }

        # Root-level entry/project describe a single-package layout. In a monorepo
        # the per-workspace blocks below own that, and a monorepo root usually has
        # no src/ at all -- emitting these would point Knip at a path that does
        # not exist.
        if not self.scan.is_monorepo:
            entries = self._build_entries()
            if entries:
                config["entry"] = entries
            config["project"] = self._build_project_pattern()

        # Targeted ignores (strictly avoid broad top-level "ignore")
        config.update(DEFAULT_TARGETED_IGNORES)

        # Strict rules configuration
        rules = dict(DEFAULT_STRICT_RULES)
        # NestJS or decorator heavy repos benefit from disabling classMembers to prevent false positives
        if "nest" in self.scan.frameworks:
            rules["classMembers"] = "off"
        config["rules"] = rules

        # Plugins
        plugins = self._build_plugins()
        config.update(plugins)

        # Monorepo Workspaces
        if self.scan.is_monorepo and self.scan.workspace_patterns:
            workspaces: dict[str, Any] = {
                ".": {
                    "entry": ["scripts/**/*.{js,mjs,ts}"],
                    "project": ["scripts/**/*.{js,mjs,ts}"],
                }
            }
            for pattern in self.scan.workspace_patterns:
                clean_pattern = pattern.rstrip("/")
                # pnpm-workspace.yaml expresses exclusions as '!apps/website'.
                # Knip workspace keys are directory globs with no negation form,
                # so a '!'-prefixed key names a directory that does not exist.
                # Drop exclusions here; the positive globs still cover the rest.
                if clean_pattern.startswith("!"):
                    continue
                if clean_pattern.startswith("packages") or clean_pattern.startswith("libs"):
                    workspaces[clean_pattern] = {
                        "entry": ["src/index.ts!"],
                        "project": ["src/**/*.{js,jsx,ts,tsx}"],
                    }
                elif clean_pattern.startswith("apps"):
                    workspaces[clean_pattern] = {
                        "project": ["src/**/*.{js,jsx,ts,tsx}"],
                    }
                else:
                    workspaces[clean_pattern] = {
                        "entry": ["src/index.{js,ts}!"],
                        "project": ["src/**/*.{js,jsx,ts,tsx}"],
                    }
            config["workspaces"] = workspaces

        return config

    def _build_entries(self) -> list[str]:
        """Collect entry points tailored to discovered frameworks and existing files."""
        entries: list[str] = []
        fw = self.scan.frameworks
        target = self.scan.target_dir

        if "next" in fw:
            # Next.js App Router and Pages Router conventions
            entries.extend([
                "app/**/{page,layout,loading,error,not-found,route,default,template}.{js,jsx,ts,tsx}",
                "pages/**/*.{js,jsx,ts,tsx}",
                "middleware.{js,ts}",
                "instrumentation.{js,ts}",
            ])
        if "remix" in fw:
            entries.extend([
                "app/root.{jsx,tsx}",
                "app/routes/**/*.{jsx,tsx}",
                "app/entry.{client,server}.{jsx,tsx}",
            ])
        if "astro" in fw:
            entries.extend([
                "src/pages/**/*.{astro,md,mdx,html,js,ts}",
                "src/content/config.ts",
            ])
        if "nuxt" in fw:
            entries.extend([
                "app.vue",
                "pages/**/*.{vue,js,ts}",
                "server/**/*.{js,ts}",
                "middleware/**/*.{js,ts}",
                "plugins/**/*.{js,ts}",
            ])
        if "sveltekit" in fw:
            entries.extend([
                "src/routes/**/+{page,layout,error,server}.{svelte,js,ts}",
                "src/hooks.{client,server}.{js,ts}",
            ])
        if "nest" in fw:
            entries.append("src/main.ts!")
        if "vite" in fw and not entries:
            entries.append("index.html")
        if "express" in fw and not ("next" in fw or "remix" in fw or "nest" in fw):
            for candidate in ("src/index.ts", "src/server.ts", "src/app.ts", "src/index.js", "src/server.js", "src/app.js"):
                if (target / candidate).is_file():
                    entries.append(candidate)
            if not entries:
                entries.append("src/index.ts")

        # Standard default fallback if no meta-framework entry points added
        if not entries:
            for default_entry in ("src/index.ts", "src/main.ts", "src/index.js", "src/main.js", "index.ts", "index.js"):
                if (target / default_entry).is_file():
                    entries.append(default_entry)
                    break
            if not entries:
                entries.append("src/index.ts")

        # Deduplicate while preserving order
        seen: set[str] = set()
        deduped: list[str] = []
        for e in entries:
            if e not in seen:
                seen.add(e)
                deduped.append(e)
        return deduped

    def _build_project_pattern(self) -> list[str]:
        """Construct project file matching patterns matching discovered extensions."""
        exts = ["js", "jsx", "ts", "tsx"]
        fw = self.scan.frameworks

        if "astro" in fw:
            exts.append("astro")
        if "nuxt" in fw:
            exts.append("vue")
        if "sveltekit" in fw:
            exts.append("svelte")

        ext_pattern = ",".join(exts)
        return [f"src/**/*.{{{ext_pattern}}}"]

    def _build_plugins(self) -> dict[str, Any]:
        """Auto-configure detected plugins."""
        plugins: dict[str, Any] = {}
        fw = self.scan.frameworks

        # Frameworks
        if "next" in fw:
            plugins["next"] = True
        if "remix" in fw:
            plugins["remix"] = True
        if "vite" in fw:
            plugins["vite"] = True
        if "astro" in fw:
            plugins["astro"] = True
        if "nuxt" in fw:
            plugins["nuxt"] = True
        if "sveltekit" in fw:
            plugins["svelte"] = True
        if "nest" in fw:
            plugins["nest"] = True

        # Testing tools
        if "vitest" in fw:
            plugins["vitest"] = True
        if "jest" in fw:
            plugins["jest"] = True
        if "cypress" in fw:
            plugins["cypress"] = True
        if "playwright" in fw:
            plugins["playwright"] = True
        if "storybook" in fw:
            plugins["storybook"] = True

        # Linters and formatters
        if "tailwind" in fw:
            plugins["tailwind"] = True
        if "eslint" in fw:
            plugins["eslint"] = True
        if "prettier" in fw:
            plugins["prettier"] = True

        # Monorepos
        if "turbo" in fw:
            plugins["turbo"] = True
        if "nx" in fw:
            plugins["nx"] = True

        return plugins

    def to_json(self) -> str:
        """Format configuration as strict standard JSON."""
        config = self.build_config()
        return json.dumps(config, indent=2) + "\n"

    def to_jsonc(self) -> str:
        """Format configuration as JSONC with pedagogical, actionable comments."""
        config = self.build_config()
        fw_list = ", ".join(sorted(self.scan.frameworks)) or "None detected (standard TypeScript/JavaScript)"
        monorepo_desc = f"{self.scan.monorepo_type} monorepo" if self.scan.is_monorepo else "Single-package repository"

        lines: list[str] = [
            "// Knip Configuration (knip.jsonc)",
            "// Auto-generated by init-knip-config.py",
            f"// Architecture: {monorepo_desc}",
            f"// Discovered Frameworks & Tooling: {fw_list}",
            "//",
            "// Webpro Rule: NEVER use top-level 'ignore' to bypass warnings.",
            "// Broad ignores cause transitive graph blindness, creating false",
            "// unused dependency warnings and dangerous dead file deletion risks.",
            "{",
            f'  "$schema": "{self.schema_url}",',
        ]

        # Entry
        if "entry" in config:
            lines.append("  // Entry points tailored to discovered frameworks and routing conventions")
            lines.append('  "entry": [')
            for i, entry in enumerate(config["entry"]):
                comma = "," if i < len(config["entry"]) - 1 else ""
                lines.append(f'    "{entry}"{comma}')
            lines.append("  ],")

        # Project
        lines.append("  // Project files included in the dependency graph analysis")
        lines.append('  "project": [')
        for i, p in enumerate(config["project"]):
            comma = "," if i < len(config["project"]) - 1 else ""
            lines.append(f'    "{p}"{comma}')
        lines.append("  ],")

        # Targeted ignores
        lines.append("  // Targeted ignores: silences local helper exports without breaking transitive graph walking")
        lines.append('  "ignoreExportsUsedInFile": {')
        lines.append('    "interface": true,')
        lines.append('    "type": true')
        lines.append("  },")

        lines.append('  "ignoreDependencies": [')
        for i, d in enumerate(config["ignoreDependencies"]):
            comma = "," if i < len(config["ignoreDependencies"]) - 1 else ""
            lines.append(f'    "{d}"{comma}')
        lines.append("  ],")

        lines.append("  // Ignore host binaries invoked via package scripts that are not direct dependencies")
        lines.append('  "ignoreBinaries": [')
        for i, b in enumerate(config["ignoreBinaries"]):
            comma = "," if i < len(config["ignoreBinaries"]) - 1 else ""
            lines.append(f'    "{b}"{comma}')
        lines.append("  ],")

        # Rules
        lines.append("  // Strict enterprise rule configuration: enforce clean dependencies, files, and exports")
        lines.append('  "rules": {')
        rule_items = list(config["rules"].items())
        for i, (k, v) in enumerate(rule_items):
            comma = "," if i < len(rule_items) - 1 else ""
            lines.append(f'    "{k}": "{v}"{comma}')
        lines.append("  }")

        # Plugins
        plugin_keys = [
            k for k in config.keys()
            if k not in ("$schema", "entry", "project", "ignoreExportsUsedInFile", "ignoreDependencies", "ignoreBinaries", "rules", "workspaces")
        ]
        if plugin_keys:
            lines[-1] = lines[-1] + ","
            lines.append("  // Auto-configured ecosystem plugins")
            for i, k in enumerate(plugin_keys):
                comma = "," if (i < len(plugin_keys) - 1 or "workspaces" in config) else ""
                v_str = "true" if config[k] is True else json.dumps(config[k])
                lines.append(f'  "{k}": {v_str}{comma}')

        # Workspaces
        if "workspaces" in config:
            if not lines[-1].endswith(","):
                lines[-1] = lines[-1] + ","
            lines.append("  // Monorepo workspace mapping")
            ws_json = json.dumps({"workspaces": config["workspaces"]}, indent=2)
            # ws_lines has 2-space indentation matching config level
            ws_lines = ws_json.splitlines()[1:-1]
            for line in ws_lines:
                lines.append(line)

        lines.append("}")
        return "\n".join(lines) + "\n"


def main() -> int:
    """CLI Entrypoint for init-knip-config."""
    parser = argparse.ArgumentParser(
        description="Scan project and generate optimal, framework-tuned Knip configuration (knip.jsonc or knip.json).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --target /path/to/project --format jsonc
  %(prog)s --format json --force
  %(prog)s --dry-run
        """,
    )
    parser.add_argument(
        "--target",
        type=str,
        default=".",
        help="Path to project root directory (default: current directory).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "jsonc"],
        default="jsonc",
        help="Configuration file format (default: jsonc).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing Knip configuration file if found.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Output the generated configuration to stdout without writing to disk.",
    )

    args = parser.parse_args()
    target_path = Path(args.target).resolve()

    if not target_path.is_dir():
        print(f"Error: Target path '{target_path}' is not a valid directory.", file=sys.stderr)
        return 1

    try:
        scanner = ProjectScanner(target_path)
        scan_result = scanner.scan()
    except Exception as e:
        print(f"Error during project scan: {e}", file=sys.stderr)
        return 1

    dest_filename = f"knip.{args.format}"
    dest_path = target_path / dest_filename

    # Collision check if not dry-run
    if not args.dry_run:
        existing = scan_result.existing_config_file
        if existing and existing.exists() and not args.force:
            print(
                f"Error: Knip configuration file already exists at '{existing}'. Use --force to overwrite.",
                file=sys.stderr,
            )
            return 1

    schema_url = knip_schema_url(detect_knip_major(target_path), args.format)
    generator = ConfigGenerator(scan_result, schema_url=schema_url)
    content = generator.to_jsonc() if args.format == "jsonc" else generator.to_json()

    if args.dry_run:
        sys.stdout.write(content)
        return 0

    try:
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully generated {dest_path}")
        print(f"Discovered Frameworks: {', '.join(sorted(scan_result.frameworks)) or 'None'}")
        if scan_result.is_monorepo:
            print(f"Monorepo Type: {scan_result.monorepo_type}")
            print(f"Workspaces: {', '.join(scan_result.workspace_patterns)}")
        return 0
    except Exception as e:
        print(f"Error writing configuration to '{dest_path}': {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
