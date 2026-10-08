# Prompting Adaptive Evidence Research

Prompt each stage for the uncertainty it owns. Planning defines what must be established, search retrieves source candidates via multi-query consensus, and extraction tests explicit requirements against source text with verifiable citations.

---

## 1. Strategy & Advisory Planning (`plan-research`)

### A. Formulate Strategy Before Planning
Do not outsource your initial thinking to `plan-research`.
1. **Articulate Your Hypothesis:** State your understanding of the problem, the core trade-offs, and your planned exploration angles to the user first.
2. **Use Planning as a Sounding Board:** Call `plan-research` not to receive a rigid script, but to stress-test your strategy. Ask:
   - Did the planner identify a critical cluster or failure seam you overlooked?
   - Did it formulate a more rigorous stop condition or falsifiable metric?
   - Did it suggest exact academic or technical terminology?
3. **Adapt, Don't Copy-Paste:** Adopt the high-yield clusters and specific stop conditions; ignore generic or low-priority padding.

### B. Crafting a High-Yield `objective`
A strong objective provides sufficient constraints and negative boundaries to focus the search bank without dictating a bloated query list.

Include:
1. The core decision, claim, or diagnosis to resolve.
2. Specific user/workload constraints (scale, platform, runtime, team size).
3. Known facts and adjacent topics to **explicitly skip**.
4. Key uncertainties that could reverse the decision.
5. Freshness/version window (e.g., "past 18 months" or "version 4.x+").
6. Concrete stop conditions (what exact evidence or benchmark numbers settle the question).

**Weak Objective:**
```text
Compare package A and package B.
```

**Strong Objective:**
```text
Decide between package A and package B for a Linux production service running Node 22, processing 5k req/s with a small on-call team. Skip basic installation and shared standard features. Verify runtime compatibility, memory leakage under sustained concurrency, maintenance posture, and recent practitioner post-mortems. A complete answer must recommend one option, cite empirical benchmark evidence, surface contradictions, and state the exact conditions that would reverse the choice.
```

---

## 2. Multi-Query SERP Intelligence & Consensus Weighting (`web-search`)

### A. The SERP Ranking Reality (CTR & Position Weighting)
Search engine algorithms invest massive engineering to order the top 10 results. Click-through behavior demonstrates that rank #1 commands ~30% click-share, rank #2 ~15%, with steep decay thereafter.
- `web-search` leverages this reality: it accepts 1–50 complete queries, retrieves top results, and calculates a normalized consensus score based on position and frequency across clusters.
- When an authoritative source appears near the top across multiple distinct queries, its score approaches 100.00.

### B. The Anti-Pattern: Synonymous Query Waste
Submitting 20 paraphrases of the same question:
- `"ai text detection accuracy"`
- `"how accurate is ai text detection"`
- `"can ai detector tell if text is ai"`
- `"accuracy of ai detector tools"`

**Why this fails:** All 20 queries hit the exact same SEO-optimized landing pages and marketing blogs. You burn query quota without gaining new information dimensions.

### C. The Best Practice: Orthogonal Dimensional Nets
Formulate queries that attack the problem from completely orthogonal angles:

| Dimension | Probe Focus | Example Query String |
|---|---|---|
| **Theoretical Bounds** | Mathematical limits, formal theorems | `"Can AI-Generated Text be Reliably Detected?" Sadasivan bounds total variation` |
| **Empirical Bias & FPR** | Independent academic studies on edge cohorts | `Liang et al "GPT detectors are biased against non-native English writers" false positive rate` |
| **Adversarial Evasion** | Paraphrasing attacks, prompt engineering | `recursive paraphrasing attack AI text detectors openreview` |
| **Watermarking Schemes** | Cryptographic/statistical token watermarks | `Kirchenbauer "watermark for large language models" spoofing attack` |
| **Practitioner Reality** | Production complaints, institutional bans | `site:reddit.com/r/Professors "AI detector" Turnitin false positive policy` |

**The Consensus Signal:** When orthogonal queries across theory, benchmarks, and practitioner forums all converge on the same primary paper or documentation, you have identified ground truth.

---

## 3. Iterative Search Deepening (The Feedback Loop)

Research is not a one-pass waterfall. Treat search as an interactive discovery loop:

```text
[Search Wave 1: Reconnaissance]
             │
             ▼
[Inspect SERP Signals] ──► (Discovered new entity, unexpected RFC, or specific error code)
             │
             ▼
[Search Wave 2: Deep Dive Probes] ──► (Target the discovered terminology)
             │
             ▼
[Search Wave 3: Practitioner Verification] ──► (Probe for post-mortems & edge-case failures)
             │
             ▼
[Extract Evidence on Solidified Candidates]
```

### Reading the SERP Landscape
After executing a search wave, pause and inspect the leads:
- **Terminology Shift:** Did search leads reveal that the industry uses different terminology than your initial prompt? (e.g., discovering "total variation distance" or "perplexity/burstiness").
- **Key Entities & Standards:** Which authors, RFC numbers, GitHub repositories, or CVE IDs recur?
- **Emerging Contradictions:** Do vendor marketing snippets claim 99% accuracy while an academic title says "impossibility theorem"?
- **Deepen Before Extracting:** Launch targeted follow-up queries (even 5–10 iterative search rounds if needed) to track down the newly discovered entities before spending extraction budget.

---

## 4. Checkable Evidence Requirements (`extract-evidence`)

`extract-evidence` reads actual page bodies and enforces strict quotation-grounded extraction. Its input must consist of checkable, falsifiable requirements.

### Weak Requirements (Vague / Subjective)
- `"Tell me everything about the detector."`
- `"Is the tool good or bad?"`
- `"Summarize the paper's feelings."`

### Strong Requirements (Falsifiable & Bounded)
- `"What exact numerical false positive rate was reported for TOEFL essays written by non-native speakers?"`
- `"What mathematical relationship is proven between AUROC of the detector and the Total Variation distance?"`
- `"Under what specific workload or concurrency level does the memory leak occur?"`
- `"What workaround or configuration change is explicitly recommended in the issue resolution?"`

### The Value of Negative Evidence (`not-found`)
- Good requirements allow a source to honestly return `not-found`.
- If an official security advisory makes no mention of a workaround, or a product documentation page omits support for a feature, `not-found` is **valuable negative proof**, not a failure.
- Never force an extractor to invent an answer when the source does not contain it.

---

## 5. Strict Schema Reminders

- `web-search`: Only accepts `queries: string[]`. Never pass `country`, `freshness`, or `domain` as JSON keys; embed all filters directly into the query strings (e.g. `site:github.com`, `after:2024`).
- `extract-evidence`: Accepts `urls: string[]` (max 20) and `evidence_requirements: string[]` (max 20).
- If `extract-evidence` returns `continuation.required: true`, invoke `continuation.next_call` immediately in the same session without modifying arguments.
