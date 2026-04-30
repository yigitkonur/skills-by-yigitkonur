# Teams, Users, Views, Favorites

Org-level surface — teams, users (incl. `me`), custom views, and personal favorites.

## Teams

```bash
linear-cli t list
linear-cli t list --output json --compact

linear-cli t get ENG                          # by team key
linear-cli t members ENG

linear-cli t create "Platform" -k PLT
linear-cli t create "Mobile" -k MOB --description "Mobile team" --private

linear-cli t update ENG --name "Engineering" --timezone "America/New_York"

linear-cli t delete TEAM_ID --force
```

### Team keys

A team key is the short prefix used in identifiers (e.g. `LIN`, `ENG`, `MOB`). Pass it as `-t KEY` everywhere — `i list -t ENG`, `i create "..." -t ENG`, `c list -t ENG`, etc.

Resolve unknowns:

```bash
linear-cli t list --output json --compact --fields key,name
```

## Users

```bash
linear-cli u list                             # all workspace users
linear-cli u list --team ENG                  # team members only
linear-cli u me                               # the calling user
linear-cli whoami                             # alias for u me
linear-cli u get "ada@example.com"            # lookup
```

### Resolve "me" once per session

```bash
ME=$(linear-cli u me --output json --fields id,name,email --compact)
echo "$ME" | jq -r '.email'
```

## Custom views

Saved filter sets, applied to `i list` / `p list`.

```bash
linear-cli v list
linear-cli v list --shared                    # shared views only
linear-cli v get "Bug Triage"

linear-cli v create "Open Bugs" -t ENG --shared
linear-cli v update VIEW_ID --name "Open Bugs (P0–P2)"
linear-cli v delete VIEW_ID --force

linear-cli i list --view "Bug Triage"
linear-cli p list --view "Active Projects"
```

Use views to encode the team's blessed filters once and have agents reference them by name instead of re-deriving filter logic.

## Favorites

Personal pinning to issues / projects.

```bash
linear-cli fav list
linear-cli fav add LIN-123                    # add issue
linear-cli fav add PROJECT_UUID               # add project
linear-cli fav remove LIN-123
linear-cli fav list --output json
```

## Recipe: "list all teams in my workspace"

```bash
# List all teams accessible in the current workspace
linear-cli t list --output json
```

Note: This lists all teams in the workspace, not just those you belong to. `linear-cli` does not currently expose a "teams I'm a member of" filter; to check membership, review the `members` field in the JSON output for each team.

## Recipe: "resolve a label by name to its UUID"

```bash
LABEL_ID=$(linear-cli l list --output json --compact \
  | jq -r '.[] | select(.name == "bug") | .id')
```

## Recipe: "find every issue assigned to a teammate"

```bash
linear-cli i list --assignee "Ada Lovelace" \
  --output json --fields identifier,title,state.name --compact
```

## Common confusions

| Looks like | Is actually |
|---|---|
| `t` | Teams |
| `u` | Users |
| `v` | Custom views |
| `fav` | Favorites (personal pins) |
| `whoami` | Alias for `u me` |

## See also

- `issues/search-and-filter.md` — applying views to `i list`.
- `setup.md` — workspaces vs teams; profiles vs accounts.
- `planning/projects-and-cycles.md` — assigning issues to projects.
