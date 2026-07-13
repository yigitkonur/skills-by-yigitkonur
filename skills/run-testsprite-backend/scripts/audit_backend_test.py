#!/usr/bin/env python3
"""Statically audit TestSprite backend Python before uploading it.

The checks are intentionally conservative and never print suspected secret
values. They catch TestSprite-specific footguns; they are not a Python linter.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import ipaddress
import json
import re
import sys
import sysconfig
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse


HTTP_METHODS = {"delete", "get", "head", "options", "patch", "post", "put", "request"}
SUPPORTED_THIRD_PARTY = {"numpy", "pytest", "requests", "scipy"}
SENSITIVE_HEADER_KEYS = {"authorization", "cookie", "x-api-key", "api-key", "apikey"}
SENSITIVE_REQUEST_KWARGS = {"auth", "cookies"}
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


def static_truth(value: ast.AST) -> bool | None:
    """Return the truth of a literal expression, or None when it is dynamic."""

    try:
        return bool(ast.literal_eval(value))
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return None


class ExecutableCallCollector(ast.NodeVisitor):
    """Collect calls on statically reachable paths in a statement block."""

    def __init__(self) -> None:
        self.calls: list[ast.Call] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        return

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        return

    def visit_Lambda(self, node: ast.Lambda) -> None:  # noqa: N802
        return

    def visit_If(self, node: ast.If) -> None:  # noqa: N802
        self.visit(node.test)
        truth = static_truth(node.test)
        if truth is True:
            statements = node.body
        elif truth is False:
            statements = node.orelse
        else:
            statements = [*node.body, *node.orelse]
        for statement in statements:
            self.visit(statement)

    def visit_IfExp(self, node: ast.IfExp) -> None:  # noqa: N802
        self.visit(node.test)
        truth = static_truth(node.test)
        if truth is True:
            self.visit(node.body)
        elif truth is False:
            self.visit(node.orelse)
        else:
            self.visit(node.body)
            self.visit(node.orelse)

    def visit_While(self, node: ast.While) -> None:  # noqa: N802
        self.visit(node.test)
        truth = static_truth(node.test)
        statements = node.orelse if truth is False else [*node.body, *node.orelse]
        for statement in statements:
            self.visit(statement)

    def visit_For(self, node: ast.For) -> None:  # noqa: N802
        self.visit(node.iter)
        try:
            empty = len(ast.literal_eval(node.iter)) == 0
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
            empty = False
        statements = node.orelse if empty else [*node.body, *node.orelse]
        for statement in statements:
            self.visit(statement)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:  # noqa: N802
        for value in node.values:
            self.visit(value)
            truth = static_truth(value)
            if isinstance(node.op, ast.And) and truth is False:
                break
            if isinstance(node.op, ast.Or) and truth is True:
                break

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        self.calls.append(node)
        self.generic_visit(node)


def executable_calls(statements: list[ast.stmt]) -> list[ast.Call]:
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


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def is_stdlib_module(root: str) -> bool:
    stdlib_names = getattr(sys, "stdlib_module_names", None)
    if stdlib_names is not None:
        return root in stdlib_names
    if root in STDLIB_FALLBACK:
        return True
    try:
        spec = importlib.util.find_spec(root)
    except (ImportError, AttributeError, ValueError):
        return False
    if spec is None:
        return False
    if spec.origin in {"built-in", "frozen"}:
        return True
    candidates: list[Path] = []
    if spec.origin:
        candidates.append(Path(spec.origin))
    if spec.submodule_search_locations:
        candidates.extend(Path(location) for location in spec.submodule_search_locations)
    paths = sysconfig.get_paths()
    stdlib_roots = {
        Path(paths[key])
        for key in ("stdlib", "platstdlib")
        if paths.get(key)
    }
    third_party_roots = {
        Path(paths[key])
        for key in ("purelib", "platlib")
        if paths.get(key)
    }
    return any(
        any(path_is_within(candidate, root_path) for root_path in stdlib_roots)
        and not any(path_is_within(candidate, root_path) for root_path in third_party_roots)
        for candidate in candidates
    )


def bound_names(target: ast.AST | None) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return {name for element in target.elts for name in bound_names(element)}
    return set()


def creates_session(
    value: ast.AST,
    modules: set[str],
    session_factories: set[str],
) -> bool:
    if not isinstance(value, ast.Call):
        return False
    if isinstance(value.func, ast.Name):
        return value.func.id in session_factories
    return (
        isinstance(value.func, ast.Attribute)
        and value.func.attr.lower() == "session"
        and dotted_root(value.func) in modules
    )


def request_aliases(tree: ast.Module) -> tuple[set[str], set[str], set[str], set[str]]:
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
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if not creates_session(value, modules, session_factories):
                continue
            for target in targets:
                sessions.update(bound_names(target))
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if creates_session(item.context_expr, modules, session_factories):
                    sessions.update(bound_names(item.optional_vars))
    return modules, sessions, direct_methods, session_factories


def is_request_call(
    node: ast.Call,
    modules: set[str],
    sessions: set[str],
    direct_methods: set[str],
    session_factories: set[str],
) -> bool:
    if isinstance(node.func, ast.Name):
        return node.func.id in direct_methods
    if not isinstance(node.func, ast.Attribute) or node.func.attr.lower() not in HTTP_METHODS:
        return False
    receiver = node.func.value
    if isinstance(receiver, ast.Name) and receiver.id in sessions:
        return True
    if dotted_root(node.func) in modules:
        return True
    return creates_session(receiver, modules, session_factories)


def contains_literal_credential(node: ast.AST) -> bool:
    return any(
        isinstance(child, ast.Constant)
        and isinstance(child.value, (str, bytes))
        and bool(child.value)
        and (not isinstance(child.value, str) or not is_placeholder(child.value))
        for child in ast.walk(node)
    )


def is_globals_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "globals"
        and not node.args
        and not node.keywords
    )


def expression_uses_managed_auth(node: ast.AST, aliases: set[str]) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in aliases:
            return True
        if (
            isinstance(child, ast.Subscript)
            and is_globals_call(child.value)
            and isinstance(child.slice, ast.Constant)
            and child.slice.value == "__AUTH_HEADERS__"
        ):
            return True
        if (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr == "get"
            and is_globals_call(child.func.value)
            and child.args
            and isinstance(child.args[0], ast.Constant)
            and child.args[0].value == "__AUTH_HEADERS__"
        ):
            return True
    return False


def managed_auth_aliases(tree: ast.Module) -> set[str]:
    aliases = {"__AUTH_HEADERS__"}
    assignments: list[tuple[list[ast.AST], ast.AST]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            assignments.append((list(node.targets), node.value))
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            assignments.append(([node.target], node.value))
    changed = True
    while changed:
        changed = False
        for targets, value in assignments:
            if not expression_uses_managed_auth(value, aliases):
                continue
            for target in targets:
                for name in bound_names(target):
                    if name not in aliases:
                        aliases.add(name)
                        changed = True
    return aliases


def request_uses_managed_auth(node: ast.Call, aliases: set[str]) -> bool:
    return any(
        keyword.arg == "headers" and expression_uses_managed_auth(keyword.value, aliases)
        for keyword in node.keywords
    )


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
    modules, sessions, direct_methods, session_factories = request_aliases(tree)
    module_calls = executable_calls(tree.body)
    called = {
        node.func.id
        for node in module_calls
        if isinstance(node.func, ast.Name)
    }
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    function_calls = {
        name: executable_calls(node.body)
        for name, node in functions.items()
    }
    request_memo: dict[str, bool] = {}

    def reaches_request(name: str, visiting: set[str]) -> bool:
        if name in request_memo:
            return request_memo[name]
        if name in visiting:
            return False
        next_visiting = visiting | {name}
        for call in function_calls.get(name, []):
            if is_request_call(call, modules, sessions, direct_methods, session_factories):
                request_memo[name] = True
                return True
            if (
                isinstance(call.func, ast.Name)
                and call.func.id in functions
                and reaches_request(call.func.id, next_visiting)
            ):
                request_memo[name] = True
                return True
        request_memo[name] = False
        return False

    for name, line in tests.items():
        if name not in called:
            report.errors.append(Finding("uncalled-test", f"Call {name}() at module scope", line))
        elif not reaches_request(name, set()):
            report.errors.append(
                Finding("no-http-request", f"{name}() does not reach a requests HTTP call", line)
            )

    permitted = SUPPORTED_THIRD_PARTY | allowed_modules | {"__future__"}
    for root, line in imported_roots(tree):
        if root not in permitted and not is_stdlib_module(root):
            report.errors.append(
                Finding("unsupported-import", f"Module {root!r} is not in the documented TestSprite sandbox", line)
            )

    request_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and is_request_call(node, modules, sessions, direct_methods, session_factories)
    ]
    auth_aliases = managed_auth_aliases(tree)
    if auth_required and not any(request_uses_managed_auth(node, auth_aliases) for node in request_calls):
        report.errors.append(
            Finding(
                "missing-managed-auth",
                "At least one HTTP request must consume TestSprite-managed __AUTH_HEADERS__",
            )
        )

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
                if key.value.lower() not in SENSITIVE_HEADER_KEYS:
                    continue
                if isinstance(value, ast.Constant) and isinstance(value.value, str) and not is_placeholder(value.value):
                    report.errors.append(
                        Finding("embedded-secret", "Literal authentication/cookie header found; use managed credentials", node.lineno)
                    )

        if not isinstance(node, ast.Call):
            continue
        if not is_request_call(node, modules, sessions, direct_methods, session_factories):
            continue
        for keyword in node.keywords:
            if keyword.arg in SENSITIVE_REQUEST_KWARGS and contains_literal_credential(keyword.value):
                report.errors.append(
                    Finding("embedded-secret", f"Literal {keyword.arg} credential found; use managed credentials", node.lineno)
                )
        if not any(keyword.arg == "timeout" for keyword in node.keywords):
            report.errors.append(Finding("missing-timeout", "Every HTTP request needs an explicit timeout", node.lineno))

    return report


def run_self_test() -> None:
    good = '''
from pathlib import Path
import requests
BASE_URL = "https://staging.acme.com"
HEADERS = dict(globals().get("__AUTH_HEADERS__", {}))
def test_health():
    assert Path("/").is_absolute()
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
    focused_bad = {
        "literal-cookie": '''
import requests
def test_cookie():
    requests.get("https://staging.acme.com/me", headers={"Cookie": "session=live-value"}, timeout=30)
test_cookie()
''',
        "literal-basic-auth": '''
import requests
def test_basic():
    requests.get("https://staging.acme.com/me", auth=("user", "live-password"), timeout=30)
test_basic()
''',
        "dead-call": '''
import requests
def test_dead():
    requests.get("https://staging.acme.com/me", timeout=30)
if False:
    test_dead()
''',
        "no-http": '''
def test_vacuous():
    assert True
test_vacuous()
''',
        "chained-session-timeout": '''
import requests
def test_session():
    requests.Session().get("https://staging.acme.com/me")
test_session()
''',
        "docstring-auth": '''
import requests
"""Mentioning __AUTH_HEADERS__ here must not satisfy managed authentication."""
def test_auth():
    requests.get("https://staging.acme.com/me", timeout=30)
test_auth()
''',
    }
    expected = {
        "literal-cookie": "embedded-secret",
        "literal-basic-auth": "embedded-secret",
        "dead-call": "uncalled-test",
        "no-http": "no-http-request",
        "chained-session-timeout": "missing-timeout",
        "docstring-auth": "missing-managed-auth",
    }
    for name, source in focused_bad.items():
        report = audit_source(source, auth_required=name == "docstring-auth", allowed_modules=set())
        assert expected[name] in {finding.code for finding in report.errors}, name
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
