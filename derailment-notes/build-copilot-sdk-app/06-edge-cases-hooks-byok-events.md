# F-05, F-06, F-07, F-08 — Edge Cases (P2)

## F-05 — BYOK without model doesn't error at createSession (O2)
Session creates silently; error surfaces at send time. Pitfall table is misleading.
Fix: Clarified wording.

## F-06 — Hooks void return not documented (M6)
Returning void from hooks is valid but undocumented.
Fix: Added note to hooks.md.

## F-07 — Parallel tool event interleaving (M5)
No example shows `toolCallId` correlation for parallel tools.
Fix: Added subsection to events-and-streaming.md.

## F-08 — No node version check command (S1)
"Requires Node.js >= 20" stated but no command shown.
Fix: Added `node --version` to prerequisites.
