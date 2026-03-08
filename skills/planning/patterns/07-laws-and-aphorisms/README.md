# 07 — Laws and Aphorisms of Software Engineering

Empirical observations, heuristics, and folk wisdom that have survived decades of software development. These are not rules to follow blindly — they are lenses for understanding why systems and teams behave the way they do.

## Index

| File | Law | One-Line Summary |
|---|---|---|
| [conways-law.md](./conways-law.md) | Conway's Law | Systems mirror the communication structure of the organizations that build them |
| [brooks-law.md](./brooks-law.md) | Brooks's Law | Adding people to a late project makes it later due to communication overhead |
| [hyrums-law.md](./hyrums-law.md) | Hyrum's Law | With enough users, all observable behaviors of your API become depended upon |
| [goodharts-law.md](./goodharts-law.md) | Goodhart's Law | When a measure becomes a target, it ceases to be a good measure |
| [hofstadters-law.md](./hofstadters-law.md) | Hofstadter's Law | It always takes longer than you expect, even accounting for Hofstadter's Law |
| [parkinsons-law.md](./parkinsons-law.md) | Parkinson's Law | Work expands to fill the time available for its completion |
| [galls-law.md](./galls-law.md) | Gall's Law | Complex working systems evolve from simple working systems, never from scratch |
| [lehman-laws.md](./lehman-laws.md) | Lehman's Laws | Eight empirical laws governing how software systems evolve over time |
| [kernighans-law.md](./kernighans-law.md) | Kernighan's Law | Debugging is twice as hard as writing code — so write code at half your skill level |
| [zawinskis-law.md](./zawinskis-law.md) | Zawinski's Law | Every program expands until it can read mail — the law of feature creep |
| [linuss-law.md](./linuss-law.md) | Linus's Law | Given enough eyeballs, all bugs are shallow — the case for code review and open source |
| [sturgeons-law.md](./sturgeons-law.md) | Sturgeon's Law | 90% of everything is crud — develop strong evaluation skills for libraries and advice |
| [cunninghams-law.md](./cunninghams-law.md) | Cunningham's Law | The best way to get the right answer is to post the wrong one — feedback loops |
| [peter-principle.md](./peter-principle.md) | Peter Principle | People rise to their level of incompetence — the developer-to-manager trap |
| [rule-of-three.md](./rule-of-three.md) | Rule of Three | Duplicate up to three times before abstracting — balancing DRY and YAGNI |
| [zero-one-infinity.md](./zero-one-infinity.md) | Zero-One-Infinity | The only reasonable numbers in design are zero, one, and infinity |

## How to Use These

These laws are **diagnostic tools**, not prescriptions. Use them to:

1. **Explain** why a problem is occurring (Conway's Law explains why your API boundaries match team boundaries)
2. **Predict** what will happen next (Lehman's Laws predict complexity growth in long-lived systems)
3. **Argue** for or against a decision (Brooks's Law argues against adding headcount to a late project)
4. **Recognize** patterns as they emerge (Zawinski's Law helps you see feature creep before it is too late)

## Relationships Between Laws

- **Brooks's Law + Conway's Law:** Adding people changes communication structure, which changes architecture
- **Hofstadter's Law + Parkinson's Law:** Estimates are always wrong, and available time is always filled
- **Goodhart's Law + Sturgeon's Law:** Metrics get gamed, and most gaming produces crud
- **Gall's Law + Lehman's Laws:** Start simple (Gall), then manage inevitable complexity growth (Lehman)
- **Kernighan's Law + Linus's Law:** Write simple code (Kernighan) so reviewers can actually find bugs (Linus)
- **Rule of Three + Zawinski's Law:** Resist abstraction (Rule of Three) and resist feature creep (Zawinski)
