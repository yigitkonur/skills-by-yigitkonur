# cli/code-templates.md

Production code samples in 5 languages — Go, Python, Node.js, Rust, Bash — for the canonical envelope, exit-code constants, standard flags, TTY detection, and NDJSON streaming. Copy-paste templates that ship with the JSON shape and exit-code taxonomy already wired. Cross-language consistency is the contract: the JSON envelope and exit codes must match across every language so an agent harness can call any language CLI and get the same shape. Source: `optimize-agentic-cli/references/examples.md`.

## Cross-language contract

Every template below ships with the same envelope:

```json
{
  "ok": true,
  "result": { "...": "..." },
  "schema_version": "1"
}
```

```json
{
  "ok": false,
  "error": {
    "class": "validation",
    "code": "VALIDATION_FAILED",
    "message": "Field 'name' is required.",
    "retryable": false,
    "suggestion": "Add --name=<value> to the command."
  },
  "schema_version": "1"
}
```

And the same exit codes:

| Code | Class | Retryable |
|---|---|---|
| 0 | success | n/a |
| 1 | crash / general | maybe |
| 2 | usage | no |
| 3 | not_found | no |
| 4 | auth | no |
| 5 | conflict | no |
| 6 | validation | no |
| 7 | transient | yes |

And the same standard flags:

| Flag | Short | Purpose |
|---|---|---|
| `--json` | — | Structured JSON output on stdout |
| `--quiet` | `-q` | Bare-value pipeline output |
| `--yes` | `-y` | Auto-confirm interactive prompts |
| `--no-input` | — | Fail rather than prompt; CI/agent default |
| `--timeout` | — | Per-command timeout in seconds |

Cross-link `output-envelope.md` for the envelope deep dive, `exit-codes.md` for the full exit-code taxonomy, and `flags-and-discovery.md` for the standard flag registry.

## Go (stdlib)

Stdlib only — no Cobra, no Viper. Demonstrates envelope writer, exit-code constants, flag handling via `flag` package, TTY detection, NDJSON streaming. Use this for binary CLIs distributed via Homebrew, GitHub Releases, or `go install`.

```go
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"golang.org/x/term"
)

// Exit-code taxonomy — matches the cross-language contract.
const (
	ExitSuccess    = 0
	ExitCrash      = 1
	ExitUsage      = 2
	ExitNotFound   = 3
	ExitAuth       = 4
	ExitConflict   = 5
	ExitValidation = 6
	ExitTransient  = 7
)

// Envelope — single canonical shape; differs only in which fields populate.
type Envelope struct {
	OK            bool        `json:"ok"`
	Result        any         `json:"result,omitempty"`
	Error         *ErrorBody  `json:"error,omitempty"`
	SchemaVersion string      `json:"schema_version"`
}

type ErrorBody struct {
	Class      string `json:"class"`
	Code       string `json:"code"`
	Message    string `json:"message"`
	Retryable  bool   `json:"retryable"`
	Suggestion string `json:"suggestion,omitempty"`
}

// emit writes an envelope to stdout. Pretty-prints only when stdout is a TTY.
func emit(env Envelope) {
	enc := json.NewEncoder(os.Stdout)
	if term.IsTerminal(int(os.Stdout.Fd())) {
		enc.SetIndent("", "  ")
	}
	_ = enc.Encode(env)
}

// emitNDJSON writes one event per line; flushes after each.
func emitNDJSON(event any) {
	line, _ := json.Marshal(event)
	fmt.Println(string(line)) // stdout sync on Println.
}

// Standard flags shared by every command.
type stdFlags struct {
	jsonOut bool
	quiet   bool
	yes     bool
	noInput bool
	timeout time.Duration
}

func parseStdFlags() *stdFlags {
	f := &stdFlags{}
	flag.BoolVar(&f.jsonOut, "json", false, "structured JSON output")
	flag.BoolVar(&f.quiet, "quiet", false, "bare values for pipeline use")
	flag.BoolVar(&f.yes, "yes", false, "auto-confirm prompts")
	flag.BoolVar(&f.noInput, "no-input", false, "fail rather than prompt")
	flag.DurationVar(&f.timeout, "timeout", 30*time.Second, "per-command timeout")
	flag.Parse()

	// Auto-flip to JSON when stdout is non-TTY (pipeline / harness).
	if !term.IsTerminal(int(os.Stdout.Fd())) {
		f.jsonOut = true
	}
	return f
}

// Example: a "greet" command.
func main() {
	f := parseStdFlags()

	if flag.NArg() == 0 {
		emit(Envelope{
			OK: false,
			Error: &ErrorBody{
				Class: "usage", Code: "MISSING_COMMAND",
				Message: "no command given", Retryable: false,
				Suggestion: "run mytool --help",
			},
			SchemaVersion: "1",
		})
		os.Exit(ExitUsage)
	}

	switch strings.ToLower(flag.Arg(0)) {
	case "greet":
		name := ""
		for i, a := range flag.Args() {
			if a == "--name" && i+1 < flag.NArg() {
				name = flag.Arg(i + 1)
			}
		}
		if name == "" {
			emit(Envelope{
				OK: false,
				Error: &ErrorBody{
					Class: "validation", Code: "MISSING_NAME",
					Message: "--name is required", Retryable: false,
					Suggestion: "pass --name=<value>",
				},
				SchemaVersion: "1",
			})
			os.Exit(ExitValidation)
		}
		emit(Envelope{
			OK:            true,
			Result:        map[string]any{"greeting": fmt.Sprintf("Hello, %s!", name)},
			SchemaVersion: "1",
		})
		os.Exit(ExitSuccess)
	default:
		emit(Envelope{
			OK: false,
			Error: &ErrorBody{
				Class: "usage", Code: "UNKNOWN_COMMAND",
				Message: fmt.Sprintf("unknown command: %s", flag.Arg(0)),
				Retryable: false,
			},
			SchemaVersion: "1",
		})
		os.Exit(ExitUsage)
	}
}
```

Dependencies: stdlib + `golang.org/x/term` for TTY detection (or use `os.Stdout.Stat()` and check `(stat.Mode() & os.ModeCharDevice) != 0` for stdlib-only).

## Python (stdlib)

Stdlib only — no Click, no Typer. Demonstrates envelope writer, exit-code constants, flag handling via `argparse`, TTY detection, NDJSON streaming. Use this for pip-installable CLIs or scripts distributed in repos.

```python
#!/usr/bin/env python3
"""Agent-ready CLI — envelope, exit codes, flags, TTY detection."""

import argparse, json, os, sys
from typing import Any

# Exit-code taxonomy — cross-language contract.
EXIT_SUCCESS, EXIT_CRASH, EXIT_USAGE, EXIT_NOT_FOUND = 0, 1, 2, 3
EXIT_AUTH, EXIT_CONFLICT, EXIT_VALIDATION, EXIT_TRANSIENT = 4, 5, 6, 7


def is_tty() -> bool:
    return sys.stdout.isatty() and not os.environ.get("NO_TTY")


def emit(envelope: dict) -> None:
    """Write an envelope to stdout. Pretty-prints only when stdout is a TTY."""
    indent = 2 if is_tty() else None
    print(json.dumps(envelope, indent=indent), flush=True)


def emit_ndjson(event: dict) -> None:
    """One JSON object per line; flushes immediately."""
    print(json.dumps(event), flush=True)


def emit_success(result: Any, **extra) -> None:
    emit({"ok": True, "result": result, "schema_version": "1", **extra})


def emit_error(error_class: str, code: str, message: str, *,
               retryable: bool = False, suggestion: str | None = None,
               exit_code: int = EXIT_CRASH) -> None:
    err: dict = {"class": error_class, "code": code, "message": message, "retryable": retryable}
    if suggestion:
        err["suggestion"] = suggestion
    emit({"ok": False, "error": err, "schema_version": "1"})
    sys.exit(exit_code)


def add_std_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="structured JSON output")
    parser.add_argument("-q", "--quiet", action="store_true", help="bare values")
    parser.add_argument("-y", "--yes", action="store_true", help="auto-confirm prompts")
    parser.add_argument("--no-input", action="store_true", help="fail rather than prompt")
    parser.add_argument("--timeout", type=int, default=30, help="per-command timeout")


def cmd_greet(args) -> None:
    if not args.name:
        emit_error("validation", "MISSING_NAME", "--name is required",
                   suggestion="pass --name=<value>", exit_code=EXIT_VALIDATION)
    emit_success({"greeting": f"Hello, {args.name}!"})
    sys.exit(EXIT_SUCCESS)


def main() -> None:
    parser = argparse.ArgumentParser(prog="mytool")
    add_std_flags(parser)
    sub = parser.add_subparsers(dest="command")
    greet = sub.add_parser("greet", help="greet someone by name")
    greet.add_argument("--name", help="name to greet")
    greet.set_defaults(func=cmd_greet)

    args = parser.parse_args()
    if not is_tty():
        args.json = True
    if not args.command:
        emit_error("usage", "MISSING_COMMAND", "no command given",
                   suggestion="run mytool --help", exit_code=EXIT_USAGE)
    args.func(args)


if __name__ == "__main__":
    main()
```

Dependencies: stdlib only. For more ergonomic flag handling, swap `argparse` for `click` (adds dependency) — same envelope and exit-code patterns hold.

## Node.js (`commander`)

Uses `commander` for flag handling. Demonstrates envelope writer, exit-code constants, flag handling, TTY detection, NDJSON streaming via `process.stdout.write`. Use this for npm-distributable CLIs.

```javascript
#!/usr/bin/env node
// mytool.js — agent-ready CLI in Node.js with commander.

const { Command } = require("commander");

// Exit-code taxonomy — cross-language contract.
const EXIT = {
  SUCCESS: 0,
  CRASH: 1,
  USAGE: 2,
  NOT_FOUND: 3,
  AUTH: 4,
  CONFLICT: 5,
  VALIDATION: 6,
  TRANSIENT: 7,
};

const isTTY = () => process.stdout.isTTY && !process.env.NO_TTY;

function emit(envelope) {
  const pretty = isTTY();
  process.stdout.write(JSON.stringify(envelope, null, pretty ? 2 : 0) + "\n");
}

function emitNDJSON(event) {
  process.stdout.write(JSON.stringify(event) + "\n");
}

function emitSuccess(result, extra = {}) {
  emit({ ok: true, result, schema_version: "1", ...extra });
}

function emitError({ class: cls, code, message, retryable = false, suggestion, exitCode = EXIT.CRASH }) {
  const error = { class: cls, code, message, retryable };
  if (suggestion) error.suggestion = suggestion;
  emit({ ok: false, error, schema_version: "1" });
  process.exit(exitCode);
}

function addStdFlags(cmd) {
  return cmd
    .option("--json", "structured JSON output")
    .option("-q, --quiet", "bare values")
    .option("-y, --yes", "auto-confirm prompts")
    .option("--no-input", "fail rather than prompt")
    .option("--timeout <secs>", "per-command timeout", "30");
}

const program = new Command();
program.name("mytool").description("Agent-ready CLI example").version("1.0.0");

addStdFlags(
  program
    .command("greet")
    .description("greet someone by name")
    .option("--name <name>", "name to greet"),
).action((opts) => {
  if (!opts.name) {
    emitError({
      class: "validation",
      code: "MISSING_NAME",
      message: "--name is required",
      suggestion: "pass --name=<value>",
      exitCode: EXIT.VALIDATION,
    });
  }
  emitSuccess({ greeting: `Hello, ${opts.name}!` });
  process.exit(EXIT.SUCCESS);
});

// Auto-JSON when stdout is non-TTY.
if (!isTTY()) {
  process.argv.push("--json");
}

program.parse(process.argv);
```

Dependencies: `commander`. Alternative: `yargs` (similar API) or `arg` (lower-level). Whatever the parser, the envelope and exit-code shapes stay constant.

`package.json`:

```json
{
  "name": "mytool",
  "version": "1.0.0",
  "bin": {"mytool": "./mytool.js"},
  "dependencies": {"commander": "^12.0.0"}
}
```

## Rust (`clap` + `serde`)

Uses `clap` for derive-style flag handling, `serde` for JSON. Demonstrates envelope writer, exit-code enum, flag handling. Use this for binary CLIs distributed via `cargo install` or `crates.io`.

```rust
// src/main.rs
use clap::{Parser, Subcommand};
use serde::Serialize;
use std::io::{self, IsTerminal, Write};
use std::process::ExitCode;

#[repr(u8)]
#[derive(Clone, Copy)]
enum Exit { Success = 0, Crash = 1, Usage = 2, NotFound = 3,
            Auth = 4, Conflict = 5, Validation = 6, Transient = 7 }

impl From<Exit> for ExitCode {
    fn from(e: Exit) -> Self { ExitCode::from(e as u8) }
}

#[derive(Serialize)]
struct Envelope<T: Serialize> {
    ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")] result: Option<T>,
    #[serde(skip_serializing_if = "Option::is_none")] error: Option<ErrorBody>,
    schema_version: String,
}

#[derive(Serialize)]
struct ErrorBody {
    class: String, code: String, message: String, retryable: bool,
    #[serde(skip_serializing_if = "Option::is_none")] suggestion: Option<String>,
}

fn emit<T: Serialize>(env: &Envelope<T>) {
    let s = if io::stdout().is_terminal() {
        serde_json::to_string_pretty(env).unwrap()
    } else {
        serde_json::to_string(env).unwrap()
    };
    println!("{}", s);
    io::stdout().flush().ok();
}

fn emit_success<T: Serialize>(result: T) {
    emit(&Envelope { ok: true, result: Some(result), error: None, schema_version: "1".into() });
}

fn emit_error(class: &str, code: &str, message: &str, retryable: bool, suggestion: Option<&str>) {
    emit(&Envelope::<()> {
        ok: false, result: None,
        error: Some(ErrorBody {
            class: class.into(), code: code.into(), message: message.into(),
            retryable, suggestion: suggestion.map(String::from),
        }),
        schema_version: "1".into(),
    });
}

#[derive(Parser)]
#[command(name = "mytool", about = "Agent-ready CLI example")]
struct Cli {
    #[arg(long, global = true)] json: bool,
    #[arg(short, long, global = true)] quiet: bool,
    #[arg(short, long, global = true)] yes: bool,
    #[arg(long, global = true)] no_input: bool,
    #[arg(long, global = true, default_value_t = 30)] timeout: u64,
    #[command(subcommand)] command: Option<Commands>,
}

#[derive(Subcommand)]
enum Commands {
    Greet { #[arg(long)] name: Option<String> },
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    match cli.command {
        Some(Commands::Greet { name }) => match name {
            Some(n) => {
                emit_success(serde_json::json!({"greeting": format!("Hello, {}!", n)}));
                Exit::Success.into()
            }
            None => {
                emit_error("validation", "MISSING_NAME", "--name is required",
                           false, Some("pass --name=<value>"));
                Exit::Validation.into()
            }
        },
        None => {
            emit_error("usage", "MISSING_COMMAND", "no command given",
                       false, Some("run mytool --help"));
            Exit::Usage.into()
        }
    }
}
```

`Cargo.toml`: `clap = { version = "4", features = ["derive"] }`, `serde = { version = "1", features = ["derive"] }`, `serde_json = "1"`. NDJSON streaming via `println!` + `flush`; same pattern as Go and Python.

## Bash (pure)

Pure POSIX `bash`. Demonstrates envelope writer, exit-code constants, flag handling, TTY detection. Use this for shell scripts distributed in repos or wrapping other tools.

```bash
#!/usr/bin/env bash
# mytool — agent-ready CLI shell wrapper.
set -uo pipefail

# Exit-code taxonomy — cross-language contract.
readonly EXIT_SUCCESS=0 EXIT_CRASH=1 EXIT_USAGE=2 EXIT_NOT_FOUND=3
readonly EXIT_AUTH=4 EXIT_CONFLICT=5 EXIT_VALIDATION=6 EXIT_TRANSIENT=7

is_tty() { [ -t 1 ] && [ -z "${NO_TTY:-}" ]; }

emit() {
  # $1: JSON string. Pretty-prints via jq when on TTY.
  if is_tty && command -v jq >/dev/null 2>&1; then
    printf '%s\n' "$1" | jq .
  else
    printf '%s\n' "$1"
  fi
}

emit_ndjson() { printf '%s\n' "$1"; }  # one event per line

emit_success() {
  emit "$(printf '{"ok":true,"result":%s,"schema_version":"1"}' "$1")"
}

emit_error() {
  # $1=class $2=code $3=message $4=retryable $5=suggestion (optional)
  local class="$1" code="$2" msg="$3" retryable="$4" suggestion="${5:-}"
  local err
  if [ -n "$suggestion" ]; then
    err=$(printf '{"class":"%s","code":"%s","message":"%s","retryable":%s,"suggestion":"%s"}' \
                 "$class" "$code" "$msg" "$retryable" "$suggestion")
  else
    err=$(printf '{"class":"%s","code":"%s","message":"%s","retryable":%s}' \
                 "$class" "$code" "$msg" "$retryable")
  fi
  emit "$(printf '{"ok":false,"error":%s,"schema_version":"1"}' "$err")"
}

# Standard flag defaults.
JSON=false; QUIET=false; YES=false; NO_INPUT=false; TIMEOUT=30
COMMAND=""; NAME=""

while [ $# -gt 0 ]; do
  case "$1" in
    --json) JSON=true; shift ;;
    -q|--quiet) QUIET=true; shift ;;
    -y|--yes) YES=true; shift ;;
    --no-input) NO_INPUT=true; shift ;;
    --timeout=*) TIMEOUT="${1#*=}"; shift ;;
    --name=*) NAME="${1#*=}"; shift ;;
    --name) NAME="$2"; shift 2 ;;
    greet) COMMAND="greet"; shift ;;
    *) emit_error "usage" "UNKNOWN_FLAG" "unknown flag: $1" false ""
       exit $EXIT_USAGE ;;
  esac
done

is_tty || JSON=true  # auto-JSON on non-TTY

case "$COMMAND" in
  "") emit_error "usage" "MISSING_COMMAND" "no command given" false "run mytool --help"
      exit $EXIT_USAGE ;;
  greet)
    [ -z "$NAME" ] && {
      emit_error "validation" "MISSING_NAME" "--name is required" false "pass --name=<value>"
      exit $EXIT_VALIDATION
    }
    emit_success "$(printf '{"greeting":"Hello, %s!"}' "$NAME")"
    exit $EXIT_SUCCESS ;;
esac
```

Dependencies: `bash` ≥ 4. `jq` is optional for pretty-printing on TTY and required on the consumer side for parsing.

## Cross-language harness verification

The same agent harness (Python `subprocess`) can call any of the five language CLIs above and get the same JSON shape. That's the contract. Verify with this test:

```python
import subprocess, json

CLIS = ["./mytool-go", "./mytool.py", "./mytool.js", "./target/release/mytool", "./mytool.sh"]

for cli in CLIS:
    # Happy path.
    r = subprocess.run([cli, "greet", "--name=alice", "--json"], capture_output=True, text=True)
    assert r.returncode == 0, f"{cli}: exit {r.returncode}"
    env = json.loads(r.stdout)
    assert env["ok"] is True
    assert env["result"]["greeting"] == "Hello, alice!"
    assert env["schema_version"] == "1"

    # Validation failure.
    r = subprocess.run([cli, "greet", "--json"], capture_output=True, text=True)
    assert r.returncode == 6, f"{cli}: validation exit {r.returncode}"
    env = json.loads(r.stdout)
    assert env["ok"] is False
    assert env["error"]["class"] == "validation"
    assert env["error"]["retryable"] is False
```

Every language returns the same envelope shape, the same exit code, the same error class. The agent's harness writes once and runs against any of the five.

## Cross-references

- For the canonical envelope contract, read `output-envelope.md`.
- For the exit-code taxonomy, read `exit-codes.md`.
- For standard flag conventions, read `flags-and-discovery.md`.
- For TTY detection patterns and headless operation, read `auth-headless.md`.
- For NDJSON streaming and progress events, read `iterative-pattern.md`.
- For the harness on the consumer side, read `subprocess-harness.md`.
- For new-CLI design that picks the right templates, read `architect-new.md`.
