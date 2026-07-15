# Cross-layer bug triage for on-device product testing

The screen is the *last* layer of the product. When a flow misbehaves on-device, the defect is usually in one of six layers, and fixing the wrong one wastes a rebuild-retest cycle each time. Work cheapest-probe-first, and write down which layer you proved before editing anything.

## The six layers

1. **UI rendering** — the screen draws wrong given correct data.
2. **App logic/state** — handlers, navigation, context/effects deliver wrong data or drop writes.
3. **Delivery runtime** — the running bundle/binary doesn't contain the code you think it does.
4. **API boundary** — requests malformed, auth missing, wrong endpoint/schema, response misparsed.
5. **Backend** — server logic, jobs, database, third-party gateways.
6. **Environment/config** — env vars, feature flags, credentials, model/gateway endpoints, deploy-time snapshots.

Real-world base rates from live product testing: empty-screen and wrong-data bugs land in 4–6 far more often than 1–2; "my fix didn't work" is usually 3.

## Probe order per symptom

### Empty screen / missing data / infinite spinner

1. `agent-device network dump --include headers` — did the request fire at all? Status? Then `--include body` for the payload.
2. Request fired and returned data → the bug is UI/state (layer 1–2). Request 4xx/5xx → read the body; auth vs validation vs server error. No request at all → app logic never fired it (layer 2), or it's gated on a value that's missing (often an id the app expected in session/user metadata that was never written — check both the read site *and* the write site).
3. Response empty-but-200 → move server-side: query the datastore directly for the rows the endpoint should have returned, **as the current test user** (see "Identify the current user" below). Rows exist but API returns none → backend query/filter bug. No rows → whatever should have produced them (a job, a trigger, an earlier request) is the real target.

### Action "succeeds" but nothing happens

1. Read the settled diff / run `diff snapshot -i` — did *anything* change?
2. Check the action response for `targetHittable: false` — the tap may have resolved to a non-interactive node; re-target by @ref or longer text.
3. `snapshot -i` — is something *on top*? Floating dev bubbles, FABs, toasts, and invisible overlays eat taps while looking innocent. Move blockers instead of fighting them: `gesture pan <x> <y> <dx> <dy> <durationMs>`, or press a coordinate offset away from the overlay.
4. Still nothing → the handler may be silently early-returning on a falsy dependency. Suspect stale closures (a `useCallback`/memo capturing an old value) **and** state that was reset between screens (a provider/effect that clears state when an upstream dependency like the auth user changes). A dependency-array fix is not proof — retest observably.

### The fix didn't hold

This deserves its own discipline because it has two very different causes:

**(a) The fix never ran.** Prove delivery before doubting the logic:
- JS: is the Metro serving this app the one from the checkout you edited? Multiple worktrees/clones = multiple candidate Metros; a dev client keeps loading from whichever it bonded to. Check listening ports and process cwd; reload after confirming.
- Backend: deployed platforms often snapshot env vars at deploy time — an `.env` edit does nothing until you *redeploy*. Order matters: env edit → deploy → retest. A deploy that predates the env edit silently ships the old values.
- When in doubt, add a temporary visible marker (log line, string on screen, version field in a response) and confirm it appears at runtime.

**(b) The symptom has multiple causes.** Fixing cause #1 exposes cause #2 behind the identical symptom. Treat every retest failure as a *new* investigation: re-read the actual error text/response body; do not pattern-match to the previous failure. It is common for one "broken feature" to be three stacked defects (e.g. a dead config endpoint + a hardcoded stale value + a second dead endpoint used by a sibling path).

**Anti-sunk-cost rule:** after ~3 distinct fix attempts on one symptom, stop patching. Re-derive the root cause from fresh evidence. Also audit for *siblings* of a confirmed root cause (`grep` the codebase for the same hardcoded value/pattern) — where there was one, there are usually more.

### Wrong or surprising data

- `network dump --include body` first: is the app rendering exactly what it was given?
- Then verify the backend's own inputs. Classic trap: a query references a column/field that doesn't exist (or was renamed) and the platform fails *silently* for every user — verify schema assumptions against the live schema, not the code's beliefs.
- Distinguish "data for the wrong user" from "wrong data": see next section.

### Works once, fails on repeat

Server-side leftovers: idempotency keys, unique constraints, already-created records, consumed one-time states. Either clean the specific record, use a fresh account, or accept-and-assert the "already exists" path explicitly.

## Identify the current test user (multi-account trap)

Repeated fresh-state testing creates many accounts server-side. Before reasoning from any backend row:

- Sort by `created_at` descending and correlate with the wall-clock time of *this* run.
- Cross-check with a value you just typed on-device (name, email) or observed in `network dump` (user id in a request).
- Never query "the user" — always pin the id, and re-pin after every fresh-account cycle.

Misreading someone else's rows produces confident, completely wrong conclusions.

## Async / job-driven products

Many product features complete server-side seconds-to-minutes after the UI action (generation jobs, pipelines, webhooks):

- On-device, wait for the *named* outcome with a generous timeout: `wait text "…" 30000` — not snapshot spam.
- Server-side, poll the job/run platform's API for a **terminal** state (`completed|failed|crashed|timed_out`) — treat "still executing" and silence as *no result*, and read the error payload on failure instead of inferring from the UI.
- Prefer background polls (run the poll loop as a background process) over blocking the interactive session; keep testing other surfaces meanwhile.
- When a fan-out triggers several children (e.g. one action spawns multiple generation jobs), check **each child** to terminal state — the parent "succeeding" only proves it spawned them.
- Manual re-trigger of a failed job via the platform's API is a legitimate probe: it isolates "job logic broken" from "trigger wiring broken." Check the payload schema first (required ids and correlation fields).

## Auth-sensitive backend probing

When probing a backend that enforces row-level security / per-user scoping, the *credential class* changes the result:

- An anonymous/public key often gets "permission denied" where a real signed-in user gets a scoped result. **Do not** conclude "clients can't access this" from an anon-key probe — mint a real user token (e.g. an anonymous sign-up endpoint) and re-probe before deciding an app-side query is architecturally wrong.
- Service-role/admin keys bypass scoping entirely — great for *inspecting* state, useless for proving what the app can see. Label every probe with which credential it used.

Getting this wrong flips conclusions 180°: a correct app-side fallback can look "impossible" under the wrong key and get reverted.

## Verification ladder

State which rung you reached; never imply a higher one:

1. Code read / diff reviewed
2. Typecheck / lint pass
3. Unit tests pass
4. Fix deployed & runtime freshness proven
5. **Original symptom re-exercised live on-device from adequately fresh state — passes**
6. Downstream artifacts verified end-to-end (the data/record/file the feature exists to produce is real and correct)

Only 5–6 close a bug. A green diff at rung 1–3 plus "should work now" has repeatedly turned out false at rung 5.
