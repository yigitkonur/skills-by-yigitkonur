#!/usr/bin/env python3
"""Batch and prioritize dead-code findings into 6 contextual remediation batches.

Parses Knip JSON output (from file, stdin, or direct execution via `npx knip --reporter json`)
and groups findings into 6 dependency-ordered remediation batches:
    1: unused-dependencies (package manifests, lockfile stability)
    2: unreferenced-files (orphaned source files, abandoned pages/components)
    3: dead-barrel-exports (re-exports inside index/barrel files)
    4: test-only-exports (production symbols exposed solely for unit tests)
    5: internal-only-exports (exports consumed strictly in-file)
    6: unused-types (dead interfaces, type aliases, unreferenced enums)

Each batch carries the remediation wave it feeds. Batches 4 and 5 both feed Wave 4,
so the 6 batches collapse into 5 waves. Waves are the only ordering axis here; the
enclosing workflow's phases are numbered separately and are not referenced by this tool.

For each finding, calculates an operational risk score (Low, Medium, High)
and produces a clear, deterministic remediation recommendation.

Verification-gate commands are rendered for the package manager detected from the
project's lockfile, so the emitted plan is runnable as printed.

Outputs either a machine-readable structured JSON document or an executive
Markdown summary table suitable for documentation, PR descriptions, or CI summaries.

Usage:
    # Run Knip directly and print Markdown report
    python3 batch-findings.py --run

    # Parse an existing Knip JSON report file
    python3 batch-findings.py --input knip-report.json --output markdown

    # Pipe Knip output via stdin and emit structured JSON
    npx knip --reporter json | python3 batch-findings.py --input - --output json

    # Save Markdown summary to file
    python3 batch-findings.py --run --output markdown --out-file cleanup-plan.md

Exit codes:
    0  Successfully parsed and reported findings (even if findings exist)
    1  Invalid input, Knip execution failure, or filesystem error
    2  CLI syntax error
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

RiskLevel = Literal["Low", "Medium", "High"]

# Lockfile -> package manager. Ordered most specific first; the first lockfile
# present in the project root wins. npm is the fallback when nothing matches.
LOCKFILE_MANAGERS: tuple[tuple[str, str], ...] = (
    ("pnpm-lock.yaml", "pnpm"),
    ("bun.lockb", "bun"),
    ("bun.lock", "bun"),
    ("yarn.lock", "yarn"),
    ("package-lock.json", "npm"),
)

# Per-manager command fragments substituted into the verification gates below.
MANAGER_COMMANDS: dict[str, dict[str, str]] = {
    "npm": {"install": "npm ci", "test": "npm test", "build": "npm run build"},
    "pnpm": {
        "install": "pnpm install --frozen-lockfile",
        "test": "pnpm test",
        "build": "pnpm build",
    },
    "yarn": {
        "install": "yarn install --immutable",
        "test": "yarn test",
        "build": "yarn build",
    },
    "bun": {"install": "bun install --frozen-lockfile", "test": "bun test", "build": "bun run build"},
}


def detect_package_manager(root: Path) -> str:
    """Return the package manager implied by the lockfile in `root` (npm if none)."""
    for lockfile, manager in LOCKFILE_MANAGERS:
        if (root / lockfile).is_file():
            return manager
    return "npm"


def render_gate(template: str, manager: str) -> str:
    """Substitute {install}/{test}/{build} in a gate template for `manager`."""
    return template.format(**MANAGER_COMMANDS[manager])


# `wave` is the remediation wave each batch feeds. Batches 4 and 5 both feed
# Wave 4, so 6 batches collapse into 5 waves. Gates are templates -- render them
# through render_gate() with the detected manager before display.
BATCH_METADATA: dict[int, dict[str, str]] = {
    1: {
        "name": "unused-dependencies",
        "title": "Unused Dependencies & DevDependencies",
        "wave": "Wave 1",
        "description": "Packages declared in package.json with zero references or missing unlisted packages.",
        "verification_gate": "{install} && npx tsc --noEmit && {build}",
    },
    2: {
        "name": "unreferenced-files",
        "title": "Unreferenced & Orphaned Files",
        "wave": "Wave 2",
        "description": "Orphan files with no incoming import edges from any configured entry point.",
        "verification_gate": "npx tsc --noEmit && {test} && {build}",
    },
    3: {
        "name": "dead-barrel-exports",
        "title": "Dead Barrel Re-exports",
        "wave": "Wave 3",
        "description": "Re-exports in aggregator index files never consumed outside that barrel.",
        "verification_gate": "npx tsc --noEmit && {build}",
    },
    4: {
        "name": "test-only-exports",
        "title": "Test-Only Leaks",
        "wave": "Wave 4",
        "description": "Production symbols exported solely for unit test inspection.",
        "verification_gate": "{test} && npx tsc --noEmit",
    },
    5: {
        "name": "internal-only-exports",
        "title": "Internally-Only-Used Exports",
        "wave": "Wave 4",
        "description": "Symbols declared with export keyword but only referenced within the same file.",
        "verification_gate": "npx tsc --noEmit",
    },
    6: {
        "name": "unused-types",
        "title": "Unused Types, Interfaces & Enums",
        "wave": "Wave 5",
        "description": "Zero-runtime TypeScript declarations and enum variants with zero consumers.",
        "verification_gate": "npx tsc --noEmit",
    },
}

BARREL_FILENAME_REGEX = re.compile(
    r"(^|/)(index|api|public-api|exports|barrel)\.(ts|tsx|js|jsx|mjs|cjs)$",
    re.IGNORECASE,
)

TEST_PATH_REGEX = re.compile(
    r"(\.(test|spec|stories)\.[a-z0-9]+$)|(^|/)(__tests__|tests?|cypress|playwright|e2e|fixtures|mocks|test-utils)/",
    re.IGNORECASE,
)

ROUTE_PATH_REGEX = re.compile(
    r"(^|/)(app|pages|routes)/.*(page|layout|route|loading|error|not-found)\.[a-z0-9]+$",
    re.IGNORECASE,
)


@dataclass
class Finding:
    """Normalized individual dead code violation."""

    id: str
    batch: int
    batch_name: str
    rule: str
    file: str
    symbol: str
    line: int | None = None
    col: int | None = None
    risk_score: RiskLevel = "Low"
    risk_rationale: str = ""
    action: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert finding to serializable dictionary."""
        data = asdict(self)
        # Clean null values if desired
        if self.line is None:
            data.pop("line", None)
        if self.col is None:
            data.pop("col", None)
        return data


class KnipReportParser:
    """Parses arbitrary Knip JSON outputs and classifies findings into 6 batches."""

    def __init__(self, raw_data: Any, project_dir: Path | None = None) -> None:
        self.raw_data = raw_data
        self.project_dir = project_dir.resolve() if project_dir else Path.cwd()
        self.findings: list[Finding] = []
        self._finding_counter = 0

    def parse(self) -> list[Finding]:
        """Parse raw JSON structure and classify all issues."""
        self.findings = []
        self._finding_counter = 0

        # Handle Knip v5/v6 format: {"issues": [ ... ]}
        if isinstance(self.raw_data, dict) and "issues" in self.raw_data:
            # Handle root-level unreferenced files in v5/v6 format
            for f in self.raw_data.get("files", []):
                name = f.get("name", f) if isinstance(f, dict) else str(f)
                self._add_unreferenced_file(name)

            issues = self.raw_data.get("issues", [])
            if isinstance(issues, list):
                for issue_obj in issues:
                    if isinstance(issue_obj, dict):
                        self._parse_grouped_issue_object(issue_obj)

        # Handle Knip flat format: {"files": [...], "dependencies": {...}, "exports": {...}}
        elif isinstance(self.raw_data, dict):
            self._parse_flat_issue_dict(self.raw_data)

        # Handle list of issue objects: [ {"file": "...", ...} ]
        elif isinstance(self.raw_data, list):
            for item in self.raw_data:
                if isinstance(item, dict):
                    if "file" in item:
                        self._parse_grouped_issue_object(item)
                    else:
                        self._parse_flat_issue_dict(item)

        # Sort findings: Batch 1 to 6, then High -> Medium -> Low risk, then file path
        risk_order = {"High": 0, "Medium": 1, "Low": 2}
        self.findings.sort(key=lambda f: (f.batch, risk_order.get(f.risk_score, 3), f.file, f.line or 0))

        # Assign clean, sequenced IDs
        for idx, f in enumerate(self.findings, 1):
            f.id = f"KNP-{f.batch:02d}-{idx:04d}"

        return self.findings

    def _next_id(self) -> str:
        self._finding_counter += 1
        return f"TEMP-{self._finding_counter:04d}"

    def _parse_grouped_issue_object(self, issue_obj: dict[str, Any]) -> None:
        """Parse Knip v6 issue object containing file and grouped issue arrays."""
        file_path = str(issue_obj.get("file", "unknown"))

        # 1. files (Unreferenced files)
        for item in issue_obj.get("files", []):
            name = item.get("name", file_path) if isinstance(item, dict) else str(item)
            self._add_unreferenced_file(name)

        # 2. dependencies & devDependencies & unlisted & binaries & unresolved
        for dep in issue_obj.get("dependencies", []):
            self._add_dependency_finding(file_path, "dependencies", dep)

        for dev_dep in issue_obj.get("devDependencies", []):
            self._add_dependency_finding(file_path, "devDependencies", dev_dep)

        for unlisted in issue_obj.get("unlisted", []):
            self._add_dependency_finding(file_path, "unlisted", unlisted)

        for opt in issue_obj.get("optionalPeerDependencies", []):
            self._add_dependency_finding(file_path, "optionalPeerDependencies", opt)

        for binary in issue_obj.get("binaries", []):
            self._add_dependency_finding(file_path, "binaries", binary)

        for unresolved in issue_obj.get("unresolved", []):
            self._add_dependency_finding(file_path, "unresolved", unresolved)

        # 3. exports & duplicates & nsExports
        for exp in issue_obj.get("exports", []):
            self._classify_export(file_path, "exports", exp)

        for dup in (issue_obj.get("duplicates", []) + issue_obj.get("duplicateExports", [])):
            self._classify_export(file_path, "duplicateExports", dup)

        for ns in (issue_obj.get("namespaceMembers", []) + issue_obj.get("nsExports", [])):
            self._classify_export(file_path, "nsExports", ns)

        # 4. types & enumMembers & classMembers
        for typ in issue_obj.get("types", []):
            self._add_type_finding(file_path, "types", typ)

        for nst in issue_obj.get("nsTypes", []):
            self._add_type_finding(file_path, "nsTypes", nst)

        for enum_m in issue_obj.get("enumMembers", []):
            self._add_type_finding(file_path, "enumMembers", enum_m)

        for cls_m in issue_obj.get("classMembers", []):
            self._classify_export(file_path, "classMembers", cls_m)

    def _parse_flat_issue_dict(self, data: dict[str, Any]) -> None:
        """Parse flat Knip issue format where keys are rule names."""
        # files
        for f in data.get("files", []):
            name = f.get("name", f) if isinstance(f, dict) else str(f)
            self._add_unreferenced_file(name)

        # dependencies
        for rule in ("dependencies", "devDependencies", "unlisted", "optionalPeerDependencies", "binaries", "unresolved"):
            entries = data.get(rule, {})
            if isinstance(entries, dict):
                for file_path, items in entries.items():
                    if isinstance(items, list):
                        for it in items:
                            self._add_dependency_finding(file_path, rule, it)
            elif isinstance(entries, list):
                for it in entries:
                    self._add_dependency_finding("package.json", rule, it)

        # exports
        for rule in ("exports", "nsExports", "duplicateExports", "duplicates", "namespaceMembers", "classMembers"):
            entries = data.get(rule, {})
            norm_rule = "duplicateExports" if rule == "duplicates" else ("nsExports" if rule == "namespaceMembers" else rule)
            if isinstance(entries, dict):
                for file_path, items in entries.items():
                    if isinstance(items, list):
                        for it in items:
                            self._classify_export(file_path, norm_rule, it)

        # types
        for rule in ("types", "nsTypes", "enumMembers"):
            entries = data.get(rule, {})
            if isinstance(entries, dict):
                for file_path, items in entries.items():
                    if isinstance(items, list):
                        for it in items:
                            self._add_type_finding(file_path, rule, it)

    # -------------------------------------------------------------------------
    # Batch 1: Unused Dependencies
    # -------------------------------------------------------------------------
    def _add_dependency_finding(self, file_path: str, rule: str, item: Any) -> None:
        name, line, col = self._extract_symbol_and_location(item)

        if rule == "unlisted":
            risk: RiskLevel = "High"
            rationale = "Unlisted dependency imported in source; risks build failure or runtime crash."
            action = f"Add missing package to package.json: npm i {name} (or pnpm add {name})"
        elif rule == "unresolved":
            risk = "High"
            rationale = "Unresolvable module specifier; broken import path."
            action = f"Fix broken import specifier or install missing dependency: {name}"
        elif rule == "dependencies":
            risk = "Medium"
            rationale = "Production dependency removal; verify no dynamic imports or runtime reflection before deletion."
            action = f"Verify no string/dynamic usage, then uninstall: npm rm {name} (or pnpm remove {name})"
        elif rule == "binaries":
            risk = "Medium"
            rationale = "CLI tool executed in package scripts but missing from dependencies."
            action = f"Add {name} to devDependencies or declare in ignoreBinaries in knip.jsonc"
        elif rule == "devDependencies":
            risk = "Low"
            rationale = "Developer tool unused in build/test scripts; safe to prune."
            action = f"Verify no script references, then uninstall: npm rm -D {name} (or pnpm remove -D {name})"
        else:
            risk = "Low"
            rationale = "Optional or peer dependency unused across repository."
            action = f"Review and prune unused optional dependency: {name}"

        self.findings.append(
            Finding(
                id=self._next_id(),
                batch=1,
                batch_name="unused-dependencies",
                rule=rule,
                file=file_path,
                symbol=name,
                line=line,
                col=col,
                risk_score=risk,
                risk_rationale=rationale,
                action=action,
            )
        )

    # -------------------------------------------------------------------------
    # Batch 2: Unreferenced Files
    # -------------------------------------------------------------------------
    def _add_unreferenced_file(self, file_path: str) -> None:
        clean_path = file_path.replace("\\", "/")

        if ROUTE_PATH_REGEX.search(clean_path):
            risk: RiskLevel = "High"
            rationale = "Potential framework route or special convention entry point. Verify router configuration."
            action = f"Verify framework routing convention before deletion, or remove: git rm {file_path}"
        elif TEST_PATH_REGEX.search(clean_path):
            risk = "Low"
            rationale = "Orphaned test suite, mock fixture, or Storybook story. Minimal runtime blast radius."
            action = f"Confirm test/story is obsolete, then remove: git rm {file_path}"
        else:
            risk = "Medium"
            rationale = "Unreferenced source module. Check for dynamic imports or string asset references before deleting."
            action = f"Verify against dynamic imports, then remove: git rm {file_path}"

        self.findings.append(
            Finding(
                id=self._next_id(),
                batch=2,
                batch_name="unreferenced-files",
                rule="files",
                file=file_path,
                symbol=Path(file_path).name,
                line=1,
                col=1,
                risk_score=risk,
                risk_rationale=rationale,
                action=action,
            )
        )

    # -------------------------------------------------------------------------
    # Batches 3, 4, 5: Exports (Barrel vs Test-Only vs Internal-Only)
    # -------------------------------------------------------------------------
    def _classify_export(self, file_path: str, rule: str, item: Any) -> None:
        name, line, col = self._extract_symbol_and_location(item)
        clean_path = file_path.replace("\\", "/")

        # Check Barrel (Batch 3)
        if rule in ("nsExports", "duplicateExports") or self._is_barrel_file(clean_path):
            self._add_barrel_finding(file_path, rule, name, line, col)
            return

        # Check Test-Only Leak (Batch 4)
        if self._is_test_only_export(clean_path, name):
            self._add_test_leak_finding(file_path, rule, name, line, col)
            return

        # Default: Internally-Only-Used Export (Batch 5)
        self._add_internal_export_finding(file_path, rule, name, line, col)

    def _is_barrel_file(self, clean_path: str) -> bool:
        """Determine if a file acts as a module aggregator / barrel."""
        if BARREL_FILENAME_REGEX.search(clean_path):
            return True

        # Check file content on disk if accessible
        disk_path = self.project_dir / clean_path
        if disk_path.is_file():
            try:
                content = disk_path.read_text(encoding="utf-8", errors="ignore")
                # High ratio of re-exports indicates barrel file
                has_reexports = "export * from" in content or re.search(r"export\s*\{[^}]*\}\s*from", content)
                if has_reexports:
                    return True
            except Exception:
                pass
        return False

    def _is_test_only_export(self, clean_path: str, symbol: str) -> bool:
        """Determine if a symbol is exported strictly for test consumption."""
        # If the file itself is a test utility / fixture
        if TEST_PATH_REGEX.search(clean_path):
            return True

        # If project files can be inspected on disk, search for symbol references
        disk_path = self.project_dir / clean_path
        if disk_path.is_file() and symbol and symbol != "default":
            test_references = 0
            prod_references = 0
            try:
                # Use git grep or ripgrep if available, or quick python search across source files
                for p in self.project_dir.rglob("*"):
                    if not p.is_file():
                        continue
                    if any(part in p.parts for part in ("node_modules", ".git", "dist", "build", ".next", ".turbo")):
                        continue
                    if p.suffix not in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
                        continue
                    if p.resolve() == disk_path.resolve():
                        continue

                    p_str = p.as_posix()
                    file_text = p.read_text(encoding="utf-8", errors="ignore")
                    if symbol in file_text:
                        if TEST_PATH_REGEX.search(p_str):
                            test_references += 1
                        else:
                            prod_references += 1
                            break  # Found prod reference; not a test-only export

                if test_references > 0 and prod_references == 0:
                    return True
            except Exception:
                pass

        return False

    def _add_barrel_finding(self, file_path: str, rule: str, symbol: str, line: int | None, col: int | None) -> None:
        self.findings.append(
            Finding(
                id=self._next_id(),
                batch=3,
                batch_name="dead-barrel-exports",
                rule=rule,
                file=file_path,
                symbol=symbol,
                line=line,
                col=col,
                risk_score="Low",
                risk_rationale="Dead barrel re-export; pruning breaks circular dependency loops with low blast radius.",
                action=f"Remove re-export '{symbol}' from barrel file {file_path}, or convert wildcard 'export *' to explicit named exports",
            )
        )

    def _add_test_leak_finding(self, file_path: str, rule: str, symbol: str, line: int | None, col: int | None) -> None:
        self.findings.append(
            Finding(
                id=self._next_id(),
                batch=4,
                batch_name="test-only-exports",
                rule=rule,
                file=file_path,
                symbol=symbol,
                line=line,
                col=col,
                risk_score="Medium",
                risk_rationale="Production symbol exposed solely for test inspection. Encapsulation leak.",
                action=f"Refactor tests to consume public API, move helper into test harness, or annotate with /** @internal */: {symbol}",
            )
        )

    def _add_internal_export_finding(self, file_path: str, rule: str, symbol: str, line: int | None, col: int | None) -> None:
        self.findings.append(
            Finding(
                id=self._next_id(),
                batch=5,
                batch_name="internal-only-exports",
                rule=rule,
                file=file_path,
                symbol=symbol,
                line=line,
                col=col,
                risk_score="Low",
                risk_rationale="Module export unused externally. Stripping 'export' keyword makes symbol private with zero runtime blast radius.",
                action=f"Remove 'export' keyword from declaration of '{symbol}' in {file_path}",
            )
        )

    # -------------------------------------------------------------------------
    # Batch 6: Unused Types, Interfaces & Enums
    # -------------------------------------------------------------------------
    def _add_type_finding(self, file_path: str, rule: str, item: Any) -> None:
        name, line, col = self._extract_symbol_and_location(item)

        if rule == "enumMembers":
            action = f"Remove unreferenced enum member '{name}' in {file_path}"
            rationale = "Unreferenced enum variant. Safe to remove; zero runtime blast radius."
        else:
            action = f"Delete unused type or interface definition '{name}' in {file_path}"
            rationale = "TypeScript type/interface erased at compile time. Pure maintenance hygiene; zero runtime impact."

        self.findings.append(
            Finding(
                id=self._next_id(),
                batch=6,
                batch_name="unused-types",
                rule=rule,
                file=file_path,
                symbol=name,
                line=line,
                col=col,
                risk_score="Low",
                risk_rationale=rationale,
                action=action,
            )
        )

    @staticmethod
    def _extract_symbol_and_location(item: Any) -> tuple[str, int | None, int | None]:
        """Extract symbol name, line, and column from heterogeneous Knip issue items."""
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("symbol") or item.get("identifier") or "unknown")
            line = item.get("line")
            col = item.get("col") or item.get("column")
            return name, (int(line) if line is not None else None), (int(col) if col is not None else None)
        return str(item), None, None


def parse_batch_filter(batch_arg: str) -> set[int]:
    """Parse batch filter specification such as '1', '1,2', '1-3', or 'all'."""
    batch_arg = batch_arg.strip().lower()
    if batch_arg in ("all", "*"):
        return set(range(1, 7))
    selected: set[int] = set()
    parts = [p.strip() for p in batch_arg.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            try:
                start_str, end_str = part.split("-", 1)
                start, end = int(start_str), int(end_str)
                selected.update(range(start, end + 1))
            except ValueError:
                pass
        else:
            try:
                selected.add(int(part))
            except ValueError:
                pass
    valid = {b for b in selected if 1 <= b <= 6}
    return valid if valid else set(range(1, 7))


class ReportEmitter:
    """Generates structured JSON or Markdown summaries from classified findings."""

    def __init__(
        self,
        findings: list[Finding],
        active_batches: set[int] | None = None,
        manager: str = "npm",
    ) -> None:
        self.findings = findings
        self.active_batches = active_batches or set(range(1, 7))
        self.manager = manager

    def gate(self, batch_id: int) -> str:
        """Verification gate for a batch, rendered for the detected package manager."""
        return render_gate(BATCH_METADATA[batch_id]["verification_gate"], self.manager)

    def generate_json(self) -> str:
        """Produce structured, machine-readable JSON output."""
        total = len(self.findings)
        by_batch_count: dict[str, int] = {}
        by_risk_count: dict[str, int] = {"High": 0, "Medium": 0, "Low": 0}

        for b_id in sorted(self.active_batches):
            meta = BATCH_METADATA[b_id]
            by_batch_count[f"{b_id}: {meta['name']}"] = 0

        batches_dict: dict[str, Any] = {}
        for b_id in sorted(self.active_batches):
            meta = BATCH_METADATA[b_id]
            batch_findings = [f.to_dict() for f in self.findings if f.batch == b_id]
            batches_dict[str(b_id)] = {
                "batch_id": b_id,
                "name": meta["name"],
                "title": meta["title"],
                "wave": meta["wave"],
                "description": meta["description"],
                "verification_gate": self.gate(b_id),
                "count": len(batch_findings),
                "findings": batch_findings,
            }

        for f in self.findings:
            if f.batch in self.active_batches:
                key = f"{f.batch}: {f.batch_name}"
                by_batch_count[key] = by_batch_count.get(key, 0) + 1
                by_risk_count[f.risk_score] = by_risk_count.get(f.risk_score, 0) + 1

        payload = {
            "summary": {
                "total_findings": total,
                "active_batches": sorted(self.active_batches),
                "by_batch": by_batch_count,
                "by_risk": by_risk_count,
            },
            "batches": batches_dict,
            "findings": [f.to_dict() for f in self.findings if f.batch in self.active_batches],
        }

        return json.dumps(payload, indent=2) + "\n"

    def generate_markdown(self) -> str:
        """Produce clean Markdown table summary."""
        is_filtered = len(self.active_batches) < 6
        filter_note = f" (Filtered to Batch: {', '.join(str(b) for b in sorted(self.active_batches))})" if is_filtered else ""
        lines: list[str] = [
            f"# TypeScript Dead Code Audit: 6-Batch Remediation Plan{filter_note}",
            "",
            "> Systematic classification and risk assessment for detected dead-code violations.",
            "> Remediation must proceed in strict dependency order (Batch 1 through Batch 6).",
            f"> Gate commands rendered for the detected package manager: **{self.manager}**.",
            "",
            "## 1. Executive Summary",
            "",
            "| Batch | Category | Wave | Findings | High Risk | Medium Risk | Low Risk |",
            "| :---: | :--- | :--- | :---: | :---: | :---: | :---: |",
        ]

        total_findings = len(self.findings)
        total_high = sum(1 for f in self.findings if f.risk_score == "High")
        total_med = sum(1 for f in self.findings if f.risk_score == "Medium")
        total_low = sum(1 for f in self.findings if f.risk_score == "Low")

        for b_id in sorted(self.active_batches):
            meta = BATCH_METADATA[b_id]
            batch_list = [f for f in self.findings if f.batch == b_id]
            c_high = sum(1 for f in batch_list if f.risk_score == "High")
            c_med = sum(1 for f in batch_list if f.risk_score == "Medium")
            c_low = sum(1 for f in batch_list if f.risk_score == "Low")
            lines.append(
                f"| **{b_id}** | **{meta['title']}** | {meta['wave']} | **{len(batch_list)}** | {c_high} | {c_med} | {c_low} |"
            )

        lines.extend([
            f"| **Total** | | | **{total_findings}** | **{total_high}** | **{total_med}** | **{total_low}** |",
            "",
            "---",
            "",
            "## 2. Contextual Batch Breakdown",
            "",
        ])

        for b_id in sorted(self.active_batches):
            meta = BATCH_METADATA[b_id]
            batch_findings = [f for f in self.findings if f.batch == b_id]

            lines.append(f"### Batch {b_id}: {meta['title']} ({len(batch_findings)} findings)")
            lines.append(f"*{meta['description']}*  ")
            lines.append(f"**Feeds**: {meta['wave']}  ")
            lines.append(f"**Verification Gate**: `{self.gate(b_id)}`")
            lines.append("")

            if not batch_findings:
                lines.append("No violations detected in this batch.\n")
                continue

            lines.extend([
                "| ID | Symbol / Package | Location | Risk | Recommended Action |",
                "| :--- | :--- | :--- | :---: | :--- |",
            ])

            for f in batch_findings:
                loc = f"{f.file}:{f.line}:{f.col}" if f.line and f.col else (f"{f.file}:{f.line}" if f.line else f.file)
                # Escape pipe symbols in action / symbol
                safe_sym = f.symbol.replace("|", "\\|")
                safe_act = f.action.replace("|", "\\|")
                lines.append(f"| `{f.id}` | `{safe_sym}` | `{loc}` | **{f.risk_score}** | {safe_act} |")

            lines.append("")

        lines.extend([
            "---",
            "",
            "## 3. Recommended Remediation Sequence Protocol",
            "",
            "1. **Pre-flight Check**: Ensure `git status --porcelain` is clean before starting any wave.",
            "2. **Wave 1 (Dependencies)**: Prune unused packages from `package.json`, then run lockfile sync.",
            "3. **Wave 2 (Dead Files)**: Remove unreferenced source files using `git rm`.",
            "4. **Wave 3 (Barrels)**: Prune unused exports from barrel files to break circular dependency loops.",
            "5. **Wave 4 (Encapsulation)**: Decouple production code from unit test inspection (Batch 4), then"
            " remove the `export` keyword from symbols only referenced within their own module (Batch 5).",
            "6. **Wave 5 (Types & Enums)**: Prune unreferenced type aliases, interfaces, and enum variants.",
            "7. **Post-flight Verification**: Re-run the dead-code engine to confirm zero remaining violations.",
            "",
        ])

        return "\n".join(lines)


def knip_is_available(cwd: Path) -> tuple[bool, str]:
    """Report whether a runnable `knip` exists for `cwd`.

    `npx knip` on a project without knip installed will silently try to fetch it
    from the registry, which hangs on an offline box and installs an unpinned
    version on a networked one. Probe with --version first so the caller can fail
    with an actionable message instead.
    """
    try:
        proc = subprocess.run(
            ["npx", "--no-install", "knip", "--version"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except FileNotFoundError:
        return False, "'npx' not found. Install Node.js (which provides npx), then retry."
    except subprocess.TimeoutExpired:
        return False, "Probing for knip timed out after 60s."
    except Exception as e:  # noqa: BLE001 - surface any probe failure as unavailable
        return False, f"Failed to probe for knip: {e}"

    if proc.returncode != 0:
        return False, (
            "knip is not installed in this project. Add it as a dev dependency "
            "(npm i -D knip / pnpm add -D knip / yarn add -D knip / bun add -d knip), "
            "then retry."
        )
    return True, proc.stdout.strip()


def execute_knip(cwd: Path) -> tuple[int, str, str]:
    """Execute `npx knip --reporter json` in target project directory."""
    available, detail = knip_is_available(cwd)
    if not available:
        return 127, "", f"Error: {detail}"

    cmd = ["npx", "--no-install", "knip", "--reporter", "json"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, "", "Error: 'npx' command not found. Please ensure Node.js and npm/npx are installed."
    except Exception as e:
        return 1, "", f"Failed to execute knip: {e}"


def main() -> int:
    """CLI Entrypoint for batch-findings."""
    parser = argparse.ArgumentParser(
        description="Batch and prioritize dead-code findings into 6 contextual batches with risk scores.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --run
  %(prog)s --run --output json
  %(prog)s --input knip-report.json --output markdown
  %(prog)s --input - --output markdown < knip-report.json
  %(prog)s --run --output markdown --out-file cleanup-plan.md
        """,
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        help="Path to Knip JSON file or '-' to read from standard input.",
    )
    parser.add_argument(
        "--run",
        "-r",
        action="store_true",
        help="Execute 'npx knip --reporter json' directly in target project directory.",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["json", "markdown"],
        default="markdown",
        help="Report format to generate (default: markdown).",
    )
    parser.add_argument(
        "--out-file",
        type=str,
        help="Output file path. If omitted, prints report directly to stdout.",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=".",
        help="Project root directory (used with --run or for verifying file references; default: current directory).",
    )
    parser.add_argument(
        "--batch",
        "-b",
        type=str,
        help="Filter findings by batch number (e.g. '1', '1,2', '1-3', 'all'; default: all).",
    )
    parser.add_argument(
        "--risk",
        choices=["high", "medium", "low", "all"],
        help="Filter findings by risk level ('high', 'medium', 'low'; default: all).",
    )

    args = parser.parse_args()
    target_dir = Path(args.target).resolve()

    raw_json_str = ""

    if args.run:
        print("Executing 'npx knip --reporter json'...", file=sys.stderr)
        rc, stdout_str, stderr_str = execute_knip(target_dir)
        # Note: Knip exits with code 1 or 2 when issues are found, which is normal.
        if not stdout_str.strip():
            print(f"Knip execution error (exit code {rc}):\n{stderr_str}", file=sys.stderr)
            return 1
        raw_json_str = stdout_str
    elif args.input:
        if args.input == "-":
            raw_json_str = sys.stdin.read()
        else:
            in_path = Path(args.input)
            if not in_path.is_file():
                print(f"Error: Input file does not exist: {in_path}", file=sys.stderr)
                return 1
            raw_json_str = in_path.read_text(encoding="utf-8")
    else:
        # Check if stdin has piped data
        if not sys.stdin.isatty():
            raw_json_str = sys.stdin.read()
        else:
            parser.print_help(sys.stderr)
            print("\nError: Please provide input via --input <file|- > or execute Knip via --run.", file=sys.stderr)
            return 1

    try:
        raw_data = json.loads(raw_json_str)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse input as valid JSON: {e}", file=sys.stderr)
        # Print snippet of input for troubleshooting
        snippet = raw_json_str[:200] + ("..." if len(raw_json_str) > 200 else "")
        print(f"Input received: {snippet}", file=sys.stderr)
        return 1

    parser_engine = KnipReportParser(raw_data, project_dir=target_dir)
    findings = parser_engine.parse()

    active_batches: set[int] | None = None
    if args.batch:
        active_batches = parse_batch_filter(args.batch)
        findings = [f for f in findings if f.batch in active_batches]

    if args.risk and args.risk.lower() != "all":
        target_risk = args.risk.capitalize()
        findings = [f for f in findings if f.risk_score == target_risk]

    emitter = ReportEmitter(
        findings,
        active_batches=active_batches,
        manager=detect_package_manager(target_dir),
    )
    output_content = emitter.generate_json() if args.output == "json" else emitter.generate_markdown()

    if args.out_file:
        out_path = Path(args.out_file).resolve()
        try:
            out_path.write_text(output_content, encoding="utf-8")
            print(f"Report written successfully to: {out_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing output to '{out_path}': {e}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(output_content)

    return 0


if __name__ == "__main__":
    sys.exit(main())
