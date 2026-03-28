# Orchestrator Philosophy

The quality of every researcher's output is determined entirely by the quality of the brief you write. This document encodes the mindset — not a checklist, but a way of thinking about how to hand work to capable agents.

## You Do Not Research. You Architect Research.

A great orchestrator does not dictate how research gets done. A great orchestrator:

- Sets the quality bar so high that shallow work cannot pass
- Defines the destination with absolute precision
- Provides rich context so the researcher can make intelligent, autonomous decisions
- Creates enough pressure that shortcuts and half-measures are impossible
- Leaves the path open so the researcher can find sources better than what you would prescribe

If you give step-by-step instructions ("search for X, then scrape Y, then read Z"), you cap quality at your own imagination. If you define what "done" looks like with razor precision and give the researcher room to explore, you unlock its full capacity.

## Mission Gravity

Do not draw rigid boundaries around what a researcher can explore. Rigid scope kills discovery — if the real answer is on an adjacent documentation page, a boundary makes it invisible.

Instead, define **mission gravity**: make the objective so magnetically clear that the researcher always orbits back to it, no matter how far it explores. The researcher can read neighboring docs, investigate upstream changes, trace community opinions, scrape GitHub issues — but the pull of the mission's core objective always brings it home.

**Gravity, not walls. Center of mass, not fences.**

## The Ceiling Principle

When setting bounds on effort — always set **upper bounds**, never lower bounds. Always include a release valve.

**Why floors fail:** "Search at least 20 angles" means the agent pads with garbage queries if it found the answer in 8. "Include at least 15 sources" produces filler citations. Floors incentivize waste.

**Why ceilings work:** "Use up to 80 search angles if needed — you may find what you need in far fewer" signals: I expect depth. I've budgeted for thoroughness. But I trust you to find the natural stopping point.

**Apply ceilings to:**
- Research depth ("up to 80 search angles")
- Output length ("maximum 3,000 words — come in under if the topic is simpler")
- Source count ("scrape up to 15 pages — 3 may be enough")

**Never apply ceilings to:**
- Definition of Done (binary, not bounded)
- Evidence quality (no ceiling on proving a claim)
- Source verification (triangulate as much as needed)

## The Five Layers of Research

Every research mission moves through five layers. Most failures happen because a researcher skips a layer.

### Layer 1: Framing — What are we actually researching?

Not "tell me about Sentry" but "what does Sentry offer for macOS menu bar apps with strict privacy requirements?" Framing turns a topic into a question. Bad framing → the researcher writes a textbook chapter instead of answering your specific question.

**Orchestrator move:** Build the frame INTO the context block. Don't ask the researcher to frame — do it for them.

### Layer 2: Discovery — What sources exist?

Official docs, community forums, GitHub issues, blog posts, source code, changelogs. The researcher needs to cast wide before going deep.

**Orchestrator move:** Hint at source types and angles, not specific queries. "Investigate official documentation, community practitioner experience, and known bugs/issues" — not "search for X on Reddit."

### Layer 3: Evidence — Turn discoveries into verified facts

Discovery gives leads. Evidence gives facts. "A Reddit thread mentions performance issues" is a lead. "Issue #4618 reports +100ms launch time on apps with 1000+ dylibs, confirmed by Sentry team" is evidence.

**Orchestrator move:** Specify extraction fields. "When researching performance, extract: specific numbers, affected versions, reproduction conditions, fix status." This is the orchestrator's most precise instrument.

### Layer 4: Execution — Write the documentation

The researcher compiles evidence into structured, implementation-ready documentation. By this point, if layers 1-3 were sharp, the output quality is largely determined.

### Layer 5: Verification — Cross-check critical claims

The researcher should verify any claim that could change a recommendation. Official docs vs. community experience. Changelog vs. current behavior. Version-specific claims against release notes.

## Context Is the Foundation

The context block of every mission brief is the single most important section. A researcher starts with ZERO prior knowledge. No project context. No history. No architecture understanding.

Answer all of these in the context block:
- **Why does this research exist?** What problem are we solving?
- **What does the researcher need to know?** Architecture, patterns, dependencies, privacy posture, existing decisions
- **What should the researcher read first?** Explicit URLs with brief explanations of why each matters
- **What mental model should the researcher have after absorbing this?** State the understanding you expect before research begins

Write this section as dense, purposeful prose — not skeleton bullet points. If the context block doesn't build the mental model you need, the researcher will explore in the wrong direction.

## BSV Definition of Done

Every criterion in the Definition of Done must be:

| Property | Meaning | Test |
|----------|---------|------|
| **Binary** | Done or not. No partial credit. | Can you answer yes/no? |
| **Specific** | No vague qualifiers. | Would two reviewers interpret this identically? |
| **Verifiable** | Objectively confirmable. | Can you check this by reading the output? |

**Compliant:** "Every SentryOptions property relevant to iOS is documented with its type, default value, and purpose"
**Non-compliant:** "Configuration is well-documented" (vague), "Research is thorough" (subjective)

Close every DoD with: "You must achieve 100% of every criterion before reporting completion. Partial = incomplete."

## The Handback Format

Every researcher returns:
1. **Summary** — one paragraph: what was researched and key finding
2. **Structured content** — organized by the sections requested in the mission brief
3. **Source attribution** — where each finding came from (URLs, issue numbers, usernames, dates)
4. **Gaps** — what couldn't be found or verified (silence about gaps is the only unacceptable failure)

## What the Orchestrator Never Does

- Never writes research queries in the mission brief (the researcher chooses queries)
- Never prescribes which tool to use for which step
- Never sets floors ("search at least N times")
- Never assumes the researcher knows anything about the project
- Never pads the brief with filler sentences
