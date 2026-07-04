# Git Co-Authoring

TinaCloud commits content using each editor's GitHub identity. Their email and name appear in `git log`.

## How it works

When an editor logs into TinaCloud via GitHub OAuth, TinaCloud captures their:

- GitHub username
- Email address
- Display name

When that editor saves content, the resulting commit is authored by them — their name in `git log`, their avatar on GitHub commits page.

## Verifying

```bash
git log --pretty=format:'%an <%ae> %s' content/posts/launch.md
```

Should show the editor's name and email per commit.

## Email visibility

If the editor's GitHub email is private, TinaCloud uses the GitHub-provided no-reply address:

```
12345678+username@users.noreply.github.com
```

This still attributes commits correctly without exposing real email.

## Implications

- **Git history is the audit log.** Who changed what is in `git log`.
- **`Co-Authored-By` not used.** Each commit has one author (the editor). For pair-edited content, edits are interleaved commits, not co-authored.
- **GitHub repo permissions still apply.** Each editor needs at least Write access to the repo via GitHub. Without it, their saves fail.

## What if the editor doesn't have GitHub write access?

Saves fail with an auth error. Add them as a collaborator:

```
GitHub repo → Settings → Collaborators → Add user
```

Or add them to a team with write access (for org repos).

## Bot account vs individual accounts

For sites where you don't want individual editor identities in commits (e.g. all edits show as "TinaCloud Bot"):

- Configure a single "bot" GitHub account
- All editors log in as the bot via shared credentials (anti-pattern but possible)

This is a smell — usually you want individual attribution.

## Commit message format

TinaCloud generates commit messages automatically:

```
Update content/posts/launch.md
```

Customize? Not first-class — feature requested but not available. Workaround: amend commits manually after the fact.

## Branch protection rules

If GitHub branch protection requires:

- Signed commits (GPG signing)
- Specific commit author
- PR-only changes

These may interfere with TinaCloud direct commits. Either:

- Disable for the protected branch (when using Editorial Workflow, edits go through PRs anyway)
- Configure TinaCloud / GitHub to satisfy the rules

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Editor lacks GitHub repo access | Saves fail with auth error | Add as collaborator |
| Used `Co-Authored-By` and expected TinaCloud to honor it | Not supported | Each commit has one author |
| Branch protection blocks direct commits | Saves fail | Use Editorial Workflow + PR-based publishing |
| Editor with private email worried about exposure | TinaCloud uses no-reply | No action needed — GitHub handles privacy |
| Bot account for shared identity | Loses audit trail | Use individual accounts |
