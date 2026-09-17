# freeze-gate Specification

**Manifest format version:** `1.0` · **Spec status:** Draft · **Last updated:** 2026-09-11

This document is the normative reference for the freeze manifest format and the
gate checks. The JSON Schema in [`schema/freeze-manifest.schema.json`](../schema/freeze-manifest.schema.json)
encodes the structural rules; this document defines their semantics.

---

## 1. Terminology

| Term | Meaning |
|---|---|
| **Core** | A directory of artifacts that together make up one deployable unit — model weights, persona/config files, prompts. |
| **Frozen core** | A core that has been snapshotted: every file digested and recorded in a manifest. After freezing, the core MUST NOT change. |
| **Freeze manifest** | The `freeze-manifest.json` file written into the core root at freeze time. The single source of truth for what the core contains and claims to be. |
| **The gate** | The set of verification checks (FG-001 … FG-005) run against a frozen core before it is loaded, served, or redistributed. |
| **Honest labeling** | The requirement that a core plainly states what it is built on, what was changed, and what it is for — no silent substitutions, no unstated fine-tunes. |
| **Root freeze** | A freeze with no parent core (`provenance.parent_core` is `null`). |

## 2. Design principles

1. **The manifest travels with the core.** It lives inside the core directory, so the core is self-describing wherever it is copied.
2. **The manifest never lists itself.** Its own digest would be self-referential; the manifest is authenticated by signing (future work, §7), not by inclusion.
3. **Absence is a claim.** An empty `modifications` array is an explicit statement of "no modifications" — different from a missing label, which the gate flags.
4. **Integrity failures are FAIL; honesty gaps are WARN.** A byte that changed voids the freeze outright. A missing label leaves the bytes intact but the story incomplete — callers decide via `--strict` whether that is acceptable.
5. **Check IDs are stable.** `FG-xxx` identifiers are never renumbered or reused, so tooling and logs can rely on them across versions.

## 3. Manifest format

Top-level shape (all five keys REQUIRED):

```json
{
  "manifest_version": "1.0",
  "core":       { "id": "...", "version": "...", "frozen_at": "..." },
  "labeling":   { "base_model": "...", "modifications": [], "intended_use": "..." },
  "provenance": { "parent_core": null, "frozen_by": "..." },
  "artifacts":  [ { "path": "...", "sha256": "...", "bytes": 0 } ]
}
```

### 3.1 `manifest_version`

The version of this format. Gates MUST refuse manifests whose version they do
not speak (FG-001). Currently `"1.0"`.

### 3.2 `core`

| Field | Type | Rules |
|---|---|---|
| `id` | string | Stable identifier across freezes of the same lineage, e.g. `ara-core`. Non-empty. |
| `version` | string | Identifies this particular freeze. Non-empty. Recommended: semver. |
| `frozen_at` | string | ISO 8601 UTC timestamp of the freeze. |

### 3.3 `labeling` — the honest label

| Field | Type | Rules |
|---|---|---|
| `base_model` | string \| null | What the core is built on, stated plainly. `null` ⇒ FG-004 WARN. |
| `modifications` | array of string | Every modification applied to the base (fine-tunes, overlays, prompt pinning…). Empty array = explicit "none". |
| `intended_use` | string \| null | What the core is for. `null` ⇒ FG-004 WARN. |

Additional labeling fields are permitted and preserved; the gate only enforces
the three above.

### 3.4 `provenance`

| Field | Type | Rules |
|---|---|---|
| `parent_core` | string \| null | `id@version` of the freeze this one derives from. `null` marks a root freeze and is legitimate. |
| `frozen_by` | string \| null | Who performed the freeze. `null` ⇒ FG-005 WARN (unattributed freeze). |

### 3.5 `artifacts`

One entry per regular file in the core, excluding `freeze-manifest.json` itself.
MUST contain at least one entry — an empty core cannot be frozen.

| Field | Type | Rules |
|---|---|---|
| `path` | string | POSIX-style path relative to the core root. |
| `sha256` | string | Lowercase hex SHA-256 of the file contents (64 chars). |
| `bytes` | integer | File size at freeze time, ≥ 0. |

## 4. Gate checks

| ID | Name | Failure mode | Severity |
|---|---|---|---|
| **FG-001** | Manifest structure | Required keys missing, unsupported `manifest_version`, empty `core` fields, or an empty/non-list `artifacts` array. Short-circuits all other checks. | FAIL |
| **FG-002** | Artifact digests | A listed artifact is missing from disk or its SHA-256 does not match. | FAIL |
| **FG-003** | Freeze integrity | A file exists in the core that is not listed in the manifest (the bundle mutated after freeze). | FAIL |
| **FG-004** | Honest labeling | `base_model` or `intended_use` is null/empty, or `modifications` is null/absent. An empty `modifications` array is a valid "none" claim and PASSes. | WARN |
| **FG-005** | Provenance chain | `frozen_by` is null/empty — nobody is accountable for the freeze. | WARN |

### 4.1 Verdict

The gate verdict is the worst status observed: any FAIL ⇒ **FAIL**; otherwise
any WARN ⇒ **WARN**; otherwise **PASS**.

### 4.2 Exit codes (CLI)

| Verdict | `verify` | `verify --strict` |
|---|---|---|
| PASS | 0 | 0 |
| WARN | 0 | 2 |
| FAIL | 1 | 1 |

## 5. Freeze procedure

1. Assemble the core directory with its final contents.
2. Run `freeze-gate freeze <dir>` with the full honest label (`--base-model`, `--modification`…, `--intended-use`) and provenance (`--parent`, `--frozen-by`).
3. The tool walks the directory, digests every file, and writes `freeze-manifest.json` into the core root.
4. From this moment the core is frozen: any byte change, deletion, or addition will trip the gate.

Re-freezing a modified core is done by bumping `core.version` and setting
`provenance.parent_core` to the previous `id@version` — never by editing an
existing manifest in place.

## 6. Gate placement

The gate SHOULD run at every trust boundary:

- **Load time** — before a serving process reads the core.
- **Transfer time** — after copying a core between hosts or registries.
- **Audit time** — periodically, to detect drift on long-lived deployments.

## 7. Future work (not yet normative)

- **Signing** — detached signature over the canonical manifest bytes (minisign/sigstore), closing the "attacker edits manifest + files together" gap. Tracked in [NOTES.md](NOTES.md).
- **Lineage walking** — `freeze-gate lineage` resolving `parent_core` chains across a registry of manifests.
- **Manifest format 1.1** — optional `environment` block (freezer toolchain versions) under discussion.
