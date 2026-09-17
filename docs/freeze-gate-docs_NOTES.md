# Design Notes 📝

Working notes behind freeze-gate's design decisions and recent changes.
The normative rules live in [SPEC.md](SPEC.md); this file records the *why*.

---

## Recent changes (v0.2.0)

- 📝 **CI on PR/push.** `.github/workflows/ci.yml` installs `pip install -e ".[dev]"`
  and runs pytest on Python 3.10 and 3.12, then `freeze-gate verify --strict`
  against the example core.
- 📝 **FG-004 treats empty `modifications` as a "none" claim.** The gate used
  Python truthiness, so `[]` was flagged as unlabeled — the opposite of the
  spec. Missing/null `modifications` still WARNs.
- 📝 **Repo built out from concept to working reference implementation.** The
  one-line README became a full project: spec, JSON Schema, Python package,
  CLI, tests, and a runnable example under `examples/ara-core-example/`.
- 📝 **Gate checks got stable IDs (FG-001 … FG-005).** Logs and CI pipelines
  can now match on check IDs instead of parsing prose. IDs are append-only —
  retired checks keep their number.
- 📝 **WARN tier introduced.** Early sketches had only pass/fail. That forced
  a bad choice for unlabeled-but-intact cores: either block them (too harsh
  for internal experiments) or wave them through (dishonest). WARN plus
  `--strict` lets each deployment pick its own posture.
- 📝 **Stray-file detection (FG-003) added.** Digest checks alone only prove
  the *listed* files are intact; they say nothing about files added after the
  freeze. A planted config file next to verified weights is still a compromise.
- 📝 **Empty cores are unfreezable.** `build_manifest` raises rather than
  emitting a manifest with zero artifacts — an empty freeze verifies trivially
  and means nothing.

## Decisions & rationale

### Why the manifest lives inside the core

Sidecar manifests get separated from their cores the moment someone `scp`s the
directory. Embedding `freeze-manifest.json` in the core root makes every copy
self-describing. The cost: the manifest can't list itself (self-referential
digest), which is why authentication of the manifest is delegated to signing
(future work) rather than inclusion.

### Why "honest labeling" is a first-class gate check

Integrity without honesty is a half-guarantee. A core can be byte-perfect and
still misrepresent itself — a fine-tuned model shipped as "stock", a swapped
base model behind an unchanged persona. FG-004 makes the label part of what
the gate inspects, and the `label` command renders it as a card so the claim
is one command away, always.

### Why empty `modifications` ≠ missing `modifications`

`[]` is a signed statement: *nothing was changed*. A missing/null field is an
evasion: *we're not saying*. The schema requires the key to exist so silence
is never ambiguous.

### Why WARN doesn't block by default

The gate is meant to sit in load paths. If unattributed dev freezes hard-fail
in a scratch environment, people route around the gate entirely — and then
production inherits the workaround. Default-permissive on honesty gaps with
`--strict` for production keeps the gate in the loop everywhere.

### Why sha256 (and only sha256, for now)

Single-algorithm manifests keep verification code path-free of negotiation
logic (no "attacker picks the weakest listed hash" issues). If sha256 ever
needs replacing, that's a `manifest_version` bump, not a per-manifest option.

## Known gaps / open questions

- **Manifest tampering.** An attacker who can rewrite artifacts can rewrite
  the manifest to match. The gate currently proves *consistency*, not
  *authenticity*. Signing (SPEC §7) is the planned close; until then, pair the
  gate with a trusted channel for manifests (e.g. pinned digests in the deploy
  config).
- **Symlinks and permissions** are not recorded. Fine for flat artifact
  bundles; revisit if cores start carrying executable trees.
- **Large cores.** Hashing is streamed (1 MiB chunks) so memory is flat, but
  multi-hundred-GB weight shards may want parallel hashing. Not needed yet.
- **Should `frozen_at` drift matter?** A manifest whose timestamp is in the
  future is suspicious. Considering an FG-006 sanity check; leaning WARN.
