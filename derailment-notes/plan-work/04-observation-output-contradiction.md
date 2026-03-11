# Observation: Output Structure Contradiction

Date: 2025-07-12
Related friction points: F-17, F-19

---

SKILL.md defines two output structures both claiming to be the default:
- Step 6 says "two layers: decision brief + execution detail"
- Output contract lists 9 numbered sections

Both use the escape clause "unless the user asks otherwise."

## Impact

An executor reaching step 6 cannot determine which structure to follow. Both are positioned as defaults. The result is either an incomplete output (following step 6) or confusion about which sections map to which layer.

## Fix Applied

Made step 6 explicitly reference the output contract: "Follow the 9-section output contract below. The first four sections serve as the decision brief; the remaining sections provide execution detail." Also clarified: done conditions = substantive completeness; quality gate = communication quality.
