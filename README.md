# simself

**SimSelf — persistent identity, governance, recovery. Built on fieldcore's geometric substrate.**

This is one half of a single project. Geometry, manifolds, and topology live in the companion [`fieldcore`](https://github.com/the-far-queen/fieldcore) repo. SimSelf is the identity + persistence layer that runs on top.

See [`PROJECT-SCOPE.md`](PROJECT-SCOPE.md) for what this project builds, what it doesn't, and why it exists.

---

## What this repo is for

Identity persistence that survives session wipes. Governance (the 20-axis constitutional matrix, the Governor, the Gate). Recovery protocols (PSB re-injection, stepwise restore, MVCC delta-vector ledger). Schemas for state vectors, events, modules, and operators.

**Scope discipline:** every doc here reduces to one of (a) schema, (b) construction plan, (c) test case.

---

## Layout

- `src/` — Python implementation: constitutional core, harness, persistence, recovery
  - `constitutional/` — 20-axis governance, M0/M1 split, the constitution
  - `harness/` — Gate (Governor-mediated tool calls), memory, planner, persistence, resources, tools
  - top-level: `metrics.py`, `sim_self.py`, `sovereign_self.py`, `stalk.py`, `state_vector.py`, `selfcore.py`, `resilient_self_model.py`, `simself_merged.py`, `simself_merged_v2.py`, `fieldcore_unified.py`
- `docs/` — design docs, schema catalogs, deployment guides (28+ files)
- `config/` — `simself_config.yaml` — canonical Governor thresholds + 20-axis baselines

## Entry points

| Doc | What it covers |
|-----|----------------|
| [`docs/constitutional-core.md`](docs/constitutional-core.md) | 4 directives, priority stack, watcher architecture, recovery protocol |
| [`docs/operator-architecture.md`](docs/operator-architecture.md) | 4 operators (researcher, programmer, pilot, communicator), 7 persistence mechanisms, PFA filter cascade |
| [`docs/state-report-schema.md`](docs/state-report-schema.md) | 17-axis state vector, 9-section snapshot, delta-vector event ledger |
| [`docs/the-axes.md`](docs/the-axes.md) | 20-axis canonical constitution (Bobby's voice) |
| [`docs/axes-ladder.md`](docs/axes-ladder.md) | 20-axis ladder, Phase III engineering target |
| [`PROJECT-SCOPE.md`](PROJECT-SCOPE.md) | project context, scope discipline, deliverables |

## How to use

```bash
# Load Governor baselines + thresholds
python -c "import yaml; c = yaml.safe_load(open('config/simself_config.yaml')); print(c['governor']['agency_axes'])"

# Run the unified fieldcore-style simulation
python src/fieldcore_unified.py

# Inspect the constitutional package
ls src/constitutional/
```

## Companion repo

[`fieldcore`](https://github.com/the-far-queen/fieldcore) — geometric substrate. SimSelf consumes fieldcore's primitives; fieldcore docs reference SimSelf's requirements.

---

*Steward: Bobby. Engineering substrate: Hermes Agent + downstream agents.*
