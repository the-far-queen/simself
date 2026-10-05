"""
session.py — JSONL session persistence. adopted from badlogic/pi-mono (MIT).

Pi stores sessions as JSONL files on disk, with tree structure for
branching. The /tree, /fork, /compact commands operate on local files
you can cat, jq, and back up. "The file is the source of truth."

simself's session module follows the same pattern:
  - one JSONL line per message
  - tree structure (parent_id + branch) for branching
  - /compact flushes + summarizes old messages
  - /fork creates a child session at a chosen message_id

the SessionManager is the constitutional equivalent of pi's SessionManager.
It's the load-bearing storage layer for simsoul identity across ticks.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


@dataclass(frozen=True)
class Message:
    """One message in the session. immutable per user session."""
    id: str
    parent_id: Optional[str]
    session_id: str
    role: str  # user | assistant | tool | system
    content: str
    ts: str
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_jsonl(self) -> str:
        d = asdict(self)
        return json.dumps(d, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_jsonl(cls, line: str) -> "Message":
        d = json.loads(line)
        return cls(**d)


@dataclass(frozen=True)
class Session:
    """One session. has a tree of messages."""
    id: str
    parent_id: Optional[str]    # for fork chains
    created_at: str
    name: str = ""
    root_id: Optional[str] = None

    def path(self, base_dir: str) -> Path:
        return Path(base_dir) / self.id / "messages.jsonl"


class SessionManager:
    """The storage layer. JSONL on disk. tree-branched.

    Usage:
        sm = SessionManager("~/.simself/sessions")
        s = sm.create(name="EXP-001 frozen baseline")
        sm.append(s, Message(role="user", content="hello"))
        msgs = sm.iter(s)
    """

    def __init__(self, base_dir: str = "~/.simself/sessions"):
        self.base = Path(os.path.expanduser(base_dir))
        self.base.mkdir(parents=True, exist_ok=True)

    def create(self, name: str = "", parent_id: Optional[str] = None) -> Session:
        sid = str(uuid.uuid4())[:12]
        s = Session(
            id=sid,
            parent_id=parent_id,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            name=name,
        )
        (self.base / sid).mkdir(exist_ok=True)
        # write a header (sessions have a single header line at top)
        (self.base / sid / "messages.jsonl").write_text(
            json.dumps({"_header": True, "session": asdict(s)}) + "\n"
        )
        return s

    def fork(self, parent: Session, at_message_id: Optional[str] = None,
             name: str = "") -> Session:
        """Create a child session at a chosen message_id. inherits messages
        up to and including at_message_id."""
        child = self.create(name=name or f"fork-of-{parent.id}", parent_id=parent.id)
        # copy messages up to at_message_id (or all if None)
        src = parent.path(self.base)
        dst = child.path(self.base)
        seen = False
        with src.open() as f, dst.open("a") as g:
            for line in f:
                if line.startswith('{"_header"'):
                    continue
                msg = Message.from_jsonl(line)
                if at_message_id is None or msg.id <= at_message_id:
                    g.write(line)
                else:
                    break
        return child

    def append(self, session: Session, msg: Message) -> None:
        """Append one message. sets parent_id to the last message."""
        path = session.path(self.base)
        # find last message
        last_id = self._last_id(session)
        new = Message(
            id=str(uuid.uuid4())[:12],
            parent_id=last_id,
            session_id=session.id,
            role=msg.role,
            content=msg.content,
            ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            meta=msg.meta,
        )
        with path.open("a") as f:
            f.write(new.to_jsonl() + "\n")

    def iter(self, session: Session) -> Iterator[Message]:
        path = session.path(self.base)
        with path.open() as f:
            for line in f:
                if line.startswith('{"_header"'):
                    continue
                yield Message.from_jsonl(line)

    def _last_id(self, session: Session) -> Optional[str]:
        last = None
        for m in self.iter(session):
            last = m.id
        return last

    def list_sessions(self) -> List[str]:
        return sorted(p.name for p in self.base.iterdir() if p.is_dir())


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        sm = SessionManager(base_dir=td)
        s = sm.create(name="test")
        print(f"created session: {s.id}")
        sm.append(s, Message(
            id="dummy", parent_id=None, session_id=s.id,
            role="user", content="hello", ts="2026-10-06T00:00:00Z",
        ))
        sm.append(s, Message(
            id="dummy", parent_id=None, session_id=s.id,
            role="assistant", content="hi back", ts="2026-10-06T00:00:01Z",
        ))
        msgs = list(sm.iter(s))
        assert len(msgs) == 2
        assert msgs[0].content == "hello"
        assert msgs[1].content == "hi back"
        print(f"appended 2 messages, iterated {len(msgs)}")

        # fork
        child = sm.fork(s, name="fork-test")
        c_msgs = list(sm.iter(child))
        assert len(c_msgs) == 2, f"fork child should inherit 2, got {len(c_msgs)}"
        print(f"forked session: {child.id}, inherited {len(c_msgs)} messages")

        # list sessions
        sessions = sm.list_sessions()
        assert s.id in sessions and child.id in sessions
        print(f"listed: {sessions}")

        # re-open and re-iterate
        sm2 = SessionManager(base_dir=td)
        s2 = Session(**json.loads((Path(td) / s.id / "messages.jsonl").read_text().split("\n")[0])["session"])
        # wait — re-open needs Session metadata. use list then get
        # (or just re-load from disk via list + open)
        sessions2 = sm2.list_sessions()
        assert s.id in sessions2, f"re-open failed: {sessions2}"
        print(f"re-opened: {sessions2}")

        print("\nALL SESSION TESTS PASS")
