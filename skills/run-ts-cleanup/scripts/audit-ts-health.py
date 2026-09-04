#!/usr/bin/env python3
"""Audit TypeScript Codebase Health: AI Slop, Linters, tsconfig, and Circular Dependencies.

Performs automated static quality audits across TypeScript and JavaScript repositories:
  1. AI Slop Markers: Useless try/catch rethrow blocks, duplicate utility functions
     (cn, formatDate, slugify, etc.), and verbose boolean ternaries / boolean theater.
  2. Linter & Formatter Detection: Identifies Biome, Oxlint, ESLint, Prettier, Ultracite,
     checks for configuration pairing and conflicts, and recommends autofix recipes.
  3. TypeScript Config Health: Audits tsconfig.json compilerOptions for strict mode,
     isolatedDeclarations, noUncheckedIndexedAccess, declaration emit, and modern flags.
  4. Circular Dependency Risk: Detects import cycles via built-in dependency graph
     scanning or madge (if installed), flagging high-risk barrel file loops.

Outputs either an executive Markdown summary or a machine-readable JSON document.

Usage:
    # Run full health audit on current directory and emit Markdown
    python3 audit-ts-health.py

    # Target specific project directory
    python3 audit-ts-health.py --target /path/to/project

    # Output structured JSON for automation or CI pipelines
    python3 audit-ts-health.py --format json

    # Run specific audit modules
    python3 audit-ts-health.py --check-slop --check-circular
    python3 audit-ts-health.py --check-linters --format markdown --out-file report.md

Exit codes:
    0  Audit completed successfully (even if warnings or findings exist)
    1  Target directory does not exist or fatal error
    2  CLI syntax error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

Severity = Literal["High", "Medium", "Low", "Info"]
HealthStatus = Literal["PASS", "WARN", "FAIL"]

IGNORED_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    ".next",
    ".turbo",
    ".nuxt",
    ".svelte-kit",
    ".astro",
    "coverage",
    ".cache",
    "out",
    ".output",
    "storybook-static",
    "vendor",
}

SOURCE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}

COMMON_UTILITY_NAMES = {
    "cn",
    "clsx",
    "formatDate",
    "formatTime",
    "formatDateTime",
    "formatCurrency",
    "slugify",
    "capitalize",
    "sleep",
    "delay",
    "truncate",
    "clamp",
    "safeJsonParse",
    "isStringEmpty",
    "getUserId",
    "buildFullName",
}

BARREL_FILENAME_REGEX = re.compile(
    r"(^|/)(index|api|public-api|exports|barrel)\.(ts|tsx|js|jsx|mjs|cjs)$",
    re.IGNORECASE,
)


def parse_jsonc(text: str) -> dict[str, Any]:
    """Parse JSON with single-line comments, block comments, and trailing commas."""
    def replace_comment(match: re.Match[str]) -> str:
        if match.group(1):
            return match.group(1)
        return ""

    clean = re.sub(r'("(?:\\.|[^"\\])*")|//[^\r\n]*|/\*[\s\S]*?\*/', replace_comment, text)
    clean = re.sub(r',\s*([}\]])', r'\1', clean)
    return json.loads(clean)


# =============================================================================
# 1. AI Slop Markers
# =============================================================================

@dataclass
class SlopFinding:
    """Individual AI slop marker violation."""

    id: str
    category: str
    rule: str
    file: str
    line: int
    risk: Severity
    snippet: str
    action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SlopDetector:
    """Detects useless try/catch wrappers, utility duplication, and boolean theater."""

    def __init__(self, target_dir: Path) -> None:
        self.target_dir = target_dir.resolve()
        self.findings: list[SlopFinding] = []
        self._finding_count = 0

        self.re_catch_block = re.compile(
            r"catch\s*(?:\((?P<var>[a-zA-Z0-9_$]+)(?:\s*:\s*[^)]+)?\))?\s*\{(?P<body>[^{}]*?)\}",
            re.DOTALL,
        )
        self.re_ternary = re.compile(r"\?\s*(?:true\s*:\s*false|false\s*:\s*true)\b")
        self.re_bool_eq = re.compile(r"(?:===|!==)\s*(?:true|false)\b|\b(?:true|false)\s*(?:===|!==)")
        self.re_if_else_bool = re.compile(
            r"if\s*\([^)]+\)\s*\{\s*return\s+true\s*;?\s*\}\s*else\s*\{\s*return\s+false\s*;?\s*\}",
            re.DOTALL,
        )
        self.re_double_neg = re.compile(r"return\s+!!(?:is|has|can|should)[A-Za-z0-9_$]*\b")
        self.re_fn_decl = re.compile(
            r"(?:export\s+)?(?:async\s+)?(?:function\s+(?P<fn>[a-zA-Z0-9_$]+)|(?:const|let|var)\s+(?P<var>[a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[a-zA-Z0-9_$]+)?\s*=>)"
        )

    def scan(self) -> list[SlopFinding]:
        self.findings = []
        self._finding_count = 0

        utility_declarations: dict[str, list[tuple[str, int, str]]] = {
            name: [] for name in COMMON_UTILITY_NAMES
        }

        for file_path in self._find_source_files():
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            rel_file = file_path.relative_to(self.target_dir).as_posix()

            # 1. Check Useless Try/Catch Wrappers
            self._scan_try_catch(rel_file, content)

            # 2. Check Boolean Theater
            self._scan_boolean_theater(rel_file, content)

            # 3. Collect utility declarations
            self._collect_utilities(rel_file, content, utility_declarations)

        # 4. Analyze utility duplication across files
        self._analyze_utility_duplication(utility_declarations)

        return self.findings

    def _find_source_files(self) -> list[Path]:
        files: list[Path] = []
        for root, dirs, filenames in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for filename in filenames:
                ext = Path(filename).suffix
                if ext in SOURCE_EXTENSIONS and not filename.endswith(".d.ts"):
                    files.append(Path(root) / filename)
        return files

    def _next_id(self) -> str:
        self._finding_count += 1
        return f"SLOP-{self._finding_count:03d}"

    def _scan_try_catch(self, file_path: str, content: str) -> None:
        for m in self.re_catch_block.finditer(content):
            body = m.group("body").strip()
            var = m.group("var") or "e"
            lines = [re.sub(r"//.*", "", line).strip() for line in body.splitlines()]
            clean_body = " ".join(line for line in lines if line)
            line_no = content[:m.start()].count("\n") + 1

            if re.match(rf"^throw\s+{re.escape(var)}\s*;?$", clean_body):
                snippet = m.group(0).strip().replace("\n", " ")
                if len(snippet) > 80:
                    snippet = snippet[:77] + "..."
                self.findings.append(
                    SlopFinding(
                        id=self._next_id(),
                        category="Useless Try/Catch",
                        rule="passthrough-rethrow",
                        file=file_path,
                        line=line_no,
                        risk="High",
                        snippet=snippet,
                        action="Remove try/catch wrapper and let error bubble to caller or error boundary.",
                    )
                )
            elif re.match(r"^(?:console\.[a-zA-Z0-9_$]+\([^)]*\)\s*;?\s*)?return\s+(null|undefined|false)\s*;?$", clean_body):
                snippet = m.group(0).strip().replace("\n", " ")
                if len(snippet) > 80:
                    snippet = snippet[:77] + "..."
                self.findings.append(
                    SlopFinding(
                        id=self._next_id(),
                        category="Useless Try/Catch",
                        rule="blind-error-swallowing",
                        file=file_path,
                        line=line_no,
                        risk="High",
                        snippet=snippet,
                        action="Replace silent return with explicit typed error or domain error boundary.",
                    )
                )
            elif clean_body == "":
                self.findings.append(
                    SlopFinding(
                        id=self._next_id(),
                        category="Useless Try/Catch",
                        rule="empty-catch-block",
                        file=file_path,
                        line=line_no,
                        risk="Medium",
                        snippet="catch (...) { }",
                        action="Handle exception or remove empty catch block.",
                    )
                )

    def _scan_boolean_theater(self, file_path: str, content: str) -> None:
        # Ternaries returning booleans
        for m in self.re_ternary.finditer(content):
            line_no = content[:m.start()].count("\n") + 1
            match_str = m.group(0).strip()
            self.findings.append(
                SlopFinding(
                    id=self._next_id(),
                    category="Boolean Theater",
                    rule="redundant-boolean-ternary",
                    file=file_path,
                    line=line_no,
                    risk="Medium",
                    snippet=match_str,
                    action="Simplify ternary: replace 'cond ? true : false' with 'Boolean(cond)' or '!cond'.",
                )
            )

        # Equality comparison against true/false
        for m in self.re_bool_eq.finditer(content):
            line_no = content[:m.start()].count("\n") + 1
            match_str = m.group(0).strip()
            self.findings.append(
                SlopFinding(
                    id=self._next_id(),
                    category="Boolean Theater",
                    rule="explicit-boolean-comparison",
                    file=file_path,
                    line=line_no,
                    risk="Low",
                    snippet=match_str,
                    action="Simplify condition: replace 'x === true' with 'x' or 'x === false' with '!x'.",
                )
            )

        # Multi-line if/else returning booleans
        for m in self.re_if_else_bool.finditer(content):
            line_no = content[:m.start()].count("\n") + 1
            snippet = m.group(0).replace("\n", " ").strip()
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
            self.findings.append(
                SlopFinding(
                    id=self._next_id(),
                    category="Boolean Theater",
                    rule="if-else-boolean-return",
                    file=file_path,
                    line=line_no,
                    risk="Medium",
                    snippet=snippet,
                    action="Collapse branch: replace 'if (c) return true; else return false;' with 'return Boolean(c);'.",
                )
            )

        # Double negation on boolean identifiers
        for m in self.re_double_neg.finditer(content):
            line_no = content[:m.start()].count("\n") + 1
            match_str = m.group(0).strip()
            self.findings.append(
                SlopFinding(
                    id=self._next_id(),
                    category="Boolean Theater",
                    rule="redundant-double-negation",
                    file=file_path,
                    line=line_no,
                    risk="Low",
                    snippet=match_str,
                    action="Remove redundant '!!' operator on identifier already declared or typed as boolean.",
                )
            )

    def _collect_utilities(
        self,
        file_path: str,
        content: str,
        utility_declarations: dict[str, list[tuple[str, int, str]]],
    ) -> None:
        for m in self.re_fn_decl.finditer(content):
            fn_name = m.group("fn") or m.group("var")
            if fn_name and fn_name in COMMON_UTILITY_NAMES:
                line_no = content[:m.start()].count("\n") + 1
                decl_line = content.splitlines()[line_no - 1].strip()
                utility_declarations[fn_name].append((file_path, line_no, decl_line))

    def _analyze_utility_duplication(
        self, utility_declarations: dict[str, list[tuple[str, int, str]]]
    ) -> None:
        for util_name, occurrences in utility_declarations.items():
            distinct_files = {occ[0] for occ in occurrences}
            if len(distinct_files) > 1:
                for file_path, line_no, decl_line in occurrences:
                    other_files = [f for f in sorted(distinct_files) if f != file_path]
                    other_preview = ", ".join(other_files[:2]) + ("..." if len(other_files) > 2 else "")
                    self.findings.append(
                        SlopFinding(
                            id=self._next_id(),
                            category="Utility Duplication",
                            rule=f"duplicate-utility-{util_name}",
                            file=file_path,
                            line=line_no,
                            risk="Medium",
                            snippet=f"{decl_line[:60]}",
                            action=(
                                f"Consolidate duplicate '{util_name}' into canonical module "
                                f"(e.g. src/lib/utils.ts); also defined in: {other_preview}."
                            ),
                        )
                    )


# =============================================================================
# 2. Linter & Formatter Detection
# =============================================================================

@dataclass
class ToolDetection:
    """Individual linter or formatter discovery."""

    name: str
    category: Literal["linter", "formatter", "all-in-one"]
    detected: bool
    config_file: str | None = None
    manifest_dependency: str | None = None
    autofix_command: str | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LinterFormatterReport:
    """Complete linter and formatter evaluation."""

    primary_linter: str = "none"
    primary_formatter: str = "none"
    tools: list[ToolDetection] = field(default_factory=list)
    autofix_command: str = "none"
    conflicts_or_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tools"] = [t.to_dict() for t in self.tools]
        return data


class LinterDetector:
    """Discovers installed linters/formatters and produces pairing advice."""

    def __init__(self, target_dir: Path) -> None:
        self.target_dir = target_dir.resolve()
        self.package_json: dict[str, Any] = {}
        self._load_package_json()

    def _load_package_json(self) -> None:
        pkg_file = self.target_dir / "package.json"
        if pkg_file.is_file():
            try:
                self.package_json = json.loads(pkg_file.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                self.package_json = {}

    def _has_dep(self, name: str) -> str | None:
        deps = self.package_json.get("dependencies", {})
        dev_deps = self.package_json.get("devDependencies", {})
        if name in deps:
            return f"dependencies: {name}@{deps[name]}"
        if name in dev_deps:
            return f"devDependencies: {name}@{dev_deps[name]}"
        return None

    def detect(self) -> LinterFormatterReport:
        report = LinterFormatterReport()

        # 1. Ultracite
        ultracite_configs = ["ultracite.json", ".ultraciterc"]
        u_cfg = self._find_first(ultracite_configs)
        u_dep = self._has_dep("ultracite")
        u_detected = bool(u_cfg or u_dep)
        report.tools.append(
            ToolDetection(
                name="Ultracite",
                category="all-in-one",
                detected=u_detected,
                config_file=u_cfg,
                manifest_dependency=u_dep,
                autofix_command="npx ultracite fix",
                notes="Zero-config Biome-based linter and formatter wrapper.",
            )
        )

        # 2. Biome
        biome_configs = ["biome.json", "biome.jsonc"]
        b_cfg = self._find_first(biome_configs)
        b_dep = self._has_dep("@biomejs/biome")
        b_detected = bool(b_cfg or b_dep)
        report.tools.append(
            ToolDetection(
                name="Biome",
                category="all-in-one",
                detected=b_detected,
                config_file=b_cfg,
                manifest_dependency=b_dep,
                autofix_command="npx @biomejs/biome check --write",
                notes="Fast Rust-based all-in-one linter, formatter, and import organizer.",
            )
        )

        # 3. Oxlint
        oxlint_configs = [".oxlintrc.json", "oxlint.json", ".oxlintrc"]
        ox_cfg = self._find_first(oxlint_configs)
        ox_dep = self._has_dep("oxlint")
        ox_detected = bool(ox_cfg or ox_dep)
        report.tools.append(
            ToolDetection(
                name="Oxlint",
                category="linter",
                detected=ox_detected,
                config_file=ox_cfg,
                manifest_dependency=ox_dep,
                autofix_command="npx oxlint --fix",
                notes="Ultra-fast linter; does not format code or sort imports.",
            )
        )

        # 4. ESLint
        eslint_flat = ["eslint.config.js", "eslint.config.mjs", "eslint.config.cjs", "eslint.config.ts"]
        eslint_legacy = [".eslintrc", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json", ".eslintrc.yaml", ".eslintrc.yml"]
        es_flat_cfg = self._find_first(eslint_flat)
        es_leg_cfg = self._find_first(eslint_legacy)
        es_cfg = es_flat_cfg or es_leg_cfg
        es_dep = self._has_dep("eslint")
        es_pkg_key = "eslintConfig" in self.package_json
        es_detected = bool(es_cfg or es_dep or es_pkg_key)
        es_kind = "Flat Config (v9+)" if es_flat_cfg else ("Legacy Config" if es_leg_cfg else "Standard")
        report.tools.append(
            ToolDetection(
                name="ESLint",
                category="linter",
                detected=es_detected,
                config_file=es_cfg or ("package.json (eslintConfig)" if es_pkg_key else None),
                manifest_dependency=es_dep,
                autofix_command="npx eslint --fix",
                notes=f"AST-based linter using {es_kind}.",
            )
        )

        # 5. Prettier
        prettier_configs = [
            ".prettierrc",
            ".prettierrc.json",
            ".prettierrc.yml",
            ".prettierrc.yaml",
            ".prettierrc.js",
            ".prettierrc.cjs",
            ".prettierrc.mjs",
            ".prettierrc.toml",
            "prettier.config.js",
            "prettier.config.cjs",
            "prettier.config.mjs",
        ]
        pr_cfg = self._find_first(prettier_configs)
        pr_dep = self._has_dep("prettier")
        pr_pkg_key = "prettier" in self.package_json
        pr_detected = bool(pr_cfg or pr_dep or pr_pkg_key)
        report.tools.append(
            ToolDetection(
                name="Prettier",
                category="formatter",
                detected=pr_detected,
                config_file=pr_cfg or ("package.json (prettier)" if pr_pkg_key else None),
                manifest_dependency=pr_dep,
                autofix_command='npx prettier --write "src/**/*.{ts,tsx,js,jsx,json}"',
                notes="Opinionated code formatter.",
            )
        )

        # Synthesize primary engines and pairing
        if u_detected:
            report.primary_linter = "Ultracite"
            report.primary_formatter = "Ultracite"
            report.autofix_command = "npx ultracite fix"
        elif b_detected:
            report.primary_linter = "Biome"
            report.primary_formatter = "Biome"
            report.autofix_command = "npx @biomejs/biome check --write"
            if es_detected or pr_detected:
                report.conflicts_or_warnings.append(
                    "Biome detected alongside ESLint/Prettier. Ensure responsibilities are decoupled or migrate fully to Biome."
                )
        elif ox_detected:
            report.primary_linter = "Oxlint"
            if pr_detected:
                report.primary_formatter = "Prettier"
                report.autofix_command = 'npx oxlint --fix && npx prettier --write "src/**/*.{ts,tsx}"'
            else:
                report.primary_formatter = "none"
                report.autofix_command = "npx oxlint --fix"
                report.conflicts_or_warnings.append(
                    "Oxlint does not format code or sort imports. Pair Oxlint with Prettier or Biome for formatting."
                )
        elif es_detected:
            report.primary_linter = "ESLint"
            if pr_detected:
                report.primary_formatter = "Prettier"
                report.autofix_command = 'npx eslint --fix && npx prettier --write "src/**/*.{ts,tsx}"'
                has_eslint_prettier = bool(self._has_dep("eslint-config-prettier"))
                if not has_eslint_prettier:
                    report.conflicts_or_warnings.append(
                        "ESLint and Prettier detected without 'eslint-config-prettier'. Conflicting rules may cause formatting churn."
                    )
            else:
                report.primary_formatter = "none"
                report.autofix_command = "npx eslint --fix"
        elif pr_detected:
            report.primary_linter = "none"
            report.primary_formatter = "Prettier"
            report.autofix_command = 'npx prettier --write "src/**/*.{ts,tsx}"'
        else:
            report.primary_linter = "none"
            report.primary_formatter = "none"
            report.autofix_command = "none"
            report.conflicts_or_warnings.append(
                "No linter or formatter configuration detected. Recommend installing Biome or ESLint + Prettier."
            )

        return report

    def _find_first(self, candidates: list[str]) -> str | None:
        for c in candidates:
            if (self.target_dir / c).is_file():
                return c
        return None


# =============================================================================
# 3. TypeScript Config Health
# =============================================================================

@dataclass
class FlagStatus:
    """Evaluation of an individual tsconfig compiler option."""

    flag: str
    enabled: bool
    importance: Literal["Critical", "High", "Recommended", "Optional"]
    current_value: Any
    description: str
    remediation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TsConfigReport:
    """Comprehensive TypeScript compiler configuration audit."""

    config_path: str | None = None
    status: HealthStatus = "PASS"
    score_percentage: int = 100
    extends: str | None = None
    flags: list[FlagStatus] = field(default_factory=list)
    missing_flags: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["flags"] = [f.to_dict() for f in self.flags]
        return data


class TsConfigAuditor:
    """Audits tsconfig.json for strictness, isolatedDeclarations, and indexing safety."""

    def __init__(self, target_dir: Path) -> None:
        self.target_dir = target_dir.resolve()

    def _find_workspace_tsconfigs(self) -> list[Path]:
        """Find per-package tsconfigs one or two levels down (monorepo layout)."""
        found: list[Path] = []
        for pattern in ("*/tsconfig.json", "*/*/tsconfig.json"):
            for path in sorted(self.target_dir.glob(pattern)):
                if "node_modules" in path.parts or ".git" in path.parts:
                    continue
                found.append(path)
        return found

    def _resolve_compiler_options(
        self, ts_file: Path, config: dict, _depth: int = 0
    ) -> tuple[dict, list[str]]:
        """Merge compilerOptions along the `extends` chain, base-first.

        A config that inherits `strict` from a shared base declares nothing itself.
        Reading only the leaf reports every inherited flag as unset, so a correctly
        configured repo scores 0%. Walk the chain instead, and say so when a link
        cannot be resolved rather than silently treating it as absent.
        """
        notes: list[str] = []
        parent_spec = config.get("extends")
        merged: dict = {}

        if parent_spec and _depth < 8:
            # A list-valued `extends` applies left to right; later entries win.
            specs = parent_spec if isinstance(parent_spec, list) else [parent_spec]
            for spec in specs:
                if not isinstance(spec, str):
                    continue
                if spec.startswith("."):
                    parent_path = (ts_file.parent / spec).resolve()
                    if parent_path.is_dir():
                        parent_path = parent_path / "tsconfig.json"
                    if not parent_path.suffix:
                        parent_path = parent_path.with_suffix(".json")
                    if not parent_path.is_file():
                        notes.append(
                            f"`extends` target '{spec}' does not exist relative to "
                            f"{ts_file.name}; inherited flags could not be checked."
                        )
                        continue
                    try:
                        parent_config = parse_jsonc(
                            parent_path.read_text(encoding="utf-8", errors="ignore")
                        )
                    except Exception as e:  # noqa: BLE001 - report, do not crash the audit
                        notes.append(f"Failed to parse `extends` target '{spec}': {e}")
                        continue
                    parent_options, parent_notes = self._resolve_compiler_options(
                        parent_path, parent_config, _depth + 1
                    )
                    merged.update(parent_options)
                    notes.extend(parent_notes)
                else:
                    # Package-name base (e.g. "@tsconfig/strictest"). Resolving it
                    # means walking node_modules; report instead of guessing.
                    notes.append(
                        f"`extends` resolves to package '{spec}'; flags it sets are "
                        "not counted in this score."
                    )

        merged.update(config.get("compilerOptions", {}) or {})
        return merged, notes

    def audit(self) -> TsConfigReport:
        report = TsConfigReport()
        ts_file = self.target_dir / "tsconfig.json"

        if not ts_file.is_file():
            # A monorepo commonly has no root tsconfig; each package owns its own.
            # Auditing only the root would score a healthy repo 0%, so fall back to
            # the highest-signal package config and say which one was used.
            workspace_configs = self._find_workspace_tsconfigs()
            if not workspace_configs:
                report.status = "FAIL"
                report.score_percentage = 0
                report.recommendations.append("No tsconfig.json found at project root.")
                return report

            ts_file = workspace_configs[0]
            report.recommendations.append(
                f"No root tsconfig.json; audited {ts_file.relative_to(self.target_dir)} "
                f"as representative of {len(workspace_configs)} workspace configs. "
                "Per-package settings may differ -- audit each package before relying on this score."
            )

        report.config_path = str(ts_file.relative_to(self.target_dir))

        try:
            raw_text = ts_file.read_text(encoding="utf-8", errors="ignore")
            config = parse_jsonc(raw_text)
        except Exception as e:
            report.status = "FAIL"
            report.score_percentage = 20
            report.recommendations.append(f"Failed to parse tsconfig.json: {e}")
            return report

        report.extends = config.get("extends")
        options, extends_notes = self._resolve_compiler_options(ts_file, config)
        report.recommendations.extend(extends_notes)

        strict_val = options.get("strict")
        strict_bool = bool(strict_val is True)
        iso_val = options.get("isolatedDeclarations")
        iso_bool = bool(iso_val is True)
        unchecked_val = options.get("noUncheckedIndexedAccess")
        unchecked_bool = bool(unchecked_val is True)
        skip_lib_val = options.get("skipLibCheck")
        skip_lib_bool = bool(skip_lib_val is True)
        decl_val = options.get("declaration")
        decl_bool = bool(decl_val is True or options.get("emitDeclarationOnly") is True)
        exact_val = options.get("exactOptionalPropertyTypes")
        exact_bool = bool(exact_val is True)

        report.flags.append(
            FlagStatus(
                flag="strict",
                enabled=strict_bool,
                importance="Critical",
                current_value=strict_val,
                description="Enables wide family of strict type-checking behaviors.",
                remediation="Enforced: strict mode active." if strict_bool else 'Add "strict": true to compilerOptions.',
            )
        )

        report.flags.append(
            FlagStatus(
                flag="isolatedDeclarations",
                enabled=iso_bool,
                importance="High",
                current_value=iso_val,
                description="Guarantees safe, fast .d.ts emit without compiler crashes (TS 5.5+).",
                remediation="Enforced: safe declaration emit active." if iso_bool else 'Add "isolatedDeclarations": true to compilerOptions.',
            )
        )

        report.flags.append(
            FlagStatus(
                flag="noUncheckedIndexedAccess",
                enabled=unchecked_bool,
                importance="High",
                current_value=unchecked_val,
                description="Adds undefined to record/array indexing lookups to prevent runtime crashes.",
                remediation="Enforced: safe dictionary/array indexing." if unchecked_bool else 'Add "noUncheckedIndexedAccess": true to compilerOptions.',
            )
        )

        report.flags.append(
            FlagStatus(
                flag="skipLibCheck",
                enabled=skip_lib_bool,
                importance="Recommended",
                current_value=skip_lib_val,
                description="Skips type checking of declaration files for faster compilation.",
                remediation="Enforced: fast declaration file skipping." if skip_lib_bool else 'Add "skipLibCheck": true to compilerOptions.',
            )
        )

        report.flags.append(
            FlagStatus(
                flag="exactOptionalPropertyTypes",
                enabled=exact_bool,
                importance="Optional",
                current_value=exact_val,
                description="Differentiates missing property keys from explicit undefined values.",
                remediation="Enforced: exact optional properties active." if exact_bool else 'Consider adding "exactOptionalPropertyTypes": true for strict schema safety.',
            )
        )

        # Calculate Score
        score = 0
        if strict_bool:
            score += 40
        else:
            report.missing_flags.append("strict")
            report.recommendations.append("Critical: Enable '\"strict\": true' in tsconfig.json.")

        if iso_bool:
            score += 25
        else:
            report.missing_flags.append("isolatedDeclarations")
            report.recommendations.append(
                "Recommended: Enable '\"isolatedDeclarations\": true' to prevent declaration emit crashes during cleanup."
            )

        if unchecked_bool:
            score += 25
        else:
            report.missing_flags.append("noUncheckedIndexedAccess")
            report.recommendations.append(
                "Recommended: Enable '\"noUncheckedIndexedAccess\": true' to prevent indexing bugs on dictionaries and arrays."
            )

        if skip_lib_bool:
            score += 10
        else:
            report.missing_flags.append("skipLibCheck")

        report.score_percentage = score

        if score >= 80:
            report.status = "PASS"
        elif score >= 50:
            report.status = "WARN"
        else:
            report.status = "FAIL"

        return report


# =============================================================================
# 4. Circular Dependency Risk
# =============================================================================

@dataclass
class CircularCycle:
    """Detected circular dependency chain."""

    id: str
    length: int
    risk: Severity
    is_barrel_cycle: bool
    chain: list[str]
    action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CircularDependencyScanner:
    """Scans repository imports for dependency cycles, leveraging madge if present."""

    def __init__(self, target_dir: Path) -> None:
        self.target_dir = target_dir.resolve()
        self.cycles: list[CircularCycle] = []
        self._cycle_count = 0
        self.tool_used = "built-in"

    def scan(self) -> list[CircularCycle]:
        self.cycles = []
        self._cycle_count = 0

        # 1. Attempt madge if installed
        madge_bin = self._find_madge()
        if madge_bin:
            madge_cycles = self._run_madge(madge_bin)
            if madge_cycles is not None:
                self.tool_used = "madge"
                self._process_raw_cycles(madge_cycles)
                return self.cycles

        # 2. Built-in Graph Scanner fallback
        self.tool_used = "built-in"
        graph = self._build_import_graph()
        sccs = self._tarjan_scc(graph)
        raw_cycles: list[list[str]] = []
        for scc in sccs:
            raw_cycles.extend(self._extract_cycles_from_scc(scc, graph))

        self._process_raw_cycles(raw_cycles)
        return self.cycles

    def _find_madge(self) -> str | None:
        local_bin = self.target_dir / "node_modules" / ".bin" / "madge"
        if local_bin.is_file() and os.access(local_bin, os.X_OK):
            return str(local_bin)
        system_bin = shutil.which("madge")
        if system_bin:
            return system_bin
        return None

    def _run_madge(self, madge_bin: str) -> list[list[str]] | None:
        cmd = [madge_bin, "--circular", "--json", "--extensions", "ts,tsx,js,jsx", "."]
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.target_dir,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if proc.stdout.strip():
                data = json.loads(proc.stdout)
                if isinstance(data, list):
                    return [c for c in data if isinstance(c, list)]
                if isinstance(data, dict):
                    return list(data.values())
        except Exception:
            pass
        return None

    def _build_import_graph(self) -> dict[str, set[str]]:
        graph: dict[str, set[str]] = {}
        paths_map = self._load_tsconfig_paths()

        re_import = re.compile(
            r"""(?:import|export)\s+(?:(?:(?:\*\s+as\s+\w+)|(?:\{[^}]*\})|(?:\w+))\s+from\s+)?['"]([^'"]+)['"]|import\(['"]([^'"]+)['"]\)|require\(['"]([^'"]+)['"]\)"""
        )

        for root, dirs, filenames in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for filename in filenames:
                f_path = Path(root) / filename
                if f_path.suffix in SOURCE_EXTENSIONS and not filename.endswith(".d.ts"):
                    rel_src = f_path.relative_to(self.target_dir).as_posix()
                    if rel_src not in graph:
                        graph[rel_src] = set()

                    try:
                        content = f_path.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue

                    for m in re_import.finditer(content):
                        spec = m.group(1) or m.group(2) or m.group(3)
                        if not spec:
                            continue
                        target_file = self._resolve_specifier(spec, f_path, paths_map)
                        if target_file and target_file != f_path:
                            try:
                                rel_target = target_file.relative_to(self.target_dir).as_posix()
                                graph[rel_src].add(rel_target)
                            except ValueError:
                                pass

        return graph

    def _load_tsconfig_paths(self) -> dict[str, list[str]]:
        ts_file = self.target_dir / "tsconfig.json"
        if ts_file.is_file():
            try:
                config = parse_jsonc(ts_file.read_text(encoding="utf-8", errors="ignore"))
                return config.get("compilerOptions", {}).get("paths", {})
            except Exception:
                pass
        return {}

    def _resolve_specifier(
        self, specifier: str, current_file: Path, paths_map: dict[str, list[str]]
    ) -> Path | None:
        extensions = [".ts", ".tsx", ".d.ts", ".js", ".jsx", ".mjs", ".cjs"]
        index_files = [f"index{ext}" for ext in extensions]

        candidate: Path | None = None
        if specifier.startswith("."):
            candidate = (current_file.parent / specifier).resolve()
        elif paths_map:
            for pattern, targets in paths_map.items():
                if pattern.endswith("/*") and specifier.startswith(pattern[:-2] + "/"):
                    suffix = specifier[len(pattern[:-2]) + 1:]
                    for t in targets:
                        t_clean = t[:-2] if t.endswith("/*") else t
                        cand = (self.target_dir / t_clean / suffix).resolve()
                        if cand.is_file():
                            return cand
                        for ext in extensions:
                            if cand.with_suffix(ext).is_file():
                                return cand.with_suffix(ext)
                        for idx in index_files:
                            if (cand / idx).is_file():
                                return cand / idx

        if candidate:
            if candidate.is_file():
                return candidate
            for ext in extensions:
                cand_ext = candidate.parent / (candidate.name + ext)
                if cand_ext.is_file():
                    return cand_ext
            if candidate.is_dir():
                for idx in index_files:
                    cand_idx = candidate / idx
                    if cand_idx.is_file():
                        return cand_idx
        return None

    def _tarjan_scc(self, graph: dict[str, set[str]]) -> list[list[str]]:
        index = 0
        indices: dict[str, int] = {}
        lowlink: dict[str, int] = {}
        stack: list[str] = []
        on_stack: set[str] = set()
        sccs: list[list[str]] = []

        def strongconnect(node: str) -> None:
            nonlocal index
            indices[node] = index
            lowlink[node] = index
            index += 1
            stack.append(node)
            on_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in indices:
                    strongconnect(neighbor)
                    lowlink[node] = min(lowlink[node], lowlink[neighbor])
                elif neighbor in on_stack:
                    lowlink[node] = min(lowlink[node], indices[neighbor])

            if lowlink[node] == indices[node]:
                scc: list[str] = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    scc.append(w)
                    if w == node:
                        break
                sccs.append(scc)

        for n in list(graph.keys()):
            if n not in indices:
                strongconnect(n)

        return [scc for scc in sccs if len(scc) > 1 or (len(scc) == 1 and scc[0] in graph.get(scc[0], set()))]

    def _extract_cycles_from_scc(
        self, scc_nodes: list[str], graph: dict[str, set[str]], max_cycles: int = 15
    ) -> list[list[str]]:
        node_set = set(scc_nodes)
        cycles: set[tuple[str, ...]] = set()

        for start_node in sorted(node_set):
            def dfs(current: str, path: tuple[str, ...], visited: set[str]) -> None:
                if len(cycles) >= max_cycles:
                    return
                for neighbor in sorted(graph.get(current, set()) & node_set):
                    if neighbor == start_node and len(path) >= 2:
                        cycle = list(path)
                        min_idx = cycle.index(min(cycle))
                        canon = tuple(cycle[min_idx:] + cycle[:min_idx])
                        cycles.add(canon)
                    elif neighbor not in visited and neighbor > start_node:
                        dfs(neighbor, path + (neighbor,), visited | {neighbor})

            dfs(start_node, (start_node,), {start_node})

        return [list(c) for c in sorted(cycles)]

    def _process_raw_cycles(self, raw_cycles: list[list[str]]) -> None:
        seen: set[tuple[str, ...]] = set()
        for c in raw_cycles:
            if not c or len(c) < 2:
                continue
            min_idx = c.index(min(c))
            canon = tuple(c[min_idx:] + c[:min_idx])
            if canon in seen:
                continue
            seen.add(canon)

            self._cycle_count += 1
            cycle_id = f"CIRC-{self._cycle_count:03d}"
            has_barrel = any(BARREL_FILENAME_REGEX.search(f) for f in c)
            risk: Severity = "High" if has_barrel else "Medium"
            chain_str = c + [c[0]]

            if has_barrel:
                action = "Decouple barrel re-exports; import directly from constituent source modules."
            else:
                action = "Extract shared dependencies into a leaf module or invert dependency via interface."

            self.cycles.append(
                CircularCycle(
                    id=cycle_id,
                    length=len(c),
                    risk=risk,
                    is_barrel_cycle=has_barrel,
                    chain=chain_str,
                    action=action,
                )
            )


# =============================================================================
# 5. Report Emitter (Markdown & JSON)
# =============================================================================

class AuditReporter:
    """Renders structured Markdown and JSON reports from audit results."""

    def __init__(
        self,
        target_dir: Path,
        slop_findings: list[SlopFinding],
        linter_report: LinterFormatterReport,
        tsconfig_report: TsConfigReport,
        circular_cycles: list[CircularCycle],
        circular_tool: str,
        enabled_checks: set[str],
    ) -> None:
        self.target_dir = target_dir
        self.slop_findings = slop_findings
        self.linter_report = linter_report
        self.tsconfig_report = tsconfig_report
        self.circular_cycles = circular_cycles
        self.circular_tool = circular_tool
        self.enabled_checks = enabled_checks

    def generate_json(self) -> str:
        high_slop = sum(1 for f in self.slop_findings if f.risk == "High")
        barrel_cycles = sum(1 for c in self.circular_cycles if c.is_barrel_cycle)

        overall_status = "PASS"
        if self.tsconfig_report.status == "FAIL" or high_slop > 5 or barrel_cycles > 0:
            overall_status = "FAIL"
        elif self.tsconfig_report.status == "WARN" or self.slop_findings or self.circular_cycles:
            overall_status = "WARN"

        payload = {
            "target": str(self.target_dir),
            "summary": {
                "overall_status": overall_status,
                "tsconfig_status": self.tsconfig_report.status,
                "tsconfig_score": f"{self.tsconfig_report.score_percentage}%",
                "linters_detected": [t.name for t in self.linter_report.tools if t.detected],
                "primary_linter": self.linter_report.primary_linter,
                "primary_formatter": self.linter_report.primary_formatter,
                "slop_issues_count": len(self.slop_findings),
                "circular_cycles_count": len(self.circular_cycles),
            },
            "enabled_checks": sorted(self.enabled_checks),
            "typescript_health": self.tsconfig_report.to_dict() if "tsconfig" in self.enabled_checks else None,
            "linters_formatters": self.linter_report.to_dict() if "linters" in self.enabled_checks else None,
            "slop_markers": {
                "total_count": len(self.slop_findings),
                "findings": [f.to_dict() for f in self.slop_findings],
            } if "slop" in self.enabled_checks else None,
            "circular_dependencies": {
                "tool": self.circular_tool,
                "total_cycles": len(self.circular_cycles),
                "cycles": [c.to_dict() for c in self.circular_cycles],
            } if "circular" in self.enabled_checks else None,
            "actionable_recommendations": self._build_recommendations(),
        }

        return json.dumps(payload, indent=2) + "\n"

    def generate_markdown(self) -> str:
        lines: list[str] = [
            "# TypeScript Codebase Health Audit Report",
            "",
            f"> Target: `{self.target_dir}`  ",
            f"> Analysis Engines: Standalone Python 3 AST & Graph Auditor (Circular Tool: {self.circular_tool})",
            "",
            "## 1. Executive Summary",
            "",
            "| Audit Category | Status | Details / Metrics | Risk |",
            "| :--- | :---: | :--- | :---: |",
        ]

        # Row 1: tsconfig
        if "tsconfig" in self.enabled_checks:
            ts_stat = f"**{self.tsconfig_report.status}** ({self.tsconfig_report.score_percentage}%)"
            ts_desc = f"strict: {self._flag_str('strict')}, isolatedDecl: {self._flag_str('isolatedDeclarations')}, noUncheckedIndex: {self._flag_str('noUncheckedIndexedAccess')}"
            ts_risk = "Low" if self.tsconfig_report.status == "PASS" else ("Medium" if self.tsconfig_report.status == "WARN" else "High")
            lines.append(f"| **TypeScript Configuration** | {ts_stat} | {ts_desc} | **{ts_risk}** |")

        # Row 2: linters
        if "linters" in self.enabled_checks:
            detected_names = [t.name for t in self.linter_report.tools if t.detected]
            l_stat = "**PASS**" if detected_names else "**WARN**"
            l_desc = f"Linter: {self.linter_report.primary_linter} | Formatter: {self.linter_report.primary_formatter}"
            l_risk = "Low" if detected_names else "Medium"
            lines.append(f"| **Linter & Formatter Pairing** | {l_stat} | {l_desc} | **{l_risk}** |")

        # Row 3: slop
        if "slop" in self.enabled_checks:
            s_count = len(self.slop_findings)
            s_stat = "**PASS**" if s_count == 0 else ("**WARN**" if s_count < 10 else "**FAIL**")
            s_high = sum(1 for f in self.slop_findings if f.risk == "High")
            s_desc = f"{s_count} markers detected ({s_high} High risk)"
            s_risk = "High" if s_high > 0 else ("Medium" if s_count > 0 else "Low")
            lines.append(f"| **AI Slop Markers** | {s_stat} | {s_desc} | **{s_risk}** |")

        # Row 4: circular
        if "circular" in self.enabled_checks:
            c_count = len(self.circular_cycles)
            c_stat = "**PASS**" if c_count == 0 else "**WARN**"
            c_barrel = sum(1 for c in self.circular_cycles if c.is_barrel_cycle)
            c_desc = f"{c_count} cycles found ({c_barrel} barrel loops)"
            c_risk = "High" if c_barrel > 0 else ("Medium" if c_count > 0 else "Low")
            lines.append(f"| **Circular Dependencies** | {c_stat} | {c_desc} | **{c_risk}** |")

        lines.extend(["", "---", ""])

        # Section 2: TypeScript Config Health
        if "tsconfig" in self.enabled_checks:
            lines.extend([
                "## 2. TypeScript Configuration Health",
                "",
                f"Configuration file: `{self.tsconfig_report.config_path or 'Not Found'}`  ",
                f"Health Score: **{self.tsconfig_report.score_percentage}%** ({self.tsconfig_report.status})  ",
                f"Extends: `{self.tsconfig_report.extends or 'None'}`",
                "",
                "| Compiler Flag | Enabled | Importance | Current Value | Guidance |",
                "| :--- | :---: | :---: | :---: | :--- |",
            ])
            for f in self.tsconfig_report.flags:
                en_str = "YES" if f.enabled else "NO"
                val_repr = "true" if f.current_value is True else ("false" if f.current_value is False else (f'"{f.current_value}"' if isinstance(f.current_value, str) else ("undefined" if f.current_value is None else str(f.current_value))))
                lines.append(
                    f"| `{f.flag}` | **{en_str}** | {f.importance} | `{val_repr}` | {f.remediation} |"
                )
            lines.extend(["", "---", ""])

        # Section 3: Linters & Formatters
        if "linters" in self.enabled_checks:
            lines.extend([
                "## 3. Linter & Formatter Detection",
                "",
                f"**Primary Linter**: `{self.linter_report.primary_linter}`  ",
                f"**Primary Formatter**: `{self.linter_report.primary_formatter}`  ",
                f"**Recommended Autofix**: `{self.linter_report.autofix_command}`",
                "",
                "| Engine | Detected | Config File | Manifest Marker | Recommended Autofix |",
                "| :--- | :---: | :--- | :--- | :--- |",
            ])
            for t in self.linter_report.tools:
                det = "YES" if t.detected else "NO"
                cfg = f"`{t.config_file}`" if t.config_file else "None"
                dep = f"`{t.manifest_dependency}`" if t.manifest_dependency else "None"
                cmd = f"`{t.autofix_command}`" if t.autofix_command else "None"
                lines.append(f"| **{t.name}** | **{det}** | {cfg} | {dep} | {cmd} |")

            if self.linter_report.conflicts_or_warnings:
                lines.extend(["", "### Pairing & Conflict Warnings"])
                for w in self.linter_report.conflicts_or_warnings:
                    lines.append(f"- ⚠️ {w}")

            lines.extend(["", "---", ""])

        # Section 4: AI Slop Markers
        if "slop" in self.enabled_checks:
            lines.extend([
                f"## 4. AI Slop Markers ({len(self.slop_findings)} findings)",
                "",
                "Scans for useless try/catch passthrough re-throws, duplicate utilities, and verbose boolean theater.",
                "",
            ])
            if not self.slop_findings:
                lines.append("No AI slop markers detected. Codebase hygiene is clean.\n")
            else:
                lines.extend([
                    "| ID | Category | Rule | Location | Risk | Snippet | Action |",
                    "| :--- | :--- | :--- | :--- | :---: | :--- | :--- |",
                ])
                for f in self.slop_findings:
                    safe_snip = f.snippet.replace("|", "\\|")
                    safe_act = f.action.replace("|", "\\|")
                    lines.append(
                        f"| `{f.id}` | {f.category} | `{f.rule}` | `{f.file}:{f.line}` | **{f.risk}** | `{safe_snip}` | {safe_act} |"
                    )
                lines.append("")

            lines.extend(["---", ""])

        # Section 5: Circular Dependency Risk
        if "circular" in self.enabled_checks:
            lines.extend([
                f"## 5. Circular Dependency Risk Analysis ({len(self.circular_cycles)} cycles)",
                "",
                f"Scanner tool: `{self.circular_tool}`. Cycle length >= 2 modules.",
                "",
            ])
            if not self.circular_cycles:
                lines.append("No circular dependency cycles detected across the import graph.\n")
            else:
                lines.extend([
                    "| ID | Length | Barrel Loop? | Risk | Dependency Chain | Remediation Recommendation |",
                    "| :--- | :---: | :---: | :---: | :--- | :--- |",
                ])
                for c in self.circular_cycles:
                    barrel_str = "YES" if c.is_barrel_cycle else "NO"
                    chain_repr = " -> ".join(f"`{Path(p).name}`" for p in c.chain)
                    safe_act = c.action.replace("|", "\\|")
                    lines.append(
                        f"| `{c.id}` | {c.length} | **{barrel_str}** | **{c.risk}** | {chain_repr} | {safe_act} |"
                    )
                lines.append("")

            lines.extend(["---", ""])

        # Section 6: Actionable Recommendations
        lines.extend([
            "## 6. Actionable Recommendations for Agent & Developer",
            "",
        ])
        recommendations = self._build_recommendations()
        if recommendations:
            for idx, rec in enumerate(recommendations, 1):
                lines.append(f"{idx}. {rec}")
        else:
            lines.append("Codebase satisfies all TypeScript strictness, linting, and slop-free standards.")

        lines.append("")
        return "\n".join(lines)

    def _flag_str(self, flag_name: str) -> str:
        for f in self.tsconfig_report.flags:
            if f.flag == flag_name:
                return "true" if f.enabled else "false"
        return "not-set"

    def _build_recommendations(self) -> list[str]:
        recs: list[str] = []

        # Circular dependencies first
        barrel_cycles = [c for c in self.circular_cycles if c.is_barrel_cycle]
        if barrel_cycles:
            recs.append(
                f"**Break Barrel Loops**: Decouple {len(barrel_cycles)} barrel index file cycles to eliminate import loops."
            )
        elif self.circular_cycles:
            recs.append(
                f"**Resolve Circular Imports**: Refactor {len(self.circular_cycles)} module cycles into leaf modules."
            )

        # AI Slop
        rethrow_count = sum(1 for f in self.slop_findings if f.rule == "passthrough-rethrow")
        if rethrow_count > 0:
            recs.append(
                f"**Prune Passthrough Re-throws**: Eliminate {rethrow_count} useless try/catch rethrow blocks."
            )

        dupe_utils = {f.rule for f in self.slop_findings if f.category == "Utility Duplication"}
        if dupe_utils:
            recs.append(
                f"**Consolidate Utilities**: Merge duplicate helpers ({len(dupe_utils)} utilities) into canonical modules (e.g. `src/lib/utils.ts`)."
            )

        # tsconfig
        for r in self.tsconfig_report.recommendations:
            recs.append(f"**TypeScript Config**: {r}")

        # Post-wave linter autofix
        if self.linter_report.autofix_command and self.linter_report.autofix_command != "none":
            recs.append(
                f"**Post-Wave Linter Bridge**: Run `{self.linter_report.autofix_command}` after Wave 4 to strip dangling imports."
            )

        return recs


# =============================================================================
# 6. CLI Entrypoint
# =============================================================================

def main() -> int:
    """CLI Entrypoint for audit-ts-health."""
    parser = argparse.ArgumentParser(
        description="Audit TypeScript codebase health: AI slop markers, linter configs, tsconfig health, and circular dependencies.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --target /path/to/repo
  %(prog)s --format json
  %(prog)s --check-slop --check-circular
  %(prog)s --check-linters --format markdown --out-file audit-report.md
        """,
    )
    parser.add_argument(
        "--target",
        type=str,
        default=".",
        help="Target project directory to audit (default: current directory).",
    )
    parser.add_argument(
        "--check-slop",
        action="store_true",
        help="Scan for AI slop markers (useless try/catch, duplicate utilities, boolean theater).",
    )
    parser.add_argument(
        "--check-circular",
        action="store_true",
        help="Scan for circular dependency risk via import graph or madge.",
    )
    parser.add_argument(
        "--check-linters",
        action="store_true",
        help="Detect and audit linter & formatter configurations (Biome, Oxlint, ESLint, Prettier, Ultracite).",
    )
    parser.add_argument(
        "--check-tsconfig",
        action="store_true",
        help="Audit tsconfig.json compilerOptions for strict mode, isolatedDeclarations, and indexing safety.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output report format (default: markdown).",
    )
    parser.add_argument(
        "--out-file",
        type=str,
        help="Path to write report to (default: stdout).",
    )

    args = parser.parse_args()
    target_dir = Path(args.target).resolve()

    if not target_dir.is_dir():
        print(f"Error: Target directory does not exist: {target_dir}", file=sys.stderr)
        return 1

    # Determine which check modules to run
    user_specified_checks = any([args.check_slop, args.check_circular, args.check_linters, args.check_tsconfig])
    enabled_checks: set[str] = set()

    if user_specified_checks:
        if args.check_slop:
            enabled_checks.add("slop")
        if args.check_circular:
            enabled_checks.add("circular")
        if args.check_linters:
            enabled_checks.add("linters")
        if args.check_tsconfig:
            enabled_checks.add("tsconfig")
    else:
        # Default: run all 4 health audits
        enabled_checks = {"slop", "circular", "linters", "tsconfig"}

    # 1. AI Slop Markers
    slop_findings: list[SlopFinding] = []
    if "slop" in enabled_checks:
        slop_detector = SlopDetector(target_dir)
        slop_findings = slop_detector.scan()

    # 2. Linters & Formatters
    linter_report = LinterFormatterReport()
    if "linters" in enabled_checks:
        linter_detector = LinterDetector(target_dir)
        linter_report = linter_detector.detect()

    # 3. TypeScript Config Health
    tsconfig_report = TsConfigReport()
    if "tsconfig" in enabled_checks:
        tsconfig_auditor = TsConfigAuditor(target_dir)
        tsconfig_report = tsconfig_auditor.audit()

    # 4. Circular Dependencies
    circular_cycles: list[CircularCycle] = []
    circular_tool = "built-in"
    if "circular" in enabled_checks:
        circular_scanner = CircularDependencyScanner(target_dir)
        circular_cycles = circular_scanner.scan()
        circular_tool = circular_scanner.tool_used

    # Generate Report
    reporter = AuditReporter(
        target_dir=target_dir,
        slop_findings=slop_findings,
        linter_report=linter_report,
        tsconfig_report=tsconfig_report,
        circular_cycles=circular_cycles,
        circular_tool=circular_tool,
        enabled_checks=enabled_checks,
    )

    output_content = reporter.generate_json() if args.format == "json" else reporter.generate_markdown()

    if args.out_file:
        out_path = Path(args.out_file).resolve()
        try:
            out_path.write_text(output_content, encoding="utf-8")
            print(f"Health audit written to: {out_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing report to '{out_path}': {e}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(output_content)

    return 0


if __name__ == "__main__":
    sys.exit(main())
