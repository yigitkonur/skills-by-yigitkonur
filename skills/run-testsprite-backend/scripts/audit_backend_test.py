#!/usr/bin/env python3
"""Statically audit TestSprite backend Python before uploading it.

The checks are intentionally conservative and never print suspected secret
values. They catch TestSprite-specific footguns; they are not a Python linter.
"""

from __future__ import annotations

import argparse
import ast
import ipaddress
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse


HTTP_METHODS = {"delete", "get", "head", "options", "patch", "post", "put", "request"}
SUPPORTED_THIRD_PARTY = {"numpy", "pytest", "requests", "scipy"}
AUTH_KEYS = {"authorization", "x-api-key", "api-key", "apikey"}
SECRET_NAMES = re.compile(r"(?:api[_-]?key|access[_-]?token|auth[_-]?token|token|password|secret)$", re.I)
SECRET_SHAPES = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.I),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
)
PLACEHOLDER_WORDS = {"changeme", "dummy", "example", "placeholder", "redacted", "replace", "sample"}
STDLIB_FALLBACK = {
    "base64",
    "collections",
    "contextlib",
    "csv",
    "datetime",
    "decimal",
    "hashlib",
    "hmac",
    "html",
    "http",
    "io",
    "ipaddress",
    "itertools",
    "json",
    "math",
    "os",
    "random",
    "re",
    "secrets",
    "statistics",
    "string",
    "time",
    "typing",
    "unittest",
    "urllib",
    "uuid",
}


@dataclass
class Finding:
    code: str
    message: str
    line: int | None = None

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {"code": self.code, "message": self.message}
        if self.line is not None:
            result["line"] = self.line
        return result


@dataclass
class Report:
    errors: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(word in lowered for word in PLACEHOLDER_WORDS) or "<" in value or "${" in value


def dotted_root(node: ast.AST) -> str | None:
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


class ExecutableCallCollector(ast.NodeVisitor):
    """Collect calls that execute while the module is loaded."""

    def __init__(self) -> None:
        self.calls: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        return

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        return

    def visit_Lambda(self, node: ast.Lambda) -> None:  # noqa: N802
        return

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        self.generic_visit(node)


def executable_calls(statements: list[ast.stmt]) -> set[str]:
    collector = ExecutableCallCollector()
    for statement in statements:
        collector.visit(statement)
    return collector.calls


def imported_roots(tree: ast.Module) -> list[tuple[str, int]]:
    roots: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.extend((alias.name.split(".", 1)[0], node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append((node.module.split(".", 1)[0], node.lineno))
    return roots


def request_aliases(tree: ast.Module) -> tuple[set[str], set[str], set[str]]:
    modules = {"requests"}
    sessions: set[str] = set()
    direct_methods: set[str] = set()
    session_factories: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "requests":
                    modules.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "requests":
            for alias in node.names:
                imported_name = alias.name
                local_name = alias.asname or imported_name
                if imported_name.lower() in HTTP_METHODS:
                    direct_methods.add(local_name)
                elif imported_name == "Session":
                    session_factories.add(local_name)
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if not isinstance(value, ast.Call):
                continue
            creates_session = (
                isinstance(value.func, ast.Attribute)
                and value.func.attr == "Session"
                and dotted_root(value.func) in modules
            ) or (isinstance(value.func, ast.Name) and value.func.id in session_factories)
            if not creates_session:
                continue
            for target in targets:
                if isinstance(target, ast.Name):
                    sessions.add(target.id)
    return modules, sessions, direct_methods


def inspect_url(value: str, line: int, report: Report) -> None:
    if not value.startswith(("http://", "https://")):
        return
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if not host:
        return
    if host in {"localhost", "0.0.0.0"} or host.endswith((".local", ".internal")):
        report.errors.append(Finding("private-target", "TestSprite cloud cannot reach this local/private target", line))
        return
    try:
        if ipaddress.ip_address(host).is_private:
            report.errors.append(Finding("private-target", "TestSprite cloud cannot reach this private IP target", line))
            return
    except ValueError:
        pass
    reserved_example = host in {"example.com", "example.net", "example.org"} or host.endswith(
        (".example.com", ".example.net", ".example.org")
    )
    if reserved_example or host.endswith((".example", ".invalid", ".test")):
        report.errors.append(Finding("placeholder-target", "Replace the placeholder URL before creating the test", line))


def audit_source(source: str, auth_required: bool, allowed_modules: set[str]) -> Report:
    report = Report()
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        report.errors.append(Finding("syntax", exc.msg, exc.lineno))
        return report

    tests = {
        node.name: node.lineno
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith("test_"):
            report.errors.append(
                Finding("async-test", "Async test functions are not executed by a plain module-scope call", node.lineno)
            )
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            positional = list(node.args.posonlyargs) + list(node.args.args)
            required_positional = [
                arg
                for arg, default in zip(
                    positional,
                    [None] * (len(positional) - len(node.args.defaults)) + list(node.args.defaults),
                )
                if default is None
            ]
            required_keyword = [
                arg for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults) if default is None
            ]
            if required_positional or required_keyword:
                report.errors.append(
                    Finding("test-parameters", "Top-level test functions cannot depend on pytest fixtures/arguments", node.lineno)
                )
    if not tests:
        report.errors.append(Finding("no-tests", "Define at least one top-level test_* function"))
    called = executable_calls(tree.body)
    for name, line in tests.items():
        if name not in called:
            report.errors.append(Finding("uncalled-test", f"Call {name}() at module scope", line))

    stdlib = getattr(sys, "stdlib_module_names", STDLIB_FALLBACK)
    permitted = set(stdlib) | SUPPORTED_THIRD_PARTY | allowed_modules | {"__future__"}
    for root, line in imported_roots(tree):
        if root not in permitted:
            report.errors.append(
                Finding("unsupported-import", f"Module {root!r} is not in the documented TestSprite sandbox", line)
            )

    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    managed_auth_refs = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    if auth_required and "__AUTH_HEADERS__" not in names | managed_auth_refs:
        report.errors.append(
            Finding("missing-managed-auth", "Authenticated tests must consume TestSprite-managed __AUTH_HEADERS__")
        )

    modules, sessions, direct_methods = request_aliases(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            inspect_url(node.value, node.lineno, report)
            if not is_placeholder(node.value) and any(pattern.search(node.value) for pattern in SECRET_SHAPES):
                report.errors.append(
                    Finding("embedded-secret", "Likely credential literal found; use TestSprite-managed credentials", node.lineno)
                )

        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if isinstance(value, ast.Constant) and isinstance(value.value, str) and not is_placeholder(value.value):
                for target in targets:
                    if isinstance(target, ast.Name) and SECRET_NAMES.search(target.id) and len(value.value) >= 8:
                        report.errors.append(
                            Finding("embedded-secret", "Likely secret assignment found; use managed credentials", node.lineno)
                        )

        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                    continue
                if key.value.lower() not in AUTH_KEYS:
                    continue
                if isinstance(value, ast.Constant) and isinstance(value.value, str) and not is_placeholder(value.value):
                    report.errors.append(
                        Finding("embedded-secret", "Literal authentication header found; use __AUTH_HEADERS__", node.lineno)
                    )

        if not isinstance(node, ast.Call):
            continue
        is_request = isinstance(node.func, ast.Name) and node.func.id in direct_methods
        if isinstance(node.func, ast.Attribute):
            root = dotted_root(node.func)
            is_request = node.func.attr.lower() in HTTP_METHODS and root in modules | sessions
        if not is_request:
            continue
        if not any(keyword.arg == "timeout" for keyword in node.keywords):
            report.errors.append(Finding("missing-timeout", "Every HTTP request needs an explicit timeout", node.lineno))

    return report


def run_self_test() -> None:
    good = '''
import requests
BASE_URL = "https://staging.acme.com"
HEADERS = dict(globals().get("__AUTH_HEADERS__", {}))
def test_health():
    response = requests.get(f"{BASE_URL}/health", headers=HEADERS, timeout=30)
    assert response.status_code == 200
test_health()
'''
    bad = '''
import project_code
import requests
BASE_URL = "http://127.0.0.1:3000"
API_KEY = "live-credential-value-1234"
def test_health():
    requests.get(f"{BASE_URL}/health", headers={"Authorization": "Bearer livecredential123"})
async def test_async():
    pass
def test_fixture(client):
    pass
'''
    assert audit_source(good, auth_required=True, allowed_modules=set()).ok
    bad_report = audit_source(bad, auth_required=True, allowed_modules=set())
    assert not bad_report.ok
    codes = {finding.code for finding in bad_report.errors}
    assert {
        "async-test",
        "embedded-secret",
        "missing-managed-auth",
        "missing-timeout",
        "private-target",
        "test-parameters",
        "uncalled-test",
    } <= codes
    print("audit_backend_test self-test: ok")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, help="backend Python file to audit")
    parser.add_argument("--auth-required", action="store_true", help="require __AUTH_HEADERS__ usage")
    parser.add_argument("--allow-module", action="append", default=[], help="allow an additional verified module")
    parser.add_argument("--json", action="store_true", help="emit machine-readable findings")
    parser.add_argument("--self-test", action="store_true", help="run deterministic built-in checks")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        run_self_test()
        return 0
    if args.path is None:
        raise SystemExit("path is required unless --self-test is used")
    try:
        source = args.path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"cannot read {args.path}: {exc}") from exc
    report = audit_source(source, args.auth_required, set(args.allow_module))
    payload = {
        "ok": report.ok,
        "errors": [finding.as_dict() for finding in report.errors],
        "warnings": [finding.as_dict() for finding in report.warnings],
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for severity, findings in (("ERROR", report.errors), ("WARN", report.warnings)):
            for finding in findings:
                location = f" line {finding.line}" if finding.line is not None else ""
                print(f"{severity} [{finding.code}]{location}: {finding.message}")
        print("audit_backend_test: ok" if report.ok else f"audit_backend_test: {len(report.errors)} error(s)")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
