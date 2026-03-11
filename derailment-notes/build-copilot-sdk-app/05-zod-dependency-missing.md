# F-09 — Zod Dependency Missing (P1, S1)

## Observation

The custom tool example imports `import { z } from "zod"` but `zod` is not
in the install command. Running the example fails with `Cannot find module 'zod'`.

## Root cause

S1 — Missing prerequisite. The install command doesn't list all dependencies.

## Fix applied

Changed install command to: `npm install @github/copilot-sdk tsx zod`
