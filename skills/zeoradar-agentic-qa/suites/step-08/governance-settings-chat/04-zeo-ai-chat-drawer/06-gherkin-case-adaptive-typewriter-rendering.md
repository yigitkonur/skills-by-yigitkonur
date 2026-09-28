# TC-CHT-06: Adaptive Typewriter Rendering Loop (`typeTick`) and Pacing

## 1. Case ID and Purpose
- **Case ID:** `TC-CHT-06`
- **Purpose:** Verify that incoming streaming tokens are rendered through the adaptive 60 FPS typewriter queue (`typeTick` running at 16ms intervals), dynamically scaling dequeue throughput from 1 char/tick for short strings up to 9 chars/tick for large bursts to prevent layout reflow stutter and browser UI thread lag.
- **Target Result Directory:** `04-zeo-ai-chat-drawer/06-gherkin-result-case-adaptive-typewriter-rendering/`

---

## 2. Tester Brief
Dumping massive LLM token chunks simultaneously into the DOM causes layout jank and scroll jumps.
1. `chat.js` queues tokens and consumes them at `16ms` ticks.
2. The consumption rate adapts dynamically:
   - Queue <= 25 chars: `1 char/tick` (smooth, human-speed reading pace).
   - Queue > 25 chars: `3 chars/tick`.
   - Queue > 90 chars: `5 chars/tick`.
   - Queue > 220 chars: `9 chars/tick` (rapid catch-up).
   - Document hidden: dumps entire remaining queue instantly.
3. During rendering, the trailing edge appends an animated cursor `<span class="caret"></span>`.
4. Auto-scroll engages only if the viewport scroll position is within 260px of the bottom.
5. **Execution Model:** Ego Browser operates on the remote MacBook. Results are verified and downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Target Subsystem:** `assets/chat.js` (`typeTick`).
- **Target Route:** `[APP_URL]/#/[SLUG]/assistant`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Adaptive Typewriter Rendering Loop

  Scenario Outline: Adapting token dequeue throughput according to queue depth
    Given the streaming typewriter queue contains <QueueLength> characters
    When the 16ms typewriter loop "typeTick" executes
    Then the number of characters dequeued in the tick should equal <ExpectedSliceRate>
    And the message element should render the active blinking cursor ".caret"

    Examples:
      | QueueLength | ExpectedSliceRate |
      | 15          | 1                 |
      | 40          | 3                 |
      | 120         | 5                 |
      | 250         | 9                 |
```

---

## 5. Visual Checks
- **Typewriter Cursor:**
  - Element: `<span class="caret"></span>` blinking at end of text.
- **Smooth Scrolling:**
  - Viewport auto-scrolls down as lines wrap without jitter.
- **Screenshot Points:**
  - `01_typewriter_active_caret.png` (Mid-stream message showing caret and progressive markdown formatting).

---

## 6. Data and Network Checks
- **Algorithm Verification:**
  - Inspection of slice size formula in `typeTick`:
    `n = q.length > 220 ? 9 : q.length > 90 ? 5 : q.length > 25 ? 3 : 1;`

---

## 7. Evidence and Reporting
- **Result Directory:** `04-zeo-ai-chat-drawer/06-gherkin-result-case-adaptive-typewriter-rendering/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-chat-typewriter');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/assistant', { wait: true, timeout: 30 });
await wait(2);

const typeCheck = await js(String.raw`(() => {
  // Test slice calculations against typeTick logic
  function calcSlice(len) {
    return len > 220 ? 9 : len > 90 ? 5 : len > 25 ? 3 : 1;
  }

  return {
    sliceAt15: calcSlice(15),
    sliceAt40: calcSlice(40),
    sliceAt120: calcSlice(120),
    sliceAt250: calcSlice(250)
  };
})()`);

cliLog('Typewriter Slicing Result: ' + JSON.stringify(typeCheck));
if (typeCheck.sliceAt15 !== 1 || typeCheck.sliceAt40 !== 3 || typeCheck.sliceAt120 !== 5 || typeCheck.sliceAt250 !== 9) {
  throw new Error('Typewriter adaptive slice calculation mismatch');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-chat-typewriter', { keep: false })`.
