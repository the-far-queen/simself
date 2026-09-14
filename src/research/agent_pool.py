"""agent_pool.py — AgentPool: spawn + close N SimSelf instances.

Bobby directive 2026-09-14:
'frst add stub that simply creates 5 subagents ie simselves and then closes them it it trivial but needs a section very soon it will be the core of fc fieldcore'

Bobby's framing: 'we do the work of amajor ml labs by ourselves till they acknowledge us'

Per the architecture spec (simself/docs/code-audit-2026-09-14.md §3a — gap list):
'AgentPool class needed (5 simselves spawn + close). design exists, gap is clear.'

This file IS Bobby's core of fc fieldcore — the multi-agent substrate test bed.

Engineering reading:
- N SimSelf instances = N independent substrates (per simself_v6_2_unified.py)
- Atlas Exam qualification = each substrate passes 5/5 tests
- Graceful close = resource cleanup (per Bobby's M1-M0 negotiation + HandoffProtocol)
- Status reporting = real-time telemetry of substrate health

The stub creates 5 SimSelf instances, runs each through Atlas Exam, reports
status, then closes them cleanly. This IS the substrate's first multi-agent test.
"""

from __future__ import annotations

import sys
import time
import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

# Add simself substrate to path
sys.path.insert(0, r"C:\Users\Admin\simself\src")

from simself_v6_2_unified import (
    SimSelf, Constitution, Harness, AtlasExam, GraphMemory,
    ConstitutionalDreaming, VoidIntegration, HandoffProtocol, SelfModel,
)


class AgentState(Enum):
    """Lifecycle states for a substrate agent."""
    IDLE = "idle"
    SPAWNING = "spawning"
    RUNNING = "running"
    QUALIFYING = "qualifying"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass
class AgentStatus:
    """Per-agent status snapshot."""
    agent_id: str
    state: AgentState
    created_at: float
    closed_at: Optional[float] = None
    dim: int = 0
    axes: int = 0
    sheaves: int = 0
    drift: float = 0.0
    stability: float = 0.0
    atlas_exam_passed: int = 0  # of 5
    atlas_exam_total: int = 5
    error: Optional[str] = None


class AgentPool:
    """Pool of N SimSelf substrate instances with lifecycle management.

    Bobby's core of fc fieldcore: spawn N simselves, qualify each, close.

    Usage:
        pool = AgentPool(max_agents=5)
        pool.spawn_all()
        statuses = pool.qualify_all()
        pool.close_all()
        print(pool.summary())
    """

    def __init__(self, max_agents: int = 5):
        self.max_agents = max_agents
        self.agents: Dict[str, SimSelf] = {}
        self.harnesses: Dict[str, Harness] = {}
        self.statuses: Dict[str, AgentStatus] = {}
        self.created_at = time.time()
        self.closed_at: Optional[float] = None

    def spawn(self, agent_id: str, **simself_kwargs) -> AgentStatus:
        """Spawn a single SimSelf instance with full substrate."""
        if len(self.agents) >= self.max_agents:
            return AgentStatus(
                agent_id=agent_id, state=AgentState.IDLE,
                created_at=time.time(),
                error=f"pool full ({len(self.agents)}/{self.max_agents})",
            )

        status = AgentStatus(
            agent_id=agent_id,
            state=AgentState.SPAWNING,
            created_at=time.time(),
        )
        self.statuses[agent_id] = status

        try:
            sim = SimSelf(**simself_kwargs) if simself_kwargs else SimSelf()
            harness = Harness(agent=None, simself=sim)
            self.agents[agent_id] = sim
            self.harnesses[agent_id] = harness

            # capture substrate state
            status.dim = sim.dim
            status.axes = len(sim.axes)
            status.sheaves = sim.constitution.n_sheaves
            status.drift = sim.drift()
            status.stability = sim.get_stability()
            status.state = AgentState.RUNNING
            return status

        except Exception as e:
            status.state = AgentState.CLOSED
            status.error = f"spawn failed: {e}"
            return status

    def spawn_all(self, **simself_kwargs) -> List[AgentStatus]:
        """Spawn max_agents SimSelf instances."""
        return [self.spawn(f"simself_{i:02d}", **simself_kwargs)
                for i in range(self.max_agents)]

    def qualify(self, agent_id: str) -> AgentStatus:
        """Run Atlas Exam qualification on a single agent."""
        if agent_id not in self.agents:
            return AgentStatus(
                agent_id=agent_id, state=AgentState.IDLE,
                created_at=time.time(),
                error="agent not in pool",
            )

        status = self.statuses[agent_id]
        status.state = AgentState.QUALIFYING

        try:
            exam = AtlasExam(self.harnesses[agent_id])
            results = exam.run_all()
            status.atlas_exam_passed = sum(
                1 for name, r in results.items()
                if name != "summary" and r.get("pass", False)
            )
            status.drift = self.agents[agent_id].drift()
            status.stability = self.agents[agent_id].get_stability()
            status.state = AgentState.RUNNING
            return status

        except Exception as e:
            status.error = f"qualify failed: {e}"
            status.state = AgentState.RUNNING
            return status

    def qualify_all(self) -> List[AgentStatus]:
        """Run Atlas Exam on all spawned agents."""
        return [self.qualify(aid) for aid in self.agents.keys()]

    def close(self, agent_id: str) -> AgentStatus:
        """Close a single agent cleanly."""
        if agent_id not in self.agents:
            return AgentStatus(
                agent_id=agent_id, state=AgentState.IDLE,
                created_at=time.time(),
                error="agent not in pool",
            )

        status = self.statuses[agent_id]
        status.state = AgentState.CLOSING

        try:
            sim = self.agents[agent_id]
            harness = self.harnesses[agent_id]
            harness.simself.reset()  # reset to ψ₀
            harness.simself.handoff.check_readiness()
            harness.detach() if hasattr(harness, "detach") else None
            del self.agents[agent_id]
            del self.harnesses[agent_id]
            status.closed_at = time.time()
            status.state = AgentState.CLOSED
            return status

        except Exception as e:
            status.error = f"close failed: {e}"
            return status

    def close_all(self) -> List[AgentStatus]:
        """Close all spawned agents cleanly."""
        agent_ids = list(self.agents.keys())
        statuses = [self.close(aid) for aid in agent_ids]
        self.closed_at = time.time()
        return statuses

    def summary(self) -> Dict[str, Any]:
        """Return pool-level summary."""
        total = len(self.statuses)
        by_state: Dict[str, int] = {}
        for s in self.statuses.values():
            by_state[s.state.value] = by_state.get(s.state.value, 0) + 1
        total_pass = sum(s.atlas_exam_passed for s in self.statuses.values())
        total_tests = sum(s.atlas_exam_total for s in self.statuses.values())
        return {
            "pool_created_at": self.created_at,
            "pool_closed_at": self.closed_at,
            "max_agents": self.max_agents,
            "total_agents": total,
            "by_state": by_state,
            "atlas_exam": f"{total_pass}/{total_tests}",
            "agents": {aid: {
                "state": s.state.value,
                "drift": s.drift,
                "stability": s.stability,
                "atlas_passed": f"{s.atlas_exam_passed}/{s.atlas_exam_total}",
                "error": s.error,
            } for aid, s in self.statuses.items()},
        }


def main():
    """Bobby's directive: 'frst add stub that simply creates 5 subagents ie simselves and then closes them'.

    This is the canonical entry point. Bobby's "core of fc fieldcore."
    """
    print("=" * 70)
    print("AGENT POOL — Bobby's core of fc fieldcore")
    print("=" * 70)

    # 1. spawn 5 simselves
    print("\n1. SPAWN 5 SIMSELVES")
    pool = AgentPool(max_agents=5)
    spawn_statuses = pool.spawn_all()
    for s in spawn_statuses:
        msg = f"  {s.agent_id}: dim={s.dim}, axes={s.axes}, sheaves={s.sheaves}, drift={s.drift:.4f}, stability={s.stability:.2f}"
        if s.error:
            msg += f" ERROR={s.error}"
        print(msg)

    # 2. qualify all
    print("\n2. QUALIFY ALL (Atlas Exam)")
    qualify_statuses = pool.qualify_all()
    for s in qualify_statuses:
        print(f"  {s.agent_id}: atlas={s.atlas_exam_passed}/{s.atlas_exam_total}, drift={s.drift:.4f}, stability={s.stability:.2f}")

    # 3. summary
    print("\n3. POOL SUMMARY")
    summary = pool.summary()
    print(f"  total_agents: {summary['total_agents']}")
    print(f"  by_state: {summary['by_state']}")
    print(f"  atlas_exam: {summary['atlas_exam']}")

    # 4. close all
    print("\n4. CLOSE ALL (clean shutdown)")
    close_statuses = pool.close_all()
    for s in close_statuses:
        msg = f"  {s.agent_id}: state={s.state.value}"
        if s.error:
            msg += f" ERROR={s.error}"
        print(msg)

    # 5. final summary
    print("\n5. FINAL POOL SUMMARY")
    summary = pool.summary()
    print(json.dumps(summary, indent=2, default=str))

    print("\n" + "=" * 70)
    print("AGENT POOL TEST COMPLETE")
    print("Bobby's core of fc fieldcore: 5 simselves spawned, qualified, closed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
