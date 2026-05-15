<!-- AUTO-GENERATED — DO NOT EDIT BETWEEN MARKERS -->
<!-- BEGIN HELP -->
```
render.sh — prompt rendering for orchestrate-codex (template + wrap modes).

Usage:
  render.sh --mode template INPUT_LIST TEMPLATE PROMPTS_DIR [PLACEHOLDER] [--force] [--dry-run]
  render.sh --mode wrap     INPUT_DIR OUTPUT_DIR [--prefix on|off] [--mode-target exec|single] [--force] [--dry-run]

Shared flags:
  --help, -h         this message
  --version          version string
  --force            overwrite existing output (default: refuse on collision; exit 2)
  --dry-run          print planned writes; do not modify filesystem

template mode:
  INPUT_LIST    file with one row per prompt; tab-delimited "name<TAB>content" or plain "name"
  TEMPLATE      template file containing PLACEHOLDER (default XXXXXXXXXXXXX)
  PROMPTS_DIR   output directory; per-row outputs at PROMPTS_DIR/<slug>.md
  PLACEHOLDER   string substituted (default XXXXXXXXXXXXX)

wrap mode:
  INPUT_DIR     directory of *.md files (non-recursive)
  OUTPUT_DIR    directory for wrapped outputs (one file per input, basename preserved)
  --prefix on|off    force SUBAGENT-STOP prefix on/off (auto-detected by default;
                     prefix-off triggers: research/analysis/audit content in single mode)
  --mode-target X    exec (default) or single — controls failure-protocol paragraph variant

Examples:
  render.sh --mode template inputs.txt template.md prompts/
  render.sh --mode wrap tickets/ prompts/ --mode-target single
```
<!-- END HELP -->

<!-- BEGIN WHY -->
## Why this script exists

(WHY block placeholder. Replace this paragraph with a short narrative — the
why, when to use it, and cross-references. Argument tables and exit codes
belong in the --help section above, not here.)

This block is hand-written and preserved across regenerations. The
<!-- BEGIN HELP --> / <!-- END HELP --> block above is regenerated from
`render.sh --help` by build-docs.mjs.
<!-- END WHY -->
<!-- END AUTO-GENERATED -->
