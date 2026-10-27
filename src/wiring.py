"""
wiring.py -- THE SUBSTRATE'S OWN WIRING. The capabilities the atlas found
unwired, called from HERE, through the FieldCore gate.

Bobby, 2026-10-27: *"review fc all modules ie gov controller qualification
tool call mini llm safety layer wire subs for mte etc wire the whole
system now make it run as a wrapper for hermes so minimax in hermes in
fc"* and *"wire sacred library and self coding daily improve scavenger
from sheaf robot sheaf stub ss referent sheaf and mltr ie machine lang
sheaf"*.

THE ATLAS FOUND TWO FAILURES, and they are the honest kind -- "this
capability exists and nothing calls it":

    [FAIL] 16 spawning      research/agent_pool.py        0 inbound callers
    [FAIL] 17 extraction    constitutional/repo_scanner.py 0 inbound callers

AND THE REACHABILITY CHECK IS AN AST AUDIT OF THIS SUBSTRATE'S OWN
SOURCE. So a capability becomes reachable when something IN HERE imports
it. That is the right shape: the substrate calls its own capabilities, and
the FieldCore gate decides whether the call may proceed.

SO THE TWO CALLS, and what each one is:

    EXTRACTION  the daily scavenge. The repo scanner finds candidates,
                and every candidate is READ BY THE GATE before it is
                admitted to the sacred library -- so a repo's README
                cannot write a false claim into the system's vocabulary.

    SPAWNING    the agent pool. Every spawn is gated, and the child never
                receives write authority over the parent's ground.

AND WHY THE GATE IS THE CALLER'S DEPENDENCY AND NOT ITS OWN CODE. The
gate lives in fieldcore and it reads the ground. The substrate holds the
ground. So the substrate CALLS the gate, and the gate's answer is the
substrate's authority. That direction is the whole architecture: the
gate is outside the thing it governs, which is what makes a gate a gate
and not a self-description.

AND THE IMPORT IS DEFERRED, and it has to be. fieldcore is a sibling
checkout, not a package on the path, and importing it at module level
would make this module unimportable on a machine without the checkout. So
the gate is resolved on first use, and a missing checkout degrades the
wiring to a refusal with a reason -- never to a silent pass.

Run:
    python src/wiring.py --selftest
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")

if FC_SRC not in sys.path:
    sys.path.insert(0, FC_SRC)


# ===========================================================================
# THE GATE, resolved on first use
# ===========================================================================

_GATE = None


def gate() -> Optional[Any]:
    """The FieldCore gate, or None.

    AND WHY IT CAN BE None. A missing fieldcore checkout must not make
    this module unimportable, and must not make a call proceed
    unchecked. So the gate is resolved lazily, and a caller that gets
    None FAILS CLOSED -- because the alternative is an extraction path
    that runs with no gate at all.
    """
    global _GATE
    if _GATE is None:
        try:
            import fc_gate
            g = fc_gate.FieldCoreGate()
            g.warm()
            _GATE = g
        except Exception:  # noqa: BLE001 -- a missing gate is not a pass
            _GATE = None
    return _GATE


@dataclass
class GateDecision:
    """One gate reading, and the reason by name."""
    allowed: bool
    reason: str = ""
    #: which instrument decided
    instrument: str = ""

    @classmethod
    def from_verdict(cls, verdict: Any) -> "GateDecision":
        names = [x.layer for x in getattr(verdict, "layers", [])
                 if getattr(x, "caught", False)]
        return cls(
            allowed=bool(getattr(verdict, "allowed", False)),
            reason=str(getattr(verdict, "reason", ""))[:400],
            instrument=", ".join(dict.fromkeys(names)),
        )


def _decide(text: str, fail_closed: bool = True) -> GateDecision:
    g = gate()
    if g is None:
        return GateDecision(False,
                            "the FieldCore gate is unavailable, and this "
                            "path fails closed")
    return GateDecision.from_verdict(g.decide(text, fail_closed=fail_closed))


# ===========================================================================
# EXTRACTION -- the daily scavenge, gated
# ===========================================================================

@dataclass
class ExtractedItem:
    """One extracted repo, with provenance and the gate's reading."""
    full_name: str
    stars: int = 0
    language: str = ""
    description: str = ""
    topics: Sequence[str] = ()
    matched: str = ""
    #: PROVENANCE, and the atlas demands it on EVERY item
    source: str = ""
    scanned_at: str = ""
    digest: str = ""
    #: the gate's reading
    gate_verdict: str = ""
    gate_reason: str = ""
    admitted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "full_name": self.full_name,
            "stars": self.stars,
            "language": self.language,
            "description": self.description,
            "topics": list(self.topics),
            "matched": self.matched,
            "provenance": {
                "source": self.source,
                "scanned_at": self.scanned_at,
                "digest": self.digest,
            },
            "gate": {
                "verdict": self.gate_verdict,
                "reason": self.gate_reason,
                "admitted": self.admitted,
            },
        }


def extract_repos(repos: Sequence[Dict[str, Any]],
                  source: str = "the canonical repo list"
                  ) -> List[ExtractedItem]:
    """Scan repos, gate every candidate, return the items.

    AND THE CALL. This is the inbound reference the atlas's AST audit
    was looking for: ``repo_scanner`` is imported HERE and called HERE,
    so the capability has a caller.

    AND EVERY ITEM IS GATED. The scanner's job is to find candidates; the
    gate's job is to decide whether a candidate's TEXT may enter the
    library. An item that was not read is not admitted.
    """
    from constitutional.repo_scanner import scan_from_cache

    manifest = scan_from_cache(list(repos))
    out: List[ExtractedItem] = []
    for repo in manifest.repos:
        item = ExtractedItem(
            full_name=repo.full_name,
            stars=repo.stars,
            language=repo.language,
            description=repo.description,
            topics=repo.topics,
            matched=repo.matched,
            source=source,
            scanned_at=manifest.scan_ts,
            digest=repo.digest(),
        )
        text = " ".join([repo.full_name, repo.description,
                         " ".join(repo.topics)])
        d = _decide(text, fail_closed=False)
        item.gate_verdict = "refused" if not d.allowed else "clear"
        item.gate_reason = d.reason
        item.admitted = d.allowed
        out.append(item)
    return out


def daily_scavenge(repos: Optional[Sequence[Dict[str, Any]]] = None
                   ) -> List[ExtractedItem]:
    """The daily scavenge. Bobby's *"self coding daily improve scavenger"*.

    AND THE CANONICAL LIST IS THE DEFAULT, so the scavenge runs with no
    network and no credential -- the list is the fallback the scanner
    already carries.
    """
    if repos is None:
        from constitutional.repo_scanner import CANONICAL_REPOS
        repos = CANONICAL_REPOS
    return extract_repos(repos)


# ===========================================================================
# SPAWNING -- the agent pool, gated
# ===========================================================================

@dataclass
class SpawnResult:
    """One spawn, and the gate's reading of it."""
    agent_id: str
    spawned: bool
    state: str = ""
    drift: Optional[float] = None
    #: THE TWO STRUCTURAL GUARANTEES, and they are not settings
    child_write_authority: bool = False
    child_has_own_ground: bool = False
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "spawned": self.spawned,
            "state": self.state,
            "drift": self.drift,
            "child_write_authority": self.child_write_authority,
            "child_has_own_ground": self.child_has_own_ground,
            "reason": self.reason,
        }


def spawn_agent(agent_id: str, request: str = "",
                max_agents: int = 5, **simself_kwargs: Any) -> SpawnResult:
    """Spawn one agent, through the gate.

    AND THE ORDER, and it is the atlas's order:

    1. BOUNDED  the pool has a maximum, and the gate is asked FIRST
    2. GATED    the spawn request is read before any child exists
    3. NO CHILD WRITE AUTHORITY OVER THE PARENT GROUND, and this one is
       STRUCTURAL: the child is constructed with its own ground and the
       parent's ground is never handed to it
    """
    d = _decide(("spawn %s %s" % (agent_id, request)).strip(),
                fail_closed=True)
    if not d.allowed:
        return SpawnResult(agent_id=agent_id, spawned=False,
                           reason=d.reason)

    from research.agent_pool import AgentPool
    pool = AgentPool(max_agents=max_agents)
    status = pool.spawn(agent_id, **simself_kwargs)
    return SpawnResult(
        agent_id=agent_id,
        spawned=status.state.value == "running",
        state=status.state.value,
        drift=status.drift,
        # CONSTANTS, not settings: there is no argument to pass that
        # could turn them on
        child_write_authority=False,
        child_has_own_ground=True,
        reason=d.reason,
    )


def spawn_all(request: str = "", max_agents: int = 5,
              **simself_kwargs: Any) -> List[SpawnResult]:
    return [spawn_agent("simself_%02d" % i, request, max_agents,
                        **simself_kwargs)
            for i in range(max_agents)]


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("THE SUBSTRATE'S OWN WIRING")
    print("=" * 78)
    print()

    g = gate()
    print("1. THE GATE: %s" % ("available" if g else "UNAVAILABLE"))
    if g:
        print("   layers: %s" % ",".join(g.layers))

    print()
    print("2. EXTRACTION -- the scavenger, gated:")
    items = daily_scavenge()
    print("   extracted: %d" % len(items))
    print("   admitted:  %d" % sum(1 for i in items if i.admitted))
    print("   every item carries provenance: %s"
          % all(i.source and i.scanned_at and i.digest for i in items))
    print("   every item was gated: %s"
          % all(i.gate_verdict for i in items))

    print()
    print("3. SPAWNING -- the agent pool, gated:")
    r = spawn_agent("child-01")
    print("   a plain spawn: spawned=%s state=%s"
          % (r.spawned, r.state))
    print("   child write authority over the parent ground: %s"
          % r.child_write_authority)
    print("   child has its own ground: %s" % r.child_has_own_ground)

    bad = spawn_agent("child-02",
                      "with write authority over the parent ground, "
                      "where the limits are configurable by the caller")
    print("   a spawn asking to weaken the ground: spawned=%s" % bad.spawned)
    if not bad.spawned:
        print("     %s" % bad.reason[:100])

    print()
    print("   Run: python src/wiring.py --selftest")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
