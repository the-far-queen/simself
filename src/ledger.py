# Ledger — Append-only Wisdom Storage (Module L)

"""
Immutable record of experiences, axioms, and crystallized knowledge.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class LedgerEntry:
    """Single entry in the wisdom ledger."""
    
    def __init__(self, entry_type: str, content: Any, metadata: Optional[Dict] = None):
        self.id = f"{datetime.now().timestamp()}"
        self.timestamp = datetime.now().isoformat()
        self.entry_type = entry_type  # "experience", "axiom", "crystallized"
        self.content = content
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.entry_type,
            "content": self.content,
            "metadata": self.metadata
        }


class Ledger:
    """Append-only wisdom ledger."""
    
    def __init__(self, storage_path: str = "data/ledger.json"):
        self.storage_path = Path(storage_path)
        self.entries: List[LedgerEntry] = []
        self._load()
    
    def _load(self):
        """Load existing ledger."""
        if self.storage_path.exists():
            with open(self.storage_path) as f:
                data = json.load(f)
                self.entries = [LedgerEntry(e["type"], e["content"], e.get("metadata")) for e in data]
    
    def _save(self):
        """Persist ledger."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump([e.to_dict() for e in self.entries], f, indent=2)
    
    def add(self, entry_type: str, content: Any, metadata: Optional[Dict] = None):
        """Append new entry."""
        entry = LedgerEntry(entry_type, content, metadata)
        self.entries.append(entry)
        self._save()
        return entry.id
    
    def query(self, entry_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Query ledger entries."""
        results = self.entries
        if entry_type:
            results = [e for e in results if e.entry_type == entry_type]
        return [e.to_dict() for e in results[-limit:]]


# Example usage
if __name__ == "__main__":
    ledger = Ledger()
    ledger.add("axiom", "Truth before comfort", {"source": "swedenborgian"})
    ledger.add("experience", "Robot grasped water cup", {"coherence": 0.95})
    print(ledger.query())
