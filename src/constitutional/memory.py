"""
memory.py — constitutional memory (per Grok master plan, full rewrite 2026-09-16).

Memory stores the items (admitted units), categories (short summaries), and
the typed graph (support, conflict, time, reference). It does NOT modify
ψ₀. The working state ψ is updated only by tick in the canonical SimSelf
class.

The previous version of this file had `update` methods that wrote through
the same paths the kernel uses. Per Grok: memory is a store, not a flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MemoryItem:
    id: str
    embedding_dim: int
    category: str = "uncategorized"
    committed: bool = False
    metadata: Dict = field(default_factory=dict)


class ConstitutionalMemory:
    """A simple store of memory items. Does not touch ψ₀."""

    def __init__(self):
        self.items: Dict[str, MemoryItem] = {}
        self.categories: Dict[str, List[str]] = {}

    def add_item(self, item: MemoryItem) -> None:
        self.items[item.id] = item
        self.categories.setdefault(item.category, []).append(item.id)

    def commit(self, item_id: str) -> bool:
        if item_id not in self.items:
            return False
        self.items[item_id].committed = True
        return True

    def get(self, item_id: str) -> Optional[MemoryItem]:
        return self.items.get(item_id)

    def by_category(self, category: str) -> List[str]:
        return list(self.categories.get(category, []))

    def decay_salience(self) -> None:
        """Stub. Salience decay is a maintenance task; does not modify ψ₀."""
        pass
