# Derailment Testing: A Methodology for AI Skill Quality Assurance

## Abstract

Derailment Testing is a structured quality assurance methodology for AI agent instructions (skills, prompts, workflows). The core insight: **the most effective way to find defects in procedural instructions is to follow them literally as a naive executor, documenting every moment the instructions fail to guide the next action.**

Unlike traditional software testing which validates code output, Derailment Testing validates *instructional clarity* — whether a set of written procedures can be followed without external knowledge, improvisation, or guesswork. It was developed during the construction of Claude Code skills (structured markdown instruction sets for Anthropic's Claude) and is applicable to any system where one entity writes procedures that another entity must follow.

## The Problem

AI agent instructions suffer from a unique failure mode: **they work in the author's head but derail in the executor's hands.** Authors have implicit context — they know which step is optional, what "substantial" means, where to write output files. Executors (AI agents, new team members, future-you) do not.

Traditional testing catches wrong outputs. Derailment Testing catches wrong inputs — instructions that are ambiguous, contradictory, incomplete, or assume knowledge the executor lacks.

## Key Definitions

| Term | Definition |
|---|---|
| **Skill** | A structured instruction set that tells an AI agent how to perform a task. The unit under test. |
| **Derailment** | Any moment during execution where the instructions fail to unambiguously specify the next action. |
| **Friction point** | A documented derailment with ID, severity, root cause, and fix. |
| **Dogfooding** | Executing a skill's own instructions on a real task to discover derailments. |
| **Naive executor** | The mindset adopted during testing: follow only what is written, never what is "obvious." |
| **Derail notes** | The structured artifact documenting all friction points discovered during a test run. |

## Core Principles

### 1. Follow literally, not intelligently

The tester must suppress domain knowledge and follow instructions exactly as written. If a step says "write the file" without specifying where, that is a derailment — even if the tester knows the obvious location. The goal is to simulate what happens when an AI agent with no prior context encounters these instructions.

### 2. Every derailment gets an ID

Friction points are numbered sequentially (F-01, F-02, ...) and assigned a severity. This creates a citable, trackable registry that survives across iterations.

### 3. Test on a real task, not a toy example

Dogfooding must use a genuine, non-trivial task. Toy tasks don't exercise edge cases in branching logic, error handling, or cross-reference integrity. The test task should be representative of the skill's intended use.

### 4. Fix the instructions, not the executor

When a derailment occurs, the fix goes into the instructions — not into "better agents" or "smarter users." If the instructions need external knowledge to work, they are incomplete.

### 5. The derail notes are the primary deliverable

The test report is not a pass/fail verdict. It is a structured document that records what happened, why, and what the fix is. This document has more value than the test itself because it makes the improvement trajectory visible.

## How This Differs from Existing Methods

| Method | What it tests | Failure signal |
|---|---|---|
| Unit testing | Code output correctness | Wrong value, crash, exception |
| Integration testing | Component interaction | Interface mismatch, data corruption |
| Usability testing | UI comprehensibility | User confusion, task abandonment |
| **Derailment Testing** | **Instructional completeness** | **Executor cannot determine next action** |

Derailment Testing is closest to usability testing in spirit but differs in three ways:

1. **The "user" is an AI agent**, not a human — so the threshold for ambiguity is lower (agents cannot ask clarifying questions mid-workflow)
2. **The artifact is instructions**, not a UI — so the fixes are textual edits, not design changes
3. **The tester is the author**, acting as a naive executor — creating a productive feedback loop between writing and testing

## Document Map

This methodology is documented across multiple files for progressive consumption:

| File | Purpose |
|---|---|
| `01-methodology-overview.md` | This file. Concepts, principles, and positioning. |
| `02-execution-protocol.md` | Step-by-step protocol for running a Derailment Test. |
| `03-friction-classification.md` | How to classify, score, and prioritize friction points. |
| `04-fix-patterns.md` | Common fix patterns for common derailment types. |
| `05-case-study-swift-watchos.md` | Full worked example: testing build-skills on Swift/watchOS topic. |
| `06-adaptation-guide.md` | How to apply Derailment Testing beyond AI skills. |
| `07-metrics-and-iteration.md` | Measuring improvement across multiple test cycles. |

## When to Use Derailment Testing

Use when:
- You have written procedural instructions that another entity must follow
- The executor cannot ask clarifying questions during execution
- The cost of a derailment (wasted time, wrong output, blocked workflow) exceeds the cost of testing
- You suspect your instructions "work for you but not for others"

Do not use when:
- Instructions are trivial (single step, no branching)
- The executor has full context and can improvise safely
- You need to test output quality (use evaluation suites instead)
