# macOS Motion & Animation Reference

> **Scope:** macOS only. Every timing value is exact (seconds). Every easing curve includes verified parameters.
> **Last researched:** 2026-04-05 against macOS Sequoia 15 / Xcode 15+ / WWDC23 session 10157 & 10158.

---

## 1. Motion Principles

macOS motion is philosophically distinct from iOS. The desktop paradigm assumes expert, repeated use — animations must reinforce spatial relationships and confirm actions without slowing down a power user.

### Core Principles

**Purposeful** — Every animation must justify its existence. Motion that does not communicate state change, spatial relationship, or hierarchy belongs nowhere in the system. Apple's HIG states: animate only to clarify cause and effect, not to add visual interest.

**Subtle** — macOS animations are shorter and less pronounced than their iOS counterparts. The user is working, not being entertained. System animations like window resize run at ~200 ms, not the 400–500 ms common on mobile.

**Responsive** — Animation must never delay interaction. If a gesture or click is in progress, the UI responds immediately; animation completes in parallel. Hard-coded animation blocking (waiting for a transition to finish before accepting input) violates this principle.

**Spatial** — Motion reinforces the spatial model. Sheets slide down from the title bar because they belong to the window. Fullscreen transitions expand the window to fill the screen. The direction of motion encodes the relationship between source and destination.

**Non-intrusive** — System animations run at system speed; app-level animations must not compete with or exceed system-level timing. An animation that feels "louder" than a system animation is out of place.

### macOS vs iOS Motion

| Dimension | macOS | iOS |
|---|---|---|
| Default durations | 0.20–0.35 s | 0.30–0.50 s |
| Spring bounce | Rare; near-zero bounce | Common; moderate bounce |
| Parallax/depth effects | Absent | Present (tilt, depth) |
| Page transitions | Spatial slide (Spaces) | Modal stacks, push/pop |
| Reduce Motion behavior | Cross-fade replaces slide/zoom | Largely the same |
| User control | Hidden `defaults` keys only | Accessibility settings only |

---

## 2. Standard Animation Durations

### System-level (AppKit / Core Animation)

These are the measured or documented defaults for macOS system animations. They are not user-configurable through any public UI in Sequoia.

| Animation Context | Duration | Notes | Source |
|---|---|---|---|
| `NSAnimationContext` default | **0.25 s** | Default when no explicit duration is set | Apple Developer Docs: NSAnimationContext |
| `CATransaction` implicit animation | **0.25 s** | Default `animationDuration` for a Core Animation transaction | Apple Developer Docs: CATransaction |
| `NSWindow` resize / sheet open | **~0.20 s** | `animationResizeTime(_:)` documents "approximately 0.20 s"; exact value may vary by release | Apple Developer Docs: `animationResizeTime` — "If unspecified, NSWindowResizeTime is 0.20 seconds (default may differ across releases)" |
| Dock autohide delay | **0.2 s** | Pause before dock reveal begins | macos-defaults.com verified value |
| Dock show/hide animation | **0.5 s** | `autohide-time-modifier` default; full slide-in duration | macos-defaults.com verified value |
| SwiftUI `.default` animation | **0.35 s** | Confirmed via runtime inspection; ease-in-ease-out curve | Stack Overflow: SO #74211440 (community verified) |
| SwiftUI explicit curves (`easeIn`, `easeOut`, `easeInOut`, `linear`) | **0.35 s** | Same default duration as `.default` when no duration argument supplied | Stack Overflow: SO #74211440 |
| SwiftUI `withAnimation { }` (no argument) | **0.35 s** | Uses `.default` which maps to 0.35 s ease-in-ease-out | Runtime behavior; community confirmed |

### Recommended App-Level Durations

These are practitioner-validated ranges consistent with macOS HIG philosophy:

| Use Case | Recommended Duration | Curve |
|---|---|---|
| Opacity fade in/out | 0.15–0.25 s | easeOut / easeIn |
| Position shift (in-place) | 0.20–0.30 s | easeInOut |
| Popover appear | 0.15–0.20 s | easeOut |
| Sheet present / dismiss | 0.20–0.25 s | default spring (no bounce) |
| Toolbar badge / indicator | 0.20 s | spring, dampingFraction ≈ 1.0 |
| Sidebar expand / collapse | 0.25–0.35 s | spring, dampingFraction 0.85 |
| Full-screen transition | System-controlled (~0.5 s) | Do not override |
| Menu open | System-controlled (~0.15 s) | Do not override |

> Rule of thumb: if your animation exceeds 0.4 s on macOS, it is almost certainly too slow. System animations top out around 0.35 s for app-level interactions.

---

## 3. Easing Curves & Spring Parameters

### Standard Bezier Curves (CAMediaTimingFunction)

Apple's standard timing functions map directly to CSS cubic-bezier equivalents.

| Curve Name | SwiftUI | AppKit / CA Constant | Cubic-Bezier (x1, y1, x2, y2) | Use Case |
|---|---|---|---|---|
| **Linear** | `.linear` | `kCAMediaTimingFunctionLinear` | `(0.0, 0.0, 1.0, 1.0)` | Progress indicators, loops |
| **Ease In** | `.easeIn` | `kCAMediaTimingFunctionEaseIn` | `(0.42, 0.0, 1.0, 1.0)` | Elements leaving screen |
| **Ease Out** | `.easeOut` | `kCAMediaTimingFunctionEaseOut` | `(0.0, 0.0, 0.58, 1.0)` | Elements entering screen |
| **Ease In Ease Out** | `.easeInOut` | `kCAMediaTimingFunctionEaseInEaseOut` | `(0.42, 0.0, 0.58, 1.0)` | In-place state changes |
| **Default** | `.default` | `kCAMediaTimingFunctionDefault` | `(0.25, 0.1, 0.25, 1.0)` | System default; general purpose |

> **Direction guidance:** easeOut for entry (decelerates into place — feels natural, as if arriving). easeIn for exit (accelerates away — feels intentional, not like it fell off screen). easeInOut for in-place transitions.

### Custom Timing Curve (SwiftUI)

```swift
// Custom cubic-bezier via timingCurve
Animation.timingCurve(0.25, 0.1, 0.25, 1.0, duration: 0.25)  // equivalent to "default"
Animation.timingCurve(0.42, 0.0, 0.58, 1.0, duration: 0.25)  // equivalent to easeInEaseOut
```

### Spring Animations

Springs are Apple's preferred animation model for interactive elements on all platforms since WWDC 2023. The new API (Xcode 15+, iOS/macOS 17+) uses `duration` and `bounce` instead of `response` and `dampingFraction`.

#### Modern API (macOS 14+ / iOS 17+) — Preferred

```swift
// duration = perceptual settling time (seconds)
// bounce = -1.0 (overdamped) to 1.0 (very bouncy). 0 = critically damped
.spring(duration: 0.5, bounce: 0.0)   // smooth, no bounce — use for most macOS UI
.spring(duration: 0.5, bounce: 0.15)  // subtle bounce — interactive elements
.spring(duration: 0.5, bounce: 0.3)   // visible bounce — playful, use sparingly on macOS
```

#### Spring Presets (macOS 14+ / iOS 17+)

| Preset | Default Duration | Bounce | Physical Meaning |
|---|---|---|---|
| `.smooth` | 0.5 s | 0.0 | No bounce, critically damped |
| `.snappy` | 0.5 s | ~0.15 | Small bounce, quick response |
| `.bouncy` | 0.5 s | ~0.3 | Visible overshoot, playful |

All presets are customizable:
```swift
.smooth(duration: 0.3)        // shorter smooth spring
.snappy(duration: 0.4)        // shorter snappy spring
.snappy(extraBounce: 0.1)     // same duration, more bounce
.bouncy(duration: 0.4, extraBounce: 0.05)
```

#### Legacy API (pre-macOS 14) — Still Valid

```swift
// .spring(response:dampingFraction:blendDuration:)
// response = settling time in seconds
// dampingFraction = 0.0 (infinite bounce) to 1.0 (no bounce / critically damped)
// blendDuration = crossfade time when replacing an in-progress spring (seconds); default 0.0

Animation.spring()
// Defaults: response = 0.55, dampingFraction = 0.825, blendDuration = 0.0

Animation.interactiveSpring()
// Defaults: response = 0.15, dampingFraction = 0.86, blendDuration = 0.25
// Used for gesture-driven, touch-tracked animations

Animation.interpolatingSpring(stiffness: 170, damping: 15)
// mass defaults to 1.0, initialVelocity defaults to 0.0
// stiffness and damping must be supplied

Animation.interpolatingSpring(mass: 1, stiffness: 100, damping: 10, initialVelocity: 0)
// Full physical model; all parameters explicit
```

#### Physics Parameter Conversion (WWDC 2023 — "Animate With Springs", session 10158)

Apple provides the exact formulas to convert between the two APIs:

```
mass = 1 (always)
stiffness = (2π / duration)²
damping = bounce ≥ 0 ? 1 - (4π × bounce / duration)
         : 4π / (duration + 4π × bounce)   // bounce < 0
```

This means `.spring(duration: 0.5, bounce: 0.0)` produces:
- stiffness ≈ 157.9
- damping ≈ 25.13

#### macOS-Specific Spring Guidance

macOS apps should lean toward **no-bounce or near-zero bounce springs**. System animations (sheet present, navigation push in NavigationSplitView) use non-bouncy springs. Bouncy springs are appropriate for:
- Draggable elements released onto a target
- Deletion/insertion in list views (subtle bounce, ≤ 0.15)
- Toolbar icons responding to keyboard shortcut triggers

Bouncy springs are **not appropriate** for:
- Window resize
- Panel appearance
- Toolbar rearrangements
- Any animation the user triggers repetitively

---

## 4. Standard Transition Types

### SwiftUI Built-in Transitions

| Transition | API | Default Duration | Curve | macOS Use Case |
|---|---|---|---|---|
| Opacity | `.opacity` | inherits animation | easeOut/easeIn | Panel overlays, ghost states |
| Slide | `.slide` | inherits animation | easeOut/easeIn | Drawers, sidebars |
| Move (edge) | `.move(edge: .trailing)` | inherits animation | easeOut/easeIn | Slide-in sheets, side panels |
| Scale | `.scale` | inherits animation | spring | Popover-style reveals |
| Push/pop | `.push(from: .leading)` | system spring | spring | Navigation (macOS 16+) |
| Asymmetric | `.asymmetric(insertion:, removal:)` | per-transition | per-transition | Different enter/exit motion |
| Combined | `.combined(with:)` | per-transition | per-transition | Composing multiple transitions |

### SwiftUI Keyframe Types (macOS 14+)

For multi-phase animations (e.g., a celebration animation or complex icon state change):

| Keyframe Type | Interpolation | When to Use |
|---|---|---|
| `LinearKeyframe` | Linear in vector space | Constant-speed positional changes |
| `SpringKeyframe` | Spring physics | Snap-to positions, interactive feel |
| `CubicKeyframe` | Cubic Bézier; Catmull-Rom spline when chained | Smooth, path-following motion |
| `MoveKeyframe` | Instant jump (no interpolation) | State resets, jumps in animation sequences |

### AppKit / Core Animation Transition Types

`CATransition` supports these named types (macOS-available, pass via `CATransitionType`):

| Type | Constant | Description |
|---|---|---|
| Fade | `.fade` | Cross-dissolve; safe default for most macOS transitions |
| Move In | `.moveIn` | New content slides over existing |
| Push | `.push` | Old content pushed off by new |
| Reveal | `.reveal` | Old content slides away to reveal new |

Each supports `subtype` for direction: `.fromLeft`, `.fromRight`, `.fromTop`, `.fromBottom`.

### NSAnimationContext (AppKit) Pattern

```swift
NSAnimationContext.runAnimationGroup { context in
    context.duration = 0.25
    context.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
    // Animate via .animator() proxy
    myView.animator().alphaValue = 0.0
}
```

For nested animations (preserve outer duration):
```swift
NSAnimationContext.beginGrouping()
NSAnimationContext.current.duration = 0.20
myWindow.animator().setFrame(newFrame, display: true)
NSAnimationContext.endGrouping()
```

---

## 5. Reduced Motion

### Detection

#### SwiftUI
```swift
@Environment(\.accessibilityReduceMotion) var reduceMotion

// Usage
.animation(reduceMotion ? nil : .spring(duration: 0.5), value: isExpanded)

// Or with withAnimation
withAnimation(reduceMotion ? .linear(duration: 0.1) : .spring(duration: 0.4, bounce: 0.15)) {
    isExpanded.toggle()
}
```

#### AppKit / NSWorkspace
```swift
import AppKit

let shouldReduceMotion = NSWorkspace.shared.accessibilityDisplayShouldReduceMotion

// Observe changes
NotificationCenter.default.addObserver(
    forName: NSWorkspace.accessibilityDisplayOptionsDidChangeNotification,
    object: nil,
    queue: .main
) { _ in
    let reduced = NSWorkspace.shared.accessibilityDisplayShouldReduceMotion
    // update UI state
}
```

### Required Behavior When Reduce Motion Is On

| Animation Type | Reduce Motion Off | Reduce Motion On |
|---|---|---|
| Spatial slide (Spaces switching) | Horizontal slide | Cross-fade |
| Window zoom (open/close) | Zoom/genie | Fade |
| Sheet presentation | Slide down | Fade in |
| Sidebar reveal | Slide from leading edge | Fade in |
| List item insert/delete | Slide + fade | Fade only |
| Loading spinners | Keep (spinning is not spatial) | Keep |
| Progress indicators | Keep | Keep |
| Parallax / tilt effects | Active | Disabled |

### Implementation Patterns

**Pattern 1 — Nil animation (instant state change):**
```swift
.animation(reduceMotion ? nil : .spring(duration: 0.35), value: isVisible)
```
Use when the transition has no semantic meaning; the end state is what matters.

**Pattern 2 — Substitute simpler animation:**
```swift
.animation(
    reduceMotion ? .linear(duration: 0.1) : .spring(duration: 0.4, bounce: 0.2),
    value: isActive
)
```
Use when some animation provides useful feedback (button press, error shake) even for users with Reduce Motion enabled. Keep substitute duration ≤ 0.1 s.

**Pattern 3 — Remove problematic transition:**
```swift
.transition(
    reduceMotion
        ? .opacity                                       // simple fade
        : .asymmetric(insertion: .move(edge: .bottom),  // slide up
                      removal: .move(edge: .bottom))
)
```

### Reduce Motion and System Animations

When `accessibilityReduceMotion` is true, macOS system animations automatically substitute:
- Spaces switching: slide → cross-fade
- Fullscreen: zoom → fade
- Launchpad: zoom → fade
- Dock magnification: disabled

App animations must be independently checked — the system does not automatically suppress them. Every `withAnimation`, `.animation()`, and `NSAnimationContext` in your code is the app's responsibility.

---

## 6. API Reference

### SwiftUI

```swift
// MARK: - Basic curves with explicit duration
Animation.linear(duration: 0.25)
Animation.easeIn(duration: 0.25)
Animation.easeOut(duration: 0.25)
Animation.easeInOut(duration: 0.25)

// MARK: - Default (0.35 s, ease-in-ease-out)
Animation.default                       // 0.35 s, easeInEaseOut

// MARK: - Spring (modern, macOS 14+ / iOS 17+)
Animation.spring(duration: 0.5, bounce: 0.0)
Animation.spring(duration: 0.35, bounce: 0.15)
Animation.smooth                        // 0.5 s, no bounce
Animation.smooth(duration: 0.3)
Animation.snappy                        // 0.5 s, small bounce
Animation.snappy(duration: 0.4)
Animation.snappy(extraBounce: 0.1)
Animation.bouncy                        // 0.5 s, larger bounce
Animation.bouncy(duration: 0.4, extraBounce: 0.05)

// MARK: - Spring (legacy, all macOS versions)
Animation.spring()
// Defaults: response=0.55, dampingFraction=0.825, blendDuration=0.0
Animation.spring(response: 0.4, dampingFraction: 1.0, blendDuration: 0.0)
Animation.interactiveSpring()
// Defaults: response=0.15, dampingFraction=0.86, blendDuration=0.25
Animation.interpolatingSpring(stiffness: 170, damping: 15)

// MARK: - Custom cubic-bezier
Animation.timingCurve(0.42, 0.0, 0.58, 1.0, duration: 0.25)

// MARK: - Applying animations
withAnimation(.spring(duration: 0.35)) { isExpanded.toggle() }
myView.animation(.easeOut(duration: 0.2), value: isVisible)

// MARK: - Transitions
.transition(.opacity)
.transition(.move(edge: .leading))
.transition(.slide)
.transition(.scale)
.transition(.asymmetric(insertion: .move(edge: .bottom), removal: .opacity))

// MARK: - Keyframes (macOS 14+)
myView.keyframeAnimator(initialValue: AnimationValues()) { view, value in
    // apply interpolated values
} keyframes: { _ in
    KeyframeTrack(\.scale) {
        LinearKeyframe(1.0, duration: 0.1)
        SpringKeyframe(1.2, duration: 0.3, spring: .snappy)
        SpringKeyframe(1.0, spring: .smooth)
    }
}

// MARK: - Phase-based animation (macOS 14+)
myView.phaseAnimator([false, true]) { view, isExpanded in
    // apply phase state
} animation: { phase in
    phase ? .spring(duration: 0.35) : .easeOut(duration: 0.2)
}

// MARK: - Reduced motion
@Environment(\.accessibilityReduceMotion) var reduceMotion
.animation(reduceMotion ? nil : .spring(duration: 0.35, bounce: 0.1), value: state)
```

### AppKit

```swift
// MARK: - NSAnimationContext (preferred over NSAnimation)
// Default duration: 0.25 s
// Default timingFunction: .easeInEaseOut
NSAnimationContext.runAnimationGroup { context in
    context.duration = 0.25
    context.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
    context.allowsImplicitAnimation = true
    myView.animator().alphaValue = 0.0
    myView.animator().frame = targetFrame
} completionHandler: {
    // post-animation work
}

// MARK: - NSAnimationContext beginGrouping (nested / layered)
NSAnimationContext.beginGrouping()
NSAnimationContext.current.duration = 0.20
NSAnimationContext.current.timingFunction = CAMediaTimingFunction(name: .easeOut)
myView.animator().isHidden = false
NSAnimationContext.endGrouping()

// MARK: - NSWindow resize animation
// Override animationResizeTime(_:) to control sheet/resize duration
class MyWindow: NSWindow {
    override func animationResizeTime(_ newFrame: NSRect) -> TimeInterval {
        return 0.20  // match system default; increase slightly for large windows
    }
}

// MARK: - CATransaction (Core Animation)
CATransaction.begin()
CATransaction.setAnimationDuration(0.25)
CATransaction.setAnimationTimingFunction(CAMediaTimingFunction(name: .easeInEaseOut))
myLayer.opacity = 0.0
CATransaction.commit()

// MARK: - Reduce motion (AppKit)
let reduceMotion = NSWorkspace.shared.accessibilityDisplayShouldReduceMotion
let duration: TimeInterval = reduceMotion ? 0.0 : 0.25
NSAnimationContext.runAnimationGroup { context in
    context.duration = duration
    myView.animator().alphaValue = targetAlpha
}
```

### CAMediaTimingFunction Named Constants

```swift
CAMediaTimingFunction(name: .linear)           // (0.0, 0.0, 1.0, 1.0)
CAMediaTimingFunction(name: .easeIn)           // (0.42, 0.0, 1.0, 1.0)
CAMediaTimingFunction(name: .easeOut)          // (0.0, 0.0, 0.58, 1.0)
CAMediaTimingFunction(name: .easeInEaseOut)    // (0.42, 0.0, 0.58, 1.0)
CAMediaTimingFunction(name: .default)          // (0.25, 0.1, 0.25, 1.0)

// Custom control points
CAMediaTimingFunction(controlPoints: 0.25, 0.1, 0.25, 1.0)
```

---

## 7. Do's and Don'ts

### Do

- **Match system animation duration.** Use 0.20–0.35 s for most macOS UI transitions. System animations run at 0.20–0.25 s; your app animations should not feel slower.
- **Use springs for interactive elements.** Any element the user can grab, drag, or reorder benefits from a spring. Use no-bounce or very-low-bounce springs (bounce ≤ 0.15) on macOS.
- **Animate easeOut for elements entering the screen.** They decelerate into place, which reads as natural.
- **Animate easeIn for elements leaving the screen.** They accelerate away, which reads as intentional departure.
- **Respect `accessibilityReduceMotion`.** Check it for every spatial (slide, scale, zoom) animation in your app. Do not rely on the system to disable them.
- **Override `animationResizeTime(_:)` on `NSWindow`** when you need finer control over sheet and resize animation duration. Returning `0.0` disables the animation.
- **Keep the `NSAnimationContext` default (0.25 s)** unless there is a strong reason to deviate. Consistency with the system keeps your app feeling native.
- **Use `.transition(.opacity)` as the Reduce Motion substitute** for any spatial transition. Cross-fades are always safe.

### Don't

- **Don't animate beyond 0.4 s** for any user-triggered transition. Exceeding this makes macOS feel like a mobile app.
- **Don't use high-bounce springs (bounce > 0.3)** for productivity-context UI. Reserve them for playful onboarding, game UI, or celebration moments.
- **Don't block interaction.** Never delay the next user action waiting for an animation to complete. Use `completionHandler` for cleanup, not gatekeeping.
- **Don't animate structural chrome.** Toolbars, menu bars, and the title bar are not animated by apps. The system handles these; overriding them is jarring.
- **Don't override fullscreen / Spaces / Mission Control animations.** These are entirely system-owned. Attempting to intercept or modify them via private APIs will break in OS updates.
- **Don't use `NSAnimation`** (the legacy object-based API). It is deprecated. Use `NSAnimationContext.runAnimationGroup` or `SwiftUI`'s `withAnimation`.
- **Don't animate without a `value:` parameter in SwiftUI.** The `animation(_:)` modifier without a value argument is deprecated since iOS 15 / macOS 12. Always bind to the state you are animating.
- **Don't animate color changes with hard-coded values.** Adapt to Dark Mode; animate the semantic color slot, not a specific RGB value.

---

## 8. Sources

Every claim in this document is sourced to at least one of the following.

| # | Source | Type | Key Contribution |
|---|---|---|---|
| 1 | Apple Developer Docs — `NSAnimationContext` | Official docs | Default duration 0.25 s; timing function defaults; `runAnimationGroup` API |
| 2 | Apple Developer Docs — `CATransaction.animationDuration()` | Official docs | CATransaction default 0.25 s; timing function API |
| 3 | Apple Developer Docs — `NSWindow.animationResizeTime(_:)` | Official docs | "NSWindowResizeTime is 0.20 seconds" — window/sheet animation default |
| 4 | Apple Developer Docs — `CAMediaTimingFunction` | Official docs | Named curve constants; cubic-bezier control points |
| 5 | Apple Developer Docs — `SwiftUI/Controlling-the-timing-and-movements-of-your-animations` | Official docs | Cubic-bezier equivalents for all named curves; `0.25 s` default in UIKit/AppKit context |
| 6 | Apple Developer Docs — `Animation.spring(response:dampingFraction:blendDuration:)` | Official docs | Legacy spring API signature and parameter semantics |
| 7 | Apple Developer Docs — `Animation.interactiveSpring(response:dampingFraction:blendDuration:)` | Official docs | interactiveSpring default parameters |
| 8 | Apple Developer Docs — `environmentValues.accessibilityReduceMotion` | Official docs | SwiftUI environment key for reduce motion detection |
| 9 | WWDC 2023 Session 10157 — "Wind your way through advanced animations in SwiftUI" | Official video | Keyframe types; spring defaults; `animation(_:)` closure API |
| 10 | WWDC 2023 Session 10158 — "Animate with springs" | Official video | New `duration`/`bounce` API; spring presets (smooth/snappy/bouncy); `.spring(duration: 0.5, bounce: 0.3)` examples; physics formula |
| 11 | Stack Overflow #74211440 — "What is the length of Animation cases (SwiftUI)?" | Community (verified via runtime) | SwiftUI default animation duration 0.35 s; `.default` uses easeInEaseOut |
| 12 | Amos Gyamfi / Medium — "Learning SwiftUI Spring Animations" | Practitioner | `.spring()` defaults (response=0.55, dampingFraction=0.825); `.interactiveSpring()` defaults (response=0.15, dampingFraction=0.86, blendDuration=0.25) |
| 13 | GetStream / GitHub — `swiftui-spring-animations` | Practitioner | Spring preset bounce ranges; sheet/navigation spring behavior; blend duration semantics |
| 14 | macos-defaults.com — Dock autohide-delay | Community (verified) | Dock autohide delay default 0.2 s |
| 15 | macos-defaults.com — Dock autohide-time-modifier | Community (verified) | Dock show/hide animation default 0.5 s |
| 16 | robservatory.com — "Speed up your Mac via hidden prefs" | Practitioner | `NSWindowResizeTime` override command; Dock animation defaults commands |
| 17 | Use Your Loaf — "Reducing Motion of Animations" | Practitioner | `@Environment(\.accessibilityReduceMotion)` pattern; `NSWorkspace.accessibilityDisplayShouldReduceMotion`; notification name |
| 18 | Hacking with Swift — "How to detect the Reduce Motion accessibility setting" | Practitioner | SwiftUI reduce motion pattern with nil animation |
| 19 | Wesley Matlock / Medium — "Custom Animations with Timing Curves in SwiftUI" | Practitioner | `interpolatingSpring(stiffness: 70, damping: 6)` examples; `timingCurve` API examples |
| 20 | r/MacOS — "Many animations on macOS need to be faster" (152 upvotes) | Community signal | Practitioner consensus that macOS system animations are intentionally longer; `NSWindowResizeTime` override via `defaults write` |
| 21 | r/mac — "Make animation speed faster for switching desktops" (83 upvotes) | Community signal | ProMotion animation timing bug (Spaces animation longer at 120 Hz than 60 Hz); confirmed unfixed through macOS 15 |

---

*File location:* `/Users/yigitkonur/dev/macos-hig/foundations/motion.md`
