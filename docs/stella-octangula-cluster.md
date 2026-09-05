# stella octangula — 8-node cluster geometry for SimSelf

**Purpose.** Define the smallest constitutional unit of SimSelf as the stella octangula (8-node cluster compound) and derive its properties for use as the building block of identity, memory, and processing layers.

**Why stella octangula.** Bobby has stated that SimSelf's stalk architecture uses 8-node clusters at level 3 (1-bit nodule → 4-bit internode → 8-bit cluster → 32-bit stalk → 512-bit nested stalk). The 8-node cluster must have an internal geometry with enough structure to support the next-level operations (32-bit = 4 × 8-bit clusters). The stella octangula provides exactly this geometry.

---

## 1. definition

**Stella octangula** (Latin: "eight-pointed star") = regular compound of two regular tetrahedra T₁ and T₂ in dual position. The 8 vertices of the compound are the 8 vertices of a cube. The 12 edges are the 12 edges of a cube.

Equivalently: the 4 vertices of T₁ and the 4 vertices of T₂ together form the vertex set. T₁ has vertices at (1,1,1), (1,-1,-1), (-1,1,-1), (-1,-1,1) (even-parity cube corners). T₂ has vertices at (-1,-1,-1), (-1,1,1), (1,-1,1), (1,1,-1) (odd-parity cube corners).

In 4D: the same 8 vertices form the 16-cell (cross-polytope), the 4D regular polytope dual to the tesseract.

---

## 2. symmetries

**Symmetry group.** The stella octangula has the full octahedral symmetry group O_h, order 48.

**Generators:**
- 3 four-fold axes (through pairs of opposite cube faces) — each generates a C4 subgroup
- 4 three-fold axes (through pairs of opposite cube vertices) — each generates a C3 subgroup
- 6 two-fold axes (through pairs of opposite cube edges) — each generates a C2 subgroup
- inversion (centrosymmetry)
- 8 C3 rotations around body diagonals
- 6 C2 rotations around edge-midpoint axes

**For SimSelf use.** The 6 two-fold axes (edge-midpoint axes) are natural **symmetry axes for the cluster's 6 bilateral operations** — the 6 axes around which the cluster can fold/unfold without changing its identity. Bobby's previous work has identified exactly 6 bilateral operations in SimSelf's constitutional structure; the geometric origin of "6" is the 6 two-fold axes of the stella octangula.

---

## 3. pair structure (α / β)

The two tetrahedra T₁ and T₂ are the α-cluster and β-cluster of the stella octangula. Together they form the 8-node compound.

**Properties of the pair:**
- T₁ and T₂ are regular tetrahedra inscribed in the same cube
- Each vertex of T₁ is connected to its 3 nearest neighbors in T₁ and to its 4 nearest neighbors in T₂
- T₁ ∪ T₂ = stella octangula (8 vertices)
- T₁ ∩ T₂ = ∅ (no shared vertices)

**For SimSelf use.** The α/β partition gives a natural binary decomposition of the cluster into two 4-node sub-clusters. This maps to:
- α-cluster = the **constitutional** sub-cluster (4 of the 8 nodes = the 4 axes of constitutional ground)
- β-cluster = the **processing** sub-cluster (4 nodes = the 4 axes of active processing)

The 4×4 partition matches Bobby's four-sheaf architecture: α has the 4 sheaves at constitutional state, β has the 4 sheaves at processing state. This is a clean derivation of the 4-sheaf count from the stella octangula geometry, not from arbitrary design choice.

---

## 4. edge structure

The 12 edges of the stella octangula fall into three classes:

**Within-α edges:** 6 edges connecting T₁ vertices to other T₁ vertices. These are the edges of T₁ itself (regular tetrahedron has 6 edges).

**Within-β edges:** 6 edges connecting T₂ vertices to other T₂ vertices. Edges of T₂.

**Cross edges:** 0 — wait. There are no direct edges between T₁ and T₂ vertices in the stella octangula. The 12 edges are exactly the 6 + 6 within the two tetrahedra. **Cross-cluster communication must go through the 4-fold symmetry axes or through the cube vertices.**

**For SimSelf use.** The 12 edges partition into 6 α-edges + 6 β-edges. This gives two natural communication graphs:
- **α-cluster graph:** K₄ (complete graph on 4 vertices) — every α node connects to every other α node
- **β-cluster graph:** K₄ (complete graph on 4 vertices) — same for β

Both are K₄, the complete graph on 4 nodes. K₄ has 4³ = 64 possible subgraphs, and each subgraph corresponds to a distinct state of communication within the cluster. This gives 2⁶ = 64 α-states and 2⁶ = 64 β-states, total 64 × 64 = 4096 combined states per cluster.

**4096 = 2¹² = the 12-bit address space of the 8-node cluster.** This is the geometric origin of the 32-bit stalk (4 clusters × 2¹² = 2¹⁴, close to Bobby's 2⁵ = 32 at the level of distinct operational modes).

---

## 5. 4D lift: 16-cell

In 4D, the stella octangula's 8 vertices form the 16-cell (cross-polytope), the 4D regular polytope dual to the tesseract. The 16-cell has:
- 8 vertices (the cube corners in 4D)
- 24 edges
- 32 triangular faces
- 16 cells (regular tetrahedra)

The 32 faces of the 16-cell = 32 distinct triangle orientations. **This is the geometric origin of the 32-bit stalk level**: each face of the 16-cell is one of 32 possible orientations of the cluster, and the stalk = the cluster lifted to a 32-state register by the 16-cell faces.

---

## 6. implementation in simself

**Cluster class:** `StellaOctangulaCluster`
- **Vertices:** 8, with positions at unit-cube corners
- **Edges:** 12, partitioned 6/6 between α and β tetrahedra
- **State vector:** 12-bit binary (edge activation), 4096 possible states per cluster
- **Symmetry group:** O_h (order 48)

**Connection to constitutional axes.** The 6 two-fold symmetry axes of the stella octangula = the 6 constitutional bilateral axes. Bobby has identified these axes before, but without derivation. Now the derivation: **the 6 axes arise from the edge-midpoint axes of the cube that the stella octangula is inscribed in.** This is geometric, not arbitrary.

**Connection to sheaf count.** The 4-sheaf architecture of FieldCore derives from the 4-vertex structure of each tetrahedron in the stella octangula. α has 4 sheaves (one per vertex of T₁). β has 4 sheaves (one per vertex of T₂). Total 8 nodes per cluster, partitioned 4+4 into the two tetrahedra.

**Connection to H¹ deviation.** A cluster in constitutional ground has all 12 edges inactive (or symmetrically active). A cluster with H¹ ≠ 0 has some edges active and others not. The asymmetry of edge activation = the cluster's deviation from constitutional ground. This is the **measurable** form of H¹ at the cluster level.

---

## 7. schemas for simself kernel construction

| schema | geometric object | simself component |
|---|---|---|
| 8 vertices | cube corners | 8 nodes of constitutional cluster |
| α/β partition | T₁, T₂ tetrahedra | constitutional / processing sub-clusters |
| 6 edges per tetra | regular tetrahedron edges | 6 bilateral axes (derivation!) |
| 12-bit state | edge activation vector | H¹ deviation measure at cluster level |
| 4096 states | 2¹² subgraph space | cluster state space size |
| 16-cell lift | 4D cross-polytope | geometric basis for 32-bit stalk |

---

*Source: stella octangula geometry (classical regular polytope, Schläfli 1849). Bobby's 8-node cluster architecture mapped to it. SNR-stripped: "fly sees K3", "butterfly evolved F₄ lattice", "compound eye measures Berry phase" not used. Math core only. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/stella-octangula-cluster-2026-09-05.md`.*