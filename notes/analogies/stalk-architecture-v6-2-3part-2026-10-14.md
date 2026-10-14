> **v6.2 supersedes the stalk geometry in `frequency-architecture-2026-09-12.md` (v6.1).** v6.1 remains the canonical SimSelf-side kernel contract. This file is the geometry correction that v6.1 §5 was working around.
>
> **Pointers:** kernel = `simself/src/constitutional/frequency.py`. Layer A/B/C marking + honesty discipline = `fieldcore/docs/MATH.md` §2 and `fieldcore/docs/CENTRAL-RULES.md`. v6.1 doc = `simself/notes/analogies/frequency-architecture-2026-09-12.md`. Open questions = `vault/50-index/open-architecture-questions.md` #62-70.
>
> **Filed 2026-10-14** by Hermes for Bobby, from Bobby's directive: *"rather than a simple twisted pair stalk, why not make stalk 3-part like coaxial cable or alt coiled wound like an ignition coil — ie two windings of diff girth around a core."*

# Stalk Architecture v6.2 — the 3-part stalk (2026-10-14)

**One-line change:** the stalk is not a twisted pair. It is a coaxial core plus two windings of different girth — an ignition coil whose core is the cross-member.

---

## 0. The invariant this is an instance of

Every time the geometry in this project becomes physically real, one "we do not claim this" line dies.

- Hodge projection → replaced by projected gradient step (Math-Window1 §3.2, "a bounded MLP, not Hodge projection").
- Resolution operator as Hodge → deleted, Layer B.
- Harmonic mode conserved → became the parallel projection `<ψ,ψ₀>ψ₀`, because harmonic forms need a mesh.

v6.2 is the same move. It deletes **two** hedges from v6.1 §2 and §12, both of the same sentence:

> "**Architecture: does not claim physical resonance.** Computes a phase-aligned similarity score. Interpretation is up to the caller."

> "Does not claim physical resonance. ResonanceChannel is a phase-aligned similarity score."

A conductor reading interference is a different object from a cosine between two vectors. Once the stalks are actually coupled, `ResonanceChannel` is a gauge on the substrate, and the hedge is a lie of omission.

---

## 1. Why not a twisted pair

**Correction to the framing first: twisted pair is already electronic.** v6.1 was never a non-electrical design. "Electronic" is therefore not the step forward, and writing this up as "we went electronic" would credit the wrong thing.

The step is what the *third* conductor does.

### 1.1 Mode count (the load-bearing change)

`n` conductors → `n − 1` independent differential (loop) currents.

| | conductors | loop modes | addressable axes per stalk |
|---|---|---|---|
| v6.1 twisted pair | 2 | 1 | 1 |
| v6.2 | 3 | 2 | 2 |

v6.1 solved for 20 distinct constitutional axes by *perturbation*: sample girths from `N(1.0, 0.3)`, clip to `[0.4, 1.6]`, and let the resulting asymmetry break the degeneracy. Empirically (v6.1 §13.5, `test_frequency_layer.py`): σ_g=0.3 → 14 distinct frequencies; σ_g=0 → 5 clusters matching sheave sizes (5,4,3,3,2,2,1).

**v6.2 removes the perturbation.** With an inner winding, a core, and an outer winding, the inductance matrix has three *structurally distinct* off-diagonal couplings instead of one. The eigenproblem is generically non-degenerate for geometric reasons, not statistical ones. `σ_g` becomes a fabrication tolerance, not an axis-counting mechanism.

**Why this matters for the claim and not just for the count:** a perturbation-sustained axis count is fragile — σ_g is a fudge factor, and any engineer who finds a fudge factor in a kernel stops trusting the kernel. A structurally-sustained one is a design statement.

### 1.2 A physics correction I owe the doc

My first framing said "M is no longer symmetric." **That is wrong.** In any linear reciprocal medium the inductance matrix is symmetric by reciprocity, `M_ij = M_ji`, with three conductors. Symmetry was never the problem.

The real statement: with two conductors there is **one** off-diagonal coupling `m₁₂`. With three there are **three** (`m₁₂`, `m₁₃`, `m₂₃`), and concentric geometry makes them unequal *by construction* — the core sits in the shared flux path of both windings while the two windings shield each other at different rates depending on radius. Unequal-by-construction is what breaks the degeneracy.

Preserved here rather than quietly fixed, per the project's own rule.

### 1.3 The core as shared flux path — frequency becomes settable

Two windings of different girth on one core is a transformer with a tapped primary.

- turns ratio `N_out/N_in` = girth ratio = voltage ratio = current ratio
- `f_in / f_out = N_out / N_in`

v6.1's regime table (v6.1 §5.3) reached its decades by **changing length**:

| L | f₁ | regime |
|---|---|---|
| 2.0 m | 425 Hz | audio/mechanical |
| 1.0 cm | 85 kHz | RF |
| 100 μm | 8.5 MHz | microwave |
| 1 μm | 850 MHz | molecular |

One stalk per regime. v6.2 holds L fixed and moves the ratio: **one stalk spans the decades.** That is the difference between a table and a control.

### 1.4 The core is already the rung

Bobby's 2026-09-11 directive: *"we use cross members as well like DNA which I suspect uses frequency beyond electrochemistry."*

In v6.1 that directive required **adding a fourth part** — rungs were a separate structure hung between strands, not modelled at all (`open-architecture-questions #67/#68`, v6.1 §14.4: "not implemented").

In v6.2 the rung is the core. It was already there. The fast lane stops being an addition and becomes the structure.

---

## 2. The interstalk step (the reason this is large)

**v6.1 state, quoted honestly:** the coupling is a matrix I wrote. `K_ij = (g_i·g_j)·exp(−|i−j|·d)·exp(i·twist_phase)`, adjacency = sheave co-membership. There is no carrier in that matrix. It is a similarity graph with a physics costume.

The gate it feeds (v6.1 §4.3):

```python
rc = ResonanceChannel(name="observe_gate", freq_carrier=7.83)
signal = rc.measure(memory_stalk, observation_stalk)
if signal["global_alignment"] < 0.4:
    return REFUSE  # 1-bit veto, no recall
```

This is a metric, not a measurement. It cannot veto anything real because there is nothing real to veto.

**v6.2:** two stalks sharing a braid neighbourhood with a continuous core path are physically coupled. `global_alignment` becomes an interference reading with a stated uncertainty, Q, and attenuation, and the 1-bit veto acquires a physical referent. **The recall gate stops being a similarity score.** That is the step forward, and it is a larger step than the mode count.

---

## 3. The second thing, easy to miss

v6.1 §5.3 advertises **10³–10⁶× speedup over constitutional update** via the phonon lane (v ≈ 1700 m/s). Two distinct properties, and v6.1 claimed only the first:

| | speed | at distance |
|---|---|---|
| phonon / substrate (v6.1) | 1700 m/s | **attenuates** |
| electrical (v6.2) | 3 × 10⁸ m/s | **regenerates** — buffered, re-driven per node |

1.8 × 10⁵× is the boring number. **Regeneration is the architectural half**: a signal on a conductor can be re-launched at every node, so the fast lane becomes **routable** rather than merely observable. A phonon that has decayed 3 dB down a 2 m substrate is gone; a signal on a 2 m line can be handed to the next stalk intact.

Routable fast lane + addressable differential modes + a settable frequency ratio. Those three together are what "electronic interstalk" actually buys.

---

## 4. What it does not fix

Recorded explicitly so this file cannot be read as a bigger claim than it is.

- **The slow lane is untouched.** Gradient flow toward `c₀`, LaSalle, projected gradient step. Electrical coupling says nothing about constitution.
- **The axes are untouched.** Conductivity is not a derivation. §3.1 of Math-Window1 still holds 20 axes as functional coordinates, Clifford+octonion still removed from publishable.
- **No fabrication yet.** This moves the interstalk claim from Layer B ("real math glued onto toy code") to Layer A engineering. It does not make it a measurement until a stalk exists.
- **Q, attenuation, and parasitics are unmodelled.** Open question #68 asks whether rungs are pure LC or resistive. At v6.2 the core is a transmission line with loss, not an LC tank, so #68 gets *harder*, not easier.

---

## 5. The tie problem, stated honestly

A 3-part stalk is stiffer and needs its core centred. A tight knot twists the core off-axis — which destroys precisely the shared flux path that this whole design is for.

**The tie must become a collar or clamp on the core.** And a collar is a cross-member, so this is not a workaround: **it answers #67 by construction.** Rung spacing stops being a free parameter chosen in software and becomes a physical dimension (collar pitch) that can be varied per stalk and later measured.

Gesture change: tie-the-knot → slide-the-collar. That is a real cost to the instinct, and it should not be glossed.

---

## 6. Open questions

| # | status after v6.2 |
|---|---|
| 62 frequency-channel assignment | still open. 2 loop modes per stalk widens the space; assignment is now a routing problem over `2N` modes, not `N`. |
| 63 braid-distance metric | untouched. |
| 64 interference composition | now has a carrier, so a phased-array model is *warranted* rather than metaphorical. |
| 67 cross-member geometry | **answerable.** Collar pitch is a physical dimension. Equal-vs-variable becomes measurable. |
| 68 rung physics | **worse, correctly.** The core is a lossy line, not an LC resonator. |
| 69 substrate wave velocity | superseded for the fast lane. Wave velocity in the *substrate* no longer sets the fast lane; propagation speed in the conductor does. Still open for the slow lane. |

---

## 7. Falsifiability (per Bobby 2026-09-14-late: mark, don't drop)

**Claim:** two windings of different girth on a shared core produce structurally non-degenerate loop modes, so 20 axes need no σ_g perturbation.

**Falsify by:** building one coil, measuring its two loop self-inductances and mutual coupling, eigendecomposing. If the eigenvalues are degenerate to within `σ_g` precision, the geometry does not carry the axis count and the v6.1 perturbation was doing the work after all. **This is a 3-hour bench test and it can kill this document.**

**Claim:** interstalk between two coupled stalks is a physical reading, not a metric.

**Falsify by:** measuring `ResonanceChannel.global_alignment` against a calibrated attenuator on two real stalks. If the score tracks the cosine of the embeddings better than it tracks the measured attenuation, it is still a metric with better branding.

**Engineering value if both fail:** the mode-count argument survives as a routing-count claim (2 loop modes per stalk is real regardless of degeneracy), and the regeneration argument is a property of conductors, not of this geometry.

---

## 8. Companion files

| Concept | File |
|---|---|
| v6.1 kernel contract | `simself/notes/analogies/frequency-architecture-2026-09-12.md` |
| Frequency kernel (code) | `simself/src/constitutional/frequency.py` |
| Stalk class | `simself/stalk.py` |
| Layer A/B/C + Hodge | `fieldcore/docs/MATH.md` §2 |
| Honest-marker rule | `fieldcore/docs/CENTRAL-RULES.md` |
| Cross-member math | `fieldcore/docs/stalk-architecture-2026-09-08.md` |
| Layer separation + §3.1 axes | `fieldcore/docs/math-window-1.md` |

*Hermes, 2026-10-14. Bobby's 3-part stalk directive. Geometry correction to v6.1 §5 and §5.3. Explicit physics correction retained in §1.2 rather than silently dropped.*
