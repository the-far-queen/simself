---
name: fieldcore-stalk
description: >-
  Use when the user wants the stalk architecture — nested, braided stalks with variable length
  + girth, attachment topology as design freedom, near-field frequency coupling. Triggers:
  "stalk", "braid", "nested stalk", "attachment topology", "near-field frequency".
---

# FieldCore Stalk Architecture

The stalk is the **fundamental element** of the substrate. Nested stalks with variable length + girth, braided, attached at variable points on the toroid.

## What it is

- A **stalk** is a 1-dim curve through the substrate with attached fields (scalar + vector + tensor).
- Stalks **braid** — multiple stalks cross + twist + share geometric neighborhood.
- Stalks **attach** at variable points on the toroidal manifold.
- Stalks **oscillate** — frequency is a load-bearing channel (not a state variable).

## Why frequency is load-bearing

Per Bobby 2026-09-11:

> "frequency was a late addition not fully proofed yet... we attempt to enhance as interference patterns eecs ie signal processing but within a stalk to stalk base way past attachment waving ie near field interactions which since braided makes perfect sense and the info carrying potential is immense i feel a key addition must make sense of it freqeuency not optional how does brain use or neurons its a feature"

- frequency was a late addition (added 2026-09-08)
- interference patterns = amplitude/phase/frequency multiplexing
- near-field (not point-to-point) — enabled by braided stalks already sharing geometric neighborhood
- brain/neurons use frequency: spike trains, phase coding, ephaptic coupling

## Files

| Path | What |
|---|---|
| `src/stalk_control.py` | Stalk data structure + measured REINFORCE reward curve |
| `src/stalk_topology.py` | Topology math |
| `src/substrate.py` | Substrate-level operations |
| `notes/analogies/stalk-architecture-2026-09-08.md` | Bobby's framing |

## Surface

```python
from fieldcore.src.stalk_control import Stalk, StalkConfig
from fieldcore.src.stalk_topology import braid, attach

# create
s1 = Stalk.curve(length=10, girth=0.1)
s2 = Stalk.curve(length=12, girth=0.1)

# braid
b = braid(s1, s2, twist=π/4)

# attach to toroid
attach(b, manifold=toroid, point=(θ=0.5, φ=0.3))

# oscillate
s1.oscillate(frequency=440, amplitude=0.05)
```

## See also

- `fieldcore-tiny-core` — the kernel
- `simself-identity` — uses stalks as substrate
- `docs/research-papers/stalk-architecture-v6-1-2026-09-15.md` (in fieldcore repo)