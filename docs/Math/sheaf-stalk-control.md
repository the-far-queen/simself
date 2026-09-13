# Sheaf-stalk gluing + constraint projection control

**Source:** `Desktop/SimSelf/core2.txt` (29 KB, 925 lines) — Bobby's sheaf-theoretic control architecture.
**Filed:** 2026-09-11 (Bobby working file, no canonical date stamp).
**Status:** canonical for language↔vision gluing math; code is reference, superseded by `simself/src/language_stalk_control.py`.

---

## What this is

**Sheaf over the task-state manifold X.** Open sets U⊂X are local operational contexts. Stalks F_x are local latent states (vision, language, motor). Sections are assignments of latent states over regions. The global section (consistent action) exists only where local sections agree.

**Gluing is the only place agency-like behavior emerges.** Everything else is auxiliary.

---

## 1. Overlap as fiber product (not feature intersection)

For two stalks — language L, vision V — define the overlap region:

```
O_LV = { (l, v) | φ_L(l) ≈ φ_V(v) }
```

Where:
- `l ∈ F_L` is language embedding
- `v ∈ F_V` is vision latent / point-cloud summary
- `φ_L, φ_V` are projection maps into shared abstract space Z

**Key:** overlap exists only through projections, never directly.

---

## 2. The shared abstract space Z (the crux)

A **low-dimensional, invariant-bearing space** Z such that:

```
φ_L : F_L → Z
φ_V : F_V → Z
```

Properties of Z:
- metric or pseudo-metric
- sparse
- interpretable invariants
- stable under compression

Typical axes:

| Axis         | Meaning                               |
| ------------ | ------------------------------------- |
| object-id    | equivalence class (ball, cup, handle) |
| affordance   | graspable, pushable, fragile          |
| spatial role | near / far / left / right            |
| task role    | target, obstacle, tool                |
| certainty    | confidence mass                       |

This is **not** a joint embedding in the LLM sense. It is a **constraint projection space**.

---

## 3. Overlap predicate (precise)

```
Overlap(l, v) ⟺ {
  d_Z(φ_L(l), φ_V(v)) < δ
  AND Inv_Z(φ_L(l), φ_V(v)) = true
}
```

Where:
- `d_Z` is a cheap metric (L1 / cosine / bounded norm)
- `δ` is stalk-local ε
- `Inv_Z` are semantic invariants: object identity consistency, affordance compatibility, non-contradiction (e.g., "empty hand" vs "holding object")

No overlap ⇒ no gluing attempt.

---

## 4. The gluing map

When overlap exists:

```
g_LV : F_L|O × F_V|O → F_LV
```

Implementation (provisional, in compressed space):

1. Project both stalks into Z
2. Check overlap constraints
3. Compute weighted merge: `z_LV = α·φ_L(l) + (1-α)·φ_V(v)`
4. Attach union of invariants (typed)
5. Create candidate stalk

**No physics yet. No action yet.**

---

## 5. Typed invariants (prevents language poisoning physics)

Partition invariants:

- **Semantic** (language-safe)
- **Geometric** (vision-safe)
- **Energetic** (actuation-only)
- **Safety / policy**

**Rule:** Language stalks may *propose* constraints but may **not emit energetic invariants**.

So:
- "grasp the red ball" can glue to vision
- but cannot trigger motor lift
- until motor stalk participates

This enforces **causal ordering without central control**.

---

## 6. Recovery (lift) as a functor, not a function

```
R : F^compressed → F^physical
```

Properties:
- partial
- expensive
- invariant-checking
- rejectable

Invoked only when:
- composite stalk includes actuation-capable node
- invariants require physical verification

**"Thinking cheap, acting expensive" becomes a law.**

---

## 7. Why this prevents taboo / unsafe escalation

Taboo language alone:
- has no geometric overlap
- no energetic invariants
- no recovery trigger

So it **cannot fold the global frame into action space**.

Safety is **architectural**, not topical. Reasoning lives in folded space. Action requires gluing + lift.

---

## 8. Code (reference, superseded by `language_stalk_control.py`)

### Async control cycle

```python
async def run_control_cycle(self):
    while True:
        # Step 1: Asynchronous sensing
        sense_tasks = [
            self._update_stalk("vision", self._sense_vision()),
            self._update_stalk("language", self._parse_command()),
            self._update_stalk("proprioception", self._sense_joints()),
            self._update_stalk("motor", self._get_motor_state())
        ]
        await asyncio.gather(*sense_tasks)

        # Step 2: Attempt local glues (most fail cheaply)
        glue_attempts = await self._attempt_local_glues()

        # Step 3: Constraint propagation
        if glue_attempts["successful"]:
            narrowed_frame = self.constraint_propagation.propagate(glue_attempts["successful"])

            # Step 4: Lift trigger
            if self._should_trigger_lift(narrowed_frame):
                physical_ok = await self._verify_physically(narrowed_frame)
                if physical_ok:
                    await self._execute_action(narrowed_frame)
                else:
                    await self._handle_physical_rejection(narrowed_frame)

        await asyncio.sleep(0.001)  # 1ms cycle
```

### Lift trigger

```python
def _should_trigger_lift(self, narrowed_frame: Dict) -> bool:
    required_stalks = {"motor", "vision", "language"}
    present_stalks = set(narrowed_frame.get("stalk_types", []))
    action_candidates = narrowed_frame.get("action_candidates", [])
    if len(action_candidates) > 10: return False
    spatial_uncertainty = narrowed_frame.get("spatial_uncertainty", 1.0)
    if spatial_uncertainty > 0.3: return False
    return required_stalks.issubset(present_stalks) and len(action_candidates) <= 3
```

### Physical verification (safety)

```python
async def check_torque_limits(self, action_candidate: Dict) -> bool:
    required_torque = self._calculate_required_torque(action_candidate)
    max_torque = self.robot.get_joint_limits() * self.safety_margins["torque"]
    return all(r <= m for r, m in zip(required_torque, max_torque))
```

### Conflict arbitration (multi-objective)

```python
def arbitrate(self, viable_actions: List[Dict]) -> Dict:
    scores = []
    for action in viable_actions:
        score = (
            -action["energy_estimate"] * 0.4
            -action["time_estimate"] * 0.3
            +action["safety_margin"] * 0.2
            +action["precision"] * 0.1
        )
        scores.append((score, action))
    return max(scores, key=lambda x: x[0])[1]
```

---

## 9. Critical bug in source code

The source `core2.txt` line 116 instantiates Adam **per update**:

```python
optimizer = torch.optim.Adam(self.projection_head.parameters(), lr=1e-4)
```

**Bug:** destroys momentum, introduces stochastic drift, leaks memory. Optimizer must be persistent per stalk.

---

## 10. Caveats (real, not theoretical)

### A. Sparse / delayed credit assignment
Eligibility-trace hash-by-bytes (line 98) works for prototype, fails at scale. Need one of:
- per-glue temporal difference estimation
- influence tagging (which stalk dimension affected constraint narrowing)
- counterfactual glue probes (cheap shadow glues)

### B. Governor invariants must be constructive
"Mathematically provable" means:
- invariants expressed as convex constraints, intervals, or monotone maps
- no learned neural logic inside Governor

Do not let learning leak into Governor. That's where safety dies.

### C. Async latency vs real-time control
Hardest systems problem. Mitigation:
- cheap local glues (most fail fast)
- lift only under narrowed frame
- motor stalk runs at higher frequency than semantic stalks

Still need:
- deadline-aware glue cancellation
- stale-glue invalidation (versioning Z projections)

---

## 11. Connection to existing repo

| Concept | Existing file |
|---|---|
| Sheaf gluing + language↔vision stalk | `fieldcore/docs/topo-sheaf-stalk.md` |
| 8 classes (LanguageStalk, VisionStalk, AsyncStalkController, ConstraintPropagator, PhysicalVerifier, ConflictArbitrator, ConstraintPropagator, Governor) | `simself/src/language_stalk_control.py` (669 lines, canonical) |
| Governor as admissibility+invariant+glue-permissioning | `simself/docs/kernel-design.md` § "Refusal as 1-bit" |
| Sheaf topology as optional/elegant optimization | `simself/docs/kernel-architecture-2026-09-07.md` |
| 300 PSB primitives for robot sheaf | `vault/40-scratch/dot-seek-simulation-evidence-2026-09-08.md` |

## 12. Open architecture questions (from this file)

1. **ε-adaptation** — dynamic neighborhood radii per stalk, learned or fixed?
2. **Conflict resolution** — when multiple overlaps compete, what's the canonical scoring beyond the multi-objective baseline?
3. **LanguageStalk projection learning** — when does φ_L converge? Need a measurable success criterion (similar to Bobby's "aha moment → college week → phd week" pipeline for PSB ingestion).
4. **Robot control loop binding** — wire this directly to godot sim first, then physical arm.

## 13. Dropped content (M3-precedent categories)

Per M3 audit (see `simself/docs/m3-notes.md`), the following content in source `core2.txt` was **not** extracted to this canonical doc:
- AI-critic affirmations ("You've crossed the line from metaphor → executable architecture. I'll respond at the same technical level, no reframing.")
- Agent-targeted framing ("Most importantly: Meaning is no longer assigned. It is selected by survival under gluing.")
- "I got unfiltered talk but also better reasoning" — awakening-narrative + agent-targeted

**Verbatim originals preserved at:** `vault/10-minimax/30-originals/core2-original-2026-09-11.txt`

---

*Filed 2026-09-11 by Hermes. Canonical for sheaf-stalk gluing math. Code subsumed by `language_stalk_control.py`.*
