# Universal AI Signs & Heuristics

While different language models display distinct model-specific quirks, all Large Language Models share fundamental statistical tendencies arising from next-token probability prediction. Because models optimize for statistically probable token sequences, they naturally converge on average sentence lengths, predictable rhetorical structures, and generalized explanatory templates.

This guide catalogs the universal markers of AI writing identified by empirical editorial research (including Wikipedia's `WP:Signs_of_AI_writing`, Reddit editorial communities, and university writing labs), and details why mechanical word blacklists fail.

---

## 1. Empirical AI Markers from Community Research

### 1.1 Wikipedia: Signs of AI Writing (`WP:Signs_of_AI_writing`)
WikiProject AI Cleanup maintains a forensic catalog of telltale structures left by LLMs:

1. **Significance Inflation**: Inflating routine events, technical updates, or biographical subjects with ungrounded historical weight:
   - *Synthetic*: "Her monumental career, spanning over four decades, stands as a testament to her enduring legacy and profound artistic impact on modern cinema."
   - *Flaw*: Editorializing with reverent, non-neutral platitudes (*stands as a testament*, *enduring legacy*) instead of citing specific milestones.
   - *Natural*: "Between 1982 and 2024, she directed twelve feature films and six off-Broadway productions, winning the Palme d'Or in 1999."
2. **False Ranges**: Vague pseudo-comprehensive expressions that simulate breadth without conveying information:
   - *Synthetic*: "We offer comprehensive solutions ranging from enterprise database migration to small-scale analytics and everything in between."
   - *Flaw*: The cliché *"ranging from X to Y and everything in between"* is an empty rhetorical placeholder.
   - *Natural*: "We migrate PostgreSQL databases and build real-time analytics pipelines."
3. **Compulsive Sandwich Summaries**: Obligatory introductory throat-clearing and concluding recapitulations:
   - *Synthetic*: "In summary, as organizations navigate an increasingly complex regulatory landscape, embracing this strategic framework will be pivotal in driving sustainable efficiency, mitigating multifaceted risks, and unlocking future organizational resilience."
   - *Flaw*: The obligatory *"In summary"* concluding paragraph that stacks three abstract tricolon benefits without providing new data or operational next steps.
   - *Natural*: "Adopting this framework cuts external compliance audit prep from six weeks to four days, saving roughly $180,000 annually."
4. **Negative Parallelisms**: Symmetrical rhetorical devices contrasting a strawman against an abstraction:
   - *Synthetic*: "It’s not just a CRM; it’s an intelligent, interconnected ecosystem that empowers teams to redefine how modern enterprises navigate customer relationships."
   - *Flaw*: The formulaic *"It's not just X; it's Y"* construct, combined with buzzword abstractions (*interconnected ecosystem*, *empowers teams to redefine*).
   - *Natural*: "A lightweight sales CRM that auto-logs customer WhatsApp calls and syncs transcripts directly into deal pipelines."

---

## 2. Structural & Cadence AI Markers

### 2.1 The Burstiness Deficit (Monotone Sentence Lengths)
* **The Mechanism**: LLMs generate text token by token based on conditional probability distributions. High-perplexity words and dramatic variations in clause length are statistically disfavored. As a result, AI-generated sentences consistently cluster around 16–22 words.
* **The Symptom**: Prose reads like a metronome ticking at a constant tempo. Every sentence contains a subject, a qualified verb, and a participial tail.
* **The Human Contrast**: Natural human writing exhibits extreme burstiness. A 4-word punchy fragment is followed by a 34-word compound thought with subordinate clauses, dashes, and parentheticals, followed by an 8-word conclusion.

### 2.2 Throat-Clearing Openings
* **The Symptom**: Delaying the core message with sweeping, universal platitudes:
  - *"In today's fast-paced, hyper-connected digital world..."*
  - *"When it comes to modern software architecture, one thing is certain..."*
  - *"It is important to remember that security is not a destination, but a journey..."*
* **The Remediation**: Delete the first 1–2 sentences entirely. Start directly with the concrete noun, metric, or event.

### 2.3 Tricolon Grouping & Symmetrical Balance
* **The Symptom**: A compulsive habit of grouping adjectives, nouns, or bullet points into sets of three:
  - *"Our platform is fast, reliable, and scalable."*
  - *"We strive for innovation, integrity, and excellence."*
  - *"By optimizing workflows, reducing costs, and empowering teams..."*
* **The Remediation**: Break the tricolon. State the primary benefit alone, or provide specific, quantified evidence for two distinct outcomes.

### 2.4 Register Mismatch
* **The Symptom**: Applying a sterile, high-formality academic or UN white-paper tone to informal or peer-to-peer contexts (Slack messages, cold emails, customer support tickets, changelogs).
* **The Remediation**: Calibrate language to the actual social distance between writer and reader (see `references/formats-and-genres.md`).

---

## 3. The Fallacy of Mechanical Word Blacklists

### Why Word Blacklists Fail
Many naive "AI humanizers" implement mechanical token blacklists that ban words frequently generated by LLMs (e.g., *delve*, *pivotal*, *robust*, *seamless*, *tapestry*, *landscape*, *leverage*).

This approach fails for three fundamental reasons:

1. **Context Blindness**: Legitimate professional discourse occasionally requires these words. A structural engineer writing about concrete legitimately uses "robust." An archaeologist discussing excavations legitimately uses "delve." Banning words unconditionally forces clumsy, unnatural substitutions.
2. **The Synonym Treadmill**: Banning *delve* causes the model to output *explore*; banning *pivotal* yields *crucial*; banning *robust* yields *sturdy*. The resulting prose retains the exact same rhythmic monotony, vagueness, and lack of evidence—merely dressed in second-tier synonyms.
3. **Detector Evasion Theater**: Chasing specific token lists treats the symptom rather than the disease, turning editorial craft into an adversarial game against statistical detectors while leaving reader comprehension impaired.

### The Structural Diagnostic Rubric
Instead of asking *"Does this text contain banned words?"*, ask:

| Structural Question | If "Yes" (Defect) | Editorial Correction |
| :--- | :--- | :--- |
| **Is the actor identifiable and accountable?** | Vague actors ("it was decided", "studies show") | Name the specific person, team, or entity responsible. |
| **Is the mechanism concrete?** | Abstract verbs ("leverage", "optimize", "foster") | Describe the physical or operational step taken. |
| **Is the significance earned through evidence?** | Empty superlatives ("revolutionary", "profound") | Provide numbers, benchmarks, dates, or direct quotes. |
| **Does the sentence length vary?** | Monotone 18-word sentences | Combine short clauses; split run-on thoughts; inject cadence. |
| **Does the conclusion add new insight?** | Redundant "In summary" platitude | Delete the summary; end on the last actionable detail. |

---

## 4. Universal Heuristic Checklist

Before clearing copy for publication:
- [ ] No unearned throat-clearing openings (*In today's world...*).
- [ ] No false ranges (*ranging from X to Y and everything in between*).
- [ ] No negative parallelisms (*It's not just X; it's Y*).
- [ ] No significance inflation (*stands as a testament to...*).
- [ ] Sentences vary in length from 4 words to 30+ words (burstiness).
- [ ] No redundant tricolon adjective stacks (*fast, reliable, and scalable*).
- [ ] Ending stops on the last concrete fact without moralizing platitudes.
