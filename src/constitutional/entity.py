"""
entity.py — High-fidelity entity recognition via constitutional consonance.

A text or vector is "entity" iff the average consonance across all 20 axes
exceeds a threshold (default 0.58). Signatures are cosine-matched against
known entities (threshold 0.85) for re-identification.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

import numpy as np

from .constitution import Constitution, cosine, embed_text, project_to_constitution, _TOKEN_RE, _STOPWORDS


class EntityRecognition:
    """Recognize and track entities via constitutional vector signatures."""

    def __init__(self, constitution: Constitution, threshold: float = 0.58, min_tokens: int = 2):
        self.constitution = constitution
        self.threshold = threshold
        self.min_tokens = min_tokens
        self.known_entities: Dict[str, Dict[str, Any]] = {}
        self._counter = 0

    def recognize(self, text_or_vector, is_text: bool = True) -> Dict[str, Any]:
        if is_text:
            tokens = [t for t in _TOKEN_RE.findall(str(text_or_vector).lower()) if t not in _STOPWORDS]
            if len(tokens) < self.min_tokens:
                return {"is_entity": False}
            vector = project_to_constitution(embed_text(str(text_or_vector)))
        else:
            vector = np.asarray(text_or_vector, dtype=np.float64)
            if vector.shape[0] != self.constitution.dim:
                vector = np.resize(vector, self.constitution.dim)
            n = np.linalg.norm(vector)
            vector = vector / n if n > 1e-9 else vector

        axis_scores = {
            name: self.constitution.consonance(vector, name)
            for name in self.constitution.axis_names
        }
        avg = sum(axis_scores.values()) / len(axis_scores)
        is_entity = avg > self.threshold

        entity_id, entity_type = None, "unknown"
        for eid, data in self.known_entities.items():
            if cosine(vector, np.array(data["signature"])) > 0.85:
                entity_id = eid
                entity_type = data.get("type", "known")
                break

        if is_entity and entity_id is None:
            self._counter += 1
            entity_id = f"entity_{self._counter}"
            self.known_entities[entity_id] = {
                "signature": vector.tolist(),
                "coherence": avg,
                "type": "new",
                "first_seen": time.time(),
                "axis_scores": axis_scores,
            }
            entity_type = "new"

        return {
            "is_entity": is_entity,
            "coherence_score": avg,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "axis_scores": axis_scores,
        }
