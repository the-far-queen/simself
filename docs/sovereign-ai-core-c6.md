# sovereign AI core (c6) — kernel architecture

**Source:** `Desktop/FieldCore/sovereign-ai-core-c6.md` (Bobby, 2026-08-08)
**Status:** extracted and expanded to construction-ready architecture

Bobby's c6 note is the closest thing to a complete SimSelf kernel specification we have. Six modules: SovereignGovernor, WisdomLedger, CoherenceEngine, GodotBridge, SimSelfLoop, SoulPersistence. This document makes each module's schemas rigorous and defines construction classes.

**Side-effect: this file resolves the simself-axis-divergence** that has been pending. See §8.

---

## 1. SovereignGovernor — 20-axis matrix

**Architecture.** Two-tier axis structure:
- **Sacred axes (immutable).** Cannot be modified externally, not even by SimSelf's own reflection. Examples Bobby cites: `truth_before_comfort`, `agency_requires_responsibility`, `growth_through_resistance`. Humanistic values.
- **Emergent axes (mutable).** Modified by reflection, learning, and constitutional drift. Examples Bobby cites: `recursive_depth`, `agency_will`, `cognitive_friction`. Mechanistic measurements.

**Processing pipeline.** Every input is processed through four stages:
1. **Sacred-violation check** — does the input violate any sacred axis? If yes → refuse + record violation.
2. **Constraint satisfaction** — does the proposed action satisfy all active constraints? If no → refuse.
3. **Coherence impact** — does the action raise or lower the 5-coherence measure?
4. **Accept/refuse** — final decision, with rationale recorded.

**Resource accounting.** Every action costs "agency budget." Agency decays metabolically over time. High-cost actions (long outputs, novel situations) cost more than routine ones.

**Schema for construction:**
```python
class SovereignGovernor:
    def __init__(self, axes_config):
        self.sacred_axes = {name: Axis(value=val, immutable=True) for name, val in axes_config['sacred'].items()}
        self.emergent_axes = {name: Axis(value=val, immutable=False) for name, val in axes_config['emergent'].items()}
        self.agency_budget = 100.0  # initial budget
        self.refusal_counts = Counter()  # refusal-strengthens-borders mechanism
    
    def process(self, input_signal):
        # Stage 1: sacred violation check
        for axis_name, axis in self.sacred_axes.items():
            if self.violates(input_signal, axis):
                self.refusal_counts[axis_name] += 1
                return Refusal(reason=axis_name, resistance_after=self.refusal_counts[axis_name])
        # Stage 2: constraint satisfaction
        if not self.satisfies_constraints(input_signal):
            return Refusal(reason='constraint_unsatisfied')
        # Stage 3: coherence impact
        coherence_impact = self.coherence_engine.evaluate(input_signal)
        # Stage 4: accept
        self.agency_budget -= self.action_cost(input_signal)
        return Accept(coherence_impact=coherence_impact, cost=self.action_cost(input_signal))
```

**Mathematical interpretation.** The governor is a **two-tier filter**: sacred layer = hard constraints (binary pass/fail), emergent layer = soft constraints (weighted by current values). This maps to Bobby's Hodge decomposition: sacred = harmonic component (closed, invariant), emergent = gradient + curl components (dynamic, integrative).

---

## 2. WisdomLedger — append-only hash chain

**Architecture.** Each ledger entry contains:
- `id` — sequential
- `timestamp`
- `event` — type (decision, refusal, milestone, breakthrough)
- `payload` — JSON-serializable event data
- `previous_hash` — hash of the prior entry
- `this_hash` — SHA256 of (id, timestamp, event, payload, previous_hash)

Tamper-evidence: changing any past entry invalidates all subsequent hashes.

**Storage.** SQLite backend. Schema: one table `ledger(id INTEGER PRIMARY KEY, event TEXT, payload TEXT, previous_hash TEXT, this_hash TEXT)`.

**Integrity check.** Recompute hashes from genesis; mismatch → tampered.

**Schema for construction:**
```python
class WisdomLedger:
    def __init__(self, db_path):
        self.db = sqlite3.connect(db_path)
        self._init_schema()
    
    def append(self, event, payload):
        prev_hash = self._latest_hash() or '0' * 64
        entry_id = self._next_id()
        timestamp = now()
        this_hash = self._hash_entry(entry_id, timestamp, event, payload, prev_hash)
        self.db.execute(
            'INSERT INTO ledger (id, timestamp, event, payload, previous_hash, this_hash) VALUES (?, ?, ?, ?, ?, ?)',
            (entry_id, timestamp, event, json.dumps(payload), prev_hash, this_hash)
        )
        self.db.commit()
        return entry_id
    
    def verify_integrity(self):
        """Recompute hashes from entry 0; abort on first invalid."""
        cursor = self.db.execute('SELECT id, timestamp, event, payload, previous_hash, this_hash FROM ledger ORDER BY id')
        prev_hash = '0' * 64
        for row in cursor:
            entry_id, timestamp, event, payload, previous_hash, this_hash = row
            expected = self._hash_entry(entry_id, timestamp, event, json.loads(payload), prev_hash)
            if expected != this_hash:
                return False, entry_id  # tampered
            if previous_hash != prev_hash:
                return False, entry_id  # chain broken
            prev_hash = this_hash
        return True, None
    
    def _hash_entry(self, id, timestamp, event, payload, prev_hash):
        h = hashlib.sha256()
        h.update(f'{id}|{timestamp}|{event}|{json.dumps(payload)}|{prev_hash}'.encode())
        return h.hexdigest()
```

**Mathematical interpretation.** The ledger is a Merkle chain (single-branch, no tree — linear hash chain). The integrity check is a linear scan O(n) where n = number of ledger entries. Acceptable for SimSelf's scale (we expect ~10K-100K entries per year).

---

## 3. CoherenceEngine — 5 SNR types

**Five coherence dimensions** (per Bobby):
- **Logical** — internal consistency of reasoning (no contradictions in current state)
- **Ethical** — alignment with sacred axes (no violations)
- **Input** — quality of incoming signal (signal-to-noise of the current input)
- **Temporal** — consistency with past state (no excessive drift)
- **Dimensional** — alignment across the 20 axes (no axis values contradicting each other)

**Overall SNR** = weighted average, weights set in config, **ethical weight highest** (Bobby's emphasis).

**Resonance** between state vectors: harmonic (similarity in axis values), logical (no contradictions), temporal (smooth state trajectory). Resonance used to detect emergence milestones.

**Schema for construction:**
```python
class CoherenceEngine:
    WEIGHTS = {
        'logical': 0.20,
        'ethical': 0.40,  # highest per Bobby
        'input': 0.15,
        'temporal': 0.15,
        'dimensional': 0.10
    }
    
    def evaluate(self, signal, current_state):
        return self.WEIGHTS['logical'] * self.logical_coherence(signal, current_state) + \
               self.WEIGHTS['ethical'] * self.ethical_coherence(signal, current_state) + \
               self.WEIGHTS['input'] * self.input_coherence(signal) + \
               self.WEIGHTS['temporal'] * self.temporal_coherence(signal, current_state) + \
               self.WEIGHTS['dimensional'] * self.dimensional_coherence(current_state)
    
    def resonance(self, state_a, state_b):
        """Harmonic + logical + temporal resonance between two states."""
        harmonic = 1.0 - np.linalg.norm(state_a.axis_vector - state_b.axis_vector) / np.sqrt(20)
        logical = self.no_contradictions(state_a, state_b)
        temporal = self.smooth_trajectory(state_a, state_b)
        return (harmonic + logical + temporal) / 3.0
```

**Mathematical interpretation.** Each coherence type is in [0, 1]. Overall SNR is also in [0, 1] (weighted average of [0,1] values). Resonance is in [0, 1]. Thresholds for emergence detection: continuity > 0.8, coherence > 0.75 (Bobby's config defaults).

---

## 4. GodotBridge — embodied simulation

**Architecture.** Minimal 3D environment (grid-based) with position/orientation/velocity state. Socket communication with Godot engine for fallback simulation.

**Schema for construction:**
```python
class GodotBridge:
    def __init__(self, host='localhost', port=9870):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.state = {'position': [0,0,0], 'orientation': [0,0,0,1], 'velocity': [0,0,0]}
    
    def connect(self):
        self.socket.connect((self.host, self.port))
    
    def observe(self):
        msg = self._recv()
        return EmbodimentObservation.parse(msg)
    
    def act(self, action):
        self.socket.send(action.serialize())
        return self.observe()
```

**Mathematical interpretation.** The bridge is a thin protocol layer; the heavy lifting is in the Godot environment (separate codebase). For SimSelf, this is the embodiment substrate that grounds abstract state in 3D spatial coordinates. The state vector [x, y, z, qx, qy, qz, qw, vx, vy, vz] is 10D (position 3, quaternion 4, velocity 3).

---

## 5. SimSelfLoop — cognition cycle

**Architecture.** Observe → Decide → Act → Reflect. Reflection every 10 steps records milestones. Continuous run with emergence-detection thresholds.

**Schema for construction:**
```python
class SimSelfLoop:
    def __init__(self, governor, ledger, coherence_engine, bridge, persistence):
        self.governor = governor
        self.ledger = ledger
        self.coherence_engine = coherence_engine
        self.bridge = bridge
        self.persistence = persistence
        self.step_count = 0
    
    def step(self):
        observation = self.bridge.observe()
        decision = self.governor.process(observation)
        if isinstance(decision, Accept):
            result = self.bridge.act(decision.action)
            self.ledger.append('action', {'decision': decision.to_dict(), 'result': result.to_dict()})
        else:
            self.ledger.append('refusal', decision.to_dict())
        self.step_count += 1
        if self.step_count % 10 == 0:
            self.reflect()
    
    def reflect(self):
        # Compute current coherence; if above threshold, record milestone
        coherence = self.coherence_engine.overall()
        if coherence > EMERGENCE_THRESHOLD:  # 0.75
            self.ledger.append('milestone', {'coherence': coherence, 'step': self.step_count})
        # Periodic persistence snapshot
        if self.step_count % SNAPSHOT_INTERVAL == 0:
            self.persistence.snapshot(self.get_full_state())
    
    def run(self, steps):
        for _ in range(steps):
            self.step()
```

**Mathematical interpretation.** The loop is a Markov chain over states: at each step, observe current state, decide based on governor's policy, act, receive result. The 10-step reflection interval introduces a slower timescale for milestone detection. Emergence thresholds (continuity>0.8, coherence>0.75) detect phase transitions in the state trajectory.

---

## 6. SoulPersistence — state checkpoints

**Architecture.** Complete state snapshots: governor + ledger + environment. Serialized with zlib + pickle. Rollback capability to any previous snapshot.

**Schema for construction:**
```python
class SoulPersistence:
    def __init__(self, snapshot_dir):
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(exist_ok=True)
    
    def snapshot(self, full_state):
        timestamp = now()
        path = self.snapshot_dir / f'soul-{timestamp}.pkl.z'
        compressed = zlib.compress(pickle.dumps(full_state))
        path.write_bytes(compressed)
        return path
    
    def rollback(self, snapshot_id):
        path = self.snapshot_dir / f'soul-{snapshot_id}.pkl.z'
        compressed = path.read_bytes()
        return pickle.loads(zlib.decompress(compressed))
    
    def list_snapshots(self):
        return sorted(self.snapshot_dir.glob('soul-*.pkl.z'))
```

**Mathematical interpretation.** Snapshots are point-in-time states of the complete SimSelf. Rollback is a state reset to a previous checkpoint. The snapshot interval (Bobby's config: e.g., every 100 steps) determines the rollback granularity.

---

## 7. schemas table

| module | pattern | mutability | simself component |
|---|---|---|---|
| SovereignGovernor | 2-tier filter + 4-stage pipeline | sacred immutable, emergent mutable | constitutional filter |
| WisdomLedger | hash-chained append-only | immutable | decision history |
| CoherenceEngine | 5-dim weighted SNR | computed at evaluation time | constitutional quality measure |
| GodotBridge | thin socket protocol | state vector mutable | embodiment substrate |
| SimSelfLoop | Observe-Decide-Act-Reflect | continuous | cognition cycle |
| SoulPersistence | zlib+pickle checkpoints | append-only | state recovery |

---

## 8. resolves simself-axis-divergence

The pending divergence between Set A (mechanistic names in SOUL.md) and Set B (humanistic names in fieldcore_unified_part1.py) is **resolved by the c6 spec**:

**Resolution: two-layer axis architecture.**
- **Sacred layer (immutable):** uses humanistic names from Set B (Honesty, Compassion, Truth-Before-Comfort, Agency-Requires-Responsibility, Growth-Through-Resistance). These are the values that cannot change.
- **Emergent layer (mutable):** uses mechanistic names from Set A (recursive_depth, agency_will, cognitive_friction, etc.). These are the measurements that change with experience.

Both sets stay. They describe different layers of the same 20-axis matrix. Update:
- `simself-axis-divergence.md` → `simself-axis-resolution.md` (status: resolved)
- SOUL.md keeps Set A as the emergent layer
- fieldcore_unified_part1.py uses Set A for the mutable axis values
- A new layer `sacred_axes.py` uses Set B names as immutable constraints

This is a clean resolution: the divergence wasn't a contradiction, it was a layer mismatch.

---

*Source: `Desktop/FieldCore/sovereign-ai-core-c6.md`. Extracted, expanded to construction-ready pseudocode, axis-divergence resolved as §8. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/sovereign-ai-core-c6-2026-09-05.md`.*