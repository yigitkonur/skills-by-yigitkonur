# Friction Classification

These severities classify symptoms in the trace.
They do not tell you what to edit.
Several P1 symptoms from the same step usually point to one source defect in the skill text.

## Severity levels

### P0 — Blocks progress
The executor cannot continue without external intervention or guesswork.

**Assign P0 when:**
- Hard stop (tool not installed, command fails, output location unknown)
- Two sources contradict each other
- Must invent information that should have been specified

### P1 — Causes confusion or wasted time
The executor eventually continues but wastes time, makes wrong assumption, or takes incorrect path first.

**Assign P1 when:**
- Re-reads instructions multiple times to understand
- Takes wrong action before finding correct one
- Uses implicit knowledge to fill a gap that should be explicit

### P2 — Minor annoyance
Noticed something off but continues without material delay.

## Severity flowchart

```
Hard stop?
├── YES → P0
└── NO
    ├── Wasted significant time or took wrong action?
    │   ├── YES → P1
    │   └── NO → P2
    └── Needed external knowledge to continue?
        ├── YES, critical decision → P1
        └── YES, minor gap → P2
```

## Compound severity

3+ P1 items in one workflow step = **compound P0** for prioritization.
