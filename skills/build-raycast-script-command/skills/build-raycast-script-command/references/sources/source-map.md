# Source Map

Use this file when you need provenance for the skill's internal references or want to update the Raycast guidance without guessing.

## Provenance by topic

| Topic | Internal references | Primary Raycast-owned sources |
|---|---|---|
| Scope, fit, and language choice | `references/foundations/scope-and-fit.md`, `references/foundations/language-selection.md` | Raycast Manual, Script Commands README |
| Python file anatomy and overall workflow | `references/python/file-anatomy.md`, `references/foundations/workflow.md` | Raycast Manual, Python template |
| Required metadata and mode behavior | `references/metadata/required-fields.md`, `references/metadata/mode-selection.md`, `references/metadata/inline-refresh-and-errors.md`, `references/troubleshooting/runtime-and-output-issues.md` | Raycast Manual, OUTPUTMODES.md |
| Arguments and Python positional input handling | `references/arguments/typed-arguments.md`, `references/python/implementation-patterns.md` | ARGUMENTS.md, Inputs blog post |
| Community-repo conventions, portability, and discovery | `references/conventions/community-repo-conventions.md`, `references/conventions/dependencies-and-portability.md`, `references/troubleshooting/discovery-checklist.md` | Script Commands README, CONTRIBUTING.md |
| Concrete command recipes and starter patterns | `references/examples/python-recipes.md`, `references/examples/bash-recipes.md`, `assets/templates/python-script-command.py`, `assets/templates/bash-script-command.sh` | Python template, Script Commands README, Raycast Manual |

## Raycast-owned upstream sources

- Raycast Manual: `https://manual.raycast.com/script-commands`
- Raycast Script Commands README: `https://github.com/raycast/script-commands/blob/master/README.md`
- Arguments docs: `https://github.com/raycast/script-commands/blob/master/documentation/ARGUMENTS.md`
- Output mode docs: `https://github.com/raycast/script-commands/blob/master/documentation/OUTPUTMODES.md`
- Contribution guide: `https://github.com/raycast/script-commands/blob/master/CONTRIBUTING.md`
- Python template: `https://github.com/raycast/script-commands/blob/master/templates/script-command.template.py`
- Inputs blog post: `https://www.raycast.com/blog/inputs-for-script-commands`

## Structural comparison sources

These sources influenced how the skill is organized, not the Raycast technical guidance itself.

- `alexi-build/raycast-extensions-skill/raycast-extensions-skill`
- `max-sixty/worktrunk/writing-user-outputs`
- `openclaw/skills/shell-scripting`
- `thebushidocollective/han/shell-best-practices`
- `interstellar-code/claud-skills/colored-output`

## How to use this map

- Use the routed internal references first.
- Use the upstream Raycast sources when you need to verify behavior that may have changed.
- Treat the structural comparison sources as style input only; do not use them to override Raycast-owned documentation.

## Maintenance rule

When updating this skill:

1. verify the Raycast-owned source first
2. update the affected internal reference files next
3. update templates if the recommended pattern changed
4. only then adjust `SKILL.md` routing if the workflow itself changed
