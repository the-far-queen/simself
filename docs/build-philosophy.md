# Build philosophy (2026-09-05)

**Bobby's rule:**
- A method is fiction. It works.
- Especially true for Python and Rust code beyond the geometric core.
- We build a model by whatever means necessary.
- Not required to be elegant.
- Topology is an idea.

**Implications:**
- Don't gate engineering on geometric purity. If a Rust crate solves the problem, use it.
- Snippets from GitHub > writing from scratch. Even if the snippet is ugly, even if it uses bad patterns.
- "Constitutional" / "sheaf" / "harmonic" framing is inspiration, not constraint. The kernel can be ugly as long as it works.
- Don't refuse a working solution because it doesn't match the FieldCore topology. Topology is one idea among many.

**In practice:**
- Pure-Python `fieldcore_unified.py` shipped because it works, not because it has elegant sheaf structure
- Modal field controller v3.5 stays as-is (numerical patches are pragmatic, not pure)
- stalk_control.py has hash() for cache keys, magic constants in weights — fine
- Future implementations: same rule. Working > elegant. Topology as lens, not law.

**Counter-rule (still active):**
- Speculative claims about geometric phenomena being engineering still get flagged (rust-as-2,3)
- What's load-bearing vs decorative: separate, by judgment, narrate in vault

---
*Captured 2026-09-05 in conversation. Operating rule.*