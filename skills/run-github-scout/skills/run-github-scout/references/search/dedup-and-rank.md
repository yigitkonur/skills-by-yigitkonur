# Dedup and Rank

Turn raw search results into a shortlist the user can act on.

## 1. Dedup

Dedup by `owner/repo` first. Drop forks unless the fork is the actual project you want.

## 2. Classify

Group every candidate into one of three buckets:
- **Relevant**
- **Maybe relevant**
- **Off-topic**

Off-topic repos should teach you how to refine, not clutter the final answer.

## 3. Rank the relevant set

Rank by user fit first, then by lightweight quality signals.

Recommended order of importance:
1. fit to the user's actual need
2. evidence from description, topics, or README intro
3. maintenance signals (pushed date, archived status, releases, obvious activity)
4. stars as a popularity proxy, not the sole verdict

## 4. Present the shortlist

Default final structure:

```markdown
## Best fits
- owner/repo — why it matches

## Worth a look
- owner/repo — what is promising, what is uncertain

## Ruled out
- owner/repo — why it does not fit
```

Recommended table:

```markdown
| Repo | Why it fits | Useful signals | Caveat |
|---|---|---|---|
```

## 5. Be explicit about uncertainty

If the category is broad or the search was thin, say so directly. A good shortlist can still be useful without pretending the field is fully exhausted.
