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
SECRET_NAMES = re.compile(
    r"(?:api[_-]?key|access[_-]?token|auth[_-]?token|auth|cookie|token|password|secret)$",
    re.I,
)
SECRET_SHAPES = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.I),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
)
PLACEHOLDER_WORDS = {"changeme", "dummy", "example", "placeholder", "redacted", "replace", "sample"}
STDLIB_FALLBACK = {
    "base64", "collections", "contextlib", "csv", "datetime", "decimal", "hashlib",
    "hmac", "html", "http", "io", "ipaddress", "itertools", "json", "math", "os",
    "pathlib", "random", "re", "secrets", "statistics", "string", "time", "typing",
    "unittest", "urllib", "uuid",
}


@dataclass(frozen=True)
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

    def error(self, code: str, message: str, line: int | None = None) -> None:
        finding = Finding(code, message, line)
        if finding not in self.errors:
            self.errors.append(finding)


@dataclass
class ScopeState:
    bindings: dict[str, ast.AST] = field(default_factory=dict)
    managed_auth: set[str] = field(default_factory=lambda: {"__AUTH_HEADERS__"})
    had_request: bool = False
    had_managed_request: bool = False
    active: bool = True

    def clone(self) -> "ScopeState":
        return ScopeState(
            bindings=dict(self.bindings),
            managed_auth=set(self.managed_auth),
            had_request=self.had_request,
            had_managed_request=self.had_managed_request,
            active=self.active,
        )


def is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(word in lowered for word in PLACEHOLDER_WORDS) or "<" in value or "${" in value


def dotted_root(node: ast.AST) -> str | None:
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def bound_names(target: ast.AST | None) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return {name for element in target.elts for name in bound_names(element)}
    return set()


def static_truth(
    node: ast.AST,
    bindings: dict[str, ast.AST],
    visiting: frozenset[str] = frozenset(),
) -> bool | None:
    if isinstance(node, ast.Name):
        if node.id == "TYPE_CHECKING" and node.id not in bindings:
            return False
        if node.id in visiting or node.id not in bindings:
            return None
        return static_truth(bindings[node.id], bindings, visiting | {node.id})
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        value = static_truth(node.operand, bindings, visiting)
        return None if value is None else not value
    if isinstance(node, ast.BoolOp):
        values = [static_truth(value, bindings, visiting) for value in node.values]
        if isinstance(node.op, ast.And):
            if False in values:
                return False
            return True if all(value is True for value in values) else None
        if True in values:
            return True
        return False if all(value is False for value in values) else None
    try:
        return bool(ast.literal_eval(node))
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return None


def static_string_value(
    node: ast.AST,
    bindings: dict[str, ast.AST],
    visiting: frozenset[str] = frozenset(),
) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in visiting or node.id not in bindings:
            return None
        return static_string_value(bindings[node.id], bindings, visiting | {node.id})
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = static_string_value(node.left, bindings, visiting)
        right = static_string_value(node.right, bindings, visiting)
        return left + right if left is not None and right is not None else None
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                parts.append(part.value)
                continue
            if not isinstance(part, ast.FormattedValue) or part.format_spec is not None:
                return None
            value = static_string_value(part.value, bindings, visiting)
            if value is None and isinstance(part.value, ast.Constant):
                value = str(part.value.value)
            if value is None:
                return None
            if part.conversion == ord("r"):
                value = repr(value)
            elif part.conversion == ord("a"):
                value = ascii(value)
            parts.append(value)
        return "".join(parts)
    return None


def contains_literal_credential(
    node: ast.AST,
    bindings: dict[str, ast.AST],
    visiting: frozenset[str] = frozenset(),
) -> bool:
    if isinstance(node, ast.Name):
        if node.id in visiting or node.id not in bindings:
            return False
        return contains_literal_credential(bindings[node.id], bindings, visiting | {node.id})
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bytes):
            return bool(node.value)
        return isinstance(node.value, str) and bool(node.value) and not is_placeholder(node.value)
    static_value = static_string_value(node, bindings, visiting)
    if static_value is not None:
        return bool(static_value) and not is_placeholder(static_value)
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return any(contains_literal_credential(element, bindings, visiting) for element in node.elts)
    if isinstance(node, ast.Dict):
        return any(contains_literal_credential(value, bindings, visiting) for value in node.values)
    return False


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
    candidates = ([Path(spec.origin)] if spec.origin else []) + [
        Path(location) for location in (spec.submodule_search_locations or [])
    ]
    paths = sysconfig.get_paths()
    stdlib_roots = {Path(paths[key]) for key in ("stdlib", "platstdlib") if paths.get(key)}
    third_party_roots = {Path(paths[key]) for key in ("purelib", "platlib") if paths.get(key)}
    return any(
        any(path_is_within(candidate, root_path) for root_path in stdlib_roots)
        and not any(path_is_within(candidate, root_path) for root_path in third_party_roots)
        and not {"site-packages", "dist-packages"}.intersection(candidate.parts)
        for candidate in candidates
    )


def imported_roots(tree: ast.Module) -> list[tuple[str, int]]:
    roots: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.extend((alias.name.split(".", 1)[0], node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append((node.module.split(".", 1)[0], node.lineno))
    return roots


def creates_session(value: ast.AST, modules: set[str], session_factories: set[str]) -> bool:
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
                if alias.name == "requests" or alias.name.startswith("requests."):
                    modules.add(alias.asname or alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "requests" or node.module.startswith("requests."):
                for alias in node.names:
                    name = alias.name
                    local = alias.asname or name
                    if name.lower() in HTTP_METHODS:
                        direct_methods.add(local)
                    elif name == "Session":
                        session_factories.add(local)
                    elif name in {"api", "sessions"}:
                        modules.add(local)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if value is not None and creates_session(value, modules, session_factories):
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


class GuaranteedCallCollector(ast.NodeVisitor):
    """Collect calls on an expression's unconditional evaluation path."""

    def __init__(self, bindings: dict[str, ast.AST]) -> None:
        self.bindings = bindings
        self.calls: list[ast.Call] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        return

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_Lambda = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        self.generic_visit(node)
        self.calls.append(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:  # noqa: N802
        for value in node.values:
            self.visit(value)
            truth = static_truth(value, self.bindings)
            if isinstance(node.op, ast.And) and truth is not True:
                break
            if isinstance(node.op, ast.Or) and truth is not False:
                break

    def visit_IfExp(self, node: ast.IfExp) -> None:  # noqa: N802
        self.visit(node.test)
        truth = static_truth(node.test, self.bindings)
        if truth is True:
            self.visit(node.body)
        elif truth is False:
            self.visit(node.orelse)

    def visit_Compare(self, node: ast.Compare) -> None:  # noqa: N802
        self.visit(node.left)
        if node.comparators:
            self.visit(node.comparators[0])

    def _visit_comprehension(self, generators: list[ast.comprehension]) -> None:
        if generators:
            self.visit(generators[0].iter)

    def visit_ListComp(self, node: ast.ListComp) -> None:  # noqa: N802
        self._visit_comprehension(node.generators)

    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp


def guaranteed_calls(node: ast.AST, bindings: dict[str, ast.AST]) -> list[ast.Call]:
    collector = GuaranteedCallCollector(bindings)
    collector.visit(node)
    return collector.calls


class LocalBindingCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.names: set[str] = set()
        self.globals: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.names.add(node.id)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self.names.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef

    def visit_Lambda(self, node: ast.Lambda) -> None:  # noqa: N802
        return

    def visit_Global(self, node: ast.Global) -> None:  # noqa: N802
        self.globals.update(node.names)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        self.names.update(alias.asname or alias.name.split(".", 1)[0] for alias in node.names)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        self.names.update(alias.asname or alias.name for alias in node.names if alias.name != "*")

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:  # noqa: N802
        if node.name:
            self.names.add(node.name)
        for statement in node.body:
            self.visit(statement)


def local_binding_names(node: ast.FunctionDef) -> set[str]:
    collector = LocalBindingCollector()
    collector.names.update(arg.arg for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs))
    if node.args.vararg:
        collector.names.add(node.args.vararg.arg)
    if node.args.kwarg:
        collector.names.add(node.args.kwarg.arg)
    for statement in node.body:
        collector.visit(statement)
    return collector.names - collector.globals


def names_bound_in(statements: list[ast.stmt]) -> set[str]:
    collector = LocalBindingCollector()
    for statement in statements:
        collector.visit(statement)
    return collector.names - collector.globals


class ExitCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.found = False

    def visit_Return(self, node: ast.Return) -> None:  # noqa: N802
        self.found = True

    def visit_Raise(self, node: ast.Raise) -> None:  # noqa: N802
        self.found = True

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        return

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_Lambda = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef


def block_has_exit(statements: list[ast.stmt]) -> bool:
    collector = ExitCollector()
    for statement in statements:
        collector.visit(statement)
    return collector.found


def clear_names(state: ScopeState, names: set[str]) -> None:
    for name in names:
        state.bindings.pop(name, None)
        state.managed_auth.discard(name)


def assign_target(state: ScopeState, target: ast.AST, value: ast.AST | None) -> None:
    if isinstance(target, ast.Name):
        if value is None:
            clear_names(state, {target.id})
            return
        managed = expression_uses_managed_auth(value, state.managed_auth)
        state.bindings[target.id] = value
        if managed:
            state.managed_auth.add(target.id)
        else:
            state.managed_auth.discard(target.id)
        return
    if isinstance(target, (ast.Tuple, ast.List)):
        if isinstance(value, (ast.Tuple, ast.List)) and len(target.elts) == len(value.elts):
            for child_target, child_value in zip(target.elts, value.elts):
                assign_target(state, child_target, child_value)
        else:
            clear_names(state, bound_names(target))


def sensitive_headers_contain_literal(
    node: ast.AST,
    bindings: dict[str, ast.AST],
    visiting: frozenset[str] = frozenset(),
) -> bool:
    if isinstance(node, ast.Name):
        if node.id in visiting or node.id not in bindings:
            return False
        return sensitive_headers_contain_literal(bindings[node.id], bindings, visiting | {node.id})
    if isinstance(node, ast.Dict):
        for key, value in zip(node.keys, node.values):
            if key is None:
                if sensitive_headers_contain_literal(value, bindings, visiting):
                    return True
                continue
            key_value = static_string_value(key, bindings, visiting)
            if (
                key_value is not None
                and key_value.lower() in SENSITIVE_HEADER_KEYS
                and contains_literal_credential(value, bindings, visiting)
            ):
                return True
        return False
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return sensitive_headers_contain_literal(node.left, bindings, visiting) or sensitive_headers_contain_literal(
            node.right, bindings, visiting
        )
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
        return any(sensitive_headers_contain_literal(argument, bindings, visiting) for argument in node.args) or any(
            keyword.arg is not None
            and keyword.arg.lower() in SENSITIVE_HEADER_KEYS
            and contains_literal_credential(keyword.value, bindings, visiting)
            for keyword in node.keywords
        )
    return False


def inspect_request_credentials(node: ast.Call, state: ScopeState, report: Report) -> None:
    for keyword in node.keywords:
        if keyword.arg == "headers" and sensitive_headers_contain_literal(keyword.value, state.bindings):
            report.error(
                "embedded-secret",
                "Literal authentication/cookie header found; use managed credentials",
                node.lineno,
            )
        if keyword.arg in SENSITIVE_REQUEST_KWARGS and contains_literal_credential(
            keyword.value, state.bindings
        ):
            report.error(
                "embedded-secret",
                f"Literal {keyword.arg} credential found; use managed credentials",
                node.lineno,
            )


def request_uses_managed_auth(node: ast.Call, state: ScopeState) -> bool:
    return any(
        keyword.arg == "headers" and expression_uses_managed_auth(keyword.value, state.managed_auth)
        for keyword in node.keywords
    )


def observe_calls(
    node: ast.AST,
    state: ScopeState,
    module_state: ScopeState,
    functions: dict[str, ast.FunctionDef],
    request_sets: tuple[set[str], set[str], set[str], set[str]],
    report: Report,
    visiting: frozenset[str],
) -> None:
    modules, sessions, direct_methods, session_factories = request_sets
    for call in guaranteed_calls(node, state.bindings):
        if is_request_call(call, modules, sessions, direct_methods, session_factories):
            state.had_request = True
            if request_uses_managed_auth(call, state):
                state.had_managed_request = True
            inspect_request_credentials(call, state, report)
        elif isinstance(call.func, ast.Name) and call.func.id in functions and call.func.id not in state.bindings:
            helper = analyze_function(
                functions[call.func.id], module_state, functions, request_sets, report, visiting
            )
            state.had_request = state.had_request or helper.had_request
            state.had_managed_request = state.had_managed_request or helper.had_managed_request


def analyze_block(
    statements: list[ast.stmt],
    state: ScopeState,
    module_state: ScopeState,
    functions: dict[str, ast.FunctionDef],
    request_sets: tuple[set[str], set[str], set[str], set[str]],
    report: Report,
    visiting: frozenset[str],
) -> None:
    for statement in statements:
        if not state.active:
            return
        if isinstance(statement, ast.If):
            observe_calls(statement.test, state, module_state, functions, request_sets, report, visiting)
            truth = static_truth(statement.test, state.bindings)
            if truth is True:
                analyze_block(statement.body, state, module_state, functions, request_sets, report, visiting)
            elif truth is False:
                analyze_block(statement.orelse, state, module_state, functions, request_sets, report, visiting)
            else:
                clear_names(state, names_bound_in([*statement.body, *statement.orelse]))
                if block_has_exit([*statement.body, *statement.orelse]):
                    state.active = False
            continue

        if isinstance(statement, ast.Try):
            analyze_block(statement.body, state, module_state, functions, request_sets, report, visiting)
            if state.active:
                analyze_block(statement.orelse, state, module_state, functions, request_sets, report, visiting)
            if statement.finalbody:
                was_active = state.active
                state.active = True
                analyze_block(statement.finalbody, state, module_state, functions, request_sets, report, visiting)
                if not was_active:
                    state.active = False
            continue

        if isinstance(statement, (ast.With, ast.AsyncWith)):
            for item in statement.items:
                observe_calls(item.context_expr, state, module_state, functions, request_sets, report, visiting)
                clear_names(state, bound_names(item.optional_vars))
            analyze_block(statement.body, state, module_state, functions, request_sets, report, visiting)
            continue

        if isinstance(statement, ast.For):
            observe_calls(statement.iter, state, module_state, functions, request_sets, report, visiting)
            clear_names(state, bound_names(statement.target) | names_bound_in(statement.body))
            if block_has_exit(statement.body):
                state.active = False
            continue

        if isinstance(statement, ast.While):
            observe_calls(statement.test, state, module_state, functions, request_sets, report, visiting)
            clear_names(state, names_bound_in(statement.body))
            if block_has_exit(statement.body):
                state.active = False
            continue

        if isinstance(statement, ast.Assign):
            observe_calls(statement.value, state, module_state, functions, request_sets, report, visiting)
            for target in statement.targets:
                assign_target(state, target, statement.value)
            continue

        if isinstance(statement, ast.AnnAssign):
            if statement.value is not None:
                observe_calls(statement.value, state, module_state, functions, request_sets, report, visiting)
            assign_target(state, statement.target, statement.value)
            continue

        if isinstance(statement, ast.AugAssign):
            observe_calls(statement, state, module_state, functions, request_sets, report, visiting)
            clear_names(state, bound_names(statement.target))
            continue

        if isinstance(statement, (ast.Return, ast.Raise)):
            observe_calls(statement, state, module_state, functions, request_sets, report, visiting)
            state.active = False
            continue

        if isinstance(statement, ast.Delete):
            clear_names(state, {name for target in statement.targets for name in bound_names(target)})
            continue

        observe_calls(statement, state, module_state, functions, request_sets, report, visiting)


def analyze_function(
    function: ast.FunctionDef,
    module_state: ScopeState,
    functions: dict[str, ast.FunctionDef],
    request_sets: tuple[set[str], set[str], set[str], set[str]],
    report: Report,
    visiting: frozenset[str],
) -> ScopeState:
    if function.name in visiting:
        return ScopeState()
    state = module_state.clone()
    state.had_request = False
    state.had_managed_request = False
    state.active = True
    clear_names(state, local_binding_names(function))
    analyze_block(
        function.body,
        state,
        module_state,
        functions,
        request_sets,
        report,
        visiting | {function.name},
    )
    return state


def direct_test_call(statement: ast.stmt, tests: set[str]) -> str | None:
    if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
        return None
    call = statement.value
    if call.args or call.keywords or not isinstance(call.func, ast.Name):
        return None
    return call.func.id if call.func.id in tests else None


def broad_bindings(tree: ast.Module) -> dict[str, ast.AST]:
    bindings: dict[str, ast.AST] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                bindings[target.id] = value
    return bindings


def inspect_url(value: str, line: int, report: Report) -> None:
    if not value.startswith(("http://", "https://")):
        return
    parsed = urlparse(value)
    try:
        username, password, hostname = parsed.username, parsed.password, parsed.hostname
    except ValueError:
        report.error("invalid-target", "URL target is malformed", line)
        return
    if username is not None or password is not None:
        report.error("embedded-secret", "URL contains credential userinfo; use managed credentials", line)
    host = (hostname or "").lower()
    if not host:
        return
    if host in {"localhost", "0.0.0.0"} or host.endswith((".local", ".internal")):
        report.error("private-target", "TestSprite cloud cannot reach this local/private target", line)
        return
    try:
        if ipaddress.ip_address(host).is_private:
            report.error("private-target", "TestSprite cloud cannot reach this private IP target", line)
            return
    except ValueError:
        pass
    reserved = host in {"example.com", "example.net", "example.org"} or host.endswith(
        (".example.com", ".example.net", ".example.org")
    )
    if reserved or host.endswith((".example", ".invalid", ".test")):
        report.error("placeholder-target", "Replace the placeholder URL before creating the test", line)


def audit_source(source: str, auth_required: bool, allowed_modules: set[str]) -> Report:
    report = Report()
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        report.error("syntax", exc.msg, exc.lineno)
        return report

    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    tests = {name: node for name, node in functions.items() if name.startswith("test_")}
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith("test_"):
            report.error("async-test", "Async test functions cannot be called synchronously", node.lineno)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            positional = [*node.args.posonlyargs, *node.args.args]
            required_positional = positional[: len(positional) - len(node.args.defaults)]
            required_keyword = [
                arg for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults) if default is None
            ]
            if required_positional or required_keyword:
                report.error(
                    "test-parameters",
                    "Top-level test functions cannot depend on pytest fixtures/arguments",
                    node.lineno,
                )
    if not tests:
        report.error("no-tests", "Define at least one top-level test_* function")

    permitted = SUPPORTED_THIRD_PARTY | allowed_modules | {"__future__"}
    for root, line in imported_roots(tree):
        if root not in permitted and not is_stdlib_module(root):
            report.error("unsupported-import", f"Module {root!r} is not in the TestSprite sandbox", line)

    request_sets = request_aliases(tree)
    test_runs: dict[str, list[ScopeState]] = {name: [] for name in tests}
    module_state = ScopeState()
    available_functions: dict[str, ast.FunctionDef] = {}
    for statement in tree.body:
        if isinstance(statement, ast.FunctionDef):
            available_functions[statement.name] = statement
        called_test = direct_test_call(statement, set(tests))
        if called_test is not None:
            if called_test not in available_functions:
                report.error(
                    "call-before-definition",
                    f"{called_test}() is called before its function definition",
                    statement.lineno,
                )
                continue
            test_runs[called_test].append(
                analyze_function(
                    tests[called_test],
                    module_state.clone(),
                    dict(available_functions),
                    request_sets,
                    report,
                    frozenset(),
                )
            )
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                assign_target(module_state, target, statement.value)
        elif isinstance(statement, ast.AnnAssign):
            assign_target(module_state, statement.target, statement.value)

    for name, test in tests.items():
        runs = test_runs[name]
        if not runs:
            report.error("uncalled-test", f"Call {name}() directly at module scope", test.lineno)
            continue
        if any(not run.had_request for run in runs):
            report.error(
                "no-http-request",
                f"{name}() has no statically unconditional requests HTTP call",
                test.lineno,
            )
        if auth_required and any(not run.had_managed_request for run in runs):
            report.error(
                "missing-managed-auth",
                f"{name}() must send TestSprite-managed __AUTH_HEADERS__ on an unconditional request",
                test.lineno,
            )

    modules, sessions, direct_methods, session_factories = request_sets
    bindings = broad_bindings(tree)
    inspected_strings: set[str] = set()
    broad_state = ScopeState(bindings=bindings)
    for node in ast.walk(tree):
        static_value = static_string_value(node, bindings)
        if static_value is not None and static_value not in inspected_strings:
            inspected_strings.add(static_value)
            inspect_url(static_value, node.lineno, report)
            if not is_placeholder(static_value) and any(pattern.search(static_value) for pattern in SECRET_SHAPES):
                report.error(
                    "embedded-secret",
                    "Likely credential literal found; use TestSprite-managed credentials",
                    node.lineno,
                )

        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if value is not None and contains_literal_credential(value, bindings):
                for target in targets:
                    if isinstance(target, ast.Name) and SECRET_NAMES.search(target.id):
                        report.error(
                            "embedded-secret",
                            "Likely secret assignment found; use managed credentials",
                            node.lineno,
                        )
                    if isinstance(target, ast.Subscript):
                        key = static_string_value(target.slice, bindings)
                        if key is not None and key.lower() in SENSITIVE_HEADER_KEYS:
                            report.error(
                                "embedded-secret",
                                "Literal authentication/cookie header found; use managed credentials",
                                node.lineno,
                            )

        if isinstance(node, ast.Dict) and sensitive_headers_contain_literal(node, bindings):
            report.error(
                "embedded-secret",
                "Literal authentication/cookie header found; use managed credentials",
                node.lineno,
            )

        if isinstance(node, ast.Call) and is_request_call(
            node, modules, sessions, direct_methods, session_factories
        ):
            inspect_request_credentials(node, broad_state, report)
            if not any(keyword.arg == "timeout" for keyword in node.keywords):
                report.error("missing-timeout", "Every HTTP request needs an explicit timeout", node.lineno)

    return report


def source(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def run_self_test() -> None:
    good = source(
        "from pathlib import Path", "import requests", 'BASE_URL = "https://staging.acme.com"',
        'HEADERS = dict(globals().get("__AUTH_HEADERS__", {}))', "def test_health():",
        '    assert Path("/").is_absolute()',
        '    response = requests.get(f"{BASE_URL}/health", headers=HEADERS, timeout=30)',
        "    assert response.status_code == 200", "test_health()",
    )
    assert audit_source(good, auth_required=True, allowed_modules=set()).ok

    cases = {
        "variable-cookie": (False, source(
            "import requests", 'SESSION_COOKIE = "session=realistic-secret-value-123456"',
            "def test_case():", '    requests.get("https://staging.acme.com/me",',
            '        headers={"Cookie": SESSION_COOKIE}, timeout=30)', "test_case()"), "embedded-secret"),
        "variable-auth": (False, source(
            "import requests", 'BASIC_AUTH = ("live-user", "realistic-password-value-123456")',
            "def test_case():", '    requests.get("https://staging.acme.com/me", auth=BASIC_AUTH, timeout=30)',
            "test_case()"), "embedded-secret"),
        "dead-call": (False, source(
            "import requests", "def test_case():", '    requests.get("https://staging.acme.com/me", timeout=30)',
            "if False:", "    test_case()"), "uncalled-test"),
        "typing-call": (False, source(
            "from typing import TYPE_CHECKING", "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/me", timeout=30)', "if TYPE_CHECKING:",
            "    test_case()"), "uncalled-test"),
        "no-http": (False, source("def test_case():", "    assert True", "test_case()"), "no-http-request"),
        "except-only": (False, source(
            "import requests", "def test_case():", "    try:", "        value = 1", "    except Exception:",
            '        requests.get("https://staging.acme.com/me", timeout=30)', "    assert value == 1",
            "test_case()"), "no-http-request"),
        "conditional-early-return": (False, source(
            "import requests", "def test_case():", '    if globals().get("SKIP_REQUEST"):',
            "        return", '    requests.get("https://staging.acme.com/me", timeout=30)',
            "test_case()"), "no-http-request"),
        "session-timeout": (False, source(
            "import requests", "def test_case():", '    requests.Session().get("https://staging.acme.com/me")',
            "test_case()"), "missing-timeout"),
        "docstring-auth": (True, source(
            "import requests", '"""__AUTH_HEADERS__ is only documentation here."""', "def test_case():",
            '    requests.get("https://staging.acme.com/me", timeout=30)', "test_case()"),
            "missing-managed-auth"),
        "dead-auth": (True, source(
            "import requests", "def test_case():", '    requests.get("https://staging.acme.com/me", timeout=30)',
            "    if False:", '        requests.get("https://staging.acme.com/private",',
            "            headers=__AUTH_HEADERS__, timeout=30)", "test_case()"), "missing-managed-auth"),
        "shadowed-auth": (True, source(
            "import requests", "HEADERS = dict(__AUTH_HEADERS__)", "def test_case():",
            '    HEADERS = {"Accept": "application/json"}',
            '    requests.get("https://staging.acme.com/me", headers=HEADERS, timeout=30)',
            "test_case()"), "missing-managed-auth"),
        "composed-userinfo": (False, source(
            "import requests", 'SCHEME = "https://"', 'USERINFO = f"{\'agent\'}:{\'live-pass\'}@"',
            'BASE_URL = SCHEME + USERINFO + "api.acme.com"', "def test_case():",
            '    requests.get(f"{BASE_URL}/me", timeout=30)', "test_case()"), "embedded-secret"),
    }
    for name, (auth_required, body, expected) in cases.items():
        codes = {finding.code for finding in audit_source(body, auth_required, set()).errors}
        assert expected in codes, (name, expected, codes)

    positives = {
        "helper": source(
            "import requests", "def fetch():", '    return requests.get("https://staging.acme.com/me", timeout=30)',
            "def test_case():", "    assert fetch().status_code == 200", "test_case()"),
        "try": source(
            "import requests", "def test_case():", "    try:",
            '        requests.get("https://staging.acme.com/me", timeout=30)', "    finally:", "        pass",
            "test_case()"),
        "session": source(
            "import requests", "def test_case():", "    with requests.Session() as session:",
            '        session.get("https://staging.acme.com/me", timeout=30)', "test_case()"),
    }
    for name, body in positives.items():
        errors = audit_source(body, auth_required=False, allowed_modules=set()).errors
        assert not errors, (name, [(finding.code, finding.line) for finding in errors])
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
        body = args.path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"cannot read {args.path}: {exc}") from exc
    report = audit_source(body, args.auth_required, set(args.allow_module))
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
