# Advanced Multi-Agent Patterns

Patterns inspired by research on 35 multi-agent repositories (MetaGPT, CrewAI, AutoGen, ChatDev, CAMEL, OpenAI Swarm, Reflexion, MoA, and others). Each pattern is adapted to hcom primitives.

## Pattern 1: Reflexion / Self-Critique Loop

**Inspired by:** Reflexion (3.1K stars), Self-Refine (790 stars)

Agent attempts a task, a critic evaluates, agent iterates with reflection feedback. Verbal reinforcement learning without gradient updates.

```bash
#!/usr/bin/env bash
# Reflexion loop: attempt -> critique -> reflect -> retry until passing.
set -euo pipefail

LAUNCHED_NAMES=()
track_launch() { local n=$(echo "$1" | grep '^Names: ' | sed 's/^Names: //'); for x in $n; do LAUNCHED_NAMES+=("$x"); done; }
cleanup() { for n in "${LAUNCHED_NAMES[@]}"; do hcom kill "$n" --go 2>/dev/null || true; done; }
trap cleanup ERR

name_flag="" ; task="" ; max_rounds=3
while [[ $# -gt 0 ]]; do
  case "$1" in --name) name_flag="$2"; shift 2 ;; --rounds) max_rounds="$2"; shift 2 ;; -*) shift ;; *) task="$1"; shift ;; esac
done
name_arg="" ; [[ -n "$name_flag" ]] && name_arg="--name $name_flag"
[[ -z "$task" ]] && task="write a Python function to check if a number is prime"

thread="reflex-$(date +%s)"

# Launch worker agent
launch_out=$(hcom 1 claude --tag worker --go --headless \
  --hcom-prompt "Task: ${task}. Attempt it. Send your attempt: hcom send \"@critic-\" --thread ${thread} --intent request -- \"ATTEMPT: <your code/answer>\". If you get REFLECTION feedback, study it carefully, then try again with improvements. After PASS, send FINAL. Stop." 2>&1)
track_launch "$launch_out"
worker=$(echo "$launch_out" | grep '^Names: ' | sed 's/^Names: //' | tr -d ' ')

# Launch critic agent
launch_out=$(hcom 1 claude --tag critic --go --headless \
  --hcom-system-prompt "You are a rigorous code critic. Find real bugs, not style issues." \
  --hcom-prompt "On ATTEMPT from @worker-: evaluate correctness thoroughly. If bugs found: send hcom send \"@${worker}\" --thread ${thread} --intent request -- \"REFLECTION: <specific issues and how to fix>\". If correct: send hcom send \"@${worker}\" --thread ${thread} --intent inform -- \"PASS\". After ${max_rounds} attempts, pass anyway with notes. Stop after sending verdict." 2>&1)
track_launch "$launch_out"

# Wait for FINAL
result=$(hcom events --wait 180 --sql "msg_thread='${thread}' AND msg_text LIKE '%FINAL%'" $name_arg 2>/dev/null)
if [[ -n "$result" ]]; then echo "PASS"; else echo "TIMEOUT"; fi

trap - ERR
for n in "${LAUNCHED_NAMES[@]}"; do hcom kill "$n" --go 2>/dev/null || true; done
```

**Key technique:** The critic sends REFLECTION messages containing specific issues. The worker uses these as context for its next attempt. Each round builds on previous reflection.

---

## Pattern 2: Mixture-of-Agents Ensemble (MoA)

**Inspired by:** MoA (2.9K stars) -- open-source ensemble that beat GPT-4o on AlpacaEval

Multiple "reference" agents produce independent answers. An aggregator synthesizes the best parts into a superior response. Can be layered for deeper refinement.

```bash
#!/usr/bin/env bash
# Mixture-of-Agents: N reference agents + aggregator.
set -euo pipefail

LAUNCHED_NAMES=()
track_launch() { local n=$(echo "$1" | grep '^Names: ' | sed 's/^Names: //'); for x in $n; do LAUNCHED_NAMES+=("$x"); done; }
cleanup() { for n in "${LAUNCHED_NAMES[@]}"; do hcom kill "$n" --go 2>/dev/null || true; done; }
trap cleanup ERR

name_flag="" ; task="" ; agents=3
while [[ $# -gt 0 ]]; do
  case "$1" in --name) name_flag="$2"; shift 2 ;; --agents) agents="$2"; shift 2 ;; -*) shift ;; *) task="$1"; shift ;; esac
done
name_arg="" ; [[ -n "$name_flag" ]] && name_arg="--name $name_flag"
[[ -z "$task" ]] && task="explain the CAP theorem with a practical example"

thread="moa-$(date +%s)"

# Launch N reference agents in parallel
for i in $(seq 1 $agents); do
  launch_out=$(hcom 1 claude --tag "ref${i}" --go --headless \
    --hcom-prompt "Answer independently (do NOT coordinate with other agents): ${task}. Send: hcom send \"@agg-\" --thread ${thread} --intent inform -- \"REF${i}: <your complete answer>\". Stop." 2>&1)
  track_launch "$launch_out"
done

# Launch aggregator
launch_out=$(hcom 1 claude --tag agg --go --headless \
  --hcom-system-prompt "You are a synthesis expert. Combine multiple perspectives into one superior answer." \
  --hcom-prompt "Wait for ${agents} reference answers in thread ${thread}. Check: hcom events --sql \"msg_thread='${thread}' AND msg_text LIKE 'REF%'\" --last 20 $name_arg. Synthesize the best parts of all answers into one comprehensive response. Send: hcom send --thread ${thread} --intent inform -- \"SYNTHESIS: <combined answer>\". Stop." 2>&1)
track_launch "$launch_out"

result=$(hcom events --wait 180 --sql "msg_thread='${thread}' AND msg_text LIKE '%SYNTHESIS%'" $name_arg 2>/dev/null)
if [[ -n "$result" ]]; then echo "PASS"; else echo "TIMEOUT"; fi

trap - ERR
for n in "${LAUNCHED_NAMES[@]}"; do hcom kill "$n" --go 2>/dev/null || true; done
```

**Two-layer variant:** Add a second layer of reference agents that improve on the first synthesis.

---

## Pattern 3: Red Team / Blue Team

**Inspired by:** Adversarial testing (security, AI safety), FREE-MAD consensus-free debate

Red team finds vulnerabilities/problems. Blue team defends/fixes. Judge evaluates.

```bash
#!/usr/bin/env bash
# Red/Blue team: attacker finds issues, defender fixes, judge scores.
set -euo pipefail

LAUNCHED_NAMES=()
track_launch() { local n=$(echo "$1" | grep '^Names: ' | sed 's/^Names: //'); for x in $n; do LAUNCHED_NAMES+=("$x"); done; }
cleanup() { for n in "${LAUNCHED_NAMES[@]}"; do hcom kill "$n" --go 2>/dev/null || true; done; }
trap cleanup ERR

name_flag="" ; target=""
while [[ $# -gt 0 ]]; do
  case "$1" in --name) name_flag="$2"; shift 2 ;; -*) shift ;; *) target="$1"; shift ;; esac
done
name_arg="" ; [[ -n "$name_flag" ]] && name_arg="--name $name_flag"
[[ -z "$target" ]] && target="src/auth.py"

thread="redblue-$(date +%s)"

# Red team (attacker)
launch_out=$(hcom 1 claude --tag red --go --headless \
  --hcom-system-prompt "You are a security researcher. Find real vulnerabilities, not hypothetical ones." \
  --hcom-prompt "Analyze ${target} for security vulnerabilities. Read: cat ${target}. Send findings: hcom send \"@blue-\" \"@judge-\" --thread ${thread} --intent request -- \"VULNERABILITIES: <list with severity and exploit steps>\". Stop." 2>&1)
track_launch "$launch_out"

# Blue team (defender)
launch_out=$(hcom 1 claude --tag blue --go --headless \
  --hcom-system-prompt "You are a security engineer. Propose concrete fixes." \
  --hcom-prompt "Wait for VULNERABILITIES from @red-. For each vulnerability, propose a fix. Send: hcom send \"@judge-\" --thread ${thread} --intent inform -- \"DEFENSES: <fix for each vuln>\". Stop." 2>&1)
track_launch "$launch_out"

# Judge
launch_out=$(hcom 1 claude --tag judge --go --headless \
  --hcom-prompt "Wait for VULNERABILITIES and DEFENSES in thread ${thread}. Check: hcom events --sql \"msg_thread='${thread}'\" --last 10 $name_arg. Score: Are vulns real? Are fixes adequate? Send VERDICT with security grade A-F. Stop." 2>&1)
track_launch "$launch_out"

result=$(hcom events --wait 180 --sql "msg_thread='${thread}' AND msg_text LIKE '%VERDICT%'" $name_arg 2>/dev/null)
if [[ -n "$result" ]]; then echo "PASS"; else echo "TIMEOUT"; fi

trap - ERR
for n in "${LAUNCHED_NAMES[@]}"; do hcom kill "$n" --go 2>/dev/null || true; done
```

---

## Pattern 4: Pair Programming

**Inspired by:** XP pair programming, ClawTeam leader-worker pattern

Two agents alternate between driver (writes code) and navigator (reviews in real-time). They swap roles each round.

```bash
#!/usr/bin/env bash
# Pair programming: driver codes, navigator reviews, swap roles.
set -euo pipefail

LAUNCHED_NAMES=()
track_launch() { local n=$(echo "$1" | grep '^Names: ' | sed 's/^Names: //'); for x in $n; do LAUNCHED_NAMES+=("$x"); done; }
cleanup() { for n in "${LAUNCHED_NAMES[@]}"; do hcom kill "$n" --go 2>/dev/null || true; done; }
trap cleanup ERR

name_flag="" ; task=""
while [[ $# -gt 0 ]]; do
  case "$1" in --name) name_flag="$2"; shift 2 ;; -*) shift ;; *) task="$1"; shift ;; esac
done
name_arg="" ; [[ -n "$name_flag" ]] && name_arg="--name $name_flag"
[[ -z "$task" ]] && task="implement a linked list in Python with insert, delete, and search"

thread="pair-$(date +%s)"

# Agent A (starts as driver)
launch_out=$(hcom 1 claude --tag "driverA" --go --headless \
  --hcom-prompt "PAIR PROGRAMMING. You start as DRIVER. Task: ${task}. Write the first part (e.g., class definition and insert method). Send: hcom send \"@driverB-\" --thread ${thread} --intent request -- \"DRIVER DONE: <what you wrote>. Your turn to navigate/extend.\". When you get code back, NAVIGATE: review it, suggest improvements. After 2 rounds, send COMPLETE with final version. Stop." 2>&1)
track_launch "$launch_out"

# Agent B (starts as navigator)
launch_out=$(hcom 1 claude --tag "driverB" --go --headless \
  --hcom-prompt "PAIR PROGRAMMING. You start as NAVIGATOR. Task: ${task}. Wait for DRIVER DONE from @driverA-. Review their code. Then switch to DRIVER: extend with next part (e.g., delete and search methods). Send: hcom send \"@driverA-\" --thread ${thread} --intent request -- \"DRIVER DONE: <your additions>. Your turn to navigate/finalize.\". Stop after partner sends COMPLETE." 2>&1)
track_launch "$launch_out"

result=$(hcom events --wait 180 --sql "msg_thread='${thread}' AND msg_text LIKE '%COMPLETE%'" $name_arg 2>/dev/null)
if [[ -n "$result" ]]; then echo "PASS"; else echo "TIMEOUT"; fi

trap - ERR
for n in "${LAUNCHED_NAMES[@]}"; do hcom kill "$n" --go 2>/dev/null || true; done
```

---

## Pattern 5: Reactive Watcher

**Inspired by:** LangGraph event-driven flows, fatcow.sh live subscription

An agent subscribes to events and reacts automatically. No polling loop needed -- hcom's subscription engine delivers notifications.

```bash
#!/usr/bin/env bash
# Reactive watcher: subscribes to file changes and auto-reviews.
set -euo pipefail

LAUNCHED_NAMES=()
track_launch() { local n=$(echo "$1" | grep '^Names: ' | sed 's/^Names: //'); for x in $n; do LAUNCHED_NAMES+=("$x"); done; }
cleanup() { for n in "${LAUNCHED_NAMES[@]}"; do hcom kill "$n" --go 2>/dev/null || true; done; }
trap cleanup ERR

name_flag="" ; watch_path="src/"
while [[ $# -gt 0 ]]; do
  case "$1" in --name) name_flag="$2"; shift 2 ;; --path) watch_path="$2"; shift 2 ;; -*) shift ;; *) shift ;; esac
done
name_arg="" ; [[ -n "$name_flag" ]] && name_arg="--name $name_flag"

# Launch reactive reviewer
launch_out=$(hcom 1 claude --tag watcher --go --headless \
  --hcom-prompt "You are a live code reviewer. Subscribe to file changes: hcom events sub --file \"${watch_path}*.py\" $name_arg. When you get a notification about a file change, read the changed file, review it, and send feedback: hcom send \"@bigboss\" --intent inform -- \"REVIEW: <file>: <feedback>\". Stay active -- do not stop. Keep listening for more changes." 2>&1)
track_launch "$launch_out"

echo "Watcher launched. It will auto-review any .py file changes in ${watch_path}"
echo "Press Ctrl+C to stop."

# Keep script alive until interrupted
trap "cleanup; exit 0" INT
while true; do sleep 60; done
```

**Key technique:** `hcom events sub --file "pattern"` creates a subscription. When any agent edits a matching file, the watcher receives a system message automatically.

---

## Pattern 6: Batch Processing / Map-Reduce

**Inspired by:** MindSearch parallel search, AgentScope concurrent pipelines

Fan out work to N workers, collect results, reduce into final output.

```bash
#!/usr/bin/env bash
# Map-reduce: fan out tasks to workers, collect and reduce results.
set -euo pipefail

LAUNCHED_NAMES=()
track_launch() { local n=$(echo "$1" | grep '^Names: ' | sed 's/^Names: //'); for x in $n; do LAUNCHED_NAMES+=("$x"); done; }
cleanup() { for n in "${LAUNCHED_NAMES[@]}"; do hcom kill "$n" --go 2>/dev/null || true; done; }
trap cleanup ERR

name_flag=""
while [[ $# -gt 0 ]]; do
  case "$1" in --name) name_flag="$2"; shift 2 ;; -*) shift ;; *) shift ;; esac
done
name_arg="" ; [[ -n "$name_flag" ]] && name_arg="--name $name_flag"

thread="mapred-$(date +%s)"

# Define tasks (one per worker)
tasks=("Analyze src/auth.py for security issues" "Analyze src/db.py for performance issues" "Analyze src/api.py for error handling")
num_tasks=${#tasks[@]}

# MAP: Launch one worker per task
for i in $(seq 0 $((num_tasks - 1))); do
  launch_out=$(hcom 1 claude --tag "map${i}" --go --headless \
    --hcom-prompt "${tasks[$i]}. Send result: hcom send \"@reduce-\" --thread ${thread} --intent inform -- \"MAP${i}: <findings>\". Stop." 2>&1)
  track_launch "$launch_out"
done

# REDUCE: Aggregator collects all MAP results
launch_out=$(hcom 1 claude --tag reduce --go --headless \
  --hcom-prompt "Wait for ${num_tasks} MAP results in thread ${thread}. Check: hcom events --sql \"msg_thread='${thread}' AND msg_text LIKE 'MAP%'\" --last 20 $name_arg. Combine all findings into a prioritized report. Send: hcom send --thread ${thread} --intent inform -- \"REPORT: <combined findings>\". Stop." 2>&1)
track_launch "$launch_out"

result=$(hcom events --wait 180 --sql "msg_thread='${thread}' AND msg_text LIKE '%REPORT%'" $name_arg 2>/dev/null)
if [[ -n "$result" ]]; then echo "PASS"; else echo "TIMEOUT"; fi

trap - ERR
for n in "${LAUNCHED_NAMES[@]}"; do hcom kill "$n" --go 2>/dev/null || true; done
```

---

## Pattern 7: Multi-Oracle / Ask-the-Experts

**Inspired by:** CAMEL agent societies, BotSharp routing, OpenAI Swarm handoff

A triage agent classifies incoming questions and routes to specialist agents. Each specialist is deeply knowledgeable in one domain.

```bash
#!/usr/bin/env bash
# Multi-oracle: triage agent routes to domain experts.
set -euo pipefail

LAUNCHED_NAMES=()
track_launch() { local n=$(echo "$1" | grep '^Names: ' | sed 's/^Names: //'); for x in $n; do LAUNCHED_NAMES+=("$x"); done; }
cleanup() { for n in "${LAUNCHED_NAMES[@]}"; do hcom kill "$n" --go 2>/dev/null || true; done; }
trap cleanup ERR

name_flag="" ; question=""
while [[ $# -gt 0 ]]; do
  case "$1" in --name) name_flag="$2"; shift 2 ;; -*) shift ;; *) question="$1"; shift ;; esac
done
name_arg="" ; [[ -n "$name_flag" ]] && name_arg="--name $name_flag"
[[ -z "$question" ]] && question="How should I structure the database schema for a multi-tenant SaaS app?"

thread="oracle-$(date +%s)"

# Launch specialist agents
launch_out=$(hcom 1 claude --tag "db-expert" --go --headless \
  --hcom-system-prompt "You are a database architecture expert specializing in PostgreSQL, schema design, and query optimization." \
  --hcom-prompt "Wait for questions routed to you. Answer thoroughly with code examples. After answering, stop." 2>&1)
track_launch "$launch_out"

launch_out=$(hcom 1 claude --tag "sec-expert" --go --headless \
  --hcom-system-prompt "You are a security expert specializing in authentication, authorization, and data protection." \
  --hcom-prompt "Wait for questions routed to you. Answer thoroughly with code examples. After answering, stop." 2>&1)
track_launch "$launch_out"

launch_out=$(hcom 1 claude --tag "arch-expert" --go --headless \
  --hcom-system-prompt "You are a software architecture expert specializing in distributed systems and API design." \
  --hcom-prompt "Wait for questions routed to you. Answer thoroughly with code examples. After answering, stop." 2>&1)
track_launch "$launch_out"

# Launch triage agent
launch_out=$(hcom 1 claude --tag triage --go --headless \
  --hcom-prompt "Question: ${question}. Check active experts: hcom list $name_arg. Route this question to the most relevant expert(s) using @tag- prefix. Send: hcom send \"@<expert-tag>-\" --thread ${thread} --intent request -- \"QUESTION: ${question}\". Then wait for answer, forward it: hcom send --thread ${thread} --intent inform -- \"ANSWER: <expert response>\". Stop." 2>&1)
track_launch "$launch_out"

result=$(hcom events --wait 180 --sql "msg_thread='${thread}' AND msg_text LIKE '%ANSWER%'" $name_arg 2>/dev/null)
if [[ -n "$result" ]]; then echo "PASS"; else echo "TIMEOUT"; fi

trap - ERR
for n in "${LAUNCHED_NAMES[@]}"; do hcom kill "$n" --go 2>/dev/null || true; done
```

---

## Pattern 8: Hierarchical Governance

**Inspired by:** HAAS (3.1K stars) -- multi-tier agent swarm with oversight board

Three tiers: Board sets policy, Executive translates to tasks, Workers execute. Decisions flow down, reports flow up.

```bash
thread="gov-$(date +%s)"

# Board (policy layer)
launch_out=$(hcom 1 claude --tag board --go --headless \
  --hcom-system-prompt "You are a technical advisory board. Set high-level policy and constraints." \
  --hcom-prompt "Project: ${task}. Set policy: quality standards, security requirements, constraints. Send: hcom send \"@exec-\" --thread ${thread} --intent request -- \"POLICY: <requirements>\". Wait for REPORT. Send VERDICT. Stop." 2>&1)
track_launch "$launch_out"

# Executive (planning layer)
launch_out=$(hcom 1 claude --tag exec --go --headless \
  --hcom-prompt "Wait for POLICY from @board-. Translate into concrete tasks. Send: hcom send \"@worker-\" --thread ${thread} --intent request -- \"TASK: <specific work items>\". Wait for DONE. Compile report: hcom send \"@board-\" --thread ${thread} --intent inform -- \"REPORT: <summary>\". Stop." 2>&1)
track_launch "$launch_out"

# Worker (execution layer)
launch_out=$(hcom 1 claude --tag worker --go --headless \
  --hcom-prompt "Wait for TASK from @exec-. Execute each item. Send: hcom send \"@exec-\" --thread ${thread} --intent inform -- \"DONE: <results>\". Stop." 2>&1)
track_launch "$launch_out"
```

---

## Pattern 9: SOP/Artifact Pipeline

**Inspired by:** MetaGPT (66K stars), ChatDev (32K stars), Dev-Council

Agents pass structured artifacts through a defined pipeline. Each role transforms the artifact.

```bash
thread="sop-$(date +%s)"

# PM writes user stories
launch_out=$(hcom 1 claude --tag pm --go --headless \
  --hcom-system-prompt "You are a product manager. Write clear user stories with acceptance criteria." \
  --hcom-prompt "Requirement: ${task}. Write user stories. Send: hcom send \"@arch-\" --thread ${thread} --intent request -- \"STORIES: <user stories with acceptance criteria>\". Stop." 2>&1)
track_launch "$launch_out"

# Architect designs system
launch_out=$(hcom 1 claude --tag arch --go --headless \
  --hcom-system-prompt "You are a software architect. Design clean, scalable systems." \
  --hcom-prompt "Wait for STORIES from @pm-. Design system architecture. Send: hcom send \"@eng-\" --thread ${thread} --intent request -- \"DESIGN: <architecture with component diagram and API spec>\". Stop." 2>&1)
track_launch "$launch_out"

# Engineer implements
launch_out=$(hcom 1 codex --tag eng --go --headless \
  --hcom-prompt "Wait for DESIGN from @arch-. Implement the code. Send: hcom send \"@qa-\" --thread ${thread} --intent request -- \"CODE: <implementation summary>\". Stop." 2>&1)
track_launch "$launch_out"

# QA tests
launch_out=$(hcom 1 claude --tag qa --go --headless \
  --hcom-prompt "Wait for CODE from @eng-. Read transcript: hcom transcript @eng- --full --detailed $name_arg. Write and run tests. Send: hcom send --thread ${thread} --intent inform -- \"QA: pass/fail <report>\". Stop." 2>&1)
track_launch "$launch_out"
```

---

## Pattern 10: Tree-of-Thoughts Exploration

**Inspired by:** Tree of Thoughts (5.9K stars) -- branching search over reasoning paths

Multiple agents propose different approaches, evaluator scores them, selector picks top-k for the next round.

```bash
thread="tot-$(date +%s)"

# Round 1: Generate N approaches
for i in 1 2 3; do
  launch_out=$(hcom 1 claude --tag "gen${i}" --go --headless \
    --hcom-prompt "Propose approach ${i} (be creative, different from others): ${task}. Send: hcom send \"@eval-\" --thread ${thread} --intent inform -- \"APPROACH${i}: <your unique approach>\". Stop." 2>&1)
  track_launch "$launch_out"
done

# Evaluator scores approaches
launch_out=$(hcom 1 claude --tag eval --go --headless \
  --hcom-prompt "Wait for 3 approaches in thread ${thread}. Check: hcom events --sql \"msg_thread='${thread}' AND msg_text LIKE 'APPROACH%'\" --last 10 $name_arg. Score each 1-10 on feasibility, correctness, elegance. Send: hcom send --thread ${thread} --intent inform -- \"SCORES: <approach>: <score> for each. BEST: <best approach name>\". Stop." 2>&1)
track_launch "$launch_out"

# Round 2: Refine the best approach
launch_out=$(hcom 1 claude --tag refine --go --headless \
  --hcom-prompt "Wait for SCORES in thread ${thread}. Read all approaches and scores: hcom events --sql \"msg_thread='${thread}'\" --last 20 $name_arg. Take the BEST approach and refine it into a complete solution. Send: hcom send --thread ${thread} --intent inform -- \"SOLUTION: <refined complete solution>\". Stop." 2>&1)
track_launch "$launch_out"
```

---

## Pattern-to-hcom Mapping Summary

| Pattern | hcom Primitives | Key Technique |
|---------|----------------|---------------|
| Reflexion | send to critic, receive REFLECTION | Self-improvement via verbal feedback |
| MoA Ensemble | N parallel agents, aggregator reads thread | Fan-out/fan-in synthesis |
| Red/Blue Team | Attacker -> Defender -> Judge | Adversarial security testing |
| Pair Programming | Alternating driver/navigator roles | Role-swapping collaboration |
| Reactive Watcher | events sub --file, auto-review | Event-driven subscription |
| Map-Reduce | N workers with distinct tasks, reducer | Parallel analysis aggregation |
| Multi-Oracle | triage routes to specialists | Dynamic expert routing |
| Hierarchical Gov | Board -> Executive -> Worker | Three-tier policy cascade |
| SOP Pipeline | PM -> Arch -> Eng -> QA | Artifact transformation chain |
| Tree-of-Thoughts | Generate -> Evaluate -> Select -> Refine | Branching exploration with pruning |
