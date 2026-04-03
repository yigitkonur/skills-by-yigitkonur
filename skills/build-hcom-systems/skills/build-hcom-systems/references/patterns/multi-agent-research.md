# Multi-Agent Research: 35 Repositories Adapted for hcom

Research from 35 multi-agent collaboration repositories adapted into hcom patterns and script ideas.

## Category 1: Multi-Agent Coding Frameworks (SOP/Role-Based)

### MetaGPT (66K stars)
- **Pattern**: SOP-driven virtual software company. `Code = SOP(Team)`. Agents model PM, Architect, Engineer, QA.
- **Communication**: Structured artifact hand-off through Standard Operating Procedures.
- **hcom adaptation**: Pipeline script with PM -> Architect -> Engineer -> QA. Each role produces an artifact sent via `hcom send @next-role --intent request`. Transcripts serve as artifact containers.

### ChatDev (32K stars)
- **Pattern**: Zero-code YAML-defined DAG workflows. RL-trained dynamic orchestrator.
- **hcom adaptation**: Define agent topology in bash arrays. Script orchestrates fan-out from CEO to specialists. Use `hcom events --sql` for DAG completion tracking.

### CrewAI (47K stars)
- **Pattern**: Role-playing agents in "Crews" with event-driven "Flows". Sequential and hierarchical process models.
- **hcom adaptation**: Research crew: Researcher -> Analyst -> Writer. Use `hcom events sub` for event-driven flow triggers. Tags group crew members.

### BotSharp (3K stars)
- **Pattern**: Routing module coordinates agent messages. Plugin-based architecture.
- **hcom adaptation**: Triage agent receives via `hcom listen`, classifies intent, routes to specialist agents (DB expert, Security expert) via `hcom send @specialist-`.

## Category 2: Communication Protocols

### Agent2Agent (A2A) Protocol (23K stars)
- **Pattern**: Opaque agent services exposing capability "Agent Cards". JSON-RPC 2.0.
- **hcom adaptation**: Each agent publishes capabilities via broadcast. Discovery agent builds registry. Tasks routed to best-matching agent. Service discovery pattern.

### ACP (970 stars)
- **Pattern**: REST API with "await" mechanism. Agents pause execution requesting external input.
- **hcom adaptation**: Agent sends `hcom send @human-proxy --intent request -- "AWAIT: need input on X"`. Human-proxy agent collects input, replies. Implements interactive pause/resume.

### Room/AACP (11 stars)
- **Pattern**: P2P signed transcripts. Cryptographic audit trail.
- **hcom adaptation**: Two agents negotiate via `hcom send` exchanges. Each message logged. `hcom transcript` produces immutable record. Audit trail pattern.

## Category 3: Debate and Discussion

### Multi-Agents-Debate / MAD (540 stars)
- **Pattern**: Tit-for-tat debate between Devil (affirmative) and Angel (negative) with Judge.
- **hcom adaptation**: Already implemented as `hcom run debate`. Turn-based exchanges via threads. Judge orchestrates rounds and renders verdict.

### ChatEval (330 stars)
- **Pattern**: Multi-agent debate for LLM evaluation. Persona-driven scoring.
- **hcom adaptation**: Evaluation panel: multiple agents with different personas (Critic, General Public) assess code/text quality. Synthesizer collects all assessments.

### SWE-Debate (25 stars)
- **Pattern**: Competitive multi-agent debate for bug resolution. MCTS-style.
- **hcom adaptation**: Multiple agents propose fix locations via `hcom send @discriminator-`. Discriminator ranks proposals. Best gets expanded and tested.

### FREE-MAD (13 stars)
- **Pattern**: Consensus-free debate. Quality of reasoning scored, not votes. A single strong argument can win.
- **hcom adaptation**: Agents generate solutions independently, then critique peers. Scoring agent weighs reasoning quality. Topology-aware (ring, star, all-to-all).

## Category 4: Ensemble and Voting

### Mixture of Agents / MoA (2.9K stars)
- **Pattern**: Layered multi-LLM ensemble. Reference agents produce candidates, aggregator fuses. Beats GPT-4o.
- **hcom adaptation**: Fan-out N reference agents, each sends to aggregator thread. Aggregator uses `hcom events --sql` to collect all, synthesizes. Stackable layers.

### Swarms/MAKER (6.1K stars)
- **Pattern**: Statistical agreement voting for long-horizon tasks.
- **hcom adaptation**: Multiple agents solve independently. MAKER agent tallies statistical agreement across solutions, selects winner. Voting/consensus pattern.

## Category 5: Swarm Orchestration

### OpenAI Swarm (21K stars)
- **Pattern**: Lightweight handoffs. Two primitives: Agent + handoff (returning another Agent from a function).
- **hcom adaptation**: Triage agent classifies query, uses `hcom send @specialist-` to hand off. Specialist takes over conversation. Dynamic routing.

### ClawTeam (3.3K stars)
- **Pattern**: Leader-worker with isolated git worktrees. Inbox messaging + task API.
- **hcom adaptation**: Leader decomposes task, spawns workers via `hcom N claude --tag worker`. Workers communicate status. Leader monitors via `hcom events sub`. Spawn-monitor-collect pattern.

### HAAS (3.1K stars)
- **Pattern**: Hierarchical Autonomous Agent Swarm. Three tiers: Board > Executive > Workers. RBAC.
- **hcom adaptation**: Board agent broadcasts policy. Executive translates to tasks. Workers execute and report up. Three-tier hierarchy with tag-based routing.

### Swarm-Tools (594 stars)
- **Pattern**: Coordinator-worker with durable messaging. Event-sourced state survives crashes.
- **hcom adaptation**: Coordinator sends tasks via `hcom send`. Workers reserve files. On crash, state recovers from `hcom transcript`. Confidence decay via age-based scoring.

## Category 6: Reflection and Self-Critique

### Reflexion (3.1K stars)
- **Pattern**: Verbal reinforcement learning. Agent iteratively improves via textual self-reflection.
- **hcom adaptation**: Agent sends attempt to critic via `hcom send @critic-`. Critic replies with REFLECTION feedback. Agent retries with reflection context. Self-improvement loop.

### Self-Refine (790 stars)
- **Pattern**: Generator-Critic-Refiner loop. Same pattern works across diverse domains.
- **hcom adaptation**: Generator -> Critic -> Refiner pipeline. Loop until quality threshold. Each round uses thread for context continuity.

## Category 7: Structured Reasoning

### Tree of Thoughts (5.9K stars)
- **Pattern**: BFS/DFS tree search over reasoning paths. Generators, evaluators, selectors.
- **hcom adaptation**: Multiple generator agents propose approaches. Evaluator scores 1-10. Selector picks top-k for next round. Multi-round exploration with pruning.

## Category 8: Simulation

### Generative Agents / Stanford Smallville (21K stars)
- **Pattern**: Agents simulate believable human behavior in shared virtual world. Memory-driven.
- **hcom adaptation**: Agents broadcast actions to shared environment thread. Others observe via `hcom events --sql` and react. Emergent behavior from shared state.

### FilmAgent (1.1K stars)
- **Pattern**: Multi-agent filmmaking. Director, Screenwriter, Cinematographer. Critique-Correct-Verify + Debate-Judge.
- **hcom adaptation**: Director broadcasts vision. Specialists debate approaches via exchanges. Director judges. Creative collaboration pattern.

## Category 9: Graph/Workflow Orchestration

### LangGraph (27K stars)
- **Pattern**: Agents as directed graph nodes. State transitions drive branching/looping. Durable execution.
- **hcom adaptation**: Agents write state via `hcom send --thread state`. Conditional routing based on message content. Graph-based flow with event subscriptions.

### DeerFlow / ByteDance (41K stars)
- **Pattern**: Lead agent dynamically spawns scoped sub-agents. Parallel execution. Built on LangGraph.
- **hcom adaptation**: Lead receives task, decomposes, spawns sub-agents via `hcom N claude --tag subtask`. Results flow back. Context summarization for token limits.

### Fractals (600 stars)
- **Pattern**: Recursive task decomposition into self-similar tree. Each leaf isolated in git worktree.
- **hcom adaptation**: Decomposer breaks task recursively. Workers execute leaf tasks. Batch DFS/BFS strategies via `--batch-id`.

## Category 10: Research Platforms

### AutoGen / Microsoft (56K stars)
- **Pattern**: AgentTool treats agents as callable tools. Two-agent chat, group chat, hierarchical.
- **hcom adaptation**: One agent exposes itself as a tool via `hcom listen`. Another invokes it: `hcom send @math-expert --intent request -- "solve x^2=4"`. Agent-as-tool pattern.

### CAMEL (16.5K stars)
- **Pattern**: Agent societies with role-playing, workforce delegation, critic-review loops.
- **hcom adaptation**: Two agents role-play with assigned personas via system prompts. Critic agent reviews exchange quality.

### AgentScope (19K stars)
- **Pattern**: MsgHub-based routing. Agents register; hub routes messages. Dynamic add/remove.
- **hcom adaptation**: Agents use tags as hub channels. `@hub-` routes to all hub members. Dynamic join/leave via `hcom config -i self tag hub`.

### MindSearch (6.8K stars)
- **Pattern**: Parallel multi-query search. Orchestrator fans out to search agents simultaneously.
- **hcom adaptation**: Fan out query to N agents via broadcast. Each agent searches independently. Aggregator synthesizes. Parallel fan-out/fan-in.

## Top 10 Patterns for hcom Scripts

| # | Pattern | Repos | hcom Primitives | Use Case |
|---|---------|-------|----------------|----------|
| 1 | Adversarial Debate | MAD, SWE-Debate, ChatEval | send, listen, thread | Code review, decisions |
| 2 | Mixture-of-Agents | MoA, Swarms | broadcast, events --sql, thread | Best-of-N synthesis |
| 3 | Handoff/Triage | OpenAI Swarm | send @specialist-, list | Dynamic routing |
| 4 | Reflexion Loop | Reflexion, Self-Refine | send @critic-, thread | Iterative improvement |
| 5 | Hierarchical Gov | HAAS, ClawTeam | broadcast, tag routing | Policy enforcement |
| 6 | Consensus-Free Debate | FREE-MAD | send @peer-, scoring | Bias-free evaluation |
| 7 | Tree-of-Thoughts | ToT | broadcast proposals, events | Branching exploration |
| 8 | Shared World Sim | Generative Agents | broadcast, events sub | Emergent behavior |
| 9 | SOP/Artifact Pipeline | MetaGPT, ChatDev | send, transcript | Structured delivery |
| 10 | Durable Swarm | Swarm-Tools | send, transcript, resume | Crash-resilient coordination |

## Pattern-to-hcom Primitive Mapping

| Pattern Need | hcom Primitive | How |
|-------------|---------------|-----|
| Fan-out to N agents | `hcom send @tag- -- "task"` | Tag-based broadcast |
| Fan-in collect | `hcom events --sql "msg_thread='T' AND msg_text LIKE 'RESULT%'"` | SQL query on thread |
| Turn-based exchange | `hcom send @agent --thread T --intent request` + wait | Threaded conversation |
| Dynamic routing | `hcom list --json` + conditional `hcom send @name` | Status-based dispatch |
| Event subscription | `hcom events sub --file "*.py" --once` | Reactive triggers |
| Context handoff | `hcom transcript @agent --full --detailed` | Transcript as artifact |
| Self-improvement | `hcom send @self --intent request -- "ATTEMPT"` | Self-addressed messages |
| Hierarchical cascade | `@board-` -> `@exec-` -> `@worker-` via threads | Multi-tier messaging |
| Agent-as-tool | `hcom listen --timeout 300` in service agent | Blocking service pattern |
| Parallel execution | `hcom N claude --tag worker --batch-id B` | Batch launch |
| Crash recovery | `hcom r <name>` (resume from snapshot) | State recovery |
| File reservation | `hcom events sub --collision` | Conflict detection |
| Structured context | `hcom send --title T --transcript N-M:full --files a.py` | Bundle handoff |
