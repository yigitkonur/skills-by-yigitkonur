# Ultrathinking

Use ultrathinking only when the cost of being wrong is unusually high.

## When to Use It

- the change is hard to reverse
- the task could alter architecture or workflow
- the blast radius is broad
- the team may inherit this decision for a long time
- weak assumptions would be expensive to discover late

## Ultrathink Pass

### 1. Widen the frame

Ask:
- what problem am I really solving?
- what outcome actually matters?
- what am I assuming about constraints, users, or the system?

### 2. Compare real options

Do not compare one real option to two strawmen. Keep 2-3 serious options alive.

For each option, evaluate:
- reversibility
- complexity cost
- operational burden
- failure modes
- verification path

### 3. Run a pre-mortem

Ask:
- if this fails in production, what was the likely mistake?
- what did I optimize too early?
- what coupling or hidden dependency did I underestimate?

### 4. Force the simplest adequate path

Reject solutions that are technically clever but operationally heavier than the problem needs.

### 5. Define the rollback

If the chosen path fails, what is the safest recovery move?

Ultrathinking is not maximal analysis. It is disciplined analysis scaled to irreversible or high-cost decisions.
