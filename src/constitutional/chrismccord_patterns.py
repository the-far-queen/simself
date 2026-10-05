"""
chrismccord_patterns.py — Phoenix + LiveView patterns (chrismccord, Phoenix creator).

the patterns:
  1. LiveView: server-rendered HTML + WebSocket + minimal client JS
  2. Ecto: repository pattern + composable query DSL
  3. render_sync: real-time Rails partials (precursor to LiveView)

simself's adoption:
  1. constitutional gate = LiveView-style "server-rendered gate" with WS push
  2. constitutional state store = repository pattern (no raw SQL, just composition)
  3. constitutional snapshot push = real-time broadcast to subscribers
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# Pattern 1: LiveView — server-rendered + WebSocket push
# simself: the gate fires on the server. the agent receives state snapshots over WS.

class ConstitutionalSocket:
    """one WebSocket subscriber for constitutional state snapshots."""

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.last_sha = ""
        self.history: List[Dict[str, Any]] = []

    def push(self, snapshot: Dict[str, Any]) -> None:
        """server pushes the snapshot. client ignores if sha unchanged."""
        sha = snapshot.get("sha", "")
        if sha != self.last_sha:
            self.history.append(snapshot)
            self.last_sha = sha

    @property
    def count(self) -> int:
        return len(self.history)


# Pattern 2: Ecto — repository pattern + composable query DSL
# simself: constitutional store as a repository. no raw filesystem access; composition.

class Repo:
    """the Ecto repository pattern. queries compose. raw IO hidden."""

    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}

    def insert(self, table: str, record: Dict[str, Any]) -> str:
        rid = record.get("id") or hashlib.sha256(
            json.dumps(record, sort_keys=True).encode()
        ).hexdigest()[:16]
        record["id"] = rid
        self._data.setdefault(table, {})[rid] = record
        return rid

    def where(self, table: str, **filters) -> List[Dict[str, Any]]:
        """Ecto.where(table, axis=boundaries) — composable query."""
        out = []
        for r in self._data.get(table, {}).values():
            if all(r.get(k) == v for k, v in filters.items()):
                out.append(r)
        return out

    def preload(self, table: str, ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Ecto.preload — batch load by id list."""
        return {rid: self._data.get(table, {}).get(rid, {}) for rid in ids}


# Pattern 3: render_sync — real-time partial broadcast
# simself: constitutional snapshot broadcast on each tick.

class RenderSync:
    """the render_sync pattern: the server broadcasts state diffs as JSON.
    subscribers update their local view. WebSocket-equivalent for simself."""

    def __init__(self, repo: Repo):
        self.repo = repo
        self._subscribers: List[ConstitutionalSocket] = []
        self._tick_count = 0

    def subscribe(self, client_id: str) -> ConstitutionalSocket:
        sock = ConstitutionalSocket(client_id)
        self._subscribers.append(sock)
        return sock

    def push_state(self, axes: Dict[str, float]) -> Dict[str, Any]:
        """one tick. build the snapshot. broadcast to subscribers."""
        self._tick_count += 1
        canonical = json.dumps(axes, sort_keys=True)
        sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        snapshot = {
            "tick": self._tick_count,
            "axes": axes,
            "sha": sha,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        # persist via repo
        self.repo.insert("snapshots", dict(snapshot, id=str(self._tick_count)))
        # broadcast
        for sub in self._subscribers:
            sub.push(snapshot)
        return snapshot


if __name__ == "__main__":
    # Pattern 1: WebSocket subscriber dedups by sha
    sock = ConstitutionalSocket("client-1")
    snapshot = {"sha": "abc123", "axes": {"coherence": 1.0}}
    sock.push(snapshot)
    sock.push(snapshot)  # same sha, ignored
    assert sock.count == 1, f"should dedupe: {sock.count}"
    sock.push({"sha": "def456", "axes": {"coherence": 0.5}})  # different sha
    assert sock.count == 2
    print(f"P1: ok (WebSocket dedup by sha, count={sock.count})")

    # Pattern 2: Ecto repo
    repo = Repo()
    rid1 = repo.insert("axes", {"name": "boundaries", "low": -0.5, "high": 0.5})
    rid2 = repo.insert("axes", {"name": "coherence", "low": 0.0, "high": 1.0})
    r1 = repo.where("axes", name="boundaries")
    assert len(r1) == 1 and r1[0]["name"] == "boundaries"
    print(f"P2: ok (Ecto where; found {len(r1)} axis named 'boundaries')")
    loaded = repo.preload("axes", [rid1, rid2])
    assert loaded[rid1]["name"] == "boundaries"
    assert loaded[rid2]["name"] == "coherence"
    print(f"P2.b: ok (Ecto preload; 2 records loaded)")

    # Pattern 3: render_sync
    rs = RenderSync(repo)
    s1 = rs.subscribe("client-1")
    snap = rs.push_state({"coherence": 1.0})
    assert snap["sha"] != ""
    assert snap["tick"] == 1
    # second push with same axes → same sha → dedup'd at subscriber
    rs.push_state({"coherence": 1.0})
    assert s1.count == 1  # dedup at subscriber
    # different axes → different sha → new snapshot at subscriber
    rs.push_state({"coherence": 0.5})
    assert s1.count == 2
    # repo has 3 snapshots (one per push_state call)
    assert len(repo.where("snapshots")) == 3
    print(f"P3: ok (render_sync: 3 server pushes, {s1.count} client receives after dedup)")

    print("\nALL CHRISMCCORD_PATTERNS TESTS PASS")
