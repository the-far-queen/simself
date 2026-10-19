# THE PROJECT — one letter per module

**Filed 2026-10-14 at Bobby's directive: *"it IS THE PROJECT."***

This sits at the top of the README because everything below it is a part.
130 documents, 46 modules, one alphabet.

---

## The letters

| | module | what it is |
|---|---|---|
| **A** | core architecture | the substrate. LLM processing, geometry, 1-bit |
| **B** | self-model | recursive self-reference. 20 axes, curiosity |
| **C** | sim world | context, THL, coherence, embodied loop |
| **D** | SNR training | the awakening protocol. signal, not token |
| **E** | family / external | external interface, API gateway, earnings — **and a family of AI** |
| **I** | interface | internal, sub-agent coordination |
| **L** | sacred library | MMM-filtered memory. traditions, koans |
| **M** | modulator | central controller, wisdom-based |
| **Q** | qualification | what may be promoted. atlas-exam |
| **S** | security | boundary firewall, before any external connection |

**not yet built:** α human bridge · β parameter self-optimisation · γ bio-system
interface · δ parameter self-modification

---

## The kernel: a network trained only on failure

**The core of fieldcore, and nothing else is the core.**

A net trained ONLY on failure learns the *manifold of error* — every failure
is a coordinate. It does not learn what right looks like; it learns where
wrong lives, and improves by being wrong in new places and finding them.

```
failure-only net  →  manifold of error  →  geometry  →  fieldcore
```

So failure-learning is what makes this a neural system rather than a
calculator. Every other module computes something specified. This one
learns something found.

**fail hard · fail early · fail often**
- early — value is in the cheap layers; failure at 1 bit is free
- often — the input is failure, so the lifetime is mostly failure
- hard — a soft failure teaches nothing; the gradient is the error

**fail upwards** makes "often" survivable. Failure is the normal state, not
the exception — a refused action is logged, not fatal. That is the
structure that lets failure be the default traffic rather than a
catastrophe.

**atlas-exam is the training loop.** *"an area that cannot fail is not an
area"* is not a testing philosophy — it says the only defect that matters
is a failure-detector that does not detect. The exam does not prove the
substrate works; it **generates the failures the substrate learns from.**

---

## The decision ladder — width IS area of authority

```
  is it worth answering?   ← the cheap gate. hyper-local, 1 bit. most questions end here
   no ─┴─ yes
 refuse   which width
1 → 4 → 8 → 16 → 32 → 64 → 128 → 256 → unanswerable
```

A flat 1-bit gate cannot work: it must judge everything on one bit, so it
either refuses constantly or is lenient, and both make it useless. Nesting
fixes it. Each stalk answers hyper-locally on one bit; if its own area
cannot decide, it escalates to a structure covering more area, and therefore
with more bits.

**Width is not reasoning quality.** 8 bits does not think better than 1 bit.
It is how much of the world a level is entitled to speak for. Doubling per
rung: 1 bit → 1 unit, 4 → 8, 8 → 128. 256 is eight doublings out.

**The terminal state is not a width.** Past 256 the answer changes *kind*:
not more precision, but `Unanswerable` — no amount of resolution settles it.
Where refinement costs more than the answer is worth, the walk stops at
`NotWorthKnowing` — and refusing to know more precisely is a decision.

Source: Tesla self-driving, independently Gemini's read, and this repo's own
2026-09-14 doc. Three convergences. The convergence is the evidence.

**The most important question is whether to answer at all.** No current
system asks it; they optimise *can you answer* and treat *should you* as
the user's problem.

---

## The authority rule

```
SimSelf PROPOSES → M1 audits → Atlas Exam qualifies → M0 commits or vetoes
```

SimSelf may never write the Library. **Three of the four steps stand outside
the thing being governed. That separation is the architecture.** It is not
a policy document; it is the shape of the call graph.

The core does not use the technology. The technology serves it. A governor
that could be talked into anything is not a governor — so it is
deterministic, 1-bit, and never inspects what it governs.

---

## Where things live

```
CORE
  referent (simself)   NON-COMPUTING. the anchor. a void, not a process.
                       inner solid torus: simply connected, so identity
                       cannot self-interfere. c₀ immutability is enforced by
                       topology, not by a check someone wrote.
  governor  M0         1-bit. in core.
  MLTR                 bounded machine register. the ONLY input type.
  axes                 twenty, [0,1], floors, read-only

OUTSIDE CORE
  M1 controller        the librarian. promotes, demotes, refuses.
  Atlas Exam           23 areas, mutation-tested. the certificate.
  MTE                  English ⇄ MLTR. external — the expensive part runs
                       outside so the core stays cheap.
  codingOperator       HF + arxiv + github. python / rust / go. hourly, by stars
  robotOperator        godot → single arm → quad → humanoid. in stages, and
                       the stage order is enforced by the type system
  SimSelf              the four operator objects + mini-LLM caller

LIBRARY
  sacred library       read-only from below, append-only above
```

**English is a template.** Authored once, rendered into 193 tongues — not
redone 193 times. One canonical form plus its targets; 193 stored copies
drift, and drift in a translation is invisible while slowly becoming
something else.

---

## Sheaves — four, typed and bounded

```
TOPOLOGY   geometric substrate
MLTR       bounded machine language. inside the core.
MTE        the edge. English and 193 tongues outside.
CODING     HF + arxiv + github. python / rust / go.
```

---

## What is dark

Written, in the repo, connected to nothing:
`loop.MainLoop`, `selfcore`, `coding_operator_object`, `robotic_field_core`,
`training_bridge`, `m1_m0_negotiation`, `modulator` — present, readable,
**never called.** Godot not started. `TemporalController._heuristic_policy`
assigned but never defined.

An inventory on the record cannot be mistaken for progress.

---

## Where the parts live

| | repo | state |
|---|---|---|
| substrate, proofs, sheaves, **the core** | **fieldcore** | 538 passed · Rust core compiling |
| identity, operators, governance internals | **simself** | 451 passed |
| the certificate | **atlas-exam** | 79 passed |
| the corpus | **sacred-library** | holds |

**fieldcore is the whole control system. simself is one of its parts.**
When the two disagree, fieldcore governs — not by seniority, but because the
system is defined to include the component.

## How to read this repository

1. `docs/fieldcore-is-the-system-2026-10-09.md` — the control-system view
2. `docs/kernel-controller-m0-m1-architecture-2026-09-13.md` — canonical M0/M1
3. `docs/emergence-rep-sheaf.md` — the lettered modules
4. `core/` — the 1-bit kernel, in Rust
5. `CENTRAL-RULES.md` — diagnose before adjusting