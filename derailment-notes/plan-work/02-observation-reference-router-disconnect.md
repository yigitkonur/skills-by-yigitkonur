# Observation: Reference Router Is Disconnected From Workflow

Date: 2025-07-12
Related friction points: F-04, F-09, F-21, F-24, F-26

---

The reference router is positioned between Operating stance and Default workflow. It provides excellent need-to-file mapping. However no workflow step mentions it. The workflow creates reference-dependent situations (5W2H in step 2, method names in step 3, Type 1/2 in step 4) without triggering reference loading.

## Impact

An executor following the workflow literally will never consult the reference files, even though the workflow uses terminology defined only in those files. This creates a class of P0 derailments where the executor cannot determine the meaning of gate conditions.

## Fix Applied

Added bridge instruction in step 3: "Consult the reference router above to load the reference file matching your planning job." Inlined minimum viable definitions for 5W2H, Type 1/Type 2, and Decision Frame so the skill is self-contained without references.
