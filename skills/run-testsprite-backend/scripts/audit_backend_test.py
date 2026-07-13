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
import math
import re
import socket
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse


HTTP_METHODS = {"delete", "get", "head", "options", "patch", "post", "put", "request"}
MUTATING_METHODS = {"__delitem__", "__setitem__", "clear", "pop", "popitem", "setdefault", "update"}
AUDITABLE_STDLIB = {
    "abc", "base64", "binascii", "calendar", "collections", "contextlib", "copy", "csv",
    "dataclasses", "datetime", "decimal", "email", "enum", "fractions", "functools", "hashlib",
    "heapq", "hmac", "html", "io", "ipaddress", "itertools", "json", "math", "pathlib",
    "random", "re", "secrets", "statistics", "string", "struct", "textwrap", "time", "typing",
    "urllib", "uuid", "zoneinfo",
}
REFLECTION_MODULES = {
    "builtins", "ctypes", "gc", "importlib", "inspect", "operator", "pkgutil", "pydoc", "runpy",
    "sys", "types", "zipimport",
}
REFLECTIVE_NAMES = {
    "__builtins__", "__import__", "__loader__", "__spec__", "compile", "delattr", "eval", "exec",
    "getattr", "globals", "locals", "setattr", "vars",
}
REFLECTIVE_ATTRIBUTES = {
    "ag_frame", "attrgetter", "cr_frame", "exec_module", "f_builtins", "f_globals", "f_locals",
    "gi_frame", "import_module", "importorskip", "load_module", "modules", "reload", "run_module",
    "tb_frame",
}
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
    request_modules: set[str] = field(default_factory=set)
    sessions: set[str] = field(default_factory=set)
    direct_methods: set[str] = field(default_factory=set)
    session_factories: set[str] = field(default_factory=set)

    def clone(self) -> "ScopeState":
        return ScopeState(
            bindings=dict(self.bindings),
            managed_auth=set(self.managed_auth),
            had_request=self.had_request,
            had_managed_request=self.had_managed_request,
            active=self.active,
            request_modules=set(self.request_modules),
            sessions=set(self.sessions),
            direct_methods=set(self.direct_methods),
            session_factories=set(self.session_factories),
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
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        template = static_string_value(node.left, bindings, visiting)
        value = static_literal_value(node.right, bindings, visiting)
        if template is None or value is None:
            return None
        try:
            rendered = template % value
        except (TypeError, ValueError, KeyError, IndexError):
            return None
        return rendered if isinstance(rendered, str) else None
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
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "format"
    ):
        template = static_string_value(node.func.value, bindings, visiting)
        if template is None:
            return None
        args = [static_literal_value(argument, bindings, visiting) for argument in node.args]
        kwargs = {
            keyword.arg: static_literal_value(keyword.value, bindings, visiting)
            for keyword in node.keywords
            if keyword.arg is not None
        }
        if any(value is None for value in args) or len(kwargs) != len(node.keywords) or any(
            value is None for value in kwargs.values()
        ):
            return None
        try:
            return template.format(*args, **kwargs)
        except (TypeError, ValueError, KeyError, IndexError, AttributeError):
            return None
    return None


def static_literal_value(
    node: ast.AST,
    bindings: dict[str, ast.AST],
    visiting: frozenset[str] = frozenset(),
) -> object | None:
    if isinstance(node, ast.Name):
        if node.id in visiting or node.id not in bindings:
            return None
        return static_literal_value(bindings[node.id], bindings, visiting | {node.id})
    string = static_string_value(node, bindings, visiting)
    if string is not None:
        return string
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
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
    if isinstance(node, ast.Call):
        return any(contains_literal_credential(child, bindings, visiting) for child in ast.iter_child_nodes(node))
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


def managed_headers_expression(
    node: ast.AST,
    aliases: set[str],
    bindings: dict[str, ast.AST],
) -> bool:
    if isinstance(node, ast.Name):
        return node.id in aliases
    if (
        isinstance(node, ast.Subscript)
        and is_globals_call(node.value)
        and "globals" not in bindings
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == "__AUTH_HEADERS__"
    ):
        return True
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and is_globals_call(node.func.value)
        and "globals" not in bindings
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "__AUTH_HEADERS__"
    ):
        return True
    if isinstance(node, ast.Dict):
        managed_unpacks = 0
        for key, value in zip(node.keys, node.values):
            if key is None:
                if not managed_headers_expression(value, aliases, bindings):
                    return False
                managed_unpacks += 1
                continue
            name = static_string_value(key, bindings)
            if name is None or name.lower() in SENSITIVE_HEADER_KEYS:
                return False
        return managed_unpacks == 1
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "dict"
        and "dict" not in bindings
    ):
        if len(node.args) != 1 or not managed_headers_expression(node.args[0], aliases, bindings):
            return False
        return all(
            keyword.arg is not None and keyword.arg.lower() not in SENSITIVE_HEADER_KEYS
            for keyword in node.keywords
        )
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "copy"
        and not node.args
        and not node.keywords
    ):
        return managed_headers_expression(node.func.value, aliases, bindings)
    return False


def managed_headers_copy(
    node: ast.AST,
    aliases: set[str],
    bindings: dict[str, ast.AST],
) -> bool:
    if isinstance(node, ast.Dict):
        return managed_headers_expression(node, aliases, bindings)
    return (
        isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id == "dict")
            or (isinstance(node.func, ast.Attribute) and node.func.attr == "copy")
        )
        and managed_headers_expression(node, aliases, bindings)
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


def request_aliases_from_bindings(
    bindings: dict[str, ast.AST],
) -> tuple[set[str], set[str], set[str], set[str]]:
    modules: set[str] = set()
    sessions: set[str] = set()
    direct_methods: set[str] = set()
    session_factories: set[str] = set()
    for local, binding in bindings.items():
        if isinstance(binding, ast.Import):
            for alias in binding.names:
                if (alias.asname or alias.name.split(".", 1)[0]) != local:
                    continue
                if alias.name == "requests" or alias.name.startswith("requests."):
                    modules.add(local)
        elif isinstance(binding, ast.ImportFrom) and binding.module and (
            binding.module == "requests" or binding.module.startswith("requests.")
        ):
            for alias in binding.names:
                if (alias.asname or alias.name) != local:
                    continue
                if alias.name.lower() in HTTP_METHODS:
                    direct_methods.add(local)
                elif alias.name == "Session":
                    session_factories.add(local)
                elif alias.name in {"api", "sessions"}:
                    modules.add(local)

    for local, value in bindings.items():
        if creates_session(value, modules, session_factories):
            sessions.add(local)
    return modules, sessions, direct_methods, session_factories


def request_aliases(tree: ast.Module) -> tuple[set[str], set[str], set[str], set[str]]:
    return request_aliases_from_bindings(broad_bindings(tree))


def scoped_request_aliases(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
    bindings: dict[str, ast.AST],
) -> tuple[set[str], set[str], set[str], set[str]]:
    modules, sessions, direct_methods, session_factories = request_aliases_from_bindings(bindings)
    current = node
    while current in parents:
        parent = parents[current]
        if isinstance(parent, (ast.With, ast.AsyncWith)) and current in parent.body:
            for item in parent.items:
                if creates_session(item.context_expr, modules, session_factories):
                    sessions.update(bound_names(item.optional_vars))
        current = parent
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


def bound_names_from_import(node: ast.Import | ast.ImportFrom) -> set[str]:
    if isinstance(node, ast.Import):
        return {alias.asname or alias.name.split(".", 1)[0] for alias in node.names}
    return {alias.asname or alias.name for alias in node.names if alias.name != "*"}


def load_request_import(state: ScopeState, node: ast.Import | ast.ImportFrom) -> None:
    if isinstance(node, ast.Import):
        for alias in node.names:
            local = alias.asname or alias.name.split(".", 1)[0]
            clear_names(state, {local})
            if alias.name == "requests" or alias.name.startswith("requests."):
                state.request_modules.add(local)
        return

    if any(alias.name == "*" for alias in node.names):
        state.request_modules.clear()
        state.sessions.clear()
        state.direct_methods.clear()
        state.session_factories.clear()
        return
    clear_names(state, bound_names_from_import(node))
    if not node.module or not (node.module == "requests" or node.module.startswith("requests.")):
        return
    for alias in node.names:
        local = alias.asname or alias.name
        if alias.name.lower() in HTTP_METHODS:
            state.direct_methods.add(local)
        elif alias.name == "Session":
            state.session_factories.add(local)
        elif alias.name in {"api", "sessions"}:
            state.request_modules.add(local)


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
        state.request_modules.discard(name)
        state.sessions.discard(name)
        state.direct_methods.discard(name)
        state.session_factories.discard(name)


def mutation_root(node: ast.AST) -> str | None:
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def assign_target(state: ScopeState, target: ast.AST, value: ast.AST | None) -> None:
    if isinstance(target, ast.Name):
        if value is None:
            clear_names(state, {target.id})
            return
        creates_runtime_session = creates_session(
            value, state.request_modules, state.session_factories
        ) or (isinstance(value, ast.Name) and value.id in state.sessions)
        managed = managed_headers_copy(value, state.managed_auth, state.bindings)
        clear_names(state, {target.id})
        state.bindings[target.id] = value
        if managed:
            state.managed_auth.add(target.id)
        if creates_runtime_session:
            state.sessions.add(target.id)
        return
    if isinstance(target, (ast.Tuple, ast.List)):
        if isinstance(value, (ast.Tuple, ast.List)) and len(target.elts) == len(value.elts):
            for child_target, child_value in zip(target.elts, value.elts):
                assign_target(state, child_target, child_value)
        else:
            clear_names(state, bound_names(target))
        return
    if isinstance(target, (ast.Attribute, ast.Subscript)):
        root = mutation_root(target)
        if root is not None:
            state.managed_auth.discard(root)
            state.request_modules.discard(root)
            state.sessions.discard(root)


def merge_states(state: ScopeState, branches: list[ScopeState]) -> None:
    state.had_request = all(branch.had_request for branch in branches)
    state.had_managed_request = all(branch.had_managed_request for branch in branches)
    state.active = all(branch.active for branch in branches)
    state.managed_auth = set.intersection(*(branch.managed_auth for branch in branches))
    state.request_modules = set.intersection(*(branch.request_modules for branch in branches))
    state.sessions = set.intersection(*(branch.sessions for branch in branches))
    state.direct_methods = set.intersection(*(branch.direct_methods for branch in branches))
    state.session_factories = set.intersection(*(branch.session_factories for branch in branches))

    shared_names = set.intersection(*(set(branch.bindings) for branch in branches))
    state.bindings = {
        name: branches[0].bindings[name]
        for name in shared_names
        if all(
            ast.dump(branch.bindings[name], include_attributes=False)
            == ast.dump(branches[0].bindings[name], include_attributes=False)
            for branch in branches[1:]
        )
    }


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


def timeout_is_bounded(
    node: ast.AST,
    bindings: dict[str, ast.AST],
    visiting: frozenset[str] = frozenset(),
) -> bool:
    if isinstance(node, ast.Name):
        if node.id in visiting or node.id not in bindings:
            return False
        return timeout_is_bounded(bindings[node.id], bindings, visiting | {node.id})
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return False

    def positive_number(candidate: object) -> bool:
        return (
            isinstance(candidate, (int, float))
            and not isinstance(candidate, bool)
            and candidate > 0
            and math.isfinite(candidate)
        )

    if positive_number(value):
        return True
    return (
        isinstance(value, (tuple, list))
        and len(value) == 2
        and all(positive_number(part) for part in value)
    )


def inspect_request_timeout(
    node: ast.Call, bindings: dict[str, ast.AST], report: Report
) -> None:
    timeout = next((keyword.value for keyword in node.keywords if keyword.arg == "timeout"), None)
    if timeout is None:
        report.error("missing-timeout", "Every HTTP request needs an explicit timeout", node.lineno)
    elif not timeout_is_bounded(timeout, bindings):
        report.error(
            "unbounded-timeout",
            "HTTP timeout must be a positive number or positive connect/read pair",
            node.lineno,
        )


def request_uses_managed_auth(node: ast.Call, state: ScopeState) -> bool:
    return any(
        keyword.arg == "headers"
        and managed_headers_expression(keyword.value, state.managed_auth, state.bindings)
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
    for call in guaranteed_calls(node, state.bindings):
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr in MUTATING_METHODS
            and (root := mutation_root(call.func.value)) is not None
        ):
            state.managed_auth.discard(root)
        if is_request_call(
            call,
            state.request_modules,
            state.sessions,
            state.direct_methods,
            state.session_factories,
        ):
            state.had_request = True
            if not request_evaluation_is_safe(call, state):
                report.error(
                    "unsafe-request-expression",
                    "HTTP request receivers and arguments must stay inside the safe expression subset",
                    call.lineno,
                )
            if request_uses_managed_auth(call, state):
                state.had_managed_request = True
            inspect_request_credentials(call, state, report)
            inspect_request_timeout(call, state.bindings, report)
            inspect_request_target(call, state.bindings, report)
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
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            load_request_import(state, statement)
            continue
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
            if statement.handlers:
                normal = state.clone()
                analyze_block(statement.body, normal, module_state, functions, request_sets, report, visiting)
                if normal.active:
                    analyze_block(
                        statement.orelse, normal, module_state, functions, request_sets, report, visiting
                    )
                branches = [normal]
                for handler in statement.handlers:
                    handled = state.clone()
                    if handler.name:
                        clear_names(handled, {handler.name})
                    analyze_block(
                        handler.body, handled, module_state, functions, request_sets, report, visiting
                    )
                    branches.append(handled)
                merge_states(state, branches)
            else:
                analyze_block(statement.body, state, module_state, functions, request_sets, report, visiting)
                if state.active:
                    analyze_block(
                        statement.orelse, state, module_state, functions, request_sets, report, visiting
                    )
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
                if item.optional_vars is not None:
                    assign_target(state, item.optional_vars, item.context_expr)
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
            for target in statement.targets:
                assign_target(state, target, None)
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


def direct_request_call(statement: ast.stmt, state: ScopeState) -> ast.Call | None:
    value: ast.AST | None = None
    if isinstance(statement, ast.Expr):
        value = statement.value
    elif isinstance(statement, ast.Assign):
        value = statement.value
    elif isinstance(statement, ast.AnnAssign):
        value = statement.value
    elif isinstance(statement, ast.Return):
        value = statement.value
    if not isinstance(value, ast.Call):
        return None
    if not is_request_call(
        value,
        state.request_modules,
        state.sessions,
        state.direct_methods,
        state.session_factories,
    ):
        return None
    return value if request_evaluation_is_safe(value, state) else None


def safe_setup_expression(node: ast.AST, state: ScopeState) -> bool:
    forbidden = (ast.Await, ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
                 ast.NamedExpr, ast.Yield, ast.YieldFrom)
    if isinstance(node, forbidden):
        return False
    if isinstance(node, ast.Call):
        if creates_session(node, state.request_modules, state.session_factories):
            return all(safe_setup_expression(child, state) for child in [*node.args, *(k.value for k in node.keywords)])
        if isinstance(node.func, ast.Name) and node.func.id in {"bool", "dict", "float", "int", "list", "set", "str", "tuple"}:
            if node.func.id in state.bindings:
                return False
            return all(safe_setup_expression(child, state) for child in [*node.args, *(k.value for k in node.keywords)])
        if is_globals_call(node):
            return "globals" not in state.bindings
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and is_globals_call(node.func.value)
        ):
            return "globals" not in state.bindings and all(
                safe_setup_expression(child, state)
                for child in [*node.args, *(k.value for k in node.keywords)]
            )
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "format"
            and static_string_value(node.func.value, state.bindings) is not None
        ):
            return all(safe_setup_expression(child, state) for child in [*node.args, *(k.value for k in node.keywords)])
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "copy"
            and managed_headers_expression(node.func.value, state.managed_auth, state.bindings)
        ):
            return (
                not node.args
                and not node.keywords
                and safe_setup_expression(node.func.value, state)
            )
        return False
    return all(safe_setup_expression(child, state) for child in ast.iter_child_nodes(node))


def request_evaluation_is_safe(node: ast.Call, state: ScopeState) -> bool:
    evaluated = [*node.args, *(keyword.value for keyword in node.keywords)]
    if isinstance(node.func, ast.Attribute):
        evaluated.append(node.func.value)
    return all(safe_setup_expression(value, state) for value in evaluated)


def function_has_direct_request_prefix(function: ast.FunctionDef, module_state: ScopeState) -> bool:
    state = module_state.clone()
    clear_names(state, local_binding_names(function))
    for statement in function.body:
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            load_request_import(state, statement)
            for name in bound_names_from_import(statement):
                state.bindings[name] = statement
            continue
        if direct_request_call(statement, state) is not None:
            return True
        if isinstance(statement, ast.Pass):
            continue
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
            continue
        if isinstance(statement, ast.Assert):
            if any(isinstance(node, (ast.Call, ast.Await, ast.Yield, ast.YieldFrom)) for node in ast.walk(statement)):
                return False
            continue
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            value = statement.value
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            if value is None or not all(isinstance(target, (ast.Name, ast.Tuple, ast.List)) for target in targets):
                return False
            if not safe_setup_expression(value, state):
                return False
            for target in targets:
                assign_target(state, target, value)
            continue
        if isinstance(statement, ast.With) and len(statement.items) == 1:
            item = statement.items[0]
            if item.optional_vars is None or not creates_session(
                item.context_expr, state.request_modules, state.session_factories
            ) or not safe_setup_expression(item.context_expr, state):
                return False
            nested = state.clone()
            assign_target(nested, item.optional_vars, item.context_expr)
            return function_body_has_direct_request_prefix(statement.body, nested)
        return False
    return False


def function_body_has_direct_request_prefix(statements: list[ast.stmt], state: ScopeState) -> bool:
    wrapper = ast.FunctionDef(
        name="_prefix",
        args=ast.arguments(
            posonlyargs=[], args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]
        ),
        body=statements,
        decorator_list=[],
    )
    return function_has_direct_request_prefix(wrapper, state)


def static_default_is_safe(
    node: ast.AST,
    bindings: dict[str, ast.AST],
    visiting: frozenset[str] = frozenset(),
) -> bool:
    if isinstance(node, ast.Name):
        if node.id in visiting or node.id not in bindings:
            return False
        return static_default_is_safe(bindings[node.id], bindings, visiting | {node.id})
    if isinstance(node, ast.Constant):
        return True
    if static_string_value(node, bindings, visiting) is not None:
        return True
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(static_default_is_safe(element, bindings, visiting) for element in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            (key is None or static_default_is_safe(key, bindings, visiting))
            and static_default_is_safe(value, bindings, visiting)
            for key, value in zip(node.keys, node.values)
        )
    try:
        ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return False
    return True


def import_binding_root(name: str, bindings: dict[str, ast.AST]) -> tuple[str, str | None] | None:
    binding = bindings.get(name)
    if isinstance(binding, ast.Import):
        for alias in binding.names:
            if (alias.asname or alias.name.split(".", 1)[0]) == name:
                return alias.name.split(".", 1)[0], None
    if isinstance(binding, ast.ImportFrom) and binding.module:
        for alias in binding.names:
            if (alias.asname or alias.name) == name:
                return binding.module.split(".", 1)[0], alias.name
    return None


def runtime_annotation_is_safe(node: ast.AST, state: ScopeState) -> bool:
    builtin_types = {
        "BaseException", "Exception", "None", "bool", "bytearray", "bytes", "complex", "dict",
        "float", "frozenset", "int", "list", "memoryview", "object", "set", "str", "tuple", "type",
    }
    if isinstance(node, ast.Constant):
        return node.value is None or node.value is Ellipsis or isinstance(node.value, str)
    if isinstance(node, ast.Name):
        if node.id in builtin_types:
            return True
        imported = import_binding_root(node.id, state.bindings)
        return imported is not None and (
            imported[0] in AUDITABLE_STDLIB
            or (imported[0] == "requests" and imported[1] == "Response")
        )
    if isinstance(node, ast.Attribute):
        root = dotted_root(node)
        if root in state.request_modules:
            return node.attr == "Response"
        imported = import_binding_root(root or "", state.bindings)
        return (
            imported is not None
            and imported[0] in AUDITABLE_STDLIB
            and not node.attr.startswith("_")
        )
    if isinstance(node, ast.Subscript):
        return runtime_annotation_is_safe(node.value, state) and runtime_annotation_is_safe(
            node.slice, state
        )
    if isinstance(node, (ast.Tuple, ast.List)):
        return all(runtime_annotation_is_safe(element, state) for element in node.elts)
    return False


def function_definition_is_safe(
    function: ast.FunctionDef,
    state: ScopeState,
    future_annotations: bool,
) -> bool:
    defaults = [*function.args.defaults, *(value for value in function.args.kw_defaults if value is not None)]
    if any(not static_default_is_safe(value, state.bindings) for value in defaults):
        return False
    if future_annotations:
        return True
    annotations = [
        function.returns,
        *(argument.annotation for argument in [
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        ]),
    ]
    return all(
        annotation is None or runtime_annotation_is_safe(annotation, state)
        for annotation in annotations
    )


def validate_constrained_subset(
    tree: ast.Module,
    tests: set[str],
    request_sets: tuple[set[str], set[str], set[str], set[str]],
    report: Report,
) -> None:
    state = ScopeState()
    available: dict[str, ast.FunctionDef] = {}
    seen_functions: set[str] = set()
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    module_bindings = broad_bindings(tree)
    future_annotations = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in tree.body
    )

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if node.name in seen_functions:
                report.error(
                    "duplicate-function",
                    f"Duplicate function definition {node.name!r} is outside the auditable subset",
                    node.lineno,
                )
            seen_functions.add(node.name)
            if any(isinstance(child, (ast.Yield, ast.YieldFrom)) for child in ast.walk(node)):
                report.error(
                    "generator-function",
                    "Generator functions are not executed by a direct top-level call",
                    node.lineno,
                )
            if not function_definition_is_safe(node, state, future_annotations):
                report.error(
                    "unsafe-function-definition",
                    "Function defaults and annotations must be side-effect-free static expressions",
                    node.lineno,
                )
            helper_has_request = False
            if not node.name.startswith("test_"):
                for child in ast.walk(node):
                    if not isinstance(child, ast.Call):
                        continue
                    child_bindings = scoped_bindings(child, parents, module_bindings)
                    child_sets = scoped_request_aliases(child, parents, child_bindings)
                    if is_request_call(child, *child_sets):
                        helper_has_request = True
                        break
            if helper_has_request:
                report.error(
                    "request-helper-unsupported",
                    "HTTP requests must be issued directly by test_* functions",
                    node.lineno,
                )
            clear_names(state, {node.name})
            state.bindings[node.name] = node
            available[node.name] = node
            continue

        called = direct_test_call(node, tests)
        if called is not None:
            function = available.get(called)
            if function is None:
                report.error(
                    "invalid-test-call",
                    f"{called}() does not resolve to its original function at this call site",
                    node.lineno,
                )
            elif not function_has_direct_request_prefix(function, state):
                report.error(
                    "unproven-request",
                    f"{called}() must issue a direct eager HTTP request before dynamic control flow",
                    function.lineno,
                )
            continue

        if isinstance(node, (ast.Import, ast.ImportFrom)):
            load_request_import(state, node)
            for name in bound_names_from_import(node):
                state.bindings[name] = node
                available.pop(name, None)
            continue

        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if (
                value is None
                or not all(isinstance(target, (ast.Name, ast.Tuple, ast.List)) for target in targets)
                or not safe_setup_expression(value, state)
                or (
                    isinstance(node, ast.AnnAssign)
                    and not future_annotations
                    and not runtime_annotation_is_safe(node.annotation, state)
                )
            ):
                report.error(
                    "unsafe-module-setup",
                    "Module setup must use side-effect-free assignments to plain names",
                    node.lineno,
                )
                continue
            for target in targets:
                assign_target(state, target, value)
                for name in bound_names(target):
                    available.pop(name, None)
            continue

        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue

        report.error(
            "unsupported-top-level",
            "Only imports, static assignments, function definitions, and direct test_* calls are auditable",
            node.lineno,
        )


def direct_bindings(statements: list[ast.stmt]) -> dict[str, ast.AST]:
    bindings: dict[str, ast.AST] = {}
    ambiguous: set[str] = set()

    def record(name: str, value: ast.AST) -> None:
        if name in bindings or name in ambiguous:
            bindings.pop(name, None)
            ambiguous.add(name)
            return
        bindings[name] = value

    for node in statements:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            targets, value = [], None
        if value is not None:
            for target in targets:
                if isinstance(target, ast.Name):
                    record(target.id, value)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            record(node.name, node)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for name in bound_names_from_import(node):
                record(name, node)
    return bindings


def broad_bindings(tree: ast.Module) -> dict[str, ast.AST]:
    """Return unambiguous module bindings only; never mix function-local scopes."""
    return direct_bindings(tree.body)


def enclosing_function_body(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    current = node
    while current in parents:
        parent = parents[current]
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return parent if current in parent.body else None
        current = parent
    return None


def scoped_bindings(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
    module_bindings: dict[str, ast.AST],
) -> dict[str, ast.AST]:
    bindings = dict(module_bindings)
    function = enclosing_function_body(node, parents)
    if function is None:
        return bindings

    for name in local_binding_names(function):
        bindings.pop(name, None)
    line = getattr(node, "lineno", 0)
    earlier = [
        statement
        for statement in function.body
        if getattr(statement, "lineno", line) < line
    ]
    bindings.update(direct_bindings(earlier))
    return bindings


def broad_managed_auth(bindings: dict[str, ast.AST]) -> set[str]:
    managed = {"__AUTH_HEADERS__"}
    while True:
        expanded = managed | {
            name
            for name, value in bindings.items()
            if managed_headers_copy(value, managed, bindings)
        }
        if expanded == managed:
            return managed
        managed = expanded


def validate_immutable_transport(
    tree: ast.Module,
    request_sets: tuple[set[str], set[str], set[str], set[str]],
    report: Report,
) -> None:
    modules, sessions, direct_methods, session_factories = request_sets
    transport_names = modules | sessions | direct_methods | session_factories
    module_bindings = broad_bindings(tree)
    bindings = module_bindings
    managed = broad_managed_auth(bindings)
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    annotation_roots = {
        annotation
        for node in ast.walk(tree)
        for annotation in (
            [node.annotation]
            if isinstance(node, ast.AnnAssign)
            else [
                node.returns,
                *(argument.annotation for argument in [
                    *node.args.posonlyargs,
                    *node.args.args,
                    *node.args.kwonlyargs,
                ]),
            ]
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            else []
        )
        if annotation is not None
    }

    def target_uses_transport(target: ast.AST) -> bool:
        return any(isinstance(child, ast.Name) and child.id in transport_names for child in ast.walk(target))

    def expression_uses_names(value: ast.AST | None, names: set[str]) -> bool:
        return value is not None and any(
            isinstance(child, ast.Name) and child.id in names for child in ast.walk(value)
        )

    def report_transport(line: int) -> None:
        report.error(
            "transport-mutation",
            "Request modules, methods, and Session instances are immutable in backend tests",
            line,
        )

    def is_within_annotation(node: ast.AST) -> bool:
        current = node
        while current in parents:
            current = parents[current]
            if current in annotation_roots:
                return True
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.AnnAssign)):
                return False
        return False

    def is_safe_response_annotation(node: ast.Name) -> bool:
        parent = parents.get(node)
        return (
            node.id in modules
            and isinstance(parent, ast.Attribute)
            and parent.value is node
            and parent.attr == "Response"
            and is_within_annotation(node)
        )

    def is_verified_transport_receiver(node: ast.Name) -> bool:
        current: ast.AST = node
        parent = parents.get(current)
        while isinstance(parent, ast.Attribute) and parent.value is current:
            current = parent
            parent = parents.get(current)
        if not isinstance(parent, ast.Call) or parent.func is not current:
            return False
        if is_request_call(parent, modules, sessions, direct_methods, session_factories):
            return True
        if not creates_session(parent, modules, session_factories):
            return False
        container = parents.get(parent)
        if isinstance(container, ast.Assign) and container.value is parent:
            return all(isinstance(target, ast.Name) for target in container.targets)
        if isinstance(container, ast.AnnAssign) and container.value is parent:
            return isinstance(container.target, ast.Name)
        if isinstance(container, ast.withitem) and container.context_expr is parent:
            return container.optional_vars is not None
        if isinstance(container, ast.Attribute) and container.value is parent:
            request = parents.get(container)
            return (
                isinstance(request, ast.Call)
                and request.func is container
                and is_request_call(request, modules, sessions, direct_methods, session_factories)
            )
        return False

    def is_verified_managed_use(node: ast.AST) -> bool:
        current: ast.AST = node
        while current in parents:
            parent = parents[current]
            if isinstance(parent, ast.keyword):
                call = parents.get(parent)
                return (
                    parent.arg == "headers"
                    and isinstance(call, ast.Call)
                    and is_request_call(call, modules, sessions, direct_methods, session_factories)
                    and managed_headers_expression(parent.value, managed, bindings)
                )
            if isinstance(parent, (ast.Assign, ast.AnnAssign)):
                value = parent.value
                return value is not None and managed_headers_copy(value, managed, bindings)
            if isinstance(parent, ast.stmt):
                return False
            current = parent
        return False

    def is_managed_globals_lookup(node: ast.Call) -> bool:
        if not is_globals_call(node) or "globals" in bindings:
            return False
        parent = parents.get(node)
        if isinstance(parent, ast.Attribute) and parent.value is node and parent.attr == "get":
            call = parents.get(parent)
            return (
                isinstance(call, ast.Call)
                and call.func is parent
                and bool(call.args)
                and static_string_value(call.args[0], bindings) == "__AUTH_HEADERS__"
                and is_verified_managed_use(node)
            )
        return (
            isinstance(parent, ast.Subscript)
            and parent.value is node
            and static_string_value(parent.slice, bindings) == "__AUTH_HEADERS__"
            and is_verified_managed_use(node)
        )

    def looks_like_untracked_http_call(node: ast.Call) -> bool:
        if not isinstance(node.func, ast.Attribute) or node.func.attr.lower() not in HTTP_METHODS:
            return False
        if is_request_call(node, modules, sessions, direct_methods, session_factories):
            return False
        if any(isinstance(argument, ast.Starred) for argument in node.args) or any(
            keyword.arg is None for keyword in node.keywords
        ):
            return True
        request_keywords = {"auth", "cookies", "data", "files", "headers", "json", "params", "timeout", "url"}
        if any(keyword.arg in request_keywords for keyword in node.keywords):
            return True
        url_index = 1 if node.func.attr.lower() == "request" else 0
        if len(node.args) <= url_index:
            return False
        prefix = static_url_prefix(node.args[url_index], bindings)
        return prefix is not None and prefix.lstrip().lower().startswith(("http://", "https://"))

    def is_safe_type_name_attribute(node: ast.Attribute) -> bool:
        return (
            node.attr == "__name__"
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "type"
            and "type" not in bindings
            and len(node.value.args) == 1
            and not node.value.keywords
        )

    for node in ast.walk(tree):
        bindings = scoped_bindings(node, parents, module_bindings)
        managed = broad_managed_auth(bindings)
        modules, sessions, direct_methods, session_factories = scoped_request_aliases(
            node, parents, bindings
        )
        transport_names = modules | sessions | direct_methods | session_factories
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            parent = parents.get(node)
            managed_globals = (
                node.id == "globals"
                and isinstance(parent, ast.Call)
                and parent.func is node
                and is_managed_globals_lookup(parent)
            )
            if node.id in REFLECTIVE_NAMES and not managed_globals:
                report.error(
                    "dynamic-reflection",
                    "Dynamic module and object lookup is outside the auditable backend-test subset",
                    node.lineno,
                )
            if (
                node.id in transport_names
                and not is_verified_transport_receiver(node)
                and not is_safe_response_annotation(node)
            ):
                report.error(
                    "transport-escape",
                    "Transport references are allowed only as verified HTTP receivers or Session constructors",
                    node.lineno,
                )
            if node.id in managed and not is_verified_managed_use(node):
                report.error(
                    "managed-auth-alias",
                    "Managed headers are allowed only in verified request headers or independent copies",
                    node.lineno,
                )

        if isinstance(node, ast.Attribute) and (
            (
                node.attr.startswith("_")
                and not is_safe_type_name_attribute(node)
            )
            or node.attr in REFLECTIVE_ATTRIBUTES
        ):
            report.error(
                "dynamic-reflection",
                "Dynamic module and object lookup is outside the auditable backend-test subset",
                node.lineno,
            )

        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        elif isinstance(node, ast.AugAssign):
            targets, value = [node.target], node.value
        else:
            targets, value = [], None

        if targets:
            session_creation = value is not None and creates_session(value, modules, session_factories)
            request_result = isinstance(value, ast.Call) and is_request_call(
                value, modules, sessions, direct_methods, session_factories
            )
            plain_session_binding = session_creation and all(isinstance(target, ast.Name) for target in targets)
            for target in targets:
                names = bound_names(target)
                if names & transport_names and not session_creation:
                    report_transport(node.lineno)
                if isinstance(target, (ast.Attribute, ast.Subscript)) and target_uses_transport(target):
                    report_transport(node.lineno)
                root = mutation_root(target)
                if root in managed and (
                    isinstance(node, ast.AugAssign) or isinstance(target, (ast.Attribute, ast.Subscript))
                ):
                    report.error(
                        "managed-auth-mutation",
                        "Managed header dictionaries are immutable; construct a fresh copy",
                        node.lineno,
                    )
            if expression_uses_names(value, transport_names) and not (
                request_result or plain_session_binding
            ):
                report.error(
                    "transport-alias",
                    "Transport objects cannot be returned, nested, or assigned through aliases",
                    node.lineno,
                )
            if expression_uses_names(value, managed) and not (
                request_result
                or (value is not None and managed_headers_copy(value, managed, bindings))
            ):
                report.error(
                    "managed-auth-alias",
                    "Managed headers may only be assigned through a verified independent copy",
                    node.lineno,
                )
            if isinstance(value, ast.Name) and value.id in transport_names:
                report.error(
                    "transport-alias",
                    "Do not alias mutable request modules, methods, or Session instances",
                    node.lineno,
                )
            if isinstance(value, ast.Name) and value.id in managed:
                report.error(
                    "managed-auth-alias",
                    "Do not create shared aliases of managed header dictionaries",
                    node.lineno,
                )

        if isinstance(node, ast.Return) and node.value is not None:
            request_result = isinstance(node.value, ast.Call) and is_request_call(
                node.value, modules, sessions, direct_methods, session_factories
            )
            if not request_result and (
                expression_uses_names(node.value, transport_names)
                or creates_session(node.value, modules, session_factories)
            ):
                report.error(
                    "transport-escape",
                    "Transport objects and Session instances cannot escape through return values",
                    node.lineno,
                )
            if not request_result and expression_uses_names(node.value, managed):
                report.error(
                    "managed-auth-alias",
                    "Managed header values cannot escape through return values",
                    node.lineno,
                )

        if isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
            line = getattr(node, "lineno", node.target.lineno)
            if bound_names(node.target) & transport_names:
                report_transport(line)
            if expression_uses_names(node.iter, transport_names):
                report.error(
                    "transport-alias",
                    "Loop and comprehension binders cannot receive transport objects",
                    line,
                )
            if expression_uses_names(node.iter, managed):
                report.error(
                    "managed-auth-alias",
                    "Loop and comprehension binders cannot receive managed headers",
                    line,
                )

        if isinstance(node, ast.NamedExpr):
            if bound_names(node.target) & transport_names:
                report_transport(node.lineno)
            if expression_uses_names(node.value, transport_names):
                report.error(
                    "transport-alias",
                    "Named expressions cannot alias transport objects",
                    node.lineno,
                )
            if expression_uses_names(node.value, managed):
                report.error(
                    "managed-auth-alias",
                    "Named expressions cannot alias managed headers",
                    node.lineno,
                )

        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars is None:
                    continue
                session_creation = creates_session(item.context_expr, modules, session_factories)
                if bound_names(item.optional_vars) & transport_names and not session_creation:
                    report_transport(node.lineno)
                if expression_uses_names(item.context_expr, transport_names) and not session_creation:
                    report.error(
                        "transport-alias",
                        "Context managers cannot alias transport objects",
                        node.lineno,
                    )
                if expression_uses_names(item.context_expr, managed):
                    report.error(
                        "managed-auth-alias",
                        "Context managers cannot alias managed headers",
                        node.lineno,
                    )

        if isinstance(node, ast.ExceptHandler) and node.name in transport_names:
            report_transport(node.lineno)

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in transport_names:
            report_transport(node.lineno)

        if isinstance(node, (ast.Import, ast.ImportFrom)):
            trusted: set[str] = set()
            if isinstance(node, ast.Import):
                trusted = {
                    alias.asname or alias.name.split(".", 1)[0]
                    for alias in node.names
                    if alias.name == "requests" or alias.name.startswith("requests.")
                }
            elif node.module and (node.module == "requests" or node.module.startswith("requests.")):
                trusted = {
                    alias.asname or alias.name
                    for alias in node.names
                    if alias.name.lower() in HTTP_METHODS
                    or alias.name in {"Session", "api", "sessions"}
                }
            if (bound_names_from_import(node) - trusted) & transport_names:
                report_transport(node.lineno)

        if isinstance(node, ast.Delete):
            for target in node.targets:
                if bound_names(target) & transport_names or target_uses_transport(target):
                    report_transport(node.lineno)
                root = mutation_root(target)
                if root in managed:
                    report.error(
                        "managed-auth-mutation",
                        "Managed header dictionaries are immutable; construct a fresh copy",
                        node.lineno,
                    )

        if not isinstance(node, ast.Call):
            continue
        reflective_name = node.func.id if isinstance(node.func, ast.Name) else None
        reflective_attr = node.func.attr if isinstance(node.func, ast.Attribute) else None
        if (
            reflective_name in REFLECTIVE_NAMES
            or reflective_attr in REFLECTIVE_NAMES | REFLECTIVE_ATTRIBUTES
        ) and not is_managed_globals_lookup(node):
            report.error(
                "dynamic-reflection",
                "Dynamic module and object lookup is outside the auditable backend-test subset",
                node.lineno,
            )
        if looks_like_untracked_http_call(node):
            report.error(
                "untracked-http-call",
                "HTTP-like calls must use a statically verified requests module, method, or Session",
                node.lineno,
            )
        if isinstance(node.func, ast.Attribute):
            root = mutation_root(node.func.value)
            if node.func.attr in MUTATING_METHODS and root in transport_names:
                report_transport(node.lineno)
            if node.func.attr in MUTATING_METHODS and root in managed:
                report.error(
                    "managed-auth-mutation",
                    "Managed header dictionaries are immutable; construct a fresh copy",
                    node.lineno,
                )
            if root in sessions and not is_request_call(
                node, modules, sessions, direct_methods, session_factories
            ):
                report_transport(node.lineno)
        if is_request_call(node, modules, sessions, direct_methods, session_factories) or creates_session(
            node, modules, session_factories
        ):
            continue
        if any(
            isinstance(child, ast.Name) and child.id in transport_names
            for argument in [*node.args, *(keyword.value for keyword in node.keywords)]
            for child in ast.walk(argument)
        ):
            report.error(
                "transport-escape",
                "Do not pass request modules, methods, or Session instances to helper calls",
                node.lineno,
            )


def canonical_hostname(value: str) -> str | None:
    value = value.lower()
    if not value or any(character.isspace() for character in value) or "\\" in value:
        return None
    try:
        value = value.encode("idna").decode("ascii").lower().rstrip(".")
    except UnicodeError:
        return None
    return value or None


def hostname_ip_address(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        pass
    if not re.fullmatch(r"[0-9a-fx.]+", host, re.I):
        return None
    try:
        return ipaddress.ip_address(socket.inet_aton(host))
    except (OSError, ValueError):
        return None


def inspect_url(value: str, line: int, report: Report) -> None:
    value = value.lstrip()
    if not value.lower().startswith(("http://", "https://")):
        return
    parsed = urlparse(value)
    try:
        username, password, hostname, _port = parsed.username, parsed.password, parsed.hostname, parsed.port
    except ValueError:
        report.error("invalid-target", "URL target is malformed", line)
        return
    if username is not None or password is not None:
        report.error("embedded-secret", "URL contains credential userinfo; use managed credentials", line)
    host = canonical_hostname(hostname or "")
    if host is None:
        report.error("invalid-target", "URL target has no valid hostname", line)
        return
    private_suffixes = (
        ".home",
        ".home.arpa",
        ".internal",
        ".lan",
        ".local",
        ".localdomain",
        ".localhost",
    )
    if host in {"home.arpa", "localhost"} or host.endswith(private_suffixes):
        report.error("private-target", "TestSprite cloud cannot reach this local/private target", line)
        return
    address = hostname_ip_address(host)
    if address is not None and not address.is_global:
        report.error("private-target", "TestSprite cloud cannot reach this non-global IP target", line)
        return
    if address is None and "." not in host:
        report.error("private-target", "TestSprite cloud requires a public fully qualified hostname", line)
        return
    reserved = host in {"example.com", "example.net", "example.org"} or host.endswith(
        (".example.com", ".example.net", ".example.org")
    )
    if reserved or host.endswith((".example", ".invalid", ".test")):
        report.error("placeholder-target", "Replace the placeholder URL before creating the test", line)


def static_url_prefix(
    node: ast.AST,
    bindings: dict[str, ast.AST],
    visiting: frozenset[str] = frozenset(),
) -> str | None:
    complete = static_string_value(node, bindings, visiting)
    if complete is not None:
        return complete
    if isinstance(node, ast.Name):
        if node.id in visiting or node.id not in bindings:
            return None
        return static_url_prefix(bindings[node.id], bindings, visiting | {node.id})
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                parts.append(part.value)
                continue
            if isinstance(part, ast.FormattedValue):
                value = static_string_value(part.value, bindings, visiting)
                if value is not None:
                    parts.append(value)
                    continue
            break
        prefix = "".join(parts)
        return prefix or None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = static_url_prefix(node.left, bindings, visiting)
        if left is None:
            return None
        right = static_string_value(node.right, bindings, visiting)
        return left + right if right is not None else left
    return None


def request_method_name(node: ast.Call, bindings: dict[str, ast.AST]) -> str:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    binding = bindings.get(node.func.id)
    if isinstance(binding, ast.ImportFrom) and binding.module and (
        binding.module == "requests" or binding.module.startswith("requests.")
    ):
        for alias in binding.names:
            if (alias.asname or alias.name) == node.func.id:
                return alias.name
    return node.func.id


def request_url_node(node: ast.Call, bindings: dict[str, ast.AST]) -> ast.AST | None:
    keyword = next((item.value for item in node.keywords if item.arg == "url"), None)
    if keyword is not None:
        return keyword
    method = request_method_name(node, bindings)
    index = 1 if method.lower() == "request" else 0
    return node.args[index] if len(node.args) > index else None


def inspect_request_target(
    node: ast.Call, bindings: dict[str, ast.AST], report: Report
) -> None:
    target = request_url_node(node, bindings)
    complete = static_string_value(target, bindings) if target is not None else None
    prefix = static_url_prefix(target, bindings) if target is not None else None
    if prefix is None:
        report.error(
            "unresolved-target",
            "HTTP target must expose a statically verifiable public URL prefix",
            node.lineno,
        )
        return
    if not prefix.lstrip().lower().startswith(("http://", "https://")):
        report.error("invalid-target", "HTTP target must use http:// or https://", node.lineno)
        return
    normalized = prefix.lstrip()
    try:
        host = urlparse(normalized).hostname
    except ValueError:
        host = None
    authority_tail = normalized.split("://", 1)[1]
    if host is None or (complete is None and not any(mark in authority_tail for mark in "/?#")):
        report.error(
            "unresolved-target",
            "Dynamic HTTP targets must expose a complete static hostname and authority boundary",
            node.lineno,
        )
        return
    inspect_url(prefix, node.lineno, report)


def audit_source(source: str, auth_required: bool, allowed_modules: set[str]) -> Report:
    report = Report()
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        report.error("syntax", exc.msg, exc.lineno)
        return report

    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not isinstance(
            parents.get(node), ast.Module
        ):
            report.error(
                "nested-definition",
                "Nested functions and classes are outside the auditable backend-test subset",
                node.lineno,
            )
        if isinstance(node, ast.Lambda):
            report.error(
                "nested-definition",
                "Lambda functions are outside the auditable backend-test subset",
                node.lineno,
            )
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            report.error(
                "scope-mutation",
                "Global and nonlocal rebinding is outside the auditable backend-test subset",
                node.lineno,
            )

    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    tests = {name: node for name, node in functions.items() if name.startswith("test_")}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.decorator_list:
            report.error(
                "decorated-function",
                "Decorated functions are not statically auditable; use an explicit direct call",
                node.lineno,
            )
        if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith("test_"):
            report.error("async-test", "Async test functions cannot be called synchronously", node.lineno)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            positional = [*node.args.posonlyargs, *node.args.args]
            if positional or node.args.kwonlyargs or node.args.vararg or node.args.kwarg:
                report.error(
                    "test-parameters",
                    "Top-level test functions must be synchronous and zero-argument",
                    node.lineno,
                )
    if not tests:
        report.error("no-tests", "Define at least one top-level test_* function")

    permitted = SUPPORTED_THIRD_PARTY | AUDITABLE_STDLIB | allowed_modules | {"__future__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
            report.error(
                "wildcard-import",
                "Wildcard imports make request provenance ambiguous; import explicit names",
                node.lineno,
            )
        if isinstance(node, ast.Import) and any(
            alias.name == "urllib.request" or alias.name.startswith("urllib.request.")
            for alias in node.names
        ):
            report.error(
                "unsupported-import",
                "Use requests for HTTP; only urllib.parse is in the auditable urllib subset",
                node.lineno,
            )
        if isinstance(node, ast.ImportFrom) and node.module and (
            node.module == "urllib.request"
            or node.module.startswith("urllib.request.")
            or (
                node.module == "urllib"
                and any(alias.name != "parse" for alias in node.names)
            )
        ):
            report.error(
                "unsupported-import",
                "Use requests for HTTP; only urllib.parse is in the auditable urllib subset",
                node.lineno,
            )
    for root, line in imported_roots(tree):
        if root in REFLECTION_MODULES:
            report.error(
                "dynamic-reflection",
                f"Module {root!r} exposes runtime reflection outside the auditable subset",
                line,
            )
            continue
        if root not in permitted:
            report.error(
                "unsupported-import",
                f"Module {root!r} is outside the auditable import subset; verify it before --allow-module",
                line,
            )

    request_sets = request_aliases(tree)
    validate_constrained_subset(tree, set(tests), request_sets, report)
    validate_immutable_transport(tree, request_sets, report)
    test_runs: dict[str, list[ScopeState]] = {name: [] for name in tests}
    module_state = ScopeState()
    available_functions: dict[str, ast.FunctionDef] = {}
    for statement in tree.body:
        if isinstance(statement, ast.FunctionDef):
            clear_names(module_state, {statement.name})
            available_functions[statement.name] = statement
        called_test = direct_test_call(statement, set(tests))
        if called_test is not None:
            if called_test not in available_functions:
                report.error(
                    "invalid-test-call",
                    f"{called_test}() does not resolve to its original function at this call site",
                    statement.lineno,
                )
                continue
            test_runs[called_test].append(
                analyze_function(
                    available_functions[called_test],
                    module_state.clone(),
                    dict(available_functions),
                    request_sets,
                    report,
                    frozenset(),
                )
            )
        elif isinstance(statement, (ast.Import, ast.ImportFrom)):
            load_request_import(module_state, statement)
            for name in bound_names_from_import(statement):
                module_state.bindings[name] = statement
                available_functions.pop(name, None)
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                assign_target(module_state, target, statement.value)
                for name in bound_names(target):
                    available_functions.pop(name, None)
        elif isinstance(statement, ast.AnnAssign):
            assign_target(module_state, statement.target, statement.value)
            for name in bound_names(statement.target):
                available_functions.pop(name, None)
        elif isinstance(statement, (ast.AsyncFunctionDef, ast.ClassDef)):
            clear_names(module_state, {statement.name})
            available_functions.pop(statement.name, None)

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
    module_bindings = broad_bindings(tree)
    inspected_strings: set[str] = set()
    for node in ast.walk(tree):
        bindings = scoped_bindings(node, parents, module_bindings)
        modules, sessions, direct_methods, session_factories = scoped_request_aliases(
            node, parents, bindings
        )
        broad_state = ScopeState(
            bindings=bindings,
            managed_auth=broad_managed_auth(bindings),
            request_modules=set(modules),
            sessions=set(sessions),
            direct_methods=set(direct_methods),
            session_factories=set(session_factories),
        )
        static_value = static_string_value(node, bindings)
        if static_value is not None and static_value not in inspected_strings:
            inspected_strings.add(static_value)
            if static_value.strip().lower() not in {"http://", "https://"}:
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
                    if (
                        isinstance(target, ast.Attribute)
                        and target.attr.lower() in {*SENSITIVE_REQUEST_KWARGS, "authorization", "cookie"}
                    ):
                        report.error(
                            "embedded-secret",
                            "Literal credential assigned to request/session state; use managed credentials",
                            node.lineno,
                        )

        if isinstance(node, ast.Dict) and sensitive_headers_contain_literal(node, bindings):
            report.error(
                "embedded-secret",
                "Literal authentication/cookie header found; use managed credentials",
                node.lineno,
            )

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"setdefault", "update"}:
                for keyword in node.keywords:
                    if (
                        keyword.arg is not None
                        and keyword.arg.lower() in SENSITIVE_HEADER_KEYS
                        and contains_literal_credential(keyword.value, bindings)
                    ):
                        report.error(
                            "embedded-secret",
                            "Literal authentication/cookie header found; use managed credentials",
                            node.lineno,
                        )
                if (
                    node.func.attr == "setdefault"
                    and len(node.args) >= 2
                    and (key := static_string_value(node.args[0], bindings)) is not None
                    and key.lower() in SENSITIVE_HEADER_KEYS
                    and contains_literal_credential(node.args[1], bindings)
                ):
                    report.error(
                        "embedded-secret",
                        "Literal authentication/cookie header found; use managed credentials",
                        node.lineno,
                    )

        if isinstance(node, ast.Call) and is_request_call(
            node, modules, sessions, direct_methods, session_factories
        ):
            if not request_evaluation_is_safe(node, broad_state):
                report.error(
                    "unsafe-request-expression",
                    "Every HTTP request receiver and argument must stay inside the safe expression subset",
                    node.lineno,
                )
            inspect_request_credentials(node, broad_state, report)
            inspect_request_timeout(node, bindings, report)
            inspect_request_target(node, bindings, report)

    return report


def source(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def run_self_test() -> None:
    good = source(
        "from pathlib import Path", "import requests", 'BASE_URL = "https://staging.acme.com"',
        'HEADERS = dict(globals().get("__AUTH_HEADERS__", {}))', "def test_health():",
        '    response = requests.get(f"{BASE_URL}/health", headers=HEADERS, timeout=30)',
        '    assert Path("/").is_absolute()',
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
        "call-auth": (False, source(
            "import requests", "def test_case():",
            '    credential = requests.auth.HTTPBasicAuth("live-user",',
            '        "realistic-password-value-123456")',
            '    requests.get("https://staging.acme.com/me", auth=credential, timeout=30)',
            "test_case()"), "embedded-secret"),
        "call-cookies": (False, source(
            "import requests", "def test_case():",
            '    cookies = requests.cookies.cookiejar_from_dict({"session":',
            '        "realistic-secret-value-123456"})',
            '    requests.get("https://staging.acme.com/me", cookies=cookies, timeout=30)',
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
        "request-helper": (False, source(
            "import requests", "def fetch():",
            '    return requests.get("https://staging.acme.com/me", timeout=30)',
            "def test_case():", "    assert fetch().status_code == 200", "test_case()"),
            "request-helper-unsupported"),
        "request-in-try": (False, source(
            "import requests", "def test_case():", "    try:",
            '        requests.get("https://staging.acme.com/me", timeout=30)', "    finally:",
            "        pass", "test_case()"), "unproven-request"),
        "handled-exception-return": (False, source(
            "import requests", "def test_case():", "    values = {}", "    try:",
            '        values["missing"]', "    except KeyError:", "        return",
            '    requests.get("https://staging.acme.com/me", timeout=30)', "test_case()"),
            "no-http-request"),
        "conditional-early-return": (False, source(
            "import requests", "def test_case():", '    if globals().get("SKIP_REQUEST"):',
            "        return", '    requests.get("https://staging.acme.com/me", timeout=30)',
            "test_case()"), "no-http-request"),
        "rebound-direct-request": (False, source(
            "from requests import get", "get = lambda *args, **kwargs: None", "def test_case():",
            '    get("https://staging.acme.com/me", timeout=30)', "test_case()"), "no-http-request"),
        "locally-shadowed-request": (False, source(
            "from requests import get", "def test_case():", "    get = lambda *args, **kwargs: None",
            '    get("https://staging.acme.com/me", timeout=30)', "test_case()"), "no-http-request"),
        "wildcard-request-shadow": (False, source(
            "from requests import get as wait_for", "from asyncio import *", "def test_case():",
            '    wait_for("https://staging.acme.com/me", timeout=30)', "test_case()"),
            "wildcard-import"),
        "shadowed-session": (False, source(
            "import requests", "session = requests.Session()", "session = object()", "def test_case():",
            '    session.get("https://staging.acme.com/me", timeout=30)', "test_case()"),
            "no-http-request"),
        "decorated-test": (False, source(
            "import requests", "def noop(function):", "    return lambda: None", "@noop",
            "def test_case():", '    requests.get("https://staging.acme.com/me", timeout=30)',
            "test_case()"), "decorated-function"),
        "optional-test-parameter": (False, source(
            "import requests", "def test_case(timeout=30):",
            '    requests.get("https://staging.acme.com/me", timeout=timeout)',
            "test_case()"), "test-parameters"),
        "generator-test": (False, source(
            "import requests", "def test_case():",
            '    yield requests.get("https://staging.acme.com/me", timeout=30)',
            "test_case()"), "generator-function"),
        "lazy-assert-message": (False, source(
            "import requests", "def test_case():",
            '    assert True, requests.get("https://staging.acme.com/me", timeout=30)',
            "test_case()"), "unproven-request"),
        "successful-exit": (False, source(
            "import sys", "import requests", "def test_case():", "    sys.exit(0)",
            '    requests.get("https://staging.acme.com/me", timeout=30)', "test_case()"),
            "unproven-request"),
        "exit-in-request-argument": (False, source(
            "import sys", "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/me", params=sys.exit(0), timeout=30)',
            "test_case()"), "unproven-request"),
        "exit-in-session-constructor": (False, source(
            "import sys", "import requests", "def test_case():",
            "    with requests.Session(sys.exit(0)) as session:",
            '        session.get("https://staging.acme.com/me", timeout=30)', "test_case()"),
            "unproven-request"),
        "top-level-rebind": (False, source(
            "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/me", timeout=30)', "if True:",
            "    test_case = lambda: None", "test_case()"), "unsupported-top-level"),
        "duplicate-test": (False, source(
            "import requests", "def test_case():", "    pass", "test_case()",
            "def test_case():", '    requests.get("https://staging.acme.com/me", timeout=30)'),
            "duplicate-function"),
        "module-method-shadow": (False, source(
            "import requests", "def test_case():", "    requests.get = lambda *args, **kwargs: None",
            '    requests.get("https://staging.acme.com/me", timeout=30)', "test_case()"),
            "unproven-request"),
        "later-method-shadow": (False, source(
            "import requests", 'BASE_URL = "https://staging.acme.com"', "def test_case():",
            '    requests.get(f"{BASE_URL}/health", timeout=30)',
            "    requests.get = lambda *args, **kwargs: None",
            '    requests.get(f"{BASE_URL}/private", timeout=30)', "test_case()"),
            "transport-mutation"),
        "later-session-shadow": (False, source(
            "import requests", 'BASE_URL = "https://staging.acme.com"', "def replacement():",
            '    return ("agent", "synthetic-password-value-123456")', "def test_case():",
            '    requests.get(f"{BASE_URL}/health", timeout=30)', "    requests.Session = replacement",
            '    requests.get(f"{BASE_URL}/private", auth=requests.Session(), timeout=30)',
            "test_case()"), "transport-mutation"),
        "returned-transport": (False, source(
            "import requests", 'BASE_URL = "https://staging.acme.com"', "def client():",
            "    return requests", "def test_case():",
            '    requests.get(f"{BASE_URL}/health", timeout=30)', "    transport = client()",
            '    transport.get(f"{BASE_URL}/private", timeout=30)', "test_case()"),
            "transport-escape"),
        "nested-transport-alias": (False, source(
            "import requests", 'BASE_URL = "https://staging.acme.com"', "def test_case():",
            '    requests.get(f"{BASE_URL}/health", timeout=30)', "    (transport,) = (requests,)",
            '    transport.get(f"{BASE_URL}/private", timeout=30)', "test_case()"),
            "transport-alias"),
        "loop-transport-alias": (False, source(
            "import requests", 'BASE_URL = "https://staging.acme.com"', "def test_case():",
            '    requests.get(f"{BASE_URL}/health", timeout=30)', "    for transport in (requests,):",
            '        transport.get(f"{BASE_URL}/private", timeout=30)', "test_case()"),
            "transport-alias"),
        "comprehension-transport-alias": (False, source(
            "import requests", 'BASE_URL = "https://staging.acme.com"', "def test_case():",
            '    requests.get(f"{BASE_URL}/health", timeout=30)',
            '    [transport.get(f"{BASE_URL}/private", timeout=30) for transport in (requests,)]',
            "test_case()"), "transport-alias"),
        "walrus-transport-alias": (False, source(
            "import requests", 'BASE_URL = "https://staging.acme.com"', "def test_case():",
            '    requests.get(f"{BASE_URL}/health", timeout=30)', "    (transport := requests)",
            '    transport.get(f"{BASE_URL}/private", timeout=30)', "test_case()"),
            "transport-alias"),
        "default-transport-capture": (False, source(
            "import requests", "def mutate(client=requests):",
            "    client.get = lambda *args, **kwargs: None", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)', "    mutate()",
            '    requests.get("https://staging.acme.com/two", timeout=30)', "test_case()"),
            "transport-escape"),
        "default-session-capture": (False, source(
            "import requests", "def mutate(client=requests.Session()):", "    client.headers.clear()",
            "def test_case():", '    requests.get("https://staging.acme.com/one", timeout=30)',
            "    mutate()", "test_case()"), "transport-escape"),
        "runtime-transport-annotation": (False, source(
            "import requests", "def holder() -> requests:", "    return None", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)', "test_case()"),
            "transport-escape"),
        "python39-union-annotation": (False, source(
            "import requests", "def status(response: requests.Response | None) -> int:",
            "    return response.status_code", "def test_case():",
            '    response = requests.get("https://staging.acme.com/one", timeout=30)',
            "    assert status(response) == 200", "test_case()"), "unsafe-function-definition"),
        "missing-default": (False, source(
            "import requests", "def status(expected=MISSING):", "    return expected", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)', "test_case()"),
            "unsafe-function-definition"),
        "raising-default": (False, source(
            "import requests", "def status(expected=1 / 0):", "    return expected", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)', "test_case()"),
            "unsafe-function-definition"),
        "missing-runtime-annotation": (False, source(
            "import requests", "def status(response: MissingType) -> int:",
            "    return response.status_code", "def test_case():",
            '    response = requests.get("https://staging.acme.com/one", timeout=30)',
            "    assert status(response) == 200", "test_case()"), "unsafe-function-definition"),
        "session-class-base": (False, source(
            "import requests", "class Client(requests.Session):", "    pass", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)', "test_case()"),
            "transport-escape"),
        "reflective-globals-transport": (False, source(
            "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            '    client = globals()["requests"]',
            '    client.get("https://staging.acme.com/two", timeout=30)', "test_case()"),
            "dynamic-reflection"),
        "reflective-sys-modules": (False, source(
            "import sys", "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            '    client = sys.modules["requests"]',
            '    client.get("https://staging.acme.com/two", timeout=30)', "test_case()"),
            "dynamic-reflection"),
        "reflective-import": (False, source(
            "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            '    client = __import__("requests")',
            '    client.get("https://staging.acme.com/two", timeout=30)', "test_case()"),
            "dynamic-reflection"),
        "function-globals-transport": (False, source(
            "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            '    client = test_case.__globals__["requests"]',
            '    client.request("GET", "https://staging.acme.com/two")', "test_case()"),
            "dynamic-reflection"),
        "qualified-builtins-transport": (False, source(
            "import builtins", "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            '    client = builtins.__import__("requests")',
            '    client.request("GET", "https://staging.acme.com/two")', "test_case()"),
            "dynamic-reflection"),
        "aliased-importlib-transport": (False, source(
            "from importlib import import_module as load", "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            '    client = load("requests")',
            '    client.request("GET", "https://staging.acme.com/two")', "test_case()"),
            "dynamic-reflection"),
        "sys-dict-transport": (False, source(
            "import sys", "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            '    client = sys.__dict__["modules"]["requests"]',
            '    client.request("GET", "https://staging.acme.com/two")', "test_case()"),
            "dynamic-reflection"),
        "sys-imported-modules": (False, source(
            "from sys import modules as registry", "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            '    client = registry["requests"]',
            '    client.request(*("GET", "https://staging.acme.com/two"))', "test_case()"),
            "dynamic-reflection"),
        "sys-frame-transport": (False, source(
            "import sys", "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            '    client = sys._getframe().f_globals["requests"]',
            '    client.get("https://staging.acme.com/two")', "test_case()"),
            "dynamic-reflection"),
        "runpy-transport": (False, source(
            "import runpy", "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            '    namespace = runpy.run_module("requests")',
            '    namespace["request"]("GET", "https://staging.acme.com/two")', "test_case()"),
            "dynamic-reflection"),
        "loader-transport": (False, source(
            "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            '    client = __loader__.load_module("requests")',
            '    client.get("https://staging.acme.com/two")', "test_case()"),
            "dynamic-reflection"),
        "aliased-reflective-builtin": (False, source(
            "import requests", "load = __import__", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            '    client = load("requests")',
            '    client.get("https://staging.acme.com/two")', "test_case()"),
            "dynamic-reflection"),
        "gc-transport": (False, source(
            "import gc", "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            "    gc.get_referents(test_case)", "test_case()"), "dynamic-reflection"),
        "nested-shadowed-transport": (False, source(
            "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            "    def fake_request(requests):",
            '        return requests.get("https://staging.acme.com/two", timeout=30)',
            "    fake_request(object())", "test_case()"), "nested-definition"),
        "untracked-request-method": (False, source(
            "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/one", timeout=30)',
            '    object().request("GET", "https://staging.acme.com/two")', "test_case()"),
            "untracked-http-call"),
        "session-timeout": (False, source(
            "import requests", "def test_case():", '    requests.Session().get("https://staging.acme.com/me")',
            "test_case()"), "missing-timeout"),
        "none-timeout": (False, source(
            "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/me", timeout=None)', "test_case()"),
            "unbounded-timeout"),
        "infinite-timeout": (False, source(
            "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/me", timeout=1e309)', "test_case()"),
            "unbounded-timeout"),
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
        "cleared-auth": (True, source(
            "import requests", 'HEADERS = dict(globals().get("__AUTH_HEADERS__", {}))',
            "def test_case():", "    HEADERS.clear()",
            '    requests.get("https://staging.acme.com/me", headers=HEADERS, timeout=30)',
            "test_case()"), "missing-managed-auth"),
        "subscript-auth-mutation": (True, source(
            "import requests", 'HEADERS = dict(globals().get("__AUTH_HEADERS__", {}))',
            "def test_case():", '    HEADERS["Authorization"] = "redacted"',
            '    requests.get("https://staging.acme.com/me", headers=HEADERS, timeout=30)',
            "test_case()"), "missing-managed-auth"),
        "aliased-auth-mutation": (True, source(
            "import requests", 'HEADERS = dict(globals().get("__AUTH_HEADERS__", {}))',
            "ALIAS = HEADERS", "def test_case():", "    HEADERS.clear()",
            '    requests.get("https://staging.acme.com/me", headers=ALIAS, timeout=30)',
            "test_case()"), "missing-managed-auth"),
        "nested-auth-alias": (True, source(
            "import requests", 'HEADERS = dict(globals().get("__AUTH_HEADERS__", {}))',
            "def test_case():",
            '    requests.get("https://staging.acme.com/one", headers=HEADERS, timeout=30)',
            "    (alias,) = (HEADERS,)", "    alias.clear()",
            '    requests.get("https://staging.acme.com/two", headers=HEADERS, timeout=30)',
            "test_case()"), "managed-auth-alias"),
        "default-auth-capture": (True, source(
            "import requests", "def strip(headers=__AUTH_HEADERS__):", "    headers.clear()",
            "def test_case():", "    strip()",
            '    requests.get("https://staging.acme.com/me", headers=__AUTH_HEADERS__, timeout=30)',
            "test_case()"), "managed-auth-alias"),
        "reflective-auth-mutation": (True, source(
            "import requests", "def test_case():",
            '    globals().get("__AUTH_HEADERS__", {}).clear()',
            '    requests.get("https://staging.acme.com/me",',
            '        headers=globals().get("__AUTH_HEADERS__", {}), timeout=30)',
            "test_case()"), "dynamic-reflection"),
        "function-globals-auth-mutation": (True, source(
            "import requests", "def test_case():",
            '    test_case.__globals__["__AUTH_HEADERS__"].clear()',
            '    requests.get("https://staging.acme.com/me", headers=__AUTH_HEADERS__, timeout=30)',
            "test_case()"), "dynamic-reflection"),
        "helper-auth-mutation": (True, source(
            "import requests", 'HEADERS = dict(globals().get("__AUTH_HEADERS__", {}))',
            "def strip_auth():", "    HEADERS.clear()", "def test_case():", "    strip_auth()",
            '    requests.get("https://staging.acme.com/me", headers=HEADERS, timeout=30)',
            "test_case()"), "unproven-request"),
        "argument-auth-mutation": (True, source(
            "import requests", 'HEADERS = dict(globals().get("__AUTH_HEADERS__", {}))',
            "ALIAS = HEADERS", "def test_case():",
            '    requests.get("https://staging.acme.com/me", params=ALIAS.clear(),',
            "        headers=HEADERS, timeout=30)", "test_case()"), "unproven-request"),
        "credential-helper-argument": (False, source(
            "import requests", "def credential():",
            '    return ("agent", "synthetic-password-value-123456")', "def test_case():",
            '    requests.get("https://staging.acme.com/me", auth=credential(), timeout=30)',
            "test_case()"), "unproven-request"),
        "later-credential-helper": (False, source(
            "import requests", 'BASE_URL = "https://staging.acme.com"', "def credential():",
            '    return ("agent", "synthetic-password-value-123456")', "def test_case():",
            '    requests.get(f"{BASE_URL}/health", timeout=30)',
            '    requests.get(f"{BASE_URL}/private", auth=credential(), timeout=30)',
            "test_case()"), "unsafe-request-expression"),
        "shadowed-dict-copy": (True, source(
            "def dict(value):", "    raise SystemExit(0)", "import requests", "def test_case():",
            '    requests.get("https://staging.acme.com/me",',
            "        headers=dict(__AUTH_HEADERS__).copy(), timeout=30)", "test_case()"),
            "unproven-request"),
        "auth-override": (True, source(
            "import requests", "def test_case():",
            '    headers = {**__AUTH_HEADERS__, "Authorization": None}',
            '    requests.get("https://staging.acme.com/me", headers=headers, timeout=30)',
            "test_case()"), "missing-managed-auth"),
        "session-auth-state": (False, source(
            "import requests", "def test_case():", "    session = requests.Session()",
            '    session.auth = ("agent", "synthetic-password-value-123456")',
            '    session.get("https://staging.acme.com/me", timeout=30)', "test_case()"),
            "embedded-secret"),
        "session-cookie-state": (False, source(
            "import requests", 'BASE_URL = "https://staging.acme.com"', "def test_case():",
            "    session = requests.Session()", '    session.get(f"{BASE_URL}/health", timeout=30)',
            '    session.cookies.set("session", "synthetic-cookie-value-123456")',
            '    session.get(f"{BASE_URL}/private", timeout=30)', "test_case()"),
            "transport-mutation"),
        "header-update-keyword": (False, source(
            "import requests", "def test_case():", "    headers = {}",
            '    headers.update(Authorization="synthetic-password-value-123456")',
            '    requests.get("https://staging.acme.com/me", headers=headers, timeout=30)',
            "test_case()"), "embedded-secret"),
        "composed-userinfo": (False, source(
            "import requests", 'SCHEME = "https://"', 'USERINFO = f"{\'agent\'}:{\'live-pass\'}@"',
            'BASE_URL = SCHEME + USERINFO + "api.acme.com"', "def test_case():",
            '    requests.get(f"{BASE_URL}/me", timeout=30)', "test_case()"), "embedded-secret"),
        "uppercase-userinfo": (False, source(
            "import requests", "def test_case():",
            '    requests.get("HTTPS://agent:realistic-password-value-123456@api.acme.com/me", timeout=30)',
            "test_case()"), "embedded-secret"),
        "formatted-private-target": (False, source(
            "import requests", 'BASE_URL = "{}://{}".format("http", "localhost")',
            "def test_case():", "    requests.get(BASE_URL, timeout=30)", "test_case()"),
            "private-target"),
        "dynamic-private-host": (False, source(
            "import requests", 'HOST = globals().get("API_HOST", "localhost")',
            'URL = f"http://{HOST}/x"', "def test_case():",
            "    requests.get(URL, timeout=30)", "test_case()"), "unresolved-target"),
        "trailing-dot-localhost": (False, source(
            "import requests", "def test_case():",
            '    requests.get("http://localhost./x", timeout=30)', "test_case()"),
            "private-target"),
    }
    for name, (auth_required, body, expected) in cases.items():
        codes = {finding.code for finding in audit_source(body, auth_required, set()).errors}
        assert expected in codes, (name, expected, codes)

    positives = {
        "session": source(
            "import requests", "def test_case():", "    with requests.Session() as session:",
            '        session.get("https://staging.acme.com/me", timeout=30)', "test_case()"),
        "session-name-scope": source(
            "import requests", "def test_session_request():", "    with requests.Session() as session:",
            '        session.get("https://staging.acme.com/one", timeout=30)',
            "def test_plain_mapping():", '    session = {"status": 200}',
            '    requests.get("https://staging.acme.com/two", timeout=30)',
            '    assert session.get("status") == 200', "test_session_request()", "test_plain_mapping()"),
        "aliased-generic-request": source(
            "from requests import request as send", "def test_case():",
            '    send("GET", "https://staging.acme.com/me", timeout=30)', "test_case()"),
        "local-imported-method": source(
            "def test_case():", "    from requests import get as send",
            '    send("https://staging.acme.com/me", timeout=30)', "test_case()"),
        "multiple-requests": source(
            "import requests", 'BASE_URL = "https://staging.acme.com"', "def test_case():",
            '    first = requests.get(f"{BASE_URL}/health", timeout=30)',
            '    second = requests.get(f"{BASE_URL}/status", timeout=30)',
            "    assert first.status_code == second.status_code", "test_case()"),
        "response-annotation": source(
            "import requests", "def status(response: requests.Response) -> int:",
            "    return response.status_code", "def test_case():",
            '    response = requests.get("https://staging.acme.com/health", timeout=30)',
            "    assert status(response) == 200", "test_case()"),
        "future-union-annotation": source(
            "from __future__ import annotations", "import requests",
            "def status(response: requests.Response | None) -> int:",
            "    return response.status_code", "def test_case():",
            '    response = requests.get("https://staging.acme.com/health", timeout=30)',
            "    assert status(response) == 200", "test_case()"),
        "static-helper-default": source(
            "import requests", "DEFAULT_STATUS = 200", "def status(response, expected=DEFAULT_STATUS):",
            "    assert response.status_code == expected", "def test_case():",
            '    response = requests.get("https://staging.acme.com/health", timeout=30)',
            "    status(response)", "test_case()"),
        "type-name-diagnostic": source(
            "import requests", "def require_object(body):",
            '    assert isinstance(body, dict), f"expected object, got {type(body).__name__}"',
            "def test_case():", '    response = requests.get("https://staging.acme.com/health", timeout=30)',
            "    require_object(response.json())", "test_case()"),
        "citation-scheme-prefixes": source(
            "import requests", "def collect_urls(value: object) -> list[str]:", "    found = []",
            '    if isinstance(value, str) and value.startswith(("http://", "https://")):',
            "        found.append(value)", "    return found", "def test_case():",
            '    response = requests.get("https://staging.acme.com/health", timeout=30)',
            "    assert collect_urls(response.json().get(\"source\", \"\"))", "test_case()"),
        "stateful-lifecycle": source(
            "import requests", 'BASE_URL = "https://staging.acme.com"', "def test_case():",
            '    created = requests.post(f"{BASE_URL}/resources", headers=__AUTH_HEADERS__,',
            '        json={"name": "fixture"}, timeout=30)', "    resource_id = created.json()[\"id\"]",
            "    try:", '        fetched = requests.get(f"{BASE_URL}/resources/{resource_id}",',
            "            headers=__AUTH_HEADERS__, timeout=30)", "        assert fetched.status_code == 200",
            "    finally:", '        requests.delete(f"{BASE_URL}/resources/{resource_id}",',
            "            headers=__AUTH_HEADERS__, timeout=30)", "test_case()"),
    }
    for name, body in positives.items():
        errors = audit_source(body, auth_required=False, allowed_modules=set()).errors
        assert not errors, (name, [(finding.code, finding.line) for finding in errors])

    private_targets = [
        "http://localhost./x",
        "http://localhost。/x",
        "http://localhost．/x",
        "http://localhost｡/x",
        "http://api.localhost/x",
        "http://127.1/x",
        "http://2130706433/x",
        "http://0x7f000001/x",
        "http://[::1]/x",
        "http://10.0.0.1/x",
        "http://service.localdomain/x",
        "http://service.local。/x",
        "http://home.arpa/x",
    ]
    for target in private_targets:
        target_report = Report()
        inspect_url(target, 1, target_report)
        assert any(finding.code == "private-target" for finding in target_report.errors), target

    for target in [
        "https://staging.acme.com/x",
        "https://staging.acme.com./x",
        "https://bücher.de/x",
        "http://8.8.8.8/x",
    ]:
        target_report = Report()
        inspect_url(target, 1, target_report)
        assert not target_report.errors, (target, [finding.code for finding in target_report.errors])

    scope_source = source(
        "import requests", 'BASE_URL = "https://module.acme.com"', "def helper():",
        '    BASE_URL = "https://helper.acme.com"', "    return BASE_URL", "def test_case():",
        '    requests.get(f"{BASE_URL}/health", timeout=30)', "test_case()",
    )
    scope_tree = ast.parse(scope_source)
    scope_report = audit_source(scope_source, auth_required=False, allowed_modules=set())
    assert not scope_report.errors, [
        (finding.code, finding.line) for finding in scope_report.errors
    ]
    scope_parents = {
        child: parent
        for parent in ast.walk(scope_tree)
        for child in ast.iter_child_nodes(parent)
    }
    scope_module = broad_bindings(scope_tree)
    scope_request = next(
        node
        for node in ast.walk(scope_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get"
    )
    scope_url = request_url_node(scope_request, scoped_bindings(scope_request, scope_parents, scope_module))
    assert scope_url is not None
    assert static_string_value(
        scope_url, scoped_bindings(scope_request, scope_parents, scope_module)
    ) == "https://module.acme.com/health"
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
