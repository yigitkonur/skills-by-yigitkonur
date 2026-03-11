# What Worked Well

## Strong points in run-playwright SKILL.md

1. **Non-negotiable rules 3-6** consistently prevented stale-ref errors.
   The "treat refs as disposable" rule (rule 6) was the most impactful single
   instruction — it prevented every potential stale-ref failure.

2. **Recovery rules** were actionable and correctly ordered by frequency.
   The most common recovery (unsure which tab) is listed first.

3. **Do this / not that table** caught real mistakes. The `tab-new` then `open`
   vs `tab-new <url>` entry prevented a known failure mode.

4. **Reference routing table** was accurate. Every file matched its declared scope
   and no reference sent the reader to the wrong place.

5. **Progressive evidence levels** (state, behavior, visual, diagnosis) provided
   a natural escalation path without over-collecting proof.

6. **eval for truth checks** caught a stale page header that snapshot missed,
   proving rule 8 ("screenshots as evidence, not default observation").

7. **Form verification pattern** (fill, eval value, submit, eval result) was
   reliable and produced trustworthy evidence.

8. **fill --submit** shortcut worked for simple single-field forms. Not documented
   but useful when discovered.
