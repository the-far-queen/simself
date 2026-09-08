# NOTICE — Vendored dependency

This directory contains the **Monolithic 102 equation set** by enuminous,
forked from https://github.com/enuminous/Monolithic_102_EFMW into
the simself project for reference and cross-referencing.

## Provenance

- **Source repo:** https://github.com/enuminous/Monolithic_102_EFMW
- **Author:** enuminous (https://github.com/enuminous)
- **Forked into simself:** 2026-09-08
- **Upstream commit at fork:** see .upstream_ref
- **License:** See upstream repo

## Use

These files are reference material for the simself project. They are
NOT covered by the simself LICENSE. Each .md file is preserved verbatim
from upstream.

## Updates

This is a vendored copy, not a git submodule. To sync with upstream:

```bash
cd /path/to/simself/src/efmw-corpus
rm -rf *
git clone https://github.com/enuminous/Monolithic_102_EFMW /tmp/efmw
cp /tmp/efmw/*.md .
echo "<new-commit-sha>" > .upstream_ref
cd /path/to/simself
git add src/efmw-corpus/
git commit -m "efmw-corpus: sync from upstream <sha>"
```

## Modifications

No equations have been modified. All ME-001 through ME-102 are preserved
verbatim per upstream's canonical numbering rule.

Files added by us (not in upstream):
- README.md (this directory's purpose)
- NOTICE.md (this file)

## See also

- `simself/src/efmw-corpus/README.md` — full integration notes
- `simself/docs/MATH.md` — Bobby's math framework
- `simself/src/coding_operator_object.py` — coding operator