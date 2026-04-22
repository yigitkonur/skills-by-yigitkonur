# Quality Gates

Lean stop-or-refine checkpoints for repo scouting.

## 1. After interpreting the request

| Signal | Action |
|---|---|
| Problem, constraints, and exclusions are clear enough to search | Start discovery immediately |
| One missing answer would materially change search direction | Ask 1-2 targeted questions, then continue |
| User already named examples or anti-examples | Use them as seed terms and skip extra clarification |

## 2. After the first pass

| Result shape | Verdict | Next move |
|---|---|---|
| 3-8 clearly relevant repos, or a clear top cluster | Strong | Shortlist now, or run one narrow refinement only if a known gap remains |
| 1-2 relevant repos plus several maybes | Thin | Run one refinement pass using the wording from relevant and maybe-relevant repos |
| Mostly off-topic results | Noisy | Broaden to the category term or switch to augmented search for naming help |
| Repos look adjacent but not exact | Ambiguous | Read README intros for the best 3-5 and extract better terms before refining |

## 3. After the refinement pass

| Signal | Action |
|---|---|
| New results mostly repeat known repos | Stop and synthesize |
| The field is still thin but the top few are plausible | Deliver the shortlist with explicit uncertainty |
| The field is still noisy because naming is fuzzy | Use optional web/MCP augmentation, then stop after one more targeted sweep |
| The user explicitly wants higher confidence | Deepen only on the top 3-5 repos |

## 4. Before deeper evaluation

Deepen only when at least one is true:
- the user asked for deeper comparison
- the top options are close and need feature evidence
- the shortlist would materially improve with README, test, or release verification
- the user asked for export, report, or a reusable artifact

## Stop conditions

Stop when any of these is true:
- the shortlist answers the user's need well enough to act
- new searches are mostly duplicates
- the remaining gaps are better stated as caveats than solved by more searching
- the user is satisfied with the markdown result
