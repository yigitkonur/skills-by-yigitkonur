#!/usr/bin/env python3
"""Trusted, read-only Jean MCP operations and run-aware bounded watching.

The CLI connects only to an already-running Jean MCP bridge. It never launches,
quits, restarts, or mutates Jean. All normal output is versioned JSON; watcher
output is versioned NDJSON plus a checkpointed result file.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
import uuid


VERSION = "2.1.0"
SCHEMA_VERSION = "jean-ops/v2"
DEFAULT_CONFIG = Path.home() / ".codex" / "config.toml"
DEFAULT_STATE_ROOT = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "state" / "orchestrate-projects-by-jean"
EXPECTED_JEAN_EXECUTABLE = Path("/Applications/Jean.app/Contents/MacOS/jean")

READ_ONLY_TOOLS = {
    "get_current_context",
    "get_project_context",
    "get_session_status",
    "get_worktree",
    "get_worktree_changes",
    "get_worktree_diff",
    "list_github_issues",
    "list_github_prs",
    "list_linear_issues",
    "list_projects",
    "list_security_advisories",
    "list_security_issues",
    "list_sessions",
    "list_worktrees",
    "read_session_messages",
}
MUTATING_TOOLS = {
    "cancel_session_run",
    "create_session",
    "create_worktree",
    "send_chat_message",
    "update_worktree_labels",
}
ESSENTIAL_CAPABILITIES = {
    "get_worktree": {"worktree_id"},
    "list_projects": set(),
    "list_worktrees": {"project_id"},
    "list_sessions": {"worktree_id"},
    "get_session_status": {"session_id"},
}
EXPECTED_REQUIRED_INPUTS = {
    "get_current_context": set(),
    "get_project_context": {"project_id"},
    "get_session_status": {"session_id"},
    "get_worktree": {"worktree_id"},
    "get_worktree_changes": {"worktree_id"},
    "get_worktree_diff": {"worktree_id"},
    "list_github_issues": {"project_id"},
    "list_github_prs": {"project_id"},
    "list_linear_issues": {"project_id"},
    "list_projects": set(),
    "list_security_advisories": {"project_id"},
    "list_security_issues": {"project_id"},
    "list_sessions": {"worktree_id"},
    "list_worktrees": {"project_id"},
    "read_session_messages": {"session_id"},
}

TERMINAL_STATES = {
    "complete",
    "completed",
    "success",
    "succeeded",
    "failure",
    "failed",
    "error",
    "cancelled",
    "canceled",
    "timeout",
    "timed_out",
}
RUNNING_STATES = {"running", "streaming", "queued", "pending", "starting"}
IDLE_STATES = {"idle", "resumable", "ready"}
WAITING_STATES = {"waiting", "waiting_for_input", "needs_input", "input_required"}
SENSITIVE_FRAGMENTS = ("token", "secret", "password", "credential", "api_key", "api-key")
SAFE_ENV_KEYS = {
    "HOME",
    "USER",
    "LOGNAME",
    "PATH",
    "TMPDIR",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "XDG_CACHE_HOME",
    "UV_CACHE_DIR",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "NO_COLOR",
    "TERM",
}

MIN_CALL_TIMEOUT = 1.0
MAX_CALL_TIMEOUT = 120.0
MIN_WATCH_TIMEOUT = 2.0
MAX_WATCH_TIMEOUT = 86400.0
MIN_INTERVAL = 1.0
MAX_INTERVAL = 60.0
MAX_TRANSIENT_RETRIES = 3
MIN_OUTPUT_BYTES = 4096
MAX_OUTPUT_BYTES = 2_000_000
MIN_STRING_CHARS = 256
MAX_STRING_CHARS = 100_000
MAX_MESSAGES = 100
MAX_CHANGED_FILES = 500
DEFAULT_MESSAGE_OUTPUT_BYTES = 100_000
EXPANDED_MESSAGE_OUTPUT_BYTES = 250_000
DEFAULT_MESSAGE_CONTENT_CHARS = 4_000
MAX_MESSAGE_CONTENT_CHARS = 20_000
DEFAULT_MAX_TOOL_CALLS = 20
MAX_MESSAGE_TOOL_CALLS = 100


class JeanOpsError(RuntimeError):
    code = "operation_error"
    category = "internal"
    retryable = False
    exit_code = 70

    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        category: Optional[str] = None,
        retryable: Optional[bool] = None,
        exit_code: Optional[int] = None,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.code
        self.category = category or self.category
        self.retryable = self.retryable if retryable is None else retryable
        self.exit_code = self.exit_code if exit_code is None else exit_code
        self.details = dict(details or {})

    def as_dict(self) -> Dict[str, Any]:
        value: Dict[str, Any] = {
            "category": self.category,
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.details:
            value["details"] = self.details
        return value


class UsageError(JeanOpsError):
    code = "invalid_usage"
    category = "usage"
    exit_code = 2


class ConfigError(JeanOpsError):
    code = "invalid_config"
    category = "config"
    exit_code = 10


class TrustError(JeanOpsError):
    code = "trust_boundary_failed"
    category = "trust"
    exit_code = 11


class UnavailableError(JeanOpsError):
    code = "dependency_unavailable"
    category = "unavailable"
    retryable = True
    exit_code = 12


class McpError(JeanOpsError):
    code = "mcp_error"
    category = "mcp"
    exit_code = 13


class LeaseConflictError(JeanOpsError):
    code = "lease_conflict"
    category = "ownership"
    exit_code = 14


class PersistenceError(JeanOpsError):
    code = "result_persistence_failed"
    category = "persistence"
    exit_code = 15


class SupersededError(JeanOpsError):
    code = "run_superseded"
    category = "run_identity"
    exit_code = 16


class DeadlineExceeded(JeanOpsError):
    code = "deadline_exceeded"
    category = "timeout"
    retryable = True
    exit_code = 124


class ControllerLostError(JeanOpsError):
    code = "controller_lost"
    category = "ownership"
    exit_code = 129


class SelfTestError(JeanOpsError):
    code = "self_test_failed"
    category = "test"
    exit_code = 1


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def iso_from_epoch(value: float) -> str:
    return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat().replace("+00:00", "Z")


def epoch_from_iso(value: Any) -> float:
    if not isinstance(value, str):
        return 0.0
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def normalize_name(value: Any) -> str:
    text = str(value or "").strip().replace("-", "_").replace(" ", "_")
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)
    return text.lower()


def json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def print_json(value: Any, pretty: bool = False) -> None:
    kwargs: Dict[str, Any] = {"ensure_ascii": False, "sort_keys": True}
    if pretty:
        kwargs["indent"] = 2
    else:
        kwargs["separators"] = (",", ":")
    print(json.dumps(value, **kwargs), flush=True)


def error_envelope(command: str, error: JeanOpsError) -> Dict[str, Any]:
    return {
        "command": command,
        "error": error.as_dict(),
        "exit_code": error.exit_code,
        "observed_at": utc_now(),
        "ok": False,
        "schema_version": SCHEMA_VERSION,
    }


def success_envelope(command: str, data: Any, meta: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    return {
        "command": command,
        "data": data,
        "meta": dict(meta or {}),
        "observed_at": utc_now(),
        "ok": True,
        "schema_version": SCHEMA_VERSION,
    }


def strip_toml_comment(value: str) -> str:
    quote: Optional[str] = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote == '"':
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
        elif char == "#":
            return value[:index].rstrip()
    return value.strip()


def parse_restricted_toml_value(raw: str) -> Any:
    value = strip_toml_comment(raw).strip()
    if not value:
        raise ConfigError("empty value in Jean MCP configuration")
    if "\"\"\"" in value or "'''" in value:
        raise ConfigError("multiline TOML strings require Python 3.11 tomllib or tomli")
    if value.startswith("[") and not value.endswith("]"):
        raise ConfigError("multiline Jean args require Python 3.11 tomllib or tomli")
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith('"') or value.startswith("["):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise ConfigError("Jean MCP values must use JSON-compatible TOML on Python 3.9") from exc
    if re.fullmatch(r"[-+]?\d+", value):
        return int(value)
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)", value):
        return float(value)
    raise ConfigError("unsupported Jean MCP TOML value; install tomli or use basic strings/arrays")


def restricted_jean_toml(path: Path) -> Dict[str, Any]:
    section = ""
    main: Dict[str, Any] = {}
    env: Dict[str, Any] = {}
    seen_sections: Dict[str, int] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("["):
                if not line.endswith("]"):
                    raise ConfigError("unterminated TOML table at line %d" % line_number)
                candidate = line[1:-1].strip()
                dequoted = candidate.replace('"', "").replace("'", "")
                if dequoted in {"mcp_servers.jean", "mcp_servers.jean.env"} and candidate != dequoted:
                    raise ConfigError("quoted Jean MCP tables require Python 3.11 tomllib or tomli")
                section = candidate
                if section in {"mcp_servers.jean", "mcp_servers.jean.env"}:
                    seen_sections[section] = seen_sections.get(section, 0) + 1
                    if seen_sections[section] > 1:
                        raise ConfigError("duplicate Jean MCP table: %s" % section)
                continue
            if section not in {"mcp_servers.jean", "mcp_servers.jean.env"}:
                continue
            if "=" not in line:
                raise ConfigError("invalid Jean MCP assignment at line %d" % line_number)
            key, raw_value = line.split("=", 1)
            key = key.strip()
            if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
                raise ConfigError("unsupported Jean MCP key syntax at line %d" % line_number)
            target = main if section == "mcp_servers.jean" else env
            if key in target:
                raise ConfigError("duplicate Jean MCP key: %s" % key)
            target[key] = parse_restricted_toml_value(raw_value)
    if "env" in main:
        raise ConfigError("inline Jean env tables require Python 3.11 tomllib or tomli")
    return {"main": main, "env": env, "parser": "restricted"}


def parse_jean_toml(path: Path) -> Dict[str, Any]:
    parser_name = ""
    parser: Any = None
    try:
        import tomllib as parser  # type: ignore

        parser_name = "tomllib"
    except ImportError:
        try:
            import tomli as parser  # type: ignore

            parser_name = "tomli"
        except ImportError:
            parser = None
    if parser is None:
        return restricted_jean_toml(path)
    try:
        with path.open("rb") as handle:
            document = parser.load(handle)
    except Exception as exc:
        raise ConfigError("cannot parse Codex TOML: %s" % exc) from exc
    servers = document.get("mcp_servers")
    if not isinstance(servers, dict) or not isinstance(servers.get("jean"), dict):
        raise ConfigError("mcp_servers.jean is missing")
    main = dict(servers["jean"])
    env = main.pop("env", {})
    if not isinstance(env, dict):
        raise ConfigError("mcp_servers.jean.env must be a table")
    return {"main": main, "env": env, "parser": parser_name}


def validate_owned_file(path: Path, *, allow_unsafe: bool, label: str) -> os.stat_result:
    try:
        info = path.stat()
    except OSError as exc:
        raise ConfigError("cannot stat %s: %s" % (label, exc)) from exc
    if not allow_unsafe:
        if info.st_uid != os.getuid():
            raise TrustError("%s is not owned by the current user" % label)
        if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise TrustError("%s is group/world writable" % label)
    return info


def load_jean_config(path: Path, *, allow_unsafe_config: bool = False) -> Dict[str, Any]:
    path = path.expanduser()
    if not path.is_file():
        raise ConfigError("Codex MCP configuration not found: %s" % path)
    if not allow_unsafe_config:
        if path.is_symlink():
            raise TrustError("Codex MCP configuration must not be a symlink")
        if path.resolve() != DEFAULT_CONFIG.resolve():
            raise TrustError("custom --config requires --allow-unsafe-config")
    validate_owned_file(path, allow_unsafe=allow_unsafe_config, label="Codex MCP configuration")
    parsed = parse_jean_toml(path)
    main = parsed["main"]
    env_raw = parsed["env"]
    command = main.get("command")
    arguments = main.get("args", [])
    if not isinstance(command, str) or not command:
        raise ConfigError("mcp_servers.jean.command is missing")
    if not isinstance(arguments, list) or not all(isinstance(item, str) for item in arguments):
        raise ConfigError("mcp_servers.jean.args must be an array of strings")
    env: Dict[str, str] = {}
    for key, value in env_raw.items():
        if not isinstance(key, str) or not isinstance(value, (str, int, float, bool)):
            raise ConfigError("Jean MCP environment must contain scalar values")
        if not allow_unsafe_config and not key.startswith("JEAN_MCP_"):
            raise TrustError("unexpected non-Jean environment key in Jean MCP config: %s" % key)
        env[key] = str(value)
    return {
        "args": list(arguments),
        "command": command,
        "env": env,
        "parser": parsed["parser"],
        "source": str(path.resolve()),
    }


def resolve_executable(value: str, label: str) -> Path:
    candidate = value if os.path.isabs(value) else shutil.which(value)
    if not candidate:
        raise UnavailableError("%s executable is unavailable: %s" % (label, value))
    path = Path(candidate).resolve()
    if not path.is_file() or not os.access(str(path), os.X_OK):
        raise UnavailableError("%s executable is not runnable: %s" % (label, path))
    return path


def validate_jean_command(config: Mapping[str, Any], *, allow_unsafe_config: bool) -> Path:
    executable = resolve_executable(str(config["command"]), "Jean MCP")
    arguments = list(config.get("args", []))
    if not allow_unsafe_config:
        if executable != EXPECTED_JEAN_EXECUTABLE.resolve():
            raise TrustError(
                "Jean MCP executable is not the installed Jean app binary",
                details={"actual": str(executable), "expected": str(EXPECTED_JEAN_EXECUTABLE)},
            )
        if arguments != ["--jean-mcp-stdio"]:
            raise TrustError("Jean MCP args must be exactly --jean-mcp-stdio")
        info = executable.stat()
        if info.st_uid not in {0, os.getuid()} or info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise TrustError("Jean MCP executable ownership or mode is unsafe")
    return executable


def socket_health(config: Mapping[str, Any], *, allow_unsafe_config: bool = False) -> Dict[str, Any]:
    raw_path = str(config.get("env", {}).get("JEAN_MCP_SOCKET", ""))
    if not raw_path:
        raise ConfigError("JEAN_MCP_SOCKET is missing from Jean MCP environment")
    path = Path(raw_path).expanduser()
    try:
        info = path.stat()
    except FileNotFoundError as exc:
        raise UnavailableError("configured Jean MCP socket is absent; do not relaunch Jean") from exc
    except OSError as exc:
        raise UnavailableError("cannot stat configured Jean MCP socket: %s" % exc) from exc
    if not stat.S_ISSOCK(info.st_mode):
        raise TrustError("configured JEAN_MCP_SOCKET is not a Unix socket")
    if not allow_unsafe_config:
        if info.st_uid != os.getuid():
            raise TrustError("Jean MCP socket is not owned by the current user")
        if info.st_mode & stat.S_IWOTH:
            raise TrustError("Jean MCP socket is world writable")
    return {"path": str(path), "uid": info.st_uid, "unix_socket": True}


def validate_backend_shape(parts: Sequence[str], *, allow_unsafe_backend: bool) -> List[str]:
    if not parts:
        raise ConfigError("mcp2cli backend command is empty")
    executable = resolve_executable(parts[0], "mcp2cli backend")
    resolved = [str(executable)] + list(parts[1:])
    name = executable.name
    safe = (name == "mcp2cli" and len(parts) == 1) or (
        name == "uvx" and list(parts[1:]) == ["--offline", "mcp2cli"]
    )
    if not safe and not allow_unsafe_backend:
        raise TrustError("custom backend requires --allow-unsafe-backend")
    if not allow_unsafe_backend:
        info = executable.stat()
        if info.st_uid not in {0, os.getuid()} or info.st_mode & stat.S_IWOTH:
            raise TrustError("mcp2cli backend ownership or mode is unsafe")
    return resolved


def resolve_backend(override: Optional[str], *, allow_unsafe_backend: bool = False) -> List[str]:
    candidate = override or os.environ.get("MCP2CLI_COMMAND")
    if candidate:
        return validate_backend_shape(shlex.split(candidate), allow_unsafe_backend=allow_unsafe_backend)
    direct = shutil.which("mcp2cli")
    if direct:
        return validate_backend_shape([direct], allow_unsafe_backend=False)
    uvx = shutil.which("uvx")
    if uvx:
        return validate_backend_shape([uvx, "--offline", "mcp2cli"], allow_unsafe_backend=False)
    raise UnavailableError("mcp2cli is unavailable in PATH and the offline uvx cache")


def minimal_environment(config_env: Mapping[str, Any]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for key in SAFE_ENV_KEYS:
        value = os.environ.get(key)
        if value is not None:
            result[key] = value
    result.setdefault("HOME", str(Path.home()))
    result.setdefault("PATH", "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin")
    result.setdefault("TMPDIR", tempfile.gettempdir())
    for key, value in config_env.items():
        result[str(key)] = str(value)
    return result


def sensitive_values(config_env: Mapping[str, Any]) -> List[str]:
    return [
        str(value)
        for key, value in config_env.items()
        if any(fragment in normalize_name(key) for fragment in SENSITIVE_FRAGMENTS)
    ]


def redact(text: str, values: Iterable[str]) -> str:
    result = text
    for value in sorted({item for item in values if len(item) >= 4}, key=len, reverse=True):
        result = result.replace(value, "<redacted>")
    result = re.sub(
        r"(?i)\b(authorization\s*:\s*bearer|bearer)\s+[A-Za-z0-9._~+/=-]{8,}",
        r"\1 <redacted>",
        result,
    )
    result = re.sub(
        r"(?i)\b([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY|APIKEY))\s*([=:])\s*([^\s,;\"']+)",
        r"\1\2<redacted>",
        result,
    )
    result = re.sub(
        r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})\b",
        "<redacted>",
        result,
    )
    return result


def remaining_seconds(deadline: float) -> float:
    return deadline - time.monotonic()


def terminate_process_group(process: subprocess.Popen[str]) -> Tuple[str, str]:
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        return process.communicate(timeout=0.5)
    except subprocess.TimeoutExpired:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        return process.communicate()


def run_subprocess(
    command: Sequence[str],
    *,
    environment: Mapping[str, str],
    deadline: float,
    secrets_to_redact: Iterable[str],
    phase: str,
    ownership_check: Optional[Callable[[], bool]] = None,
) -> Tuple[int, str, str]:
    remaining = remaining_seconds(deadline)
    if remaining <= 0:
        raise DeadlineExceeded("global deadline exhausted before %s" % phase)
    try:
        process = subprocess.Popen(
            list(command),
            env=dict(environment),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except OSError as exc:
        raise UnavailableError("unable to start %s: %s" % (phase, exc)) from exc
    while True:
        if ownership_check is not None and not ownership_check():
            terminate_process_group(process)
            raise ControllerLostError(
                "launch controller disappeared during %s" % phase,
                details={"process_group_reaped": process.poll() is not None},
            )
        remaining = remaining_seconds(deadline)
        if remaining <= 0:
            terminate_process_group(process)
            raise DeadlineExceeded(
                "deadline exhausted during %s" % phase,
                details={"process_group_reaped": process.poll() is not None},
            )
        try:
            stdout, stderr = process.communicate(timeout=min(0.5, remaining))
            break
        except subprocess.TimeoutExpired:
            continue
    return (
        int(process.returncode or 0),
        redact(stdout or "", secrets_to_redact),
        redact(stderr or "", secrets_to_redact),
    )


def parse_json_output(output: str) -> Any:
    text = output.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for line in reversed([item.strip() for item in text.splitlines() if item.strip()]):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    raise McpError("mcp2cli did not return valid JSON", code="invalid_mcp_json", retryable=False)


def summarize_cli_error(stdout: str, stderr: str) -> str:
    combined = stderr.strip() or stdout.strip()
    for line in reversed(combined.splitlines()):
        for marker in ("McpError:", "Error:"):
            if marker in line:
                return line[line.rfind(marker) :].strip()
    return combined[-1000:] if combined else "no diagnostic output"


def mcp_error_from_detail(return_code: int, detail: str) -> McpError:
    lowered = detail.lower()
    permanent_markers = ("unknown sessionid", "invalid", "required", "not found", "permission", "forbidden")
    transient_markers = (
        "broken pipe",
        "connection reset",
        "connection refused",
        "eof",
        "temporarily unavailable",
        "transport",
        "socket",
        "timed out",
        "timeout",
    )
    retryable = any(marker in lowered for marker in transient_markers) and not any(
        marker in lowered for marker in permanent_markers
    )
    code = "mcp_not_found" if "unknown sessionid" in lowered or "not found" in lowered else "mcp_call_failed"
    return McpError(
        "mcp2cli exited %d: %s" % (return_code, detail),
        code=code,
        retryable=retryable,
    )


def unwrap_result(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    if value.get("isError") is True:
        content = value.get("content")
        raise McpError("Jean MCP returned an error result", details={"content": content})
    structured = value.get("structuredContent")
    if structured not in (None, {}, []):
        return structured
    nested = value.get("result")
    if nested is not None and nested is not value:
        return unwrap_result(nested)
    content = value.get("content")
    if not isinstance(content, list):
        return value
    parsed_blocks: List[Any] = []
    text_blocks: List[str] = []
    other_blocks: List[Any] = []
    for block in content:
        if isinstance(block, dict) and isinstance(block.get("text"), str):
            text = block["text"].strip()
            if not text:
                continue
            try:
                parsed_blocks.append(json.loads(text))
            except json.JSONDecodeError:
                text_blocks.append(text)
        else:
            other_blocks.append(block)
    if len(parsed_blocks) == 1 and not text_blocks and not other_blocks:
        return parsed_blocks[0]
    if parsed_blocks or text_blocks or other_blocks:
        result: Dict[str, Any] = {}
        if len(parsed_blocks) == 1:
            result["data"] = parsed_blocks[0]
        elif parsed_blocks:
            result["json_blocks"] = parsed_blocks
        if text_blocks:
            result["text_blocks"] = text_blocks
        if other_blocks:
            result["other_blocks"] = other_blocks
        return result
    return value


def extract_tool_entries(value: Any) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    if isinstance(value, list):
        for item in value:
            entries.extend(extract_tool_entries(item))
    elif isinstance(value, dict):
        if isinstance(value.get("name"), str) and (
            isinstance(value.get("parameters"), list) or isinstance(value.get("toolName"), str)
        ):
            entries.append(dict(value))
        else:
            for key in ("tools", "commands", "items"):
                if key in value:
                    entries.extend(extract_tool_entries(value[key]))
    return entries


def entry_canonical_name(entry: Mapping[str, Any]) -> str:
    return normalize_name(entry.get("toolName") or entry.get("name"))


def parameter_map(entry: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    parameters = entry.get("parameters")
    if not isinstance(parameters, list):
        return result
    for item in parameters:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            continue
        normalized = normalize_name(item["name"])
        if normalized in result:
            raise TrustError("duplicate normalized parameter in MCP schema: %s" % normalized)
        result[normalized] = dict(item)
    return result


def required_parameters(entry: Mapping[str, Any]) -> set:
    return {name for name, item in parameter_map(entry).items() if item.get("required") is True}


def schema_hash(entries: Iterable[Mapping[str, Any]]) -> str:
    safe = [
        {
            "name": entry.get("name"),
            "parameters": entry.get("parameters", []),
            "toolName": entry.get("toolName"),
        }
        for entry in sorted(entries, key=entry_canonical_name)
    ]
    return hashlib.sha256(json_bytes(safe)).hexdigest()


def build_tool_flags(entry: Mapping[str, Any], arguments: Mapping[str, Any]) -> List[str]:
    parameters = parameter_map(entry)
    normalized_args = {normalize_name(key): value for key, value in arguments.items()}
    unknown = sorted(set(normalized_args) - set(parameters))
    if unknown:
        raise UsageError("unknown argument(s) for %s: %s" % (entry_canonical_name(entry), ", ".join(unknown)))
    missing = sorted(required_parameters(entry) - set(normalized_args))
    if missing:
        raise UsageError("missing required argument(s) for %s: %s" % (entry_canonical_name(entry), ", ".join(missing)))
    flags: List[str] = []
    for name, value in normalized_args.items():
        parameter = parameters[name]
        flag = "--" + str(parameter["name"])
        kind = normalize_name(parameter.get("type"))
        if kind in {"boolean", "bool"}:
            truthy = value if isinstance(value, bool) else str(value).lower() in {"1", "true", "yes", "on"}
            if truthy:
                flags.append(flag)
            continue
        if kind in {"int", "integer"}:
            try:
                value = str(int(value))
            except (TypeError, ValueError) as exc:
                raise UsageError("%s must be an integer" % name) from exc
        elif isinstance(value, (dict, list)):
            value = json.dumps(value, separators=(",", ":"))
        else:
            value = str(value)
        flags.extend([flag, value])
    return flags


class Mcp2Cli:
    def __init__(
        self,
        config: Mapping[str, Any],
        backend: Sequence[str],
        call_timeout: float,
    ) -> None:
        self.config = dict(config)
        self.backend = list(backend)
        self.call_timeout = call_timeout
        self.environment = minimal_environment(config.get("env", {}))
        self.secret_values = sensitive_values(config.get("env", {}))
        self._catalog: Dict[str, Dict[str, Any]] = {}
        self._schema_hash: Optional[str] = None
        self.ownership_check: Optional[Callable[[], bool]] = None

    @property
    def stdio_command(self) -> str:
        return shlex.join([str(self.config["command"])] + list(self.config.get("args", [])))

    def _phase_deadline(self, global_deadline: float) -> float:
        return min(global_deadline, time.monotonic() + self.call_timeout)

    def _run(self, args: Sequence[str], *, global_deadline: float, expect_json: bool, phase: str) -> Any:
        phase_deadline = self._phase_deadline(global_deadline)
        try:
            return_code, stdout, stderr = run_subprocess(
                self.backend + list(args),
                environment=self.environment,
                deadline=phase_deadline,
                secrets_to_redact=self.secret_values,
                phase=phase,
                ownership_check=self.ownership_check,
            )
        except DeadlineExceeded as exc:
            if remaining_seconds(global_deadline) <= 0:
                raise DeadlineExceeded("global deadline exhausted during %s" % phase, details=exc.details) from exc
            raise McpError(
                "%s exceeded per-call timeout %.1fs" % (phase, self.call_timeout),
                code="mcp_process_timeout",
                retryable=True,
                details=exc.details,
            ) from exc
        if return_code != 0:
            raise mcp_error_from_detail(return_code, summarize_cli_error(stdout, stderr))
        return parse_json_output(stdout) if expect_json else stdout.strip()

    def version(self, global_deadline: float) -> str:
        return str(self._run(["--version"], global_deadline=global_deadline, expect_json=False, phase="mcp2cli version"))

    def list_tools(self, global_deadline: float) -> List[Dict[str, Any]]:
        if self._catalog:
            return list(self._catalog.values())
        raw = self._run(
            ["--mcp-stdio", self.stdio_command, "--json", "--list"],
            global_deadline=global_deadline,
            expect_json=True,
            phase="Jean MCP discovery",
        )
        entries = extract_tool_entries(raw)
        if not entries:
            raise McpError("could not derive tool schemas from mcp2cli discovery", code="empty_capability_catalog")
        catalog: Dict[str, Dict[str, Any]] = {}
        for entry in entries:
            canonical = entry_canonical_name(entry)
            if canonical in catalog:
                raise TrustError("duplicate normalized Jean MCP tool: %s" % canonical)
            catalog[canonical] = entry
        expected_surface = ESSENTIAL_CAPABILITIES.keys()
        if not all(name in catalog for name in expected_surface):
            raise TrustError("MCP endpoint does not expose the essential Jean tool surface")
        self._catalog = catalog
        self._schema_hash = schema_hash(catalog.values())
        return list(catalog.values())

    @property
    def capability_hash(self) -> str:
        if not self._schema_hash:
            raise McpError("capability catalog has not been discovered", code="catalog_not_loaded")
        return self._schema_hash

    def resolve_tool(self, canonical_name: str, global_deadline: float) -> Dict[str, Any]:
        canonical = normalize_name(canonical_name)
        self.list_tools(global_deadline)
        entry = self._catalog.get(canonical)
        if not entry:
            raise McpError("Jean MCP tool is unavailable: %s" % canonical_name, code="tool_unavailable")
        return entry

    def validate_capabilities(
        self,
        required: Mapping[str, set],
        global_deadline: float,
    ) -> Dict[str, Any]:
        self.list_tools(global_deadline)
        checks: List[Dict[str, Any]] = []
        for tool_name, required_inputs in sorted(required.items()):
            entry = self._catalog.get(normalize_name(tool_name))
            if not entry:
                raise McpError("required Jean MCP tool is missing: %s" % tool_name, code="required_tool_missing")
            actual_required = required_parameters(entry)
            missing_inputs = sorted(set(required_inputs) - actual_required)
            if missing_inputs:
                raise McpError(
                    "required input contract changed for %s" % tool_name,
                    code="capability_contract_changed",
                    details={"expected_required": sorted(required_inputs), "actual_required": sorted(actual_required)},
                )
            checks.append(
                {
                    "required_inputs": sorted(actual_required),
                    "tool": normalize_name(tool_name),
                }
            )
        return {"checks": checks, "schema_hash": self.capability_hash}

    def call(self, canonical_name: str, arguments: Mapping[str, Any], global_deadline: float) -> Any:
        canonical = normalize_name(canonical_name)
        if canonical not in READ_ONLY_TOOLS:
            if canonical in MUTATING_TOOLS:
                raise TrustError("mutating Jean tools are blocked by jean_ops.py")
            raise UsageError("unknown or non-read-only Jean tool: %s" % canonical_name)
        entry = self.resolve_tool(canonical, global_deadline)
        flags = build_tool_flags(entry, arguments)
        raw = self._run(
            ["--mcp-stdio", self.stdio_command, "--json", str(entry["name"])] + flags,
            global_deadline=global_deadline,
            expect_json=True,
            phase="Jean MCP %s" % canonical,
        )
        return unwrap_result(raw)


def secure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = path.stat()
    if info.st_uid != os.getuid() or info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise PersistenceError("state directory ownership or mode is unsafe: %s" % path)
    try:
        os.chmod(path, 0o700)
    except OSError as exc:
        raise PersistenceError("cannot secure state directory: %s" % exc) from exc


def atomic_write_json(path: Path, value: Any) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(prefix=".%s." % path.name, dir=str(path.parent))
    try:
        os.fchmod(file_descriptor, 0o600)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, str(path))
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


class CheckpointWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.disabled = False
        self.failure: Optional[PersistenceError] = None

    @classmethod
    def create(cls, path: Path, initial: Mapping[str, Any]) -> "CheckpointWriter":
        path = path.expanduser().resolve()
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        parent_info = parent.stat()
        sticky_world_writable = bool(parent_info.st_mode & stat.S_ISVTX)
        if parent_info.st_uid != os.getuid() and not sticky_world_writable:
            raise PersistenceError("result parent is not owned by the current user: %s" % parent)
        if parent_info.st_mode & stat.S_IWOTH and not sticky_world_writable:
            raise PersistenceError("result parent is world writable without sticky protection: %s" % parent)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(str(path), flags, 0o600)
            os.close(descriptor)
            atomic_write_json(path, initial)
        except FileExistsError as exc:
            raise PersistenceError("result file already exists; choose a collision-safe path: %s" % path) from exc
        except OSError as exc:
            try:
                path.unlink()
            except OSError:
                pass
            raise PersistenceError("cannot preflight result file: %s" % exc) from exc
        return cls(path)

    def write(self, value: Mapping[str, Any]) -> Optional[PersistenceError]:
        if self.disabled:
            return self.failure
        try:
            atomic_write_json(self.path, value)
            return None
        except OSError as exc:
            self.disabled = True
            self.failure = PersistenceError("checkpoint write failed: %s" % exc)
            return self.failure


def process_alive(pid: Any) -> bool:
    try:
        numeric = int(pid)
    except (TypeError, ValueError):
        return False
    if numeric <= 0:
        return False
    try:
        os.kill(numeric, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def lease_is_live(data: Mapping[str, Any]) -> bool:
    if epoch_from_iso(data.get("expires_at")) <= time.time():
        return False
    if data.get("host") == socket.gethostname() and not process_alive(data.get("pid")):
        return False
    return True


def lease_key(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:32]


class SessionLease:
    def __init__(
        self,
        lock_dir: Path,
        data: Dict[str, Any],
        ttl_seconds: float,
    ) -> None:
        self.lock_dir = lock_dir
        self.path = lock_dir / "lease.json"
        self.data = data
        self.ttl_seconds = ttl_seconds
        self.released = False

    @classmethod
    def acquire(
        cls,
        state_root: Path,
        *,
        session_id: str,
        run_key: str,
        watcher_id: str,
        controller: str,
        controller_id: str,
        ttl_seconds: float,
        result_path: Path,
    ) -> "SessionLease":
        leases_root = state_root / "leases"
        secure_directory(state_root)
        secure_directory(leases_root)
        lock_dir = leases_root / (lease_key(session_id) + ".lock")
        for _attempt in range(3):
            try:
                os.mkdir(lock_dir, 0o700)
                break
            except FileExistsError:
                existing_path = lock_dir / "lease.json"
                try:
                    existing = json.loads(existing_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    existing = {"corrupt": True, "expires_at": "", "session_id": session_id}
                if lease_is_live(existing):
                    raise LeaseConflictError(
                        "a live controller already owns this Jean session",
                        details={
                            "controller": existing.get("controller"),
                            "controller_id": existing.get("controller_id"),
                            "expires_at": existing.get("expires_at"),
                            "run_key": existing.get("run_key"),
                            "watcher_id": existing.get("watcher_id"),
                        },
                    )
                stale_dir = lock_dir.with_name(lock_dir.name + ".stale." + uuid.uuid4().hex)
                try:
                    os.rename(lock_dir, stale_dir)
                except FileNotFoundError:
                    continue
                except OSError as exc:
                    raise LeaseConflictError("cannot reclaim stale lease: %s" % exc) from exc
                shutil.rmtree(stale_dir, ignore_errors=True)
        else:
            raise LeaseConflictError("could not acquire Jean session lease after stale recovery")
        now = time.time()
        data = {
            "controller": controller,
            "controller_id": controller_id,
            "expires_at": iso_from_epoch(now + ttl_seconds),
            "host": socket.gethostname(),
            "last_heartbeat_at": iso_from_epoch(now),
            "pid": os.getpid(),
            "result_path": str(result_path),
            "run_key": run_key,
            "session_id": session_id,
            "started_at": iso_from_epoch(now),
            "watcher_id": watcher_id,
        }
        lease = cls(lock_dir, data, ttl_seconds)
        try:
            atomic_write_json(lease.path, data)
        except OSError as exc:
            shutil.rmtree(lock_dir, ignore_errors=True)
            raise PersistenceError("cannot persist controller lease: %s" % exc) from exc
        return lease

    def renew(self, *, run_id: Optional[str], sequence: int) -> None:
        if self.released:
            raise LeaseConflictError("cannot renew a released lease")
        try:
            current = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LeaseConflictError("controller lease disappeared or became unreadable") from exc
        if current.get("watcher_id") != self.data.get("watcher_id"):
            raise LeaseConflictError("controller lease ownership changed")
        now = time.time()
        self.data.update(
            {
                "expires_at": iso_from_epoch(now + self.ttl_seconds),
                "last_heartbeat_at": iso_from_epoch(now),
                "run_id": run_id,
                "sequence": sequence,
            }
        )
        try:
            atomic_write_json(self.path, self.data)
        except OSError as exc:
            raise PersistenceError("cannot renew controller lease: %s" % exc) from exc

    def release(self) -> None:
        if self.released:
            return
        try:
            current = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            current = {}
        if current and current.get("watcher_id") != self.data.get("watcher_id"):
            raise LeaseConflictError("refusing to release a lease owned by another watcher")
        tombstone = self.lock_dir.with_name(self.lock_dir.name + ".released." + uuid.uuid4().hex)
        try:
            os.rename(self.lock_dir, tombstone)
            shutil.rmtree(tombstone, ignore_errors=True)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise PersistenceError("cannot release controller lease: %s" % exc) from exc
        self.released = True


def list_lease_records(state_root: Path) -> List[Dict[str, Any]]:
    leases_root = state_root / "leases"
    if not leases_root.is_dir():
        return []
    records: List[Dict[str, Any]] = []
    for lock_dir in sorted(leases_root.glob("*.lock"))[:200]:
        try:
            data = json.loads((lock_dir / "lease.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {"corrupt": True, "lock_dir": str(lock_dir)}
        data["live"] = lease_is_live(data)
        records.append(data)
    return records


def find_status_record(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        keys = {normalize_name(key) for key in value}
        if "status" in keys or "latest_run" in keys or "waiting_for_input" in keys:
            return value
        for item in value.values():
            found = find_status_record(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_status_record(item)
            if found:
                return found
    return {}


def get_key(record: Mapping[str, Any], *names: str) -> Any:
    targets = {normalize_name(name) for name in names}
    for key, value in record.items():
        if normalize_name(key) in targets:
            return value
    return None


def normalized_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def classify_status(payload: Any) -> Dict[str, Any]:
    record = find_status_record(payload)
    latest = get_key(record, "latestRun", "latest_run")
    if not isinstance(latest, dict):
        latest = {}
    session_status = normalize_name(get_key(record, "status", "state")) or "unknown"
    run_status = normalize_name(get_key(latest, "status", "state")) or "unknown"
    waiting = normalized_bool(get_key(record, "waitingForInput", "waiting_for_input"))
    actively_managed = normalized_bool(get_key(record, "activelyManaged", "actively_managed"))
    session_active = actively_managed or session_status in RUNNING_STATES
    stale_latest_run = session_active and run_status in TERMINAL_STATES
    if waiting or session_status in WAITING_STATES:
        category = "waiting_for_input"
    elif session_active:
        category = "running"
    elif run_status in RUNNING_STATES:
        category = "running"
    elif session_status in TERMINAL_STATES or run_status in TERMINAL_STATES:
        category = "terminal"
    elif session_status in IDLE_STATES:
        category = "idle"
    else:
        category = "unknown"
    run_id = get_key(latest, "runId", "run_id", "id")
    markers = {
        "ended_at": get_key(latest, "endedAt", "ended_at", "completedAt", "completed_at"),
        "last_message_id": get_key(record, "lastMessageId", "last_message_id", "messageId", "message_id"),
        "run_id": run_id,
        "started_at": get_key(latest, "startedAt", "started_at"),
        "updated_at": get_key(latest, "updatedAt", "updated_at") or get_key(record, "updatedAt", "updated_at"),
        "user_message_id": get_key(latest, "userMessageId", "user_message_id"),
    }
    return {
        "actively_managed": actively_managed,
        "category": category,
        "markers": {key: value for key, value in markers.items() if value is not None},
        "run_id": str(run_id) if run_id is not None else None,
        "run_status": run_status,
        "session_status": session_status,
        "stale_latest_run": stale_latest_run,
        "waiting_for_input": waiting,
    }


def state_signature(state: Mapping[str, Any]) -> str:
    signature_state = dict(state)
    guard = signature_state.get("run_guard")
    if isinstance(guard, Mapping):
        signature_state["run_guard"] = {
            key: guard.get(key)
            for key in (
                "baseline_run_id",
                "eligible",
                "superseded",
                "terminal_eligible",
                "watched_run_id",
            )
        }
    return json.dumps(signature_state, sort_keys=True, separators=(",", ":"), default=str)


class RunGuard:
    def __init__(
        self,
        *,
        expect_run_id: Optional[str],
        after_run_id: Optional[str],
        allow_existing_terminal: bool,
    ) -> None:
        self.expect_run_id = expect_run_id
        self.after_run_id = after_run_id
        self.allow_existing_terminal = allow_existing_terminal
        self.initialized = False
        self.watched_run_id: Optional[str] = expect_run_id
        self.baseline_run_id: Optional[str] = after_run_id
        self.observed_nonterminal = False
        self.awaiting_new_run = False
        self.adopted_after_baseline = False
        self.expected_seen = False

    @property
    def run_key(self) -> str:
        if self.expect_run_id:
            return "expect:%s" % self.expect_run_id
        if self.after_run_id:
            return "after:%s" % self.after_run_id
        return "auto"

    def observe(self, state: Mapping[str, Any]) -> Dict[str, Any]:
        run_id = state.get("run_id")
        category = state.get("category")
        stale = bool(state.get("stale_latest_run"))
        reason = ""
        superseded = False

        if self.expect_run_id:
            eligible = run_id == self.expect_run_id
            if eligible:
                self.expected_seen = True
            elif self.expected_seen and run_id:
                superseded = True
            if eligible:
                reason = "expected_run_matched"
            elif superseded:
                reason = "expected_run_superseded"
            else:
                reason = "waiting_for_expected_run"
        elif self.after_run_id:
            if run_id and run_id != self.after_run_id:
                if self.watched_run_id and run_id != self.watched_run_id:
                    superseded = True
                    eligible = False
                    reason = "newer_run_replaced_watched_run"
                else:
                    self.watched_run_id = str(run_id)
                    self.adopted_after_baseline = True
                    eligible = True
                    reason = "new_run_after_baseline"
            else:
                eligible = False
                reason = "waiting_for_run_after_baseline"
        else:
            if not self.initialized:
                self.baseline_run_id = str(run_id) if run_id else None
                if stale:
                    self.awaiting_new_run = True
                    reason = "session_running_with_stale_terminal_latest_run"
                elif category == "terminal" and not self.allow_existing_terminal:
                    self.awaiting_new_run = True
                    reason = "existing_terminal_requires_new_run"
                elif category in {"running", "waiting_for_input"}:
                    self.watched_run_id = str(run_id) if run_id else None
                    self.observed_nonterminal = True
                    reason = "watching_current_active_run"
                elif category == "terminal" and self.allow_existing_terminal:
                    self.watched_run_id = str(run_id) if run_id else None
                    reason = "existing_terminal_explicitly_allowed"
                else:
                    self.awaiting_new_run = True
                    reason = "waiting_for_future_run"
                self.initialized = True
            if self.awaiting_new_run:
                if run_id and run_id != self.baseline_run_id:
                    if self.watched_run_id is None:
                        self.watched_run_id = str(run_id)
                        self.adopted_after_baseline = True
                    if self.watched_run_id != run_id:
                        superseded = True
                        reason = "run_changed_after_watcher_adopted_run"
                    else:
                        reason = "new_run_observed"
                elif not reason:
                    reason = "waiting_for_run_after_baseline"
                eligible = bool(self.watched_run_id and run_id == self.watched_run_id)
            else:
                if self.watched_run_id is None and run_id and category in {"running", "waiting_for_input"}:
                    self.watched_run_id = str(run_id)
                    reason = "active_run_id_observed"
                if self.watched_run_id and run_id and run_id != self.watched_run_id:
                    superseded = True
                    reason = "run_changed_after_watcher_started"
                eligible = bool(not superseded and self.watched_run_id and run_id == self.watched_run_id)

        if category in {"running", "waiting_for_input"} and not stale:
            self.observed_nonterminal = True
        terminal_eligible = bool(
            eligible
            and category == "terminal"
            and not stale
            and (
                self.allow_existing_terminal
                or self.expect_run_id is not None
                or self.after_run_id is not None
                or self.adopted_after_baseline
                or self.observed_nonterminal
            )
        )
        return {
            "baseline_run_id": self.baseline_run_id,
            "eligible": bool(eligible),
            "reason": reason,
            "superseded": superseded,
            "terminal_eligible": terminal_eligible,
            "watched_run_id": self.watched_run_id,
        }


def target_reached(until: str, state: Mapping[str, Any], changed: bool, guard: Mapping[str, Any]) -> bool:
    category = state.get("category")
    if until == "change":
        return changed
    if until == "terminal":
        return bool(guard.get("terminal_eligible"))
    if until == "input":
        return category == "waiting_for_input" and bool(guard.get("eligible"))
    if until == "idle":
        return category in {"idle", "terminal", "waiting_for_input"} and bool(guard.get("eligible"))
    return False


def sanitize_data(value: Any, secret_values_list: Sequence[str], max_string_chars: int) -> Tuple[Any, int]:
    truncated_strings = 0

    def visit(item: Any) -> Any:
        nonlocal truncated_strings
        if isinstance(item, str):
            text = redact(item, secret_values_list)
            if len(text) > max_string_chars:
                truncated_strings += 1
                return text[:max_string_chars] + "…<truncated %d chars>" % (len(text) - max_string_chars)
            return text
        if isinstance(item, list):
            return [visit(child) for child in item]
        if isinstance(item, dict):
            return {
                str(key): (
                    "<redacted>"
                    if any(fragment in normalize_name(key) for fragment in SENSITIVE_FRAGMENTS)
                    else visit(child)
                )
                for key, child in item.items()
            }
        return item

    return visit(value), truncated_strings


def apply_output_bounds(
    value: Any,
    *,
    secret_values_list: Sequence[str],
    max_output_bytes: int,
    max_string_chars: int,
) -> Tuple[Any, Dict[str, Any]]:
    sanitized, truncated_strings = sanitize_data(value, secret_values_list, max_string_chars)
    serialized = json_bytes(sanitized)
    meta = {
        "max_output_bytes": max_output_bytes,
        "max_string_chars": max_string_chars,
        "original_bytes": len(serialized),
        "strings_truncated": truncated_strings,
    }
    if len(serialized) <= max_output_bytes:
        meta["output_truncated"] = False
        return sanitized, meta
    prefix_bytes = serialized[: max(0, max_output_bytes - 512)]
    prefix = prefix_bytes.decode("utf-8", errors="ignore")
    meta["output_truncated"] = True
    return {
        "json_prefix": prefix,
        "original_bytes": len(serialized),
        "truncated": True,
    }, meta


def compact_records(data: Any, fields: Sequence[str]) -> Any:
    if not isinstance(data, list):
        return data
    return [
        {field: item[field] for field in fields if field in item}
        for item in data
        if isinstance(item, dict)
    ]


def contains_record_id(value: Any, expected_id: str) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if normalize_name(key) == "id" and str(child) == expected_id:
                return True
            if contains_record_id(child, expected_id):
                return True
    elif isinstance(value, list):
        return any(contains_record_id(item, expected_id) for item in value)
    return False


def require_record_id(value: Any, expected_id: str, resource: str) -> None:
    if contains_record_id(value, expected_id):
        return
    raise McpError(
        "unknown Jean %s ID: %s" % (resource, expected_id),
        code="mcp_not_found",
        retryable=False,
        details={"resource": resource, "resource_id": expected_id},
    )


def count_record_values(records: Sequence[Any], field: str, fallback: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for record in records:
        value = get_key(record, field) if isinstance(record, dict) else None
        name = str(value or fallback)
        counts[name] = counts.get(name, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def compact_message_record(
    record: Mapping[str, Any],
    *,
    include_tool_details: bool,
    max_tool_calls: int,
    max_content_chars: int,
) -> Dict[str, Any]:
    fields = (
        "id",
        "role",
        "timestamp",
        "content",
        "cancelled",
        "recovered",
        "plan_approved",
        "model",
        "execution_mode",
        "thinking_level",
        "effort_level",
    )
    compact = {field: record[field] for field in fields if field in record}
    content = compact.get("content")
    if isinstance(content, str) and len(content) > max_content_chars:
        compact["content"] = content[:max_content_chars] + "…<truncated %d chars>" % (
            len(content) - max_content_chars
        )
        compact["content_original_chars"] = len(content)
        compact["content_truncated"] = True

    raw_tool_calls = record.get("tool_calls")
    tool_calls = list(raw_tool_calls) if isinstance(raw_tool_calls, list) else []
    raw_content_blocks = record.get("content_blocks")
    content_blocks = list(raw_content_blocks) if isinstance(raw_content_blocks, list) else []
    compact["tool_call_summary"] = {
        "by_name": count_record_values(tool_calls, "name", "unknown"),
        "total": len(tool_calls),
    }
    compact["content_block_summary"] = {
        "by_type": count_record_values(content_blocks, "type", "unknown"),
        "total": len(content_blocks),
    }

    if include_tool_details:
        selected_tool_calls = tool_calls[-max_tool_calls:]
        selected_ids = {
            str(item.get("id"))
            for item in selected_tool_calls
            if isinstance(item, dict) and item.get("id") is not None
        }
        compact["tool_calls"] = selected_tool_calls
        compact["tool_calls_truncated"] = max(0, len(tool_calls) - len(selected_tool_calls))
        compact["content_blocks"] = [
            block
            for block in content_blocks
            if not isinstance(block, dict)
            or normalize_name(block.get("type")) != "tool_use"
            or str(block.get("tool_call_id")) in selected_ids
        ]
        compact["content_blocks_truncated"] = max(
            0,
            len(content_blocks) - len(compact["content_blocks"]),
        )
    return compact


def compact_message_response(
    data: Any,
    *,
    limit: int,
    include_tool_details: bool,
    max_tool_calls: int,
    max_content_chars: int,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("messages"), list):
        raise McpError(
            "Jean returned an unexpected session-message shape",
            code="unexpected_message_shape",
            retryable=False,
        )
    raw_messages = data["messages"]
    if any(not isinstance(item, dict) for item in raw_messages):
        raise McpError(
            "Jean returned a non-record session message",
            code="unexpected_message_shape",
            retryable=False,
        )
    selected_messages = raw_messages[-limit:]
    result = dict(data)
    result["messages"] = [
        compact_message_record(
            item,
            include_tool_details=include_tool_details,
            max_tool_calls=max_tool_calls,
            max_content_chars=max_content_chars,
        )
        for item in selected_messages
    ]
    meta = {
        "available_session_messages": get_key(data, "messageCount", "message_count"),
        "include_tool_details": include_tool_details,
        "limit_unit": "message_records",
        "max_content_chars_per_message": max_content_chars,
        "max_tool_calls_per_message": max_tool_calls if include_tool_details else 0,
        "requested_limit": limit,
        "returned_messages": len(result["messages"]),
        "upstream_returned_messages": len(raw_messages),
        "wrapper_trimmed_messages": max(0, len(raw_messages) - len(selected_messages)),
    }
    return result, meta


def compact_sessions(data: Any) -> Any:
    if not isinstance(data, dict) or not isinstance(data.get("sessions"), list):
        return data
    fields = (
        "id",
        "name",
        "backend",
        "selectedModel",
        "selectedProvider",
        "selectedExecutionMode",
        "lastRunStatus",
        "waitingForInput",
        "waitingForInputType",
        "messageCount",
        "lastMessageAt",
        "updatedAt",
        "archivedAt",
    )
    return {
        "activeSessionId": data.get("activeSessionId"),
        "sessions": compact_records(data["sessions"], fields),
        "worktreeId": data.get("worktreeId"),
    }


def build_runtime(
    args: argparse.Namespace,
    *,
    require_socket: bool = True,
) -> Tuple[Dict[str, Any], Mcp2Cli, Dict[str, Any]]:
    config = load_jean_config(
        Path(args.config),
        allow_unsafe_config=args.allow_unsafe_config,
    )
    executable = validate_jean_command(config, allow_unsafe_config=args.allow_unsafe_config)
    socket_report = socket_health(config, allow_unsafe_config=args.allow_unsafe_config) if require_socket else {}
    backend = resolve_backend(args.backend, allow_unsafe_backend=args.allow_unsafe_backend)
    trust = {
        "backend": backend,
        "config_parser": config["parser"],
        "config_source": config["source"],
        "jean_executable": str(executable),
        "socket": socket_report,
        "unsafe_backend": bool(args.allow_unsafe_backend),
        "unsafe_config": bool(args.allow_unsafe_config),
    }
    return config, Mcp2Cli(config, backend, args.call_timeout), trust


def command_deadline(args: argparse.Namespace) -> float:
    return time.monotonic() + args.call_timeout


def emit_bounded_success(
    args: argparse.Namespace,
    data: Any,
    *,
    meta: Optional[Mapping[str, Any]],
    secret_values_list: Sequence[str],
    max_output_bytes: Optional[int] = None,
    max_string_chars: Optional[int] = None,
) -> int:
    bounded, bounds = apply_output_bounds(
        data,
        secret_values_list=secret_values_list,
        max_output_bytes=max_output_bytes if max_output_bytes is not None else args.max_output_bytes,
        max_string_chars=max_string_chars if max_string_chars is not None else args.max_string_chars,
    )
    combined_meta = dict(meta or {})
    combined_meta["bounds"] = bounds
    print_json(success_envelope(args.command, bounded, combined_meta), args.pretty)
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    deadline = command_deadline(args)
    config, client, trust = build_runtime(args)
    version = client.version(deadline)
    data: Dict[str, Any] = {
        "mcp2cli_version": version,
        "python": "%d.%d.%d" % sys.version_info[:3],
        "script_version": VERSION,
        "trust": trust,
    }
    if args.probe:
        required_names = parse_required_tools(args.require)
        required = {
            name: EXPECTED_REQUIRED_INPUTS.get(name, set())
            for name in required_names
        }
        data["capabilities"] = client.validate_capabilities(required, deadline)
        data["tool_count"] = len(client.list_tools(deadline))
    return emit_bounded_success(args, data, meta={}, secret_values_list=client.secret_values)


def parse_required_tools(values: Sequence[str]) -> List[str]:
    result: List[str] = []
    for value in values:
        result.extend(normalize_name(item) for item in value.split(",") if item.strip())
    return sorted(set(result))


def command_tools(args: argparse.Namespace) -> int:
    deadline = command_deadline(args)
    _config, client, _trust = build_runtime(args)
    entries = client.list_tools(deadline)
    data = {
        "mutating_blocked": sorted(entry["name"] for entry in entries if entry_canonical_name(entry) in MUTATING_TOOLS),
        "read_only": sorted(entry["name"] for entry in entries if entry_canonical_name(entry) in READ_ONLY_TOOLS),
        "schema_hash": client.capability_hash,
        "tool_count": len(entries),
    }
    return emit_bounded_success(args, data, meta={}, secret_values_list=client.secret_values)


def command_schema(args: argparse.Namespace) -> int:
    deadline = command_deadline(args)
    _config, client, _trust = build_runtime(args)
    entry = client.resolve_tool(args.tool, deadline)
    data = {
        "schema": entry,
        "schema_hash": client.capability_hash,
        "tool": entry_canonical_name(entry),
    }
    return emit_bounded_success(args, data, meta={}, secret_values_list=client.secret_values)


def command_capabilities(args: argparse.Namespace) -> int:
    deadline = command_deadline(args)
    _config, client, _trust = build_runtime(args)
    required_names = parse_required_tools(args.require)
    required = {name: EXPECTED_REQUIRED_INPUTS.get(name, set()) for name in required_names}
    data = client.validate_capabilities(required, deadline)
    data["available_read_tools"] = sorted(
        entry_canonical_name(entry)
        for entry in client.list_tools(deadline)
        if entry_canonical_name(entry) in READ_ONLY_TOOLS
    )
    return emit_bounded_success(args, data, meta={}, secret_values_list=client.secret_values)


def call_and_emit(
    args: argparse.Namespace,
    tool: str,
    arguments: Mapping[str, Any],
    *,
    transform: Optional[Callable[[Any], Any]] = None,
) -> int:
    deadline = command_deadline(args)
    _config, client, _trust = build_runtime(args)
    data = client.call(tool, arguments, deadline)
    if transform:
        data = transform(data)
    meta = {"schema_hash": client.capability_hash, "tool": normalize_name(tool)}
    if normalize_name(tool) == "get_session_status":
        meta["normalized_status"] = classify_status(data)
    return emit_bounded_success(args, data, meta=meta, secret_values_list=client.secret_values)


def command_projects(args: argparse.Namespace) -> int:
    return call_and_emit(
        args,
        "list_projects",
        {},
        transform=lambda data: compact_records(data, ("id", "name", "path", "default_branch", "is_folder")),
    )


def command_worktrees(args: argparse.Namespace) -> int:
    fields = (
        "id",
        "name",
        "path",
        "project_id",
        "session_type",
        "branch",
        "base_branch",
        "labels",
        "cached_uncommitted_added",
        "cached_uncommitted_removed",
        "cached_unpushed_count",
        "cached_worktree_ahead_count",
        "cached_base_branch_ahead_count",
        "cached_base_branch_behind_count",
        "cached_status_at",
        "last_opened_at",
    )
    deadline = command_deadline(args)
    _config, client, _trust = build_runtime(args)
    projects = client.call("list_projects", {}, deadline)
    require_record_id(projects, args.project_id, "project")
    data = client.call("list_worktrees", {"project_id": args.project_id}, deadline)
    return emit_bounded_success(
        args,
        compact_records(data, fields),
        meta={
            "parent_id_verified": True,
            "project_id": args.project_id,
            "schema_hash": client.capability_hash,
            "tool": "list_worktrees",
        },
        secret_values_list=client.secret_values,
    )


def command_sessions(args: argparse.Namespace) -> int:
    deadline = command_deadline(args)
    _config, client, _trust = build_runtime(args)
    worktree = client.call("get_worktree", {"worktree_id": args.worktree_id}, deadline)
    require_record_id(worktree, args.worktree_id, "worktree")
    data = client.call(
        "list_sessions",
        {"worktree_id": args.worktree_id, "include_archived": args.include_archived},
        deadline,
    )
    return emit_bounded_success(
        args,
        compact_sessions(data),
        meta={
            "parent_id_verified": True,
            "schema_hash": client.capability_hash,
            "tool": "list_sessions",
            "worktree_id": args.worktree_id,
        },
        secret_values_list=client.secret_values,
    )


def command_status(args: argparse.Namespace) -> int:
    return call_and_emit(args, "get_session_status", {"session_id": args.session_id})


def command_messages(args: argparse.Namespace) -> int:
    deadline = command_deadline(args)
    _config, client, _trust = build_runtime(args)
    raw = client.call(
        "read_session_messages",
        {"session_id": args.session_id, "limit": args.limit},
        deadline,
    )
    data, message_meta = compact_message_response(
        raw,
        limit=args.limit,
        include_tool_details=args.include_tool_details,
        max_tool_calls=args.max_tool_calls,
        max_content_chars=args.message_content_chars,
    )
    output_limit = min(
        args.max_output_bytes,
        EXPANDED_MESSAGE_OUTPUT_BYTES if args.include_tool_details else DEFAULT_MESSAGE_OUTPUT_BYTES,
    )
    return emit_bounded_success(
        args,
        data,
        meta={
            "messages": message_meta,
            "schema_hash": client.capability_hash,
            "tool": "read_session_messages",
        },
        secret_values_list=client.secret_values,
        max_output_bytes=output_limit,
    )


def command_changes(args: argparse.Namespace) -> int:
    return call_and_emit(
        args,
        "get_worktree_changes",
        {"worktree_id": args.worktree_id, "max_files": args.max_files},
    )


def parse_generic_arguments(values: Sequence[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for raw in values:
        if "=" not in raw:
            raise UsageError("--arg must use key=value")
        key, value = raw.split("=", 1)
        normalized = normalize_name(key)
        if not normalized or value == "":
            raise UsageError("--arg must use non-empty key=value")
        if any(fragment in normalized for fragment in SENSITIVE_FRAGMENTS):
            raise TrustError("credential-shaped --arg keys are forbidden")
        if normalized in result:
            raise UsageError("duplicate --arg key: %s" % key)
        result[normalized] = value
    return result


def command_read(args: argparse.Namespace) -> int:
    return call_and_emit(args, args.tool, parse_generic_arguments(args.arg))


def command_leases(args: argparse.Namespace) -> int:
    records = list_lease_records(Path(args.state_root).expanduser())
    return emit_bounded_success(args, records, meta={"count": len(records)}, secret_values_list=[])


class EventStream:
    def __init__(
        self,
        *,
        watcher_id: str,
        session_id: str,
        writer: CheckpointWriter,
    ) -> None:
        self.watcher_id = watcher_id
        self.session_id = session_id
        self.writer = writer
        self.sequence = 0

    def emit(
        self,
        event: str,
        *,
        data: Optional[Mapping[str, Any]] = None,
        error: Optional[JeanOpsError] = None,
        checkpoint: bool = True,
    ) -> Dict[str, Any]:
        self.sequence += 1
        envelope: Dict[str, Any] = {
            "event": event,
            "observed_at": utc_now(),
            "schema_version": SCHEMA_VERSION,
            "sequence": self.sequence,
            "session_id": self.session_id,
            "watcher_id": self.watcher_id,
        }
        if data:
            envelope["data"] = dict(data)
        if error:
            envelope["error"] = error.as_dict()
            envelope["exit_code"] = error.exit_code
        print_json(envelope)
        if checkpoint:
            persistence_error = self.writer.write(
                {
                    "last_event": envelope,
                    "schema_version": SCHEMA_VERSION,
                    "session_id": self.session_id,
                    "updated_at": utc_now(),
                    "watcher_id": self.watcher_id,
                }
            )
            if persistence_error:
                self.emit("persistence_error", error=persistence_error, checkpoint=False)
                raise persistence_error
        return envelope


def call_with_transient_retries(
    operation: Callable[[], Any],
    *,
    deadline: float,
    retry_budget: int,
    on_retry: Callable[[int, McpError], None],
    sleep_function: Callable[[float], bool],
) -> Any:
    attempt = 0
    while True:
        try:
            return operation()
        except McpError as exc:
            if not exc.retryable or attempt >= retry_budget:
                raise
            attempt += 1
            on_retry(attempt, exc)
            delay = min(2.0, 0.5 * (2 ** (attempt - 1)), max(0.0, remaining_seconds(deadline)))
            if delay <= 0:
                raise DeadlineExceeded("global deadline exhausted during transient retry") from exc
            if not sleep_function(delay):
                raise LeaseConflictError("watcher lost ownership during transient retry")


def default_result_path(state_root: Path, session_id: str, watcher_id: str) -> Path:
    return state_root / "results" / lease_key(session_id) / (watcher_id + ".json")


def command_watch(args: argparse.Namespace) -> int:
    deadline = time.monotonic() + args.timeout
    watcher_id = uuid.uuid4().hex
    state_root = Path(args.state_root).expanduser().resolve()
    result_path = Path(args.result_file).expanduser() if args.result_file else default_result_path(
        state_root, args.session_id, watcher_id
    )
    initial = {
        "created_at": utc_now(),
        "outcome": "starting",
        "schema_version": SCHEMA_VERSION,
        "session_id": args.session_id,
        "watcher_id": watcher_id,
    }
    try:
        writer = CheckpointWriter.create(result_path, initial)
    except JeanOpsError as exc:
        print_json(
            {
                "error": exc.as_dict(),
                "event": "error",
                "exit_code": exc.exit_code,
                "observed_at": utc_now(),
                "schema_version": SCHEMA_VERSION,
                "sequence": 1,
                "session_id": args.session_id,
                "watcher_id": watcher_id,
            }
        )
        return exc.exit_code

    stream = EventStream(watcher_id=watcher_id, session_id=args.session_id, writer=writer)
    guard = RunGuard(
        expect_run_id=args.expect_run_id,
        after_run_id=args.after_run_id,
        allow_existing_terminal=args.allow_existing_terminal,
    )
    lease: Optional[SessionLease] = None
    state: Optional[Dict[str, Any]] = None
    guard_state: Dict[str, Any] = {}
    prior_signature: Optional[str] = None
    interval = args.interval
    poll_count = 0
    launch_parent_pid = os.getppid()
    last_lease_renewal = 0.0

    try:
        _config, client, trust = build_runtime(args)
        lease = SessionLease.acquire(
            state_root,
            session_id=args.session_id,
            run_key=guard.run_key,
            watcher_id=watcher_id,
            controller=args.controller,
            controller_id=args.controller_id,
            ttl_seconds=args.lease_ttl,
            result_path=result_path.resolve(),
        )

        def renew_lease(force: bool = False) -> None:
            nonlocal last_lease_renewal
            now = time.monotonic()
            if lease and (force or now - last_lease_renewal >= min(5.0, args.lease_ttl / 3.0)):
                lease.renew(run_id=guard.watched_run_id, sequence=stream.sequence)
                last_lease_renewal = now

        def still_owned() -> bool:
            if launch_parent_pid > 1 and os.getppid() != launch_parent_pid:
                return False
            renew_lease()
            return True

        def sleep_owned(duration: float) -> bool:
            end = time.monotonic() + max(0.0, duration)
            while remaining_seconds(end) > 0:
                if not still_owned():
                    return False
                time.sleep(min(0.5, max(0.0, remaining_seconds(end))))
            return still_owned()

        client.ownership_check = still_owned

        def handle_signal(signum: int, _frame: Any) -> None:
            if signum == getattr(signal, "SIGHUP", -1):
                error = ControllerLostError("controlling terminal disappeared")
                stream.emit("controller_lost", data={"result_path": str(result_path)}, error=error)
                raise SystemExit(129)
            code = 130 if signum == signal.SIGINT else 143
            error = JeanOpsError(
                "watcher interrupted by signal %d" % signum,
                code="interrupted",
                category="interruption",
                exit_code=code,
            )
            stream.emit("interrupted", data={"result_path": str(result_path)}, error=error)
            raise SystemExit(code)

        old_handlers: Dict[int, Any] = {}
        for signum in (signal.SIGINT, signal.SIGTERM, getattr(signal, "SIGHUP", signal.SIGTERM)):
            if signum not in old_handlers:
                old_handlers[signum] = signal.signal(signum, handle_signal)

        stream.emit(
            "start",
            data={
                "after_run_id": args.after_run_id,
                "allow_existing_terminal": args.allow_existing_terminal,
                "controller": args.controller,
                "controller_id": args.controller_id,
                "deadline_seconds": args.timeout,
                "expect_run_id": args.expect_run_id,
                "lease_expires_at": lease.data["expires_at"],
                "result_path": str(result_path.resolve()),
                "schema_hash_pending": True,
                "transport": "one-shot",
                "trust": trust,
                "until": args.until,
            },
        )
        renew_lease(force=True)

        try:
            while True:
                if remaining_seconds(deadline) <= 0:
                    error = DeadlineExceeded("watcher deadline expired")
                    stream.emit(
                        "timeout",
                        data={"guard": guard_state, "result_path": str(result_path), "state": state},
                        error=error,
                    )
                    return error.exit_code
                if not still_owned():
                    error = ControllerLostError("launch controller disappeared")
                    stream.emit("controller_lost", data={"state": state}, error=error)
                    return error.exit_code

                def status_operation() -> Any:
                    return client.call(
                        "get_session_status",
                        {"session_id": args.session_id},
                        deadline,
                    )

                try:
                    payload = call_with_transient_retries(
                        status_operation,
                        deadline=deadline,
                        retry_budget=args.transient_retries,
                        on_retry=lambda attempt, error: stream.emit(
                            "retry",
                            data={"attempt": attempt, "remaining_seconds": round(max(0.0, remaining_seconds(deadline)), 3)},
                            error=error,
                        ),
                        sleep_function=sleep_owned,
                    )
                except DeadlineExceeded as exc:
                    stream.emit(
                        "timeout",
                        data={"guard": guard_state, "result_path": str(result_path), "state": state},
                        error=exc,
                    )
                    return exc.exit_code

                state = classify_status(payload)
                guard_state = guard.observe(state)
                state_with_guard = dict(state)
                state_with_guard["run_guard"] = guard_state
                signature = state_signature(state_with_guard)
                changed = prior_signature is not None and signature != prior_signature
                poll_count += 1
                heartbeat_due = args.heartbeat_every > 0 and poll_count % args.heartbeat_every == 0
                if prior_signature is None:
                    event_name = "state"
                elif changed:
                    event_name = "state"
                elif heartbeat_due:
                    event_name = "heartbeat"
                else:
                    event_name = ""
                if event_name:
                    stream.emit(
                        event_name,
                        data={
                            "changed": changed,
                            "remaining_seconds": round(max(0.0, remaining_seconds(deadline)), 3),
                            "schema_hash": client.capability_hash,
                            "state": state_with_guard,
                        },
                    )
                renew_lease(force=True)

                if guard_state.get("superseded"):
                    error = SupersededError(
                        "a different Jean run replaced the watched run",
                        details={"guard": guard_state},
                    )
                    stream.emit("superseded", data={"state": state_with_guard}, error=error)
                    return error.exit_code

                if target_reached(args.until, state, changed, guard_state):
                    outcome = "observed_%s" % args.until
                    stream.emit(
                        "target",
                        data={
                            "outcome": outcome,
                            "result_path": str(result_path.resolve()),
                            "state": state_with_guard,
                        },
                    )
                    return 0

                interval = args.interval if changed else min(args.max_interval, max(args.interval, interval * args.backoff))
                prior_signature = signature
                sleep_duration = min(interval, max(0.0, remaining_seconds(deadline)))
                if not sleep_owned(sleep_duration):
                    error = ControllerLostError("launch controller disappeared")
                    stream.emit("controller_lost", data={"state": state_with_guard}, error=error)
                    return error.exit_code
        finally:
            for signum, handler in old_handlers.items():
                signal.signal(signum, handler)
    except JeanOpsError as exc:
        stream.emit(
            "error",
            data={"guard": guard_state, "result_path": str(result_path), "state": state},
            error=exc,
            checkpoint=False,
        )
        return exc.exit_code
    except OSError as exc:
        error = PersistenceError("watcher operating-system error: %s" % exc)
        stream.emit("error", data={"result_path": str(result_path), "state": state}, error=error)
        return error.exit_code
    finally:
        if lease:
            try:
                lease.release()
            except JeanOpsError as exc:
                stream.emit("lease_cleanup_error", error=exc, checkpoint=False)


def self_check(tests: List[str], name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise SelfTestError("%s failed%s" % (name, ": " + detail if detail else ""))
    tests.append(name)


def self_expect_error(
    tests: List[str],
    name: str,
    expected: type,
    operation: Callable[[], Any],
) -> None:
    try:
        operation()
    except expected:
        tests.append(name)
        return
    except Exception as exc:
        raise SelfTestError("%s raised %s instead of %s" % (name, type(exc).__name__, expected.__name__)) from exc
    raise SelfTestError("%s did not raise %s" % (name, expected.__name__))


def command_self_test(args: argparse.Namespace) -> int:
    tests: List[str] = []
    with tempfile.TemporaryDirectory(prefix="jean-ops-self-test-") as directory:
        root = Path(directory)
        config_path = root / "config.toml"
        config_path.write_text(
            '[mcp_servers.jean]\ncommand = "/Applications/Jean.app/Contents/MacOS/jean"\nargs = ["--jean-mcp-stdio"]\n'
            '[mcp_servers.jean.env]\nJEAN_MCP_SOCKET = "/tmp/jean.sock"\nJEAN_MCP_TOKEN = "test-secret-value"\n',
            encoding="utf-8",
        )
        parsed = load_jean_config(config_path, allow_unsafe_config=True)
        self_check(tests, "config_parser", parsed["args"] == ["--jean-mcp-stdio"])

        duplicate = root / "duplicate.toml"
        duplicate.write_text(
            '[mcp_servers.jean]\ncommand = "x"\ncommand = "y"\nargs = []\n[mcp_servers.jean.env]\n',
            encoding="utf-8",
        )
        self_expect_error(
            tests,
            "config_duplicate_rejected",
            ConfigError,
            lambda: restricted_jean_toml(duplicate),
        )

        multi = unwrap_result(
            {
                "content": [
                    {"type": "text", "text": "notice"},
                    {"type": "text", "text": '{"status":"running"}'},
                ]
            }
        )
        self_check(
            tests,
            "multiple_content_blocks",
            isinstance(multi, dict) and multi.get("data", {}).get("status") == "running" and multi.get("text_blocks") == ["notice"],
        )

        stale = classify_status(
            {
                "activelyManaged": True,
                "status": "running",
                "latestRun": {"endedAt": 1, "runId": "old", "status": "completed"},
            }
        )
        self_check(
            tests,
            "old_terminal_run_is_not_terminal",
            stale["category"] == "running" and stale["stale_latest_run"] is True,
        )
        string_boolean_state = classify_status(
            {"activelyManaged": "false", "status": "idle", "latestRun": {"runId": "r", "status": "completed"}}
        )
        self_check(
            tests,
            "string_false_is_not_active",
            string_boolean_state["actively_managed"] is False and string_boolean_state["category"] == "terminal",
        )

        guard = RunGuard(expect_run_id=None, after_run_id=None, allow_existing_terminal=False)
        first_guard = guard.observe(stale)
        new_running = classify_status(
            {"activelyManaged": True, "status": "running", "latestRun": {"runId": "new", "status": "running"}}
        )
        second_guard = guard.observe(new_running)
        new_terminal = classify_status(
            {"activelyManaged": False, "status": "idle", "latestRun": {"runId": "new", "status": "completed"}}
        )
        third_guard = guard.observe(new_terminal)
        self_check(
            tests,
            "run_guard_requires_new_run",
            not first_guard["terminal_eligible"] and second_guard["watched_run_id"] == "new" and third_guard["terminal_eligible"],
        )

        late_id_guard = RunGuard(expect_run_id=None, after_run_id=None, allow_existing_terminal=False)
        unknown_first = late_id_guard.observe({"category": "unknown", "run_id": None, "stale_latest_run": False})
        late_running = late_id_guard.observe(new_running)
        late_terminal = late_id_guard.observe(new_terminal)
        self_check(
            tests,
            "late_run_id_is_adopted",
            not unknown_first["eligible"] and late_running["watched_run_id"] == "new" and late_terminal["terminal_eligible"],
        )

        expected_guard = RunGuard(expect_run_id="wanted", after_run_id=None, allow_existing_terminal=False)
        wrong = expected_guard.observe(new_terminal)
        wanted_terminal = classify_status(
            {"status": "idle", "latestRun": {"runId": "wanted", "status": "completed"}}
        )
        right = expected_guard.observe(wanted_terminal)
        self_check(tests, "expected_run_id", not wrong["eligible"] and right["terminal_eligible"])

        guard_reason_a = {
            "category": "terminal",
            "run_id": "old",
            "run_guard": {
                "baseline_run_id": "old",
                "eligible": False,
                "reason": "existing_terminal_requires_new_run",
                "superseded": False,
                "terminal_eligible": False,
                "watched_run_id": None,
            },
        }
        guard_reason_b = json.loads(json.dumps(guard_reason_a))
        guard_reason_b["run_guard"]["reason"] = "waiting_for_run_after_baseline"
        self_check(
            tests,
            "run_guard_reason_not_state",
            state_signature(guard_reason_a) == state_signature(guard_reason_b),
        )

        require_record_id([{"id": "project-1"}], "project-1", "project")
        self_check(tests, "parent_id_validation", True)
        self_expect_error(
            tests,
            "unknown_parent_rejected",
            McpError,
            lambda: require_record_id([{"id": "project-1"}], "missing", "project"),
        )

        message_fixture = {
            "id": "session-1",
            "message_count": 2,
            "messages": [
                {"id": "user-1", "role": "user", "content": "question", "tool_calls": []},
                {
                    "id": "assistant-1",
                    "role": "assistant",
                    "content": "x" * 50_000,
                    "content_blocks": [
                        {"type": "tool_use", "tool_call_id": "tool-1"},
                        {"type": "tool_use", "tool_call_id": "tool-2"},
                        {"type": "tool_use", "tool_call_id": "tool-3"},
                    ],
                    "tool_calls": [
                        {"id": "tool-1", "name": "Bash", "input": "a" * 50_000},
                        {"id": "tool-2", "name": "Bash", "input": "b" * 50_000},
                        {"id": "tool-3", "name": "FileChange", "output": "c" * 50_000},
                    ],
                },
            ],
        }
        compact_messages, compact_meta = compact_message_response(
            message_fixture,
            limit=1,
            include_tool_details=False,
            max_tool_calls=DEFAULT_MAX_TOOL_CALLS,
            max_content_chars=DEFAULT_MESSAGE_CONTENT_CHARS,
        )
        compact_record = compact_messages["messages"][0]
        self_check(
            tests,
            "message_record_limit",
            len(compact_messages["messages"]) == 1
            and compact_meta["limit_unit"] == "message_records"
            and compact_meta["wrapper_trimmed_messages"] == 1,
        )
        self_check(
            tests,
            "compact_messages_omit_tool_payloads",
            "tool_calls" not in compact_record
            and compact_record["tool_call_summary"]["total"] == 3
            and len(json_bytes(compact_messages)) < DEFAULT_MESSAGE_OUTPUT_BYTES,
        )
        expanded_messages, expanded_meta = compact_message_response(
            message_fixture,
            limit=1,
            include_tool_details=True,
            max_tool_calls=2,
            max_content_chars=DEFAULT_MESSAGE_CONTENT_CHARS,
        )
        self_check(
            tests,
            "expanded_tool_details_are_bounded",
            len(expanded_messages["messages"][0]["tool_calls"]) == 2
            and expanded_messages["messages"][0]["tool_calls_truncated"] == 1
            and expanded_meta["max_tool_calls_per_message"] == 2,
        )

        entries = [
            {"name": "list-projects", "toolName": "list_projects", "parameters": []},
            {
                "name": "get-session-status",
                "toolName": "get_session_status",
                "parameters": [{"name": "session-id", "type": "str", "required": True}],
            },
        ]
        self_check(tests, "schema_hash_stable", schema_hash(entries) == schema_hash(list(reversed(entries))))

        fake_config = {
            "args": ["--jean-mcp-stdio"],
            "command": str(EXPECTED_JEAN_EXECUTABLE),
            "env": {},
        }
        changed_schema_client = Mcp2Cli(fake_config, ["/bin/true"], 1)
        changed_schema_client._catalog = {
            "get_session_status": {
                "name": "get-session-status",
                "toolName": "get_session_status",
                "parameters": [{"name": "session-id", "type": "str", "required": False}],
            }
        }
        changed_schema_client._schema_hash = schema_hash(changed_schema_client._catalog.values())
        self_expect_error(
            tests,
            "changed_required_schema_rejected",
            McpError,
            lambda: changed_schema_client.validate_capabilities(
                {"get_session_status": {"session_id"}},
                time.monotonic() + 1,
            ),
        )

        collision_client = Mcp2Cli(fake_config, ["/bin/true"], 1)
        collision_client._run = lambda *_args, **_kwargs: [  # type: ignore
            {"name": "list-projects", "toolName": "list_projects", "parameters": []},
            {"name": "list_projects", "toolName": "list-projects", "parameters": []},
            {
                "name": "list-worktrees",
                "toolName": "list_worktrees",
                "parameters": [{"name": "project-id", "type": "str", "required": True}],
            },
            {
                "name": "list-sessions",
                "toolName": "list_sessions",
                "parameters": [{"name": "worktree-id", "type": "str", "required": True}],
            },
            {
                "name": "get-session-status",
                "toolName": "get_session_status",
                "parameters": [{"name": "session-id", "type": "str", "required": True}],
            },
        ]
        self_expect_error(
            tests,
            "tool_name_collision_rejected",
            TrustError,
            lambda: collision_client.list_tools(time.monotonic() + 1),
        )

        self_expect_error(
            tests,
            "unknown_schema_argument_rejected",
            UsageError,
            lambda: build_tool_flags(entries[1], {"session_id": "s", "invented": "x"}),
        )

        result_path = root / "result.json"
        writer = CheckpointWriter.create(result_path, {"state": "start"})
        self_check(tests, "result_mode", stat.S_IMODE(result_path.stat().st_mode) == 0o600)
        self_expect_error(
            tests,
            "result_collision",
            PersistenceError,
            lambda: CheckpointWriter.create(result_path, {"state": "again"}),
        )
        unsafe_result_parent = root / "unsafe-result-parent"
        unsafe_result_parent.mkdir(mode=0o777)
        unsafe_result_parent.chmod(0o777)
        self_expect_error(
            tests,
            "unsafe_result_parent_rejected",
            PersistenceError,
            lambda: CheckpointWriter.create(unsafe_result_parent / "result.json", {"state": "start"}),
        )
        unsafe_result_parent.chmod(0o700)
        result_path.unlink()
        result_path.mkdir()
        write_error = writer.write({"state": "fail"})
        self_check(tests, "result_failure_is_disabled", isinstance(write_error, PersistenceError) and writer.disabled)

        stream_path = root / "stream-result.json"
        stream_writer = CheckpointWriter.create(stream_path, {"state": "start"})
        stream_path.unlink()
        stream_path.mkdir()
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            self_expect_error(
                tests,
                "stream_persistence_failure",
                PersistenceError,
                lambda: EventStream(
                    watcher_id="watcher-stream",
                    session_id="session-stream",
                    writer=stream_writer,
                ).emit("state", data={"status": "running"}),
            )
        stream_events = [json.loads(line) for line in captured.getvalue().splitlines() if line.strip()]
        self_check(
            tests,
            "stream_persistence_terminal_event",
            len(stream_events) == 2 and stream_events[-1].get("event") == "persistence_error",
        )

        lease_root = root / "state"
        lease_result = root / "lease-result.json"
        lease_result.write_text("{}", encoding="utf-8")
        first_lease = SessionLease.acquire(
            lease_root,
            session_id="session-1",
            run_key="expect:run-1",
            watcher_id="watcher-1",
            controller="codex-task",
            controller_id="task-1",
            ttl_seconds=30,
            result_path=lease_result,
        )
        self_expect_error(
            tests,
            "duplicate_lease",
            LeaseConflictError,
            lambda: SessionLease.acquire(
                lease_root,
                session_id="session-1",
                run_key="expect:run-1",
                watcher_id="watcher-2",
                controller="codex-task",
                controller_id="task-2",
                ttl_seconds=30,
                result_path=lease_result,
            ),
        )
        first_lease.release()

        os.environ["AWS_SECRET_ACCESS_KEY"] = "ambient-secret"
        environment = minimal_environment({"JEAN_MCP_TOKEN": "jean-secret"})
        self_check(
            tests,
            "minimal_environment",
            "AWS_SECRET_ACCESS_KEY" not in environment and environment.get("JEAN_MCP_TOKEN") == "jean-secret",
        )
        os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
        self_check(
            tests,
            "secret_redaction",
            "test-secret-value" not in redact("value=test-secret-value", ["test-secret-value"]),
        )
        heuristic_secret_text = redact(
            "Authorization: Bearer abcdefghijklmnop API_TOKEN=token-value ghp_abcdefghijklmnopqrstuvwxyz",
            [],
        )
        self_check(
            tests,
            "heuristic_secret_redaction",
            "abcdefghijklmnop" not in heuristic_secret_text
            and "token-value" not in heuristic_secret_text
            and "ghp_" not in heuristic_secret_text,
        )
        keyed_secret, _keyed_count = sanitize_data(
            {"password": "visible-value", "message": "safe"},
            [],
            1000,
        )
        self_check(tests, "secret_key_redaction", keyed_secret["password"] == "<redacted>")

        bounded, bound_meta = apply_output_bounds(
            {"message": "x" * 1000},
            secret_values_list=[],
            max_output_bytes=4096,
            max_string_chars=300,
        )
        self_check(
            tests,
            "output_bounds",
            bound_meta["strings_truncated"] == 1 and len(bounded["message"]) < 400,
        )

        stdout_deadline = time.monotonic() + 2
        return_code, stdout, stderr = run_subprocess(
            ["/bin/sh", "-c", "printf out; printf err >&2"],
            environment=minimal_environment({}),
            deadline=stdout_deadline,
            secrets_to_redact=[],
            phase="self-test stdout separation",
        )
        self_check(tests, "stdout_stderr_separation", return_code == 0 and stdout == "out" and stderr == "err")

        child_pid_path = root / "child.pid"
        start = time.monotonic()
        self_expect_error(
            tests,
            "global_deadline",
            DeadlineExceeded,
            lambda: run_subprocess(
                [
                    "/bin/sh",
                    "-c",
                    "sleep 5 & echo $! > %s; wait" % shlex.quote(str(child_pid_path)),
                ],
                environment=minimal_environment({}),
                deadline=time.monotonic() + 0.2,
                secrets_to_redact=[],
                phase="self-test deadline",
            ),
        )
        self_check(tests, "deadline_is_bounded", time.monotonic() - start < 1.5)
        if child_pid_path.exists():
            child_pid = int(child_pid_path.read_text(encoding="utf-8").strip())
            time.sleep(0.05)
            self_check(tests, "child_process_cleanup", not process_alive(child_pid))
        else:
            raise SelfTestError("child_process_cleanup failed: child PID was not recorded")

        attempts = {"count": 0}

        def flaky() -> str:
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise McpError("temporary transport", retryable=True)
            return "ok"

        retry_value = call_with_transient_retries(
            flaky,
            deadline=time.monotonic() + 2,
            retry_budget=2,
            on_retry=lambda _attempt, _error: None,
            sleep_function=lambda _duration: True,
        )
        self_check(tests, "transient_retry", retry_value == "ok" and attempts["count"] == 3)

        ownership_pid_path = root / "ownership-child.pid"
        self_expect_error(
            tests,
            "controller_loss_detection",
            ControllerLostError,
            lambda: run_subprocess(
                [
                    "/bin/sh",
                    "-c",
                    "sleep 5 & echo $! > %s; wait" % shlex.quote(str(ownership_pid_path)),
                ],
                environment=minimal_environment({}),
                deadline=time.monotonic() + 2,
                secrets_to_redact=[],
                phase="self-test controller loss",
                ownership_check=lambda: not ownership_pid_path.exists(),
            ),
        )
        if ownership_pid_path.exists():
            ownership_child_pid = int(ownership_pid_path.read_text(encoding="utf-8").strip())
            time.sleep(0.05)
            self_check(tests, "controller_loss_child_cleanup", not process_alive(ownership_child_pid))
        else:
            raise SelfTestError("controller_loss_child_cleanup failed: child PID was not recorded")

    data = {"passed": len(tests), "tests": tests, "version": VERSION}
    print_json(success_envelope(args.command, data, {}), args.pretty)
    return 0


def bounded_int(minimum: int, maximum: int) -> Callable[[str], int]:
    def parse(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be an integer") from exc
        if parsed < minimum or parsed > maximum:
            raise argparse.ArgumentTypeError("must be between %d and %d" % (minimum, maximum))
        return parsed

    return parse


def bounded_float(minimum: float, maximum: float) -> Callable[[str], float]:
    def parse(value: str) -> float:
        try:
            parsed = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be a number") from exc
        if parsed < minimum or parsed > maximum:
            raise argparse.ArgumentTypeError("must be between %s and %s" % (minimum, maximum))
        return parsed

    return parse


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        error = UsageError(message)
        print_json(error_envelope("cli", error))
        raise SystemExit(error.exit_code)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        description="Trusted read-only Jean MCP operations and run-aware bounded watching.",
        epilog=(
            "Examples: jean_ops.py doctor --probe; jean_ops.py schema get_session_status; "
            "jean_ops.py watch-session --session-id ID --expect-run-id RUN --timeout 1800. "
            "Exit classes: 2 usage, 10 config, 11 trust, 12 unavailable, 13 MCP, "
            "14 lease, 15 persistence, 16 superseded, 124 timeout, 129/130/143 interruption."
        ),
    )
    parser.add_argument("--version", action="version", version="%(prog)s " + VERSION)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Codex config.toml; custom paths require unsafe opt-in")
    parser.add_argument("--backend", help="mcp2cli or exact 'uvx --offline mcp2cli' override")
    parser.add_argument("--allow-unsafe-config", action="store_true", help="explicitly trust a non-default Jean config/executable")
    parser.add_argument("--allow-unsafe-backend", action="store_true", help="explicitly trust a nonstandard mcp2cli backend")
    parser.add_argument(
        "--call-timeout",
        type=bounded_float(MIN_CALL_TIMEOUT, MAX_CALL_TIMEOUT),
        default=30.0,
        help="per-process timeout seconds, 1-120; global watcher deadline still wins",
    )
    parser.add_argument("--state-root", default=str(DEFAULT_STATE_ROOT), help="private leases/results root")
    parser.add_argument(
        "--max-output-bytes",
        type=bounded_int(MIN_OUTPUT_BYTES, MAX_OUTPUT_BYTES),
        default=1_000_000,
        help="JSON data bound, 4096-2000000",
    )
    parser.add_argument(
        "--max-string-chars",
        type=bounded_int(MIN_STRING_CHARS, MAX_STRING_CHARS),
        default=20_000,
        help="per-string bound, 256-100000",
    )
    parser.add_argument("--pretty", action="store_true", help="pretty-print non-streaming JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="validate config, trust, socket, backend, and capabilities")
    doctor.add_argument("--probe", action="store_true", help="perform live capability validation")
    doctor.add_argument(
        "--require",
        action="append",
        default=[",".join(sorted(ESSENTIAL_CAPABILITIES))],
        help="required comma-separated tools; repeatable",
    )
    doctor.set_defaults(handler=command_doctor)

    tools_parser = subparsers.add_parser("tools", help="list live Jean MCP tools and capability hash")
    tools_parser.set_defaults(handler=command_tools)

    schema_parser = subparsers.add_parser("schema", help="show one discovered Jean MCP tool schema")
    schema_parser.add_argument("tool")
    schema_parser.set_defaults(handler=command_schema)

    capabilities = subparsers.add_parser("capabilities", help="validate required tools/inputs and emit schema hash")
    capabilities.add_argument(
        "--require",
        action="append",
        default=[",".join(sorted(ESSENTIAL_CAPABILITIES))],
    )
    capabilities.set_defaults(handler=command_capabilities)

    projects = subparsers.add_parser("projects", help="list compact Jean projects")
    projects.set_defaults(handler=command_projects)

    worktrees = subparsers.add_parser("worktrees", help="list compact worktrees for a project")
    worktrees.add_argument("--project-id", required=True)
    worktrees.set_defaults(handler=command_worktrees)

    sessions = subparsers.add_parser("sessions", help="list compact sessions for a worktree")
    sessions.add_argument("--worktree-id", required=True)
    sessions.add_argument("--include-archived", action="store_true")
    sessions.set_defaults(handler=command_sessions)

    status_parser = subparsers.add_parser("status", help="read raw and normalized Jean session status")
    status_parser.add_argument("--session-id", required=True)
    status_parser.set_defaults(handler=command_status)

    messages = subparsers.add_parser("messages", help="read bounded recent session messages")
    messages.add_argument("--session-id", required=True)
    messages.add_argument(
        "--limit",
        type=bounded_int(1, MAX_MESSAGES),
        default=20,
        help="maximum returned message records, 1-100",
    )
    messages.add_argument(
        "--include-tool-details",
        action="store_true",
        help="include bounded tool inputs/outputs; omitted by default",
    )
    messages.add_argument(
        "--max-tool-calls",
        type=bounded_int(1, MAX_MESSAGE_TOOL_CALLS),
        default=DEFAULT_MAX_TOOL_CALLS,
        help="tool calls per returned message in expanded mode, 1-100",
    )
    messages.add_argument(
        "--message-content-chars",
        type=bounded_int(MIN_STRING_CHARS, MAX_MESSAGE_CONTENT_CHARS),
        default=DEFAULT_MESSAGE_CONTENT_CHARS,
        help="content characters per returned message, 256-20000",
    )
    messages.set_defaults(handler=command_messages)

    changes = subparsers.add_parser("changes", help="read a bounded worktree change summary")
    changes.add_argument("--worktree-id", required=True)
    changes.add_argument("--max-files", type=bounded_int(1, MAX_CHANGED_FILES), default=100, help="1-500")
    changes.set_defaults(handler=command_changes)

    read = subparsers.add_parser("read", help="call a discovered allowlisted read-only Jean tool")
    read.add_argument("tool", choices=sorted(READ_ONLY_TOOLS))
    read.add_argument("--arg", action="append", default=[], metavar="KEY=VALUE")
    read.set_defaults(handler=command_read)

    leases = subparsers.add_parser("leases", help="list durable Jean session controller leases")
    leases.set_defaults(handler=command_leases)

    watch = subparsers.add_parser("watch-session", help="watch one Jean session/run with a durable lease")
    watch.add_argument("--session-id", required=True)
    run_group = watch.add_mutually_exclusive_group()
    run_group.add_argument("--expect-run-id", help="accept terminal only for this exact run")
    run_group.add_argument("--after-run-id", help="wait for and adopt a run different from this baseline")
    watch.add_argument(
        "--allow-existing-terminal",
        action="store_true",
        help="explicitly allow the first already-terminal run; off by default",
    )
    watch.add_argument("--until", choices=("terminal", "change", "input", "idle"), default="terminal")
    watch.add_argument(
        "--timeout",
        type=bounded_float(MIN_WATCH_TIMEOUT, MAX_WATCH_TIMEOUT),
        default=1800.0,
        help="absolute watcher deadline seconds, 2-86400",
    )
    watch.add_argument(
        "--interval",
        type=bounded_float(MIN_INTERVAL, MAX_INTERVAL),
        default=2.0,
        help="initial poll interval seconds, 1-60",
    )
    watch.add_argument(
        "--max-interval",
        type=bounded_float(MIN_INTERVAL, MAX_INTERVAL),
        default=30.0,
        help="maximum poll interval seconds, 1-60",
    )
    watch.add_argument("--backoff", type=bounded_float(1.0, 4.0), default=1.5)
    watch.add_argument("--heartbeat-every", type=bounded_int(0, 1000), default=0)
    watch.add_argument("--transient-retries", type=bounded_int(0, MAX_TRANSIENT_RETRIES), default=2)
    watch.add_argument("--lease-ttl", type=bounded_float(30.0, 300.0), default=90.0, help="lease TTL seconds, 30-300")
    watch.add_argument("--controller", choices=("codex-task", "ui", "native-mcp"), default="codex-task")
    watch.add_argument("--controller-id", default=os.environ.get("CODEX_THREAD_ID", "unknown"))
    watch.add_argument("--result-file", help="new checkpoint file; existing paths are refused")
    watch.set_defaults(handler=command_watch)

    self_test = subparsers.add_parser("self-test", help="run explicit offline safety/correctness tests")
    self_test.set_defaults(handler=command_self_test)
    return parser


def validate_cross_arguments(args: argparse.Namespace) -> None:
    if args.command == "watch-session":
        if args.max_interval < args.interval:
            raise UsageError("--max-interval must be greater than or equal to --interval")
        if args.lease_ttl < args.max_interval * 2 + 10:
            raise UsageError("--lease-ttl must be at least 2*--max-interval + 10 seconds")
        if args.allow_existing_terminal and (args.expect_run_id or args.after_run_id):
            raise UsageError("--allow-existing-terminal cannot be combined with an explicit run guard")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validate_cross_arguments(args)
        return int(args.handler(args))
    except JeanOpsError as exc:
        print_json(error_envelope(getattr(args, "command", "cli"), exc), getattr(args, "pretty", False))
        return exc.exit_code
    except BrokenPipeError:
        return 141
    except KeyboardInterrupt:
        error = JeanOpsError("interrupted", code="interrupted", category="interruption", exit_code=130)
        print_json(error_envelope(getattr(args, "command", "cli"), error))
        return error.exit_code
    except OSError as exc:
        error = PersistenceError("operating-system error: %s" % exc)
        print_json(error_envelope(getattr(args, "command", "cli"), error))
        return error.exit_code


if __name__ == "__main__":
    sys.exit(main())
