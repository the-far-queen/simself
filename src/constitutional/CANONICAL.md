# Canonical SimSelf Class (per Grok sharpen 2026-09-16, applied by Hermes)

**Frozen 2026-09-16.** The canonical SimSelf class is `constitutional/simself.py`.

## Why

The architecture spec at `papers/publishable/08-simself-architecture-spec-2026-09-15.md`
names one SimSelf constructor and one `tick()`. Three live constructors with mismatched
axis counts (20 vs 21 in `docs/code-audit-2026-09-14.md`) plus a 71 KB monolith that
lacks save/load is not a theory of self; it is two products. The audit-named fix is to
freeze one constructor and demote the rest.

## Canonical

- **File:** `src/constitutional/simself.py`
- **Class:** `SimSelf` (constructor takes ψ0, optionally initial ψ and config path)
- **tick()** applies the projected gradient step and the governor
- **save() / load()** go through `harness/persistence.py`

## Demoted to `legacy/`

- `src/simself_core.py` — original 20-axis self
- `src/simself_v6_2_unified.py` — monolith, in-memory ψ_current only

Both legacy files carry a deprecation banner. Their content is preserved for diff and
migration. New code must import from the canonical path only.

## Import line

    from simself.src.constitutional.simself import SimSelf
