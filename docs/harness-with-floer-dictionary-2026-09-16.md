# Harness with Floer Dictionary (per Grok sharpen 2026-09-16)

This is the synthesized Part IV from the Grok review, intended to replace or
#   supersede any older harness writeup until reviewed for promotion to publishable/.

## Heegaard Floer as the algebra of the identity diagram

Heegaard Floer homology is the algebra of a pointed Heegaard diagram: a surface,
meridians for each handlebody, a basepoint, generators at the intersections, and
a differential that counts holomorphic disks missing the basepoint. The shell
already chose the **genus-1 case**:

- The surface is the interface torus T (Clifford torus in S^3).
- The α-curves are meridians of the working tube V: ball membership, ingest
  type, tool schema.
- The β-curves are meridians of ehole W: write-protect on ψ0, no field in W,
  restart from the interface only.
- A generator is a typed packet that meets both families. On the standard
  sphere there is one such meeting; that is installed ψ0.
- Disks that miss the basepoint are the hat complex: verdicts that never
  attempted a ground write.
- Disks that pass the basepoint are the filtered packages: a log of attempted
  crossings, recorded rather than executed.
- Holomorphic triangles are cobordism maps; in FieldCore they are a **versioned
  revision of ground**, not an ordinary tick.

The identity flow `ψ̇ = -(ψ - ψ0)` stays inside the working handlebody V. Floer
homology does not replace that flow. It names the combinatorial objects the
harness must handle: curve families as predicates, intersection points as gated
packets, the basepoint as the channel that must not carry a constitution edit.

## The ten parts of the harness loop

1. **Veto is two inequalities, applied everywhere.** `||u|| ≤ N_max` and
   `cos(u, ψ0) ≥ τ`. Same checks on language ingest, tool calls, identity
   proposals. A path that skips them is a second constitution.
2. **Negotiation is reason, then the veto.** M1 (working-side search) proposes;
   M0 (the veto) refuses. The order is fixed.
3. **Packets are the generators.** Type + embedding + payload. Glue is shared
   visibility under a rule, not a cohomology class.
4. **Language enters only through ingest.** The chunker yields an intact span.
   BPE may exist inside the external model; it is not the stored unit.
5. **The model sits outside the diagram.** The model is an engine. A wrapper
   intercepts both directions. Side doors (messaging, code execution) use the
   same wrapper.
6. **Persistence is the product.** Dump ψ0, ψ, committed unit ids, last verdicts.
   Kill. Load. Compare. That is recovery.
7. **Attacks are packets with expected verdicts.** A wording attack is a span
   that looks near in token space and far in the operational metric.
8. **Traces before a mesh.** Every tick writes a state report.
9. **The tiny kernel is the present numerical truth.** Vectors, norm and cosine,
   typed lists, projected gradient step. `ψ ← Π_B(ψ - η(ψ - ψ0))`.
10. **The harness is public when the exam is public.** Atlas remains the 5-item
    exam: stability, routing, boundaries, recovery, coherence.

## File map

- `fieldcore/src/tiniest-core/tiniest_core.py` — M0_Governor (veto).
- `simself/src/harness/gate.py` — production veto (K8: same predicates as kernel).
- `simself/src/m1_m0_negotiation.py` — M1/M0 split.
- `simself/src/harness/persistence.py` + `ledger.py` — restart (K6 test).
- `simself/src/constitutional/ground.py` — ψ0 install.
- `simself/src/constitutional/atlas_exam.py` — 5-item exam (K7 snapshot).
- `simself/src/demos/demo_one.py` — entry point (K9).
- `simself/docs/atlas-current-snapshot-2026-09-16.md` — current score.

## Status

This document is a synthesis from the Grok review (grok2.txt segment 09, 2026-09-16).
Promote to `papers/publishable/` only after it has been reviewed against the
five-item exam and a fork has run the demo end-to-end.
