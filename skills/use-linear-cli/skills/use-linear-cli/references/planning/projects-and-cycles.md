# Projects, Cycles, Sprints, Milestones, Roadmaps, Initiatives

The Linear planning surface — everything above the issue level. One file because most of these commands are read-mostly and have similar shape.

## Projects

```bash
linear-cli p list
linear-cli p list --archived
linear-cli p list --view "Active"

linear-cli p get PROJECT_ID                              # or by name
linear-cli p open "Q1 Roadmap"                           # browser

linear-cli p create "Q1 Roadmap" -t ENG
linear-cli p create "Feature" -t ENG \
  --icon "🚀" --priority 1 \
  --start-date 2025-01-01 --target-date 2025-03-31 \
  --lead USER_ID --status planned \
  --content "Project description"

linear-cli p update PROJECT_ID --name "New Name" --status completed
linear-cli p update PROJECT_ID --lead USER_ID --priority 2

linear-cli p archive PROJECT_ID
linear-cli p unarchive PROJECT_ID
linear-cli p delete PROJECT_ID --force

linear-cli p add-labels PROJECT_ID -l label1 -l label2
linear-cli p remove-labels PROJECT_ID -l label1
linear-cli p set-labels PROJECT_ID -l label1 -l label2

linear-cli p members PROJECT_ID
```

### Project create flag matrix

| Flag | Meaning |
|---|---|
| `-t TEAM` (req) | Team key |
| `--icon EMOJI` | Project icon |
| `--priority N` | 1=urgent..4=low |
| `--start-date DATE` | ISO date or `+Nw` |
| `--target-date DATE` | ISO date or `+Nw` |
| `--lead USER` | Lead (UUID, name, or email) |
| `--status STATE` | `planned`, `started`, `paused`, `completed`, `canceled` |
| `--content "..."` | Project description |
| `--id-only` | Output only the new ID |

## Project updates (status reports on a project)

Different from `i update`. These are *project health updates*.

```bash
linear-cli pu list "My Project"
linear-cli pu list "My Project" --output json
linear-cli pu get UPDATE_ID

linear-cli pu create "My Project" -b "On track this sprint"
linear-cli pu create "My Project" -b "Blocked on API" --health atRisk

linear-cli pu update UPDATE_ID -b "Updated status"
linear-cli pu archive UPDATE_ID
linear-cli pu unarchive UPDATE_ID
```

### Health values

| Value | Meaning |
|---|---|
| `onTrack` | Green — on schedule |
| `atRisk` | Yellow — slipping |
| `offTrack` | Red — won't make it |

## Milestones

```bash
linear-cli ms list -p "My Project"
linear-cli ms list -p "My Project" --output json
linear-cli ms get MILESTONE_ID

linear-cli ms create "Beta Release" -p "My Project"
linear-cli ms create "GA" -p PROJ --target-date 2025-06-01
linear-cli ms update MILESTONE_ID --target-date +2w
linear-cli ms update MILESTONE_ID --name "Renamed"
linear-cli ms delete MILESTONE_ID --force
```

`--target-date` accepts ISO `YYYY-MM-DD` or relative `+Nw`/`+Nd`.

## Cycles (Linear's name for sprints)

```bash
linear-cli c list -t ENG
linear-cli c list -t ENG --output json
linear-cli c current -t ENG                            # the active cycle
linear-cli c get CYCLE_ID                              # detail incl. issues

linear-cli c create -t ENG --name "Sprint 5"
linear-cli c create -t ENG --name "Sprint 5" \
  --starts-at 2024-01-01 --ends-at 2024-01-14

linear-cli c update CYCLE_ID --name "Sprint 5b"
linear-cli c update CYCLE_ID --description "Updated goals" --dry-run

linear-cli c complete CYCLE_ID
linear-cli c delete CYCLE_ID --force
```

## Sprint analytics

Built on top of cycles. The most commonly used live commands.

```bash
linear-cli sp status -t ENG                            # current sprint summary
linear-cli sp progress -t ENG                          # visual completion bar
linear-cli sp plan -t ENG                              # next cycle's planned issues
linear-cli sp carry-over -t ENG --force                # move incomplete to next cycle
linear-cli sp burndown -t ENG                          # ASCII burndown chart
linear-cli sp velocity -t ENG                          # last 6 cycles by default
linear-cli sp velocity -t ENG --cycles 10              # last 10 cycles
linear-cli sp velocity -t ENG --output json
```

| Subcommand | What it shows |
|---|---|
| `status` | Current sprint overview |
| `progress` | Completion bar |
| `plan` | Next cycle's planned issues |
| `carry-over` | Move incomplete to next cycle |
| `burndown` | ASCII burndown chart |
| `velocity` | Sprint velocity + trend |

## Roadmaps

Read-mostly today.

```bash
linear-cli rm list
linear-cli rm get ROADMAP_ID
linear-cli rm list --output json
```

Some binary versions support `rm create`/`rm update`/`rm delete`. Run `linear-cli rm --help` to confirm before using.

## Initiatives

High-level tracking spanning multiple projects. Read-mostly.

```bash
linear-cli init list
linear-cli init get INITIATIVE_ID
linear-cli init list --output json
```

## Recipe: "what cycle am I in and how am I tracking?"

```bash
linear-cli sp status -t ENG
linear-cli sp progress -t ENG
linear-cli sp burndown -t ENG
```

## Recipe: "carry over and start next sprint"

```bash
linear-cli c current -t ENG --output json
linear-cli sp carry-over -t ENG --force
linear-cli c create -t ENG --name "Sprint $(date +%V)" \
  --starts-at "$(date +%Y-%m-%d)" \
  --ends-at "$(date -v +14d +%Y-%m-%d)"
```

## Recipe: "post a project health update"

```bash
linear-cli pu create "Auth Workstream" \
  -b "Slipped one week — vendor SLA blocker." \
  --health atRisk
```

## Common confusions

| Looks like | Is actually |
|---|---|
| `pu` | *Project* updates — health reports on projects. |
| `cm` | *Issue* comments. |
| `c` | Cycles (Linear's sprint primitive). |
| `sp` | Sprint analytics layered over cycles. |
| `rm` | Roadmaps. |
| `init` | Initiatives. |
| `ms` | Milestones (project-scoped). |

## See also

- `planning/teams-and-org.md` — teams, users, custom views.
- `data/import-export.md` — exporting projects to CSV.
- `recipes/creating-many-issues.md` — using `--project NAME` to attach issues during bulk creation.
- `output-and-scripting.md` — `--output json` and `--fields` for plumbing.
