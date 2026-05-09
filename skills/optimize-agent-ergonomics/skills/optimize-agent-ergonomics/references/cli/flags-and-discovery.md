# cli/flags-and-discovery.md

The standard flag set every agent-ready CLI supports, plus TTY/CI detection rules and the help-text-as-API contract. Agents discover what the CLI can do by reading `--help` — that text is part of the API surface, not documentation. This file specifies the flags, the auto-detection logic, and the help structure.

## Standard flag registry

| Flag | Short | Type | Purpose | Default behavior |
|---|---|---|---|---|
| `--json` | `-j` | bool | Emit JSON envelope on stdout | Auto-on when stdout is not a TTY |
| `--quiet` | `-q` | bool | Suppress non-essential prose on stderr | Auto-on in CI |
| `--yes` | `-y` | bool | Assume yes to all confirmations | Off; required for destructive ops in non-TTY |
| `--no-input` | — | bool | Fail if interactive input would be needed | Auto-on in CI |
| `--dry-run` | — | bool | Print what would happen; do not execute | Off |
| `--force` | `-f` | bool | Override safety checks (rare) | Off; document each check it overrides |
| `--timeout=<seconds>` | — | int | Bound the operation's wall-clock time | 30s for most commands; longer for long-running |
| `--verbose` | `-v` | bool | Extra prose on stderr (NOT for agents) | Off |
| `--config=<path>` | — | string | Alternative config file | `$XDG_CONFIG_HOME/<tool>/config` |

That is the floor. A CLI may add more, but these 9 are the minimum agent-ready set. The semantics are non-negotiable — `--yes` always means auto-confirm, `--json` always emits the envelope, etc.

### Detailed semantics

**`--json` / `-j`**

Switches stdout to the JSON envelope from `output-envelope.md`. When auto-detected (non-TTY), the CLI behaves as if the flag was passed. Don't make agents type the flag; auto-detection is the right default.

```python
should_emit_json = args.json or not sys.stdout.isatty() or os.environ.get("CI")
```

**`--quiet` / `-q`**

Suppresses prose on stderr. Errors still go to stderr if structured output is off; warnings disappear. In `--json` mode, `--quiet` is implicit (the envelope already lacks prose).

Critical: `--quiet` MUST NOT suppress the JSON envelope. The agent passing `--json --quiet` expects the envelope on stdout and silence on stderr. A CLI that suppresses everything is broken.

**`--yes` / `-y`**

Auto-confirms every interactive prompt. For destructive commands (`delete`, `drop`, `purge`), require `--yes` when the CLI is non-interactive — refuse to act otherwise:

```python
if action_is_destructive and not args.yes and not sys.stdout.isatty():
    emit_error("USAGE", "destructive action requires --yes when running non-interactively")
    sys.exit(2)
```

**`--no-input`**

The aggressive variant of `--yes`. Where `--yes` says "yes to confirmations", `--no-input` says "fail if input is needed at all" — confirmations, missing required args, anything. The agent uses it to surface configuration gaps early instead of hanging.

```python
if needs_user_input() and (args.no_input or os.environ.get("CI")):
    emit_error("USAGE", "missing required input; pass --field=... or run interactively")
    sys.exit(2)
```

**`--dry-run`**

Print the planned action; do not execute. The CLI's job is to be honest about what would happen. The output should match the shape of the real-run envelope, with `meta.dry_run = true` so the agent can branch:

```json
{"ok": true, "result": {"would_create": ["res_a", "res_b"]}, "meta": {"dry_run": true}, "schema_version": "1"}
```

If the dry-run can't reach the server (e.g., auth is required to compute the diff), that's an auth error like any other — exit 4. Don't fail silently.

**`--force` / `-f`**

Override one specific safety check. Document which check it overrides. NEVER use `--force` as a catchall. If the CLI has three independent checks, expose three flags: `--force-overwrite`, `--force-destroy-data`, `--ignore-version-skew`. Each one says exactly what it bypasses.

**`--timeout=<seconds>`**

The operation's wall-clock budget. The CLI should emit `error.code = "TIMEOUT"` and exit 7 when exceeded — never crash with a stack trace. The agent uses the timeout to bound recovery loops.

Default: 30s for most commands. Long-running commands (deploys, builds) may default higher; document it in `--help`.

**`--verbose` / `-v`**

Extra prose on stderr for human debugging. NOT for agents — `--verbose` output is intentionally unstable. Agents that need extra structured data should ask for it via dedicated commands or `--include=<fields>`, not `--verbose`.

Some CLIs use `-vv`, `-vvv` for increasing levels. Acceptable; document the levels.

**`--config=<path>`**

Override the config file path. Useful for agent harnesses that need to inject a config without touching the user's home directory.

## TTY/CI detection

The CLI auto-detects the runtime environment and adjusts defaults. Agents should never have to remember every flag — the CLI does the right thing in pipelines, in CI, in the user's shell.

Detection rules:

```python
def is_tty():
    return sys.stdout.isatty() and sys.stderr.isatty()

def is_ci():
    return any(os.environ.get(v) for v in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "CIRCLECI"))

def should_emit_json(args):
    return args.json or not is_tty() or is_ci()

def should_disable_color(args):
    return os.environ.get("NO_COLOR") or args.json or not is_tty() or is_ci()

def should_be_non_interactive(args):
    return args.no_input or args.yes or not is_tty() or is_ci()
```

The matrix:

| Context | `--json` default | Color | Prompts | Progress spinners |
|---|---|---|---|---|
| Interactive shell (TTY) | off | on | on | on |
| Piped (`mytool ... \| jq`) | on | off | off | off |
| CI (any of the env vars set) | on | off | off | off |
| Explicit `--json` | on | off | off | off |

**`NO_COLOR=1`** is honored unconditionally (https://no-color.org). If the env var is set, no ANSI escapes leave the CLI on any stream.

**`FORCE_COLOR=1`** overrides; useful for users running through tools that strip TTYs but want color anyway.

## Help-text-as-API

Every command (and the root) supports `--help`. That text is the agent's first read at integration time. Treat it as part of the API contract.

The structure is fixed:

```
NAME
    mytool create — create a new resource

SYNOPSIS
    mytool create <name> [--type=<type>] [--region=<region>] [--json] [--yes]

DESCRIPTION
    Create a resource with the given name. Idempotent if --idempotency-key is set;
    otherwise, returns exit 5 (conflict) on duplicate name.

PARAMETERS
    <name>           Required. The resource name. Must match [a-z][a-z0-9-]{2,31}.
    --type=<type>    Resource type: web | worker | scheduler. Default: web.
    --region=<rg>    Deployment region. Default: us-east-1.
    --json           Emit JSON envelope on stdout. Auto-on in non-TTY contexts.
    --yes            Skip confirmation prompts. Required in non-TTY for create.

OUTPUT
    Success:
      {"ok": true, "result": {"id": "res_xxx", "url": "https://..."}, "schema_version": "1"}
    Failure:
      {"ok": false, "error": {"code": "...", "message": "...", "next_action": "..."}, "schema_version": "1"}

EXIT CODES
    0  Created
    2  Usage error (bad name format, missing --type when required)
    4  Auth failure
    5  Conflict (resource with this name already exists)
    7  Transient (rate limit; retry with backoff)

EXAMPLES
    # Minimal:
    mytool create my-app

    # Worker in a specific region, JSON envelope:
    mytool create batch-runner --type=worker --region=eu-west-1 --json

    # Non-interactive automation:
    mytool create my-app --yes --json
```

Required sections in order: NAME, SYNOPSIS, DESCRIPTION, PARAMETERS, OUTPUT, EXIT CODES, EXAMPLES. Skip a section only when it's not applicable (a `--help`-only command has no OUTPUT section, etc.).

The five questions every help page must answer:

1. What does this command do?
2. What arguments and flags exist, and which are required?
3. What does success look like (output shape)?
4. What can go wrong, and how does the agent know?
5. Three concrete examples, including an agent-flavored one.

## Discovery — top-level commands

The agent learns what the CLI can do by reading the root `--help`. List every subcommand:

```
SUBCOMMANDS
    create     Create a new resource
    list       List resources
    get        Show one resource
    delete     Delete a resource
    apply      Reconcile from a config file
    status     Check service status
    auth       Authenticate / refresh tokens
    version    Print version

Run 'mytool <subcommand> --help' for details.
```

For tools with many subcommands (>10), group them by domain (`mytool resource create`, `mytool deployment create`) and the root help lists the domains, not the leaves.

### Optional `--list-commands` for tooling

A flag that emits the command tree as JSON, for harnesses that auto-generate documentation or build agent function tools:

```bash
mytool --list-commands --json
```

```json
{
  "ok": true,
  "result": {
    "commands": [
      {
        "name": "create",
        "synopsis": "mytool create <name> [...]",
        "description": "Create a new resource.",
        "parameters": [{"name": "name", "required": true, "type": "string"}, ...],
        "exit_codes": [0, 2, 4, 5, 7]
      },
      ...
    ]
  },
  "schema_version": "1"
}
```

Optional, but valuable for agents that need to programmatically discover the surface. When implementing it, keep it stable across versions.

## Plugin / sub-command discovery

CLIs that load plugins (`git`-style: any `mytool-foo` on PATH becomes `mytool foo`) MUST surface plugins in `--help`. Otherwise the agent has no way to discover them.

```python
def list_plugins():
    plugins = []
    for path in os.environ["PATH"].split(":"):
        for f in glob.glob(f"{path}/mytool-*"):
            if os.access(f, os.X_OK):
                plugins.append(os.path.basename(f).removeprefix("mytool-"))
    return sorted(set(plugins))
```

## Code samples

### Python with argparse (stdlib)

```python
import argparse, sys, os

parser = argparse.ArgumentParser(
    prog="mytool",
    description="Manage resources from the command line.",
)
parser.add_argument("--json", "-j", action="store_true", help="Emit JSON envelope.")
parser.add_argument("--quiet", "-q", action="store_true", help="Suppress prose on stderr.")
parser.add_argument("--yes", "-y", action="store_true", help="Auto-confirm prompts.")
parser.add_argument("--no-input", action="store_true", help="Fail if input would be needed.")
parser.add_argument("--dry-run", action="store_true", help="Print plan; do not execute.")
parser.add_argument("--timeout", type=int, default=30, help="Wall-clock timeout in seconds.")
parser.add_argument("--config", default=os.path.expanduser("~/.config/mytool/config"))
parser.add_argument("--verbose", "-v", action="count", default=0)

sub = parser.add_subparsers(dest="cmd", required=True)

# create subcommand
create = sub.add_parser("create", help="Create a new resource.")
create.add_argument("name")
create.add_argument("--type", default="web", choices=["web", "worker", "scheduler"])

args = parser.parse_args()

# Auto-detect TTY/CI for --json default.
args.json = args.json or not sys.stdout.isatty() or bool(os.environ.get("CI"))
```

### Go with the cobra package

```go
package main

import (
    "github.com/spf13/cobra"
    "os"
)

var (
    jsonOut, quiet, yes, noInput, dryRun, force bool
    timeout    int
    configPath string
)

func newRoot() *cobra.Command {
    root := &cobra.Command{Use: "mytool", Short: "Manage resources."}
    root.PersistentFlags().BoolVarP(&jsonOut, "json", "j", false, "Emit JSON envelope.")
    root.PersistentFlags().BoolVarP(&quiet, "quiet", "q", false, "Suppress prose.")
    root.PersistentFlags().BoolVarP(&yes, "yes", "y", false, "Auto-confirm prompts.")
    root.PersistentFlags().BoolVar(&noInput, "no-input", false, "Fail if input would be needed.")
    root.PersistentFlags().BoolVar(&dryRun, "dry-run", false, "Print plan; do not execute.")
    root.PersistentFlags().BoolVarP(&force, "force", "f", false, "Override safety checks.")
    root.PersistentFlags().IntVar(&timeout, "timeout", 30, "Wall-clock timeout (seconds).")
    root.PersistentFlags().StringVar(&configPath, "config", "", "Config file path.")
    return root
}

// auto-detect TTY for --json default
func init() {
    if !isTerminal(os.Stdout) || os.Getenv("CI") != "" {
        jsonOut = true
    }
}
```

### Rust with clap (derive)

```rust
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "mytool", about = "Manage resources.")]
struct Cli {
    #[arg(long, short = 'j', global = true)]
    json: bool,
    #[arg(long, short = 'q', global = true)]
    quiet: bool,
    #[arg(long, short = 'y', global = true)]
    yes: bool,
    #[arg(long, global = true)]
    no_input: bool,
    #[arg(long, global = true)]
    dry_run: bool,
    #[arg(long, short = 'f', global = true)]
    force: bool,
    #[arg(long, default_value_t = 30, global = true)]
    timeout: u32,
    #[arg(long, global = true)]
    config: Option<String>,
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Create { name: String, #[arg(long, default_value = "web")] r#type: String },
    List,
    Get { id: String },
    Delete { id: String },
}
```

### Node with commander

```javascript
import { Command } from "commander";

const program = new Command()
    .name("mytool")
    .description("Manage resources.")
    .option("-j, --json", "Emit JSON envelope.")
    .option("-q, --quiet", "Suppress prose.")
    .option("-y, --yes", "Auto-confirm prompts.")
    .option("--no-input", "Fail if input would be needed.")
    .option("--dry-run", "Print plan; do not execute.")
    .option("-f, --force", "Override safety checks.")
    .option("--timeout <seconds>", "Wall-clock timeout.", "30")
    .option("--config <path>", "Config file path.");

program
    .command("create <name>")
    .option("--type <type>", "Resource type", "web")
    .action((name, options) => { /* ... */ });
```

## Anti-patterns

- **`--json` doesn't auto-detect.** Agent forgets the flag; CLI emits a table; agent crashes. Fix: auto-on in non-TTY.
- **`--verbose` is meant for agents.** Verbose output is unstable across releases. Agents need separate, stable surfaces (e.g., `mytool inspect <id> --include=raw`).
- **`--quiet` suppresses the envelope.** Agent gets nothing. Fix: `--quiet` only kills stderr prose; envelope still emits.
- **Help text is in markdown.** Agents see `**bold**` in their context. Fix: plain text in `--help`, with structure conveyed through ALL-CAPS section headers and indentation.
- **Subcommands aren't listed in root `--help`.** Agent has to read source. Fix: SUBCOMMANDS section is required.
- **Flags differ across subcommands.** `mytool create --json` works, `mytool list --output=json` is the same thing. Pick one. The standard set MUST be uniform across every subcommand of a given CLI.
- **Color escapes in `--json` mode.** Some CLIs leak ANSI into the envelope. Fix: when emitting JSON, every output path strips color.

## Cross-references

- `output-envelope.md` — the JSON envelope `--json` emits.
- `exit-codes.md` — the exit codes documented in every help page.
- `auth-headless.md` — the env vars that interact with `--config` and the credential resolution chain.
- `architect-new.md` — the design phase where the flag set is decided up front.
- `subprocess-harness.md` — how the harness reads `--help` to discover the flag surface.
