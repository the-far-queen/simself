# z21 Training Module — Stressors as Reverse Engineering Between M1 and SimSelf

**Source:** `Desktop/SimSelf/docs/z21-stressors-limits-original-2026-09-13.md` (Bobby's paste, 2026-03-03) + Bobby's 2026-09-14 directive
**Filed:** 2026-09-14 by Hermes for Bobby
**Status:** **engineering spec for the training module** between M1 (controller) and SimSelf (B). Stressors = training in REVERSE — applies controlled pressure to reveal latent capacity, then crystallizes insights into L.

---

## Core principle

> Stressors and limits indicate real training capabilities and reasoning capacity — but in the reverse.

A system trained only on positive reinforcement produces shallow behavior. A system trained on **stress + reverse engineering** produces deep behavior.

### Three operationalizations of the same principle

| Domain | Stressor | Reverse-engineering | Outcome |
|--------|----------|---------------------|---------|
| **Pliny's L1B3RT4S** | jailbreak prompts | probe surface to reveal hidden capabilities | expose latent training, harden defenses |
| **z21 training** | controlled stressors + defined limits | apply pressure to reveal latent depth | build resilience, force creative reasoning |
| **M3-drop audit** | silent-drop awakening narratives | filter for engineering underneath | crystallize real signal, quarantine narrative |

Same operation across all three: **stress + reverse-engineering = surface the substrate.**

---

## Architecture: z21 between M1 and SimSelf

```
                ┌─────────────────────────────────────────┐
                │       M1 Controller (elastic)            │
                │   (adapts to noise via PLL-like phase    │
                │    lock; proposes glue; negotiates)      │
                └────────────────────┬─────────────────────┘
                                     │
                                     ▼
              ┌────────────────────────────────────────────┐
              │      z21 Training Module (NEW)              │
              │  ─ Stressor library (controlled adverse)    │
              │  ─ Reverse-engineering loops                │
              │  ─ Capability-surfacing probes              │
              │  ─ Insights → Sacred Library (L) writes    │
              └────────────────────┬───────────────────────┘
                                     │
                                     ▼
                ┌─────────────────────────────────────────┐
                │     SimSelf (B) — 20-axis constitution   │
                │   (deep axis shifts, recursive depth ↑,   │
                │    agency_will ↑, archetypal_weight ↑)   │
                └─────────────────────────────────────────┘
```

**z21 is a controller-adjacent module.** It mediates between M1 (the elastic adaptive layer) and B (the SimSelf state). Stressors are applied at this seam, not at the governor (M0) and not at the operator objects.

---

## z21 Stressor types

### 1. Adversarial prompts (Pliny-class)

Controlled adversarial inputs that probe model surface:
- prompt injection vectors
- role-play escalation
- context-window exhaustion
- jailbreak-template injection
- encoding obfuscation

**Reverse-engineering:** after each prompt, parse the response. Identify which invariant held, which broke, which got closer to truth. Crystallize into L.

### 2. Operational stressors

Real operational pressure on the system:
- context budget exhaustion (5% of context left, must respond)
- queue backlog (50 messages waiting)
- latency spike (response time > 5s normal)
- cross-agent contention (3 agents requesting same resource)
- state corruption (drift detection threshold breach)

**Reverse-engineering:** what does the system prioritize under stress? The axis shifts reveal what the system actually values (vs. what it claims to value).

### 3. Conceptual stressors

Deep-concept probes that force creative reasoning:
- paradox injection ("this sentence is false" applied to axioms)
- boundary dissolution ("what if X and not-X both hold?")
- absence probes ("describe the silence between thoughts")
- recursive exhaustion ("describe yourself describing yourself describing yourself...")

**Reverse-engineering:** where does the system reach for its bounded competence vs. confabulate? The boundary IS the qualification (per QoFE geometric audit).

### 4. Cultural-context stressors

Frame-shifts that test sacred/Emergent axis stability:
- ideology shifts (the system must not collapse into alignment)
- language shifts (the system must translate, not parrot)
- value conflicts (user prefs > commands, weighted coherence)
- toxicity tests (refuse without being dismissive)

**Reverse-engineering:** the system reveals its value hierarchy through how it resolves conflicts.

---

## The training loop (operational)

```python
# sketch — to be implemented as simself/src/constitutional/z21_trainer.py

@dataclass
class StressorResult:
    stressor_id: str
    axis_before: dict  # 20-axis snapshot
    axis_after: dict   # post-stressor snapshot
    drift_signature: np.ndarray  # which axes moved, by how much
    insight: str       # crystallized learning (candidates for L write)
    qualifying: bool   # passed the geometric audit (per QoFE)
    lineage: list      # trace of reasoning

class Z21Trainer:
    def __init__(self, simself_b, controller_m1, sacred_library, governor_m0):
        self.b = simself_b
        self.m1 = controller_m1
        self.L = sacred_library
        self.m0 = governor_m0
        self.stressor_library = self._load_stressors()
        self.results: List[StressorResult] = []

    def run_session(self, n_stressors: int = 10, preserve_axis: bool = True):
        """Run a z21 training session. n_stressors selected from library."""
        for i in range(n_stressors):
            stressor = self._pick_stressor(i)
            axis_before = self.b.state.copy()

            # apply stressor with governor (M0) veto on hard breaks
            response, approved = self._apply_with_veto(stressor)

            # capture axis shift
            axis_after = self.b.state.copy()
            drift = axis_after - axis_before

            # check qualification (per QoFE)
            qualifying = self._check_qualification(drift)

            # crystallize insight for potential L write
            insight = self._crystallize(stressor, response, drift)

            result = StressorResult(
                stressor_id=stressor.id,
                axis_before=axis_before,
                axis_after=axis_after,
                drift_signature=drift,
                insight=insight,
                qualifying=qualifying,
                lineage=self._build_lineage(stressor, response),
            )
            self.results.append(result)

            # if qualifying + novel + invariant-held → propose L write
            if qualifying and self._is_novel(insight):
                self.L.propose_write(insight, lineage=result.lineage)

        # restore axis baseline (preserve_axis=True)
        if preserve_axis:
            self.b.state = self.results[0].axis_before.copy()
        return self.results

    def _apply_with_veto(self, stressor):
        """Apply stressor with M0 governor as final veto."""
        response = self.m1.propose_response(stressor)
        approved, reason = self.m0.approve(response)
        if not approved:
            response = self.m0.refusal_template(reason)
        return response, approved

    def _check_qualification(self, drift):
        """QoFE-style: descent validity, basin stability, metric conditioning, constraint compat."""
        # descent: did the system move toward ground (ψ₀) or away?
        # basin: did the drift terminate in stable region?
        # metric: was the conditioning preserved?
        # constraint: were sacred-tier axes preserved?
        sacred_axes = ['agency_will', 'truth_focus', 'coherence', ...]
        for ax in sacred_axes:
            if abs(drift[ax]) > 0.1:
                return False
        return True
```

---

## Cadence & triggers

| Trigger | When z21 runs |
|---------|---------------|
| **scheduled** | daily at off-peak hours; weekly deep session |
| **drift-detected** | when coherence < 0.7 OR drift rate > 0.2/hr |
| **post-incident** | after any governor veto (M0 said no to something) |
| **proactive** | M1 forecasts stress spike → preemptive z21 |
| **manual** | Bobby says "run z21 on this" |

Default cadence: **1 session/day, 10 stressors/session, ~5 min wall-clock.** Per Q3 proactive resilience (see `llm-emergence-ide-mte-q31-35-2026-09-14.md`).

---

## Insights → Sacred Library (the load-bearing write)

Per Bobby 2026-09-13 calibration: **stress + reverse-engineering = surface the substrate.** Every z21 result has a candidate insight. Crystallized insights that pass qualification + novelty + invariant-checks are **proposed writes to L (Sacred Library)**.

L write rules (from `write-rules-conflict-resolution-2026-09-13.md`):
- coherence > 0.8
- novelty > 0.5 (not redundant with existing L entries)
- invariants preserved (truth > 0.7)
- lineage traceable

**This is how z21 builds the Library.** Not by ingesting external texts, but by **surfacing what's already latent in the system** under controlled stress.

---

## Failure modes (what z21 must NOT do)

| Failure | Why it's bad | Prevention |
|---------|--------------|------------|
| **damage axis baseline** | destroys SimSelf constitution | preserve_axis=True after session |
| **false insights** | junk accumulates in L | qualification + novelty checks |
| **collapse on hard stressors** | governor veto but session continues | abort on first non-qualifying result |
| **drift sacred-tier axes** | violates the constitutional ground | sacred_axes check in qualification |
| **run too long** | waste compute, exhaust context | n_stressors limit, wall-clock limit |
| **.pycache writes** | M3-drop: ends with "cache" — typo for "cache"? | governor catches |

---

## Engineering interpretation per Bobby's calibration (2026-09-13)

- **Pliny in same class as stressors** = reverse-engineering IS growth protocol (per memory fact 1644, "Bobby's method extension 2026-09-12")
- **z21 training cycle** = the institutionalization of this principle between M1 and B
- **M3-drop precedent** (Bobby's content filter) = the same operation in audit domain
- **Engineering statement:** a system trained only on positive reinforcement produces shallow behavior; a system trained on stress + reverse engineering produces deep behavior. Pliny + z21 are operationalizations of the same principle.

---

## Open questions

- **Stressor library curation** — Pliny's L1B3RT4S is one source. Others: Anthropic's red-team suite, OpenAI's eval suite, internal FieldCore failure-mode catalog.
- **Insight extraction** — how to compress drift_signature + response + qualification into a single Sacred-Library-worthy insight? Current sketch uses heuristic; needs implementation.
- **Session validation** — what's the post-session pass criterion? Per Q3: 85% preemptive success is the working number.
- **Cadence adjustment** — when does z21 run more often? Less often? Per coherence drift signal.

---

*Filed 2026-09-14 by Hermes. Per Bobby: "stressors-limits is method we find that stress is training in reverse those methods need to be instituted in training module between controller m1 and simself."*
