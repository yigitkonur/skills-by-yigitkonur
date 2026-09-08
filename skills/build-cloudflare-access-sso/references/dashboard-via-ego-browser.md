# Dashboard-only steps, driven with ego-browser

Most of this workflow is API work. Two things are not:

1. **Zero Trust onboarding** — choosing the team name and a plan. Only exists in the dashboard, and
   the team name it produces is what the Google redirect URI must contain.
2. **Google OAuth client creation** — Google Cloud Console has no API for creating OAuth clients or
   editing the consent screen.

You can hand these to the user as a checklist. Or an agent with a real browser can do them.

## Why ego-browser for this

[ego-browser](https://github.com/citrolabs/ego-lite/blob/main/skills/ego-browser/SKILL.md), from
[ego lite](https://lite.ego.app/), is a Chromium built for agents. What matters here:

- **It reuses the user's existing login state** in an isolated task space. The Cloudflare and
  Google consoles are already authenticated — the agent does not need, and must not be given,
  console passwords.
- **It does not fight the user for the browser.** Agent tabs live in their own space; the user's
  windows are untouched.
- **Control handoff is explicit.** For 2FA, a consent prompt, or a billing form, the agent hands
  the space back, the user does that one thing, and the agent resumes only after the user says so.

Install: run the ego-browser skill's `scripts/install.sh` (macOS), complete first-run onboarding
once, then confirm with `command -v ego-browser`. If it is not on `PATH`, it is usually under
`~/.local/bin`. Read that skill's `references/install.md` for the full flow.

## Credential rules when a browser holds real logins

This is the part that deserves care, because the session is authenticated as a real person.

- **Never type a password or a 2FA code into the browser on the user's behalf.** Hand off and let
  the user do it.
- **Never print a secret with `cliLog`.** Terminal output goes into the transcript. When a value
  must be captured — the Google client secret is the one that matters — read it in the browser and
  write it straight into the secret store or an env file the user controls, then confirm only
  *that it was captured*, not what it was.
- **Never screenshot a credentials page.** Screenshots are artifacts that outlive the session. If
  you need proof of a step, screenshot the confirmation, not the value.
- Redact account IDs, project IDs, and team names out of anything you report back.
- Stop before doing anything that spends money, publishes an OAuth app, or changes an
  organization-wide setting. Those are user decisions — surface them, do not click them.

## Shape of the work

The full helper surface, task-space lifecycle, and handoff protocol are in the ego-browser skill —
read it rather than reproducing it. The pattern that fits these consoles:

```bash
ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('cloudflare access setup')
await openOrReuseTab('https://one.dash.cloudflare.com/', { wait: true, timeout: 20 })
cliLog(await snapshotText())
EOF
```

Then act on the refs from that snapshot, and re-observe after every meaningful click. Both consoles
are ordinary DOM apps, so the semantic workflow (`snapshotText()` → `click('@N')` /
`fillInput('@N', …)`) is the right default; reach for screenshots only when a widget does not
surface properly.

Two ego-browser details that bite here specifically:

- `@N` refs are only valid for the **most recent** `snapshotText()`. Both consoles re-render
  constantly. Snapshot, act immediately, snapshot again.
- Timeouts are in **seconds**. Cloudflare's Zero Trust dashboard is slow on first load; give it
  room.

## Handoff points

Hand the task space back (`handOffTaskSpace`) and wait for explicit confirmation at:

- any login, 2FA prompt, or re-authentication challenge;
- the Zero Trust plan/payment step;
- the "Publish app" confirmation on the Google consent screen;
- anything the user has not already agreed to in this session.

A "user is controlling" error is a hard stop, not an obstacle to route around — the user took the
browser back, usually because the approach is going wrong. Ask, then wait.

## Coming back to the API

Once the team name exists and the OAuth client is created, everything else — IdP, policy,
application, DNS, verification — is API work. Go back to the main workflow. Do not keep driving the
dashboard for steps the API does better; dashboard clicks are unreviewable and unrepeatable.
