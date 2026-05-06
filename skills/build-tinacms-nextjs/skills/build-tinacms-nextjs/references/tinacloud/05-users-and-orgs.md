# Users and Organizations

How TinaCloud handles team members, roles, and multi-project organizations.

## Users vs Organizations

- **Organization** — the billable entity (your company)
- **Project** — a single CMS instance (one repo)
- **User** — a person with access to one or more projects

An org can have many projects; each project has its own user list.

## Adding users

**Project Settings → Users → Invite.** Type email, send invite. The invitee:

1. Clicks the invite link
2. Signs in (creates account if new)
3. Gets access to that specific project

## Tier user limits

| Tier | Users included | Overflow |
|---|---|---|
| Free | 2 | Cannot exceed |
| Team | 3 (up to 10) | Pay per additional |
| Team Plus | 5 (up to 20) | Pay per additional |
| Business | 20+ | Configurable |
| Enterprise | Custom | Configurable |

Hitting the cap blocks new invites. Upgrade tier or remove inactive users.

## Roles

Roles are tier-dependent:

| Role | Free / Team / Team Plus | Business+ |
|---|---|---|
| Admin (manages project) | All users | Limited |
| Editor (edits content) | All users | All non-admins |
| Viewer (read-only) | – | Available |

For most teams, Editor is the default. Business+ adds finer-grained roles.

## Org-level multi-project user management (Enterprise)

For agencies / large orgs with many projects:

- Add users at the org level once
- Assign per-project roles
- SSO via your IdP (Okta, Azure AD)

Available on Enterprise plan only.

## GitHub permissions

Each user must have GitHub access to commit content. TinaCloud uses each editor's GitHub identity for git commits (see `references/tinacloud/09-git-co-authoring.md`).

If an editor lacks repo write access on GitHub, their saves fail. Add them as a collaborator/member on GitHub first.

## Removing users

Project Settings → Users → Remove. They lose access immediately. They keep their TinaCloud account; just lose access to that project.

## Org transfer

To transfer a project to a different org:

1. Project owner in current org initiates transfer
2. Recipient org accepts
3. Billing transfers to new org

For most agencies, projects stay in one org through their lifecycle.

## Multiple orgs

A single TinaCloud account can be a member of multiple orgs. Useful for:

- Freelancers serving multiple clients
- Consultants on multiple project teams

Switch orgs via the org switcher in the dashboard.

## Audit log (Business+)

Track who edited what:

- Available in Project Settings → Activity (Business+)
- Logs login, edits, settings changes
- Exportable to CSV

For lower tiers, audit happens via git history (each commit shows the editor as author).

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Invited an email but they don't see the project | They need to sign in first | Have them sign in via the invite link |
| Hit user cap on free tier | Can't invite more | Upgrade or remove inactive |
| Editor without GitHub access | Saves fail | Add them as repo collaborator |
| Wrong role assigned | Editor can't edit | Adjust in Users tab |
| Removed the only admin | Locked out of project settings | Contact TinaCMS support |
