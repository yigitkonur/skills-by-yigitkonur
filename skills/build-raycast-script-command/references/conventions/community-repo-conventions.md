# Community Repo Conventions

Use this file when the command should be easy to share or contribute to the Raycast community repo.

## Naming

- use lower-case dash-case filenames
- use real extensions like `.py` and `.sh`

Example:

- `wikipedia-search.py`
- `open-ticket.sh`

## Folder Layout

- group related scripts together
- avoid huge generic folders
- place images in a dedicated `images/` folder when needed

## Metadata Style

- titles should use title case
- `packageName` should be present for community portability
- use the mode that matches command behavior rather than defaulting blindly

## `.template.` Rule

If the script still needs user-specific edits before it can work, name it with `.template.` so it is not treated as ready-to-run.

Example:

- `create-trello-card.template.py`

## Shareable command checklist

- dash-case filename
- correct file extension
- clear `packageName`
- title-cased `title`
- dependency notes if needed
- `.template.` used when the user must fill in tokens or IDs

## Common mistakes

| Mistake | Fix |
|---|---|
| sharing a script with hard-coded personal secrets | convert to `.template.` and document setup |
| omitting `packageName` in a shared command | add it for portability |
| mixing unrelated scripts in one generic folder | group by service or workflow |
