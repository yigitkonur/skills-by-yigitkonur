# 08 — Anti-Patterns

Anti-patterns are common responses to recurring problems that appear to be beneficial but are ultimately counterproductive. Unlike simple "bad code," anti-patterns are tempting, widespread, and have well-understood negative consequences.

Each entry includes: what the anti-pattern looks like, why teams fall into it, how to recognize it, and how to recover.

## Anti-Pattern Index

| File | Anti-Pattern | Severity | One-Line Summary |
|---|---|---|---|
| [god-object.md](./god-object.md) | God Object | HIGH | One class/module that knows and does everything, becoming the dependency hub |
| [lava-flow.md](./lava-flow.md) | Lava Flow | MEDIUM | Dead code that solidifies in the codebase because it is too risky to remove |
| [golden-hammer.md](./golden-hammer.md) | Golden Hammer | MEDIUM | Using one familiar tool or technology for every problem regardless of fit |
| [premature-optimization.md](./premature-optimization.md) | Premature Optimization | HIGH | Optimizing code before measuring where the actual bottlenecks are |
| [cargo-cult-programming.md](./cargo-cult-programming.md) | Cargo Cult Programming | HIGH | Copying code or patterns without understanding why they work |
| [spaghetti-code.md](./spaghetti-code.md) | Spaghetti Code | HIGH | Tangled, unpredictable control flow with deep nesting and hidden state |
| [big-ball-of-mud.md](./big-ball-of-mud.md) | Big Ball of Mud | CRITICAL | A system with no discernible architecture where everything depends on everything |
| [accidental-complexity.md](./accidental-complexity.md) | Accidental Complexity | HIGH | Complexity from tools and decisions that is not inherent to the problem being solved |
| [boat-anchor.md](./boat-anchor.md) | Boat Anchor | LOW | Unused code kept "just in case" that adds maintenance burden with zero value |
| [analysis-paralysis.md](./analysis-paralysis.md) | Analysis Paralysis | MEDIUM | Over-analyzing decisions to the point where no decision is ever made |
| [not-invented-here.md](./not-invented-here.md) | Not Invented Here (NIH) | MEDIUM | Refusing to use existing external solutions in favor of building your own |
| [inner-platform-effect.md](./inner-platform-effect.md) | Inner Platform Effect | HIGH | A system so configurable it becomes a bad reimplementation of the platform it runs on |

## Severity Guide

| Level | Meaning | Impact |
|---|---|---|
| **CRITICAL** | Threatens the viability of the entire system | Requires architectural intervention |
| **HIGH** | Significantly impairs development velocity and reliability | Requires focused refactoring effort |
| **MEDIUM** | Causes ongoing friction and suboptimal outcomes | Address during regular maintenance |
| **LOW** | Minor nuisance, accumulates over time | Clean up opportunistically |

## How to Use This Section

1. **Recognize:** Use these descriptions to identify anti-patterns in your codebase. Most codebases have several.
2. **Prioritize:** Focus on high-severity anti-patterns first. A Big Ball of Mud matters more than a Boat Anchor.
3. **Recover:** Each entry includes recovery strategies. Most anti-patterns can be addressed incrementally.
4. **Prevent:** Understanding why teams fall into these traps helps you avoid them in new projects.

## Relationships Between Anti-Patterns

- **God Object + Spaghetti Code:** God Objects often contain spaghetti code internally.
- **Big Ball of Mud:** The end state when multiple anti-patterns go unaddressed for years.
- **Cargo Cult + Golden Hammer:** Copying a pattern without understanding leads to applying it everywhere.
- **Premature Optimization + Accidental Complexity:** Optimizing the wrong thing adds complexity that does not serve the problem.
- **Boat Anchor + Lava Flow:** Both are dead code, but boat anchors were speculative (never used) while lava flow was real (once used, now dead).
- **Analysis Paralysis + Not Invented Here:** Teams sometimes build their own to avoid the analysis paralysis of evaluating 50 external options.
- **Inner Platform Effect + Accidental Complexity:** Inner platforms are the ultimate accidental complexity — building infrastructure instead of solving the problem.

## The Anti-Pattern Lifecycle

```
1. Problem arises
2. Team applies familiar/convenient solution (the anti-pattern)
3. Short-term: appears to work
4. Medium-term: friction increases, velocity decreases
5. Long-term: system becomes difficult to maintain or extend
6. Recognition: "This is an anti-pattern"
7. Recovery: incremental refactoring toward better patterns
```
