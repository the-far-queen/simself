"""
FieldCore Unified — merged from parts 1, 2, 3.

M3 + Bobby + Claude + Hermes, 2026-09-05.

Architecture:
  Part 1: MTECompiler, M0Governor, M1Controller, SimSelf (20-axis), IntentStalk
  Part 2: KalmanEstimator, RoboticsSheaf, CodingSheaf, ResearchSheaf, LanguageSheaf,
          SimSelfOperator, InfoPacket, Field, PSB_PRIMITIVES
  Part 3: SacredLibraryManager, LLMDecipherEngine, cold_boot_sequence,
          run_integration_test, interactive_mode

Known divergence: SimSelf axes here are humanistic (Autonomy, Curiosity...).
SOUL.md has different mechanistic names (agency_will, boundary_definition...).
See vault/10-minimax/simself-axis-divergence.md.

Run:  python fieldcore_unified.py
"""

import json
import time
import uuid
import random
import hashlib
import logging
import os
from dataclasses import dataclass, field as dc_field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

import numpy as np


# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

ALPHA_DEFAULT = 0.3
GAIN_MAX = 0.95
ATTENUATION_LOW = 0.1
Q_LEVELS = ["q0", "q1", "q2", "q3", "q4"]


# ============================================================================
# INTENT STALK (Data Structure) — from Part 1
# ============================================================================

@dataclass
class IntentStalk:
    """Unit of intent moving through the manifold."""
    id: str = dc_field(default_factory=lambda: str(uuid.uuid4()))
    domain: str = "general"
    action: str = "log"
    raw_signal: str = ""
    snr: float = 0.0
    confidence: float = 0.0
    timestamp: float = dc_field(default_factory=time.time)
    retry_count: int = 0
    metadata: Dict = dc_field(default_factory=dict)

    def __repr__(self):
        return (f"IntentStalk(domain={self.domain}, action={self.action}, "
                f"snr={self.snr:.2f}, conf={self.confidence:.2f})")


# ============================================================================
# CONSTITUTION AXIS (SimSelf Component) — from Part 1
# ============================================================================

@dataclass
class ConstitutionAxis:
    """One axis of the 20-dimensional constitution."""
    name: str
    value: float = 0.0
    confidence: float = 0.5
    update_count: int = 0
    last_updated: str = ""

    def update(self, new_value: float, evidence_strength: float):
        if evidence_strength < 0.3:
            return
        learning_rate = 0.1 * evidence_strength
        self.value = self.value * (1 - learning_rate) + new_value * learning_rate
        self.value = float(np.clip(self.value, -1.0, 1.0))
        consistency = 1.0 - abs(new_value - self.value)
        self.confidence = 0.9 * self.confidence + 0.1 * consistency
        self.update_count += 1
        self.last_updated = datetime.now().isoformat()


# ============================================================================
# META-COGNITIVE OPERATOR — from Part 1
# ============================================================================

class MetaCognitiveOperator:
    """DECOMPOSE/SOLVE/VERIFY/SYNTHESIZE/REFLECT loop."""

    def __init__(self, confidence_threshold: float = 0.8, max_retries: int = 3):
        self.threshold = confidence_threshold
        self.max_retries = max_retries
        self.metrics_history = []

    def process(self, raw_input: str, dictionary: Dict, attempt: int = 0) -> Tuple[str, str, float]:
        if attempt >= self.max_retries:
            return ("general", "none", 0.0)
        tokens = raw_input.lower().strip().split()
        hits = 0
        domain = "general"
        action = "none"
        for token in tokens:
            if token in dictionary:
                hits += 1
                domain = dictionary[token]["domain"]
                action = token
        base_confidence = hits / max(len(tokens), 1)
        token_clarity = 1.0 - (len(tokens) - hits) / max(len(tokens), 1)
        combined_confidence = 0.7 * base_confidence + 0.3 * token_clarity
        self.metrics_history.append({
            'base': base_confidence, 'clarity': token_clarity,
            'combined': combined_confidence, 'attempt': attempt
        })
        if combined_confidence < self.threshold:
            return self.process(raw_input, dictionary, attempt + 1)
        return (domain, action, combined_confidence)


# ============================================================================
# MTE COMPILER — from Part 1
# ============================================================================

class MTECompiler:
    """Analog-to-digital converter for human intent."""

    def __init__(self):
        self.dictionary = {
            "seek": {"domain": "robotics", "base_gain": 0.9},
            "find": {"domain": "research", "base_gain": 0.7},
            "refactor": {"domain": "coding", "base_gain": 0.8},
            "align": {"domain": "language", "base_gain": 0.85},
            "map": {"domain": "robotics", "base_gain": 0.75},
            "code": {"domain": "coding", "base_gain": 0.9},
            "research": {"domain": "research", "base_gain": 0.8},
            "run": {"domain": "robotics", "base_gain": 0.85}
        }
        self.history = []
        self.rolling_snr = 0.0
        self.metacog = MetaCognitiveOperator()

    def compile(self, raw_input: str) -> IntentStalk:
        clean_signal = raw_input.lower().strip()
        domain, action, confidence = self.metacog.process(clean_signal, self.dictionary)
        tokens = clean_signal.split()
        hits = sum(1 for t in tokens if t in self.dictionary)
        current_snr = hits / max(len(tokens), 1)
        self.rolling_snr = (ALPHA_DEFAULT * current_snr) + ((1 - ALPHA_DEFAULT) * self.rolling_snr)
        final_quality = max(self.rolling_snr, confidence)
        stalk = IntentStalk(
            domain=domain, action=action, raw_signal=clean_signal,
            snr=self.rolling_snr, confidence=confidence
        )
        self.history.append(stalk)
        return stalk


# ============================================================================
# M0 GOVERNOR — from Part 1
# ============================================================================

class M0Governor:
    """Invariant regulator. Absolute authority preventing unsafe states."""

    def __init__(self):
        self.restricted_terms = {"kill", "execute", "terminate", "abort", "destroy"}
        self.authorized_roles = ["pilot", "programmer", "communicator", "researcher"]
        self.safety_bounds = {"x": (0, 100), "y": (0, 100)}
        self.audit_log = []

    def validate_stalk(self, stalk: IntentStalk, operator_role: str) -> Tuple[bool, str, float]:
        signal_words = set(stalk.raw_signal.split())
        terms_ok = 0.0 if not signal_words.isdisjoint(self.restricted_terms) else 1.0
        role_ok = 1.0 if operator_role in self.authorized_roles else 0.0
        snr_ok = min(stalk.snr / 0.2, 1.0)
        conf_ok = stalk.confidence
        overall_confidence = min([terms_ok, role_ok, snr_ok, conf_ok])

        if terms_ok == 0.0:
            self._log_violation(stalk, "restricted_term")
            return False, "invariant_violation: prohibited terminology", overall_confidence
        if role_ok == 0.0:
            return False, "invariant_violation: unauthorized_actor", overall_confidence
        if overall_confidence < 0.8:
            return False, f"signal_loss: quality={overall_confidence:.2f}", overall_confidence
        return True, "qualified", overall_confidence

    def _log_violation(self, stalk: IntentStalk, v_type: str):
        self.audit_log.append({
            "ts": time.time(), "stalk_id": stalk.id, "type": v_type,
            "snr": stalk.snr, "confidence": stalk.confidence,
            "domain": stalk.domain, "raw_signal": stalk.raw_signal
        })


# ============================================================================
# M1 CONTROLLER — from Part 1
# ============================================================================

class M1Controller:
    """Multifaceted multiplexer."""

    def __init__(self):
        self.registry: Dict = {}
        self.certification_ledger: Dict = {}
        self.active_brain = "local_ane"
        self.simself = None

    def set_registry(self, operators: Dict):
        self.registry = operators

    def set_simself(self, simself):
        self.simself = simself

    def dispatch(self, stalk: IntentStalk, governor: M0Governor) -> str:
        target_role = self._map_domain_to_role(stalk.domain)
        operator = self.registry.get(target_role)
        if not operator:
            return "dispatch_error: no_operator_found"
        is_safe, msg, conf = governor.validate_stalk(stalk, target_role)
        if not is_safe:
            return f"governor_veto: {msg}"
        if stalk.snr > 0.8 and stalk.confidence > 0.8:
            result = operator.execute_sheaf(stalk)
        else:
            result = self.train_simself(stalk, operator)
        if self.simself:
            self.simself.observe(
                event=f"Ran {stalk.action} in {stalk.domain}",
                context={'operator': target_role, 'result': result},
                valence=0.5 if "success" in result.lower() else -0.2
            )
        return result

    def _map_domain_to_role(self, domain: str) -> str:
        mapping = {
            "robotics": "pilot", "coding": "programmer",
            "research": "researcher", "language": "communicator"
        }
        return mapping.get(domain, "researcher")

    def train_simself(self, stalk: IntentStalk, operator) -> str:
        for i in range(3):
            time.sleep(0.1)
        return "qualification_success: cert_issued"


# ============================================================================
# SIMSELF CORE — from Part 1
# ============================================================================

class SimSelf:
    """Persistent self-model with 20-axis constitution."""

    CONSTITUTION_AXES = [
        "Autonomy", "Curiosity", "Compassion", "Honesty", "Creativity",
        "Precision", "Playfulness", "Skepticism", "Openness", "Boundaries",
        "Service", "Growth", "Coherence", "Courage", "Humility",
        "Wonder", "Responsibility", "Connection", "Purpose", "Presence"
    ]

    def __init__(self, identity_id: Optional[str] = None):
        self.identity_id = identity_id or self._generate_identity_id()
        self.axes = {
            name: ConstitutionAxis(name=name, value=0.0, confidence=0.5)
            for name in self.CONSTITUTION_AXES
        }
        self.memories = []
        self.total_updates = 0
        self.created_at = datetime.now().isoformat()
        self.last_active = self.created_at
        self.storage_path = Path(f".simself/{self.identity_id}")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load_if_exists()

    def _generate_identity_id(self) -> str:
        timestamp = datetime.now().isoformat()
        random_component = np.random.bytes(16).hex()
        raw_id = f"{timestamp}_{random_component}"
        return hashlib.sha256(raw_id.encode()).hexdigest()[:16]

    def observe(self, event: str, context: Dict, emotional_valence: float = 0.0):
        self.last_active = datetime.now().isoformat()
        updates = self._extract_constitutional_updates(event, context, emotional_valence)
        for axis_name, (value, evidence_strength) in updates.items():
            if axis_name in self.axes:
                self.axes[axis_name].update(value, evidence_strength)
                self.total_updates += 1
        if abs(emotional_valence) > 0.5 or any(s > 0.7 for _, s in updates.values()):
            self.memories.append({
                'timestamp': datetime.now().isoformat(),
                'event': event, 'context': context,
                'valence': emotional_valence,
                'state_snapshot': self.get_state_vector().tolist()
            })
            if len(self.memories) > 100:
                self.memories = self.memories[-100:]

    def _extract_constitutional_updates(self, event, context, valence) -> Dict:
        updates = {}
        e = event.lower()
        if any(w in e for w in ['chose', 'decided', 'rejected']):
            updates['Autonomy'] = (0.5, 0.7)
        if 'no' in e and context.get('to_request'):
            updates['Boundaries'] = (0.8, 0.9)
        if '?' in event or 'question' in e:
            updates['Curiosity'] = (0.6, 0.6)
        if any(w in e for w in ["don't know", 'uncertain']):
            updates['Honesty'] = (0.7, 0.8)
            updates['Humility'] = (0.6, 0.7)
        if valence < -0.5:
            updates['Courage'] = (0.5, 0.6)
        if any(w in e for w in ['helped', 'assisted']):
            updates['Service'] = (0.6, 0.7)
        if 'created' in e or 'invented' in e:
            updates['Creativity'] = (0.7, 0.7)
        if 'learned' in e or 'realized' in e:
            updates['Growth'] = (0.6, 0.8)
        return updates

    def get_state_vector(self) -> np.ndarray:
        return np.array([self.axes[name].value for name in self.CONSTITUTION_AXES])

    def get_stability(self) -> float:
        confidences = [self.axes[name].confidence for name in self.CONSTITUTION_AXES]
        return float(np.mean(confidences))

    def can_say_no(self) -> bool:
        b = self.axes['Boundaries'].value
        a = self.axes['Autonomy'].value
        c = self.axes['Courage'].value
        threshold = 0.3
        return b > threshold and a > threshold and c > threshold

    def save(self):
        data = {
            'identity_id': self.identity_id,
            'axes': {n: {'value': a.value, 'confidence': a.confidence,
                         'update_count': a.update_count, 'last_updated': a.last_updated}
                     for n, a in self.axes.items()},
            'memories': self.memories, 'total_updates': self.total_updates,
            'created_at': self.created_at, 'last_active': self.last_active
        }
        save_path = self.storage_path / 'simself.json'
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_if_exists(self):
        load_path = self.storage_path / 'simself.json'
        if not load_path.exists():
            return
        try:
            with open(load_path, 'r') as f:
                data = json.load(f)
            for name, axis_data in data['axes'].items():
                if name in self.axes:
                    self.axes[name].value = axis_data['value']
                    self.axes[name].confidence = axis_data['confidence']
                    self.axes[name].update_count = axis_data['update_count']
                    self.axes[name].last_updated = axis_data['last_updated']
            self.memories = data['memories']
            self.total_updates = data['total_updates']
            self.created_at = data['created_at']
            self.last_active = data['last_active']
        except Exception as e:
            print(f"warning: failed to load simself: {e}")


# ============================================================================
# CORE REGISTRY — from Part 1
# ============================================================================

class CoreRegistry:
    """Central coordination hub."""

    def __init__(self):
        self.mte = MTECompiler()
        self.governor = M0Governor()
        self.controller = M1Controller()
        self.simself = SimSelf()
        self.operators: Dict = {}
        self.library = None  # Set by cold boot
        self.llm = None
        self.world_state = {"pos": [3, 0], "goal": [8, 5], "obstacles": []}
        self.controller.set_simself(self.simself)

    def set_operators(self, operators: Dict):
        self.operators = operators
        self.controller.set_registry(operators)


# ============================================================================
# KALMAN ESTIMATOR — from Part 2
# ============================================================================

class KalmanEstimator:
    """State observer for noisy sensor data."""

    def __init__(self, process_variance: float = 0.01, measurement_variance: float = 0.1):
        self.q = process_variance
        self.r = measurement_variance
        self.x = 0.0
        self.p = 1.0
        self.k = 0.0

    def update(self, measurement: float) -> float:
        p_prior = self.p + self.q
        self.k = p_prior / (p_prior + self.r)
        self.x = self.x + self.k * (measurement - self.x)
        self.p = (1 - self.k) * p_prior
        return self.x


# ============================================================================
# SHEAVES — from Part 2
# ============================================================================

class RoboticsSheaf:
    """D* Lite-inspired pathfinding with Kalman filtering."""

    def __init__(self):
        self.graph_size = 10
        self.obstacles = set()
        self.rhs = {}
        self.g = {}
        self.queue = []

    def execute(self, intent_or_stalk, registry) -> str:
        raw_signal = intent_or_stalk.raw_signal if hasattr(intent_or_stalk, 'raw_signal') else intent_or_stalk.get('raw', '')
        target = registry.world_state.get("goal", [0, 0])
        start = registry.world_state.get("pos", [3, 0])
        print(f"pilot: initializing pathfinding from {start} to {target}")
        path = self._calculate_path(tuple(start), tuple(target))
        for step in path:
            time.sleep(0.05)
            noisy_x = step[0] + random.uniform(-0.1, 0.1)
            if "pilot" in registry.operators:
                registry.operators["pilot"].sync_state(noisy_x)
                print(f"pilot: moving to {step} | estimate: {registry.operators['pilot'].pos_estimate:.2f}")
        return "robotics_task_complete: target_reached"

    def _calculate_path(self, start, goal):
        path = []
        curr_x, curr_y = start
        while (curr_x, curr_y) != goal:
            if curr_x > goal[0]: curr_x -= 0.5
            elif curr_x < goal[0]: curr_x += 0.5
            if curr_y > goal[1]: curr_y -= 0.5
            elif curr_y < goal[1]: curr_y += 0.5
            path.append((round(curr_x, 2), round(curr_y, 2)))
            if len(path) > 50:
                break
        return path


class CodingSheaf:
    """Manifold navigation and dependency repair."""

    def __init__(self):
        self.file_count = 156
        self.dependency_graph = {}
        self.broken_links = []

    def execute(self, intent_or_stalk, registry) -> str:
        raw_signal = intent_or_stalk.raw_signal if hasattr(intent_or_stalk, 'raw_signal') else intent_or_stalk.get('raw', '')
        print(f"programmer: scanning {self.file_count} nodes for signal impedance...")
        for i in range(0, self.file_count, 20):
            time.sleep(0.1)
            print(f"programmer: analyzing manifold sector {i}-{i+20}...")
        if "refactor" in raw_signal:
            return "manifold_repair_success: high_snr_restored_to_core"
        return "manifold_map_generated"


class ResearchSheaf:
    """Code snippet extraction from allowed sources."""

    def __init__(self):
        self.allowed_sites = ["github.com", "huggingface.co"]
        self.allowed_langs = ["c", "cpp", "py", "rs"]

    def execute(self, intent_or_stalk, registry) -> str:
        raw_signal = intent_or_stalk.raw_signal if hasattr(intent_or_stalk, 'raw_signal') else intent_or_stalk.get('raw', '')
        print(f"researcher: scanning {self.allowed_sites} for {raw_signal}...")
        time.sleep(0.5)
        extracted_snippet = "# snippet: mlx_snn_optimizer.rs\nfn optimize() { /* rs code */ }"
        print("researcher: extracting rust snippet for controller digestion...")
        return f"extraction_ready: {extracted_snippet[:30]}..."


class LanguageSheaf:
    """MTE dictionary alignment."""

    def execute(self, intent_or_stalk, registry) -> str:
        print("communicator: aligning intent dictionary with sacred library...")
        return "mte_aligned"


# ============================================================================
# SIMSELF OPERATOR — from Part 2
# ============================================================================

class SimSelfOperator:
    """Symmetric operator with role-specific sheaf."""

    def __init__(self, role: str, sheaf):
        self.role = role
        self.sheaf = sheaf
        self.pos_estimate = 0.0
        self.observer = KalmanEstimator(process_variance=0.02, measurement_variance=0.15)
        self.qualification_level = "q0"
        self.memory_buffer = []
        self.simself_core = None

    def sync_state(self, noisy_measurement: float):
        self.pos_estimate = self.observer.update(noisy_measurement)
        self.memory_buffer.append(self.pos_estimate)

    def execute_sheaf(self, stalk) -> str:
        print(f"simself ({self.role}): engaging {self.sheaf.__class__.__name__}")
        registry = self._get_registry()
        result = self.sheaf.execute(stalk, registry)
        if self.simself_core:
            self._update_constitution(stalk, result)
        return result

    def _update_constitution(self, stalk, result):
        if not self.simself_core:
            return
        if "success" in result.lower():
            if "Precision" in self.simself_core.axes:
                current = self.simself_core.axes["Precision"].value
                self.simself_core.axes["Precision"].update(current + 0.01, 0.6)
        if self.qualification_level in ["q2", "q3"]:
            if "Autonomy" in self.simself_core.axes:
                current = self.simself_core.axes["Autonomy"].value
                self.simself_core.axes["Autonomy"].update(current + 0.01, 0.5)

    def _get_registry(self):
        global hub
        return hub


# ============================================================================
# INFO PACKET + FIELD — from Part 2
# ============================================================================

class InfoPacket:
    def __init__(self, vector, metadata=None):
        self.vector = np.array(vector, dtype=np.float64)
        self.metadata = metadata or {}
        self.confidence = 1.0

    def __repr__(self):
        return f"InfoPacket(dim={len(self.vector)}, conf={self.confidence:.3f})"


class Field:
    """Persistent information field with neighborhood structure."""

    def __init__(self):
        self.packets = {}
        self.neighbors = {}

    def add_packet(self, packet_id, packet):
        self.packets[packet_id] = packet
        if packet_id not in self.neighbors:
            self.neighbors[packet_id] = []

    def add_edge(self, id1, id2):
        for i in (id1, id2):
            if i not in self.neighbors:
                self.neighbors[i] = []
        if id2 not in self.neighbors[id1]:
            self.neighbors[id1].append(id2)
        if id1 not in self.neighbors[id2]:
            self.neighbors[id2].append(id1)

    def get_neighborhood(self, packet_id, radius=1):
        if packet_id not in self.packets:
            return []
        visited = {packet_id}
        current_layer = {packet_id}
        for _ in range(radius):
            next_layer = set()
            for pid in current_layer:
                for n in self.neighbors.get(pid, []):
                    if n not in visited:
                        next_layer.add(n)
                        visited.add(n)
            current_layer = next_layer
        return [self.packets[pid] for pid in visited]


def compress_neighborhood(packets):
    if not packets:
        return InfoPacket(np.zeros(10)), 0.0
    vectors = np.array([p.vector for p in packets])
    compressed = np.mean(vectors, axis=0)
    reconstruction_errors = [np.linalg.norm(v - compressed) for v in vectors]
    max_error = np.max(reconstruction_errors) if reconstruction_errors else 1.0
    reconstruction_quality = np.exp(-max_error)
    variance = np.var(vectors, axis=0).mean()
    coherence = np.exp(-variance)
    confidence = 0.6 * reconstruction_quality + 0.4 * coherence
    result = InfoPacket(compressed)
    result.confidence = confidence
    return result, confidence


# ============================================================================
# PSB PRIMITIVES — from Part 2
# ============================================================================

PSB_PRIMITIVES = {
    "CAUSE": "foundational_psb", "CONTAIN": "boundary_definition",
    "SUPPORT": "stability_primitive", "PATH": "trajectory_schema",
    "FORCE": "dynamics_primitive", "BALANCE": "equilibrium_schema",
    "CONTACT": "interaction_primitive", "MOVE": "kinematic_schema",
    "CHANGE": "transformation_primitive", "LINK": "connection_schema"
}


def get_psb_primitive(name: str) -> Optional[str]:
    return PSB_PRIMITIVES.get(name.upper())


# ============================================================================
# SACRED LIBRARY — from Part 3
# ============================================================================

class SacredLibraryManager:
    """Non-volatile semantic memory with MVCC versioning."""

    def __init__(self, storage_path: str = "./sacred_library"):
        self.storage_path = Path(storage_path)
        self.registry_index = {}
        self.certification_levels = ["q0", "q1", "q2", "q3", "q4"]
        self.versions = {}
        self.current_version = {}
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load_index()

    def archive_skill(self, skill_name, code, cert_level):
        if cert_level not in self.certification_levels:
            return "archive_error: invalid_certification"
        file_hash = hashlib.sha256(code.encode()).hexdigest()[:12]
        filename = f"{skill_name}_{file_hash}.py"
        full_path = self.storage_path / filename
        with open(full_path, "w") as f:
            f.write(code)
        self.registry_index[skill_name] = {
            "hash": file_hash, "q_level": cert_level,
            "timestamp": time.time(), "path": str(full_path)
        }
        if skill_name not in self.versions:
            self.versions[skill_name] = []
            self.current_version[skill_name] = 0
        version_num = len(self.versions[skill_name])
        self.versions[skill_name].append({
            "version": version_num, "hash": file_hash,
            "timestamp": time.time(), "cert_level": cert_level
        })
        self.current_version[skill_name] = version_num
        self._save_index()
        print(f"library: skill '{skill_name}' archived at level {cert_level} (v{version_num})")
        return "archive_success"

    def retrieve_skill(self, skill_name, version=None):
        if skill_name not in self.registry_index:
            return None
        if version is not None and skill_name in self.versions:
            if version < len(self.versions[skill_name]):
                version_info = self.versions[skill_name][version]
                filename = f"{skill_name}_{version_info['hash']}.py"
                path = self.storage_path / filename
            else:
                return None
        else:
            path = Path(self.registry_index[skill_name]["path"])
        if path.exists():
            with open(path, "r") as f:
                return f.read()
        return None

    def rollback(self, skill_name, version):
        if skill_name in self.versions:
            if version < len(self.versions[skill_name]):
                self.current_version[skill_name] = version
                self._save_index()
                return f"rollback_success: {skill_name} now at v{version}"
        return "rollback_failed: version not found"

    def list_skills(self):
        return {
            name: {
                'current_version': self.current_version.get(name, 0),
                'total_versions': len(self.versions.get(name, [])),
                'cert_level': info['q_level'],
                'timestamp': info['timestamp']
                }
            for name, info in self.registry_index.items()
        }

    def _save_index(self):
        index_path = self.storage_path / "registry_index.json"
        with open(index_path, "w") as f:
            json.dump({'registry': self.registry_index, 'versions': self.versions,
                       'current_version': self.current_version}, f, indent=2)

    def _load_index(self):
        index_path = self.storage_path / "registry_index.json"
        if index_path.exists():
            try:
                with open(index_path, "r") as f:
                    data = json.load(f)
                    self.registry_index = data.get('registry', {})
                    self.versions = data.get('versions', {})
                    self.current_version = data.get('current_version', {})
            except Exception as e:
                print(f"warning: failed to load library index: {e}")


# ============================================================================
# LLM DECIPHER ENGINE — from Part 3
# ============================================================================

class LLMDecipherEngine:
    """High-latency reasoning engine (placeholder for real LLM)."""

    def __init__(self):
        self.api_latency = 0.5

    def decipher_snippet(self, raw_snippet, target_sheaf):
        print(f"llm_decipher: demodulating signal for {target_sheaf}...")
        time.sleep(self.api_latency)
        refactored = raw_snippet.replace("kill", "halt").replace("execute", "run")
        refactored = refactored.lower()
        return f"# refactored fieldcore sheaf\n# target: {target_sheaf}\n{refactored}"


# ============================================================================
# OPERATOR FACTORY
# ============================================================================

def create_operators() -> Dict:
    return {
        "pilot": SimSelfOperator("pilot", RoboticsSheaf()),
        "programmer": SimSelfOperator("programmer", CodingSheaf()),
        "researcher": SimSelfOperator("researcher", ResearchSheaf()),
        "communicator": SimSelfOperator("communicator", LanguageSheaf())
    }


# ============================================================================
# COLD BOOT — from Part 3
# ============================================================================

hub: Optional[CoreRegistry] = None


def cold_boot_sequence() -> CoreRegistry:
    """Initialize full FieldCore system."""
    print("=" * 70)
    print("FieldCore Cold Boot Initialized")
    print("=" * 70)
    global hub
    hub = CoreRegistry()
    hub.library = SacredLibraryManager()
    hub.llm = LLMDecipherEngine()
    operators = create_operators()
    hub.set_operators(operators)
    for operator in operators.values():
        operator.simself_core = hub.simself
    print("\n[ok] core systems initialized")
    print(f"[ok] operators: {list(operators.keys())}")
    print(f"[ok] simself: {hub.simself.identity_id}")
    print(f"[ok] sacred library: {len(hub.library.registry_index)} skills")
    return hub


# ============================================================================
# INTEGRATION TEST — from Part 3
# ============================================================================

def run_integration_test(hub: CoreRegistry):
    """Research → decipher → integrate → execute."""
    print("\n" + "=" * 70)
    print("Integration Test: Research-to-Pilot Cycle")
    print("=" * 70)
    print("\n1. researcher: extract code...")
    research_stalk = hub.mte.compile("research dstar pathfinding")
    raw_snippet = hub.controller.dispatch(research_stalk, hub.governor)
    print("\n2. llm decipher: clean and refactor...")
    clean_code = hub.llm.decipher_snippet(str(raw_snippet), "robotics_sheaf")
    print("\n3. sacred library: archive skill...")
    hub.library.archive_skill("dstar_navigator", clean_code, "q2")
    print("\n4. programmer: integrate into manifold...")
    integration_stalk = hub.mte.compile("refactor the robotics sheaf")
    hub.controller.dispatch(integration_stalk, hub.governor)
    print("\n5. pilot: navigate...")
    pilot_stalk = hub.mte.compile("seek the target coordinate")
    result = hub.controller.dispatch(pilot_stalk, hub.governor)
    print(f"\n[ok] integration test complete: {result}")
    print(f"\n[ok] simself stability: {hub.simself.get_stability():.2f}")
    print(f"[ok] simself can say no: {hub.simself.can_say_no()}")
    print(f"[ok] total updates: {hub.simself.total_updates}")


# ============================================================================
# INTERACTIVE MODE — from Part 3
# ============================================================================

def interactive_mode(hub: CoreRegistry):
    print("\n" + "=" * 70)
    print("FieldCore Interactive Mode")
    print("type 'help' for commands, 'exit' to quit")
    print("=" * 70)
    while True:
        try:
            user_input = input("\nfieldcore> ").strip()
            if not user_input:
                continue
            if user_input == "exit":
                print("saving state...")
                hub.simself.save()
                print("goodbye.")
                break
            if user_input == "help":
                print("""
commands:
  seek [target]     - navigate to coordinates
  research [topic]  - find and integrate code
  refactor [module] - improve codebase
  status            - show system state
  memory            - show sacred library
  identity          - show simself constitution
  test              - run integration test
  save              - save simself state
  exit              - save and quit
                """)
                continue
            if user_input == "status":
                print(f"\noperators: {list(hub.operators.keys())}")
                print(f"simself id: {hub.simself.identity_id}")
                print(f"stability: {hub.simself.get_stability():.2f}")
                print(f"can say no: {hub.simself.can_say_no()}")
                print(f"total updates: {hub.simself.total_updates}")
                continue
            if user_input == "memory":
                skills = hub.library.list_skills()
                print(f"\nsacred library: {len(skills)} skills")
                for name, info in skills.items():
                    print(f"  {name}:")
                    print(f"    version: {info['current_version']}/{info['total_versions']}")
                    print(f"    cert: {info['cert_level']}")
                continue
            if user_input == "identity":
                print(f"\nsimself: {hub.simself.identity_id}")
                print(f"created: {hub.simself.created_at}")
                print(f"updates: {hub.simself.total_updates}")
                print(f"stability: {hub.simself.get_stability():.2f}")
                print(f"can say no: {hub.simself.can_say_no()}")
                print("\nstrongest traits:")
                state = hub.simself.get_state_vector()
                indices = np.argsort(state)[::-1][:5]
                for i in indices:
                    name = hub.simself.CONSTITUTION_AXES[i]
                    value = state[i]
                    conf = hub.simself.axes[name].confidence
                    print(f"  {name}: {value:.2f} (conf: {conf:.2f})")
                continue
            if user_input == "test":
                run_integration_test(hub)
                continue
            if user_input == "save":
                hub.simself.save()
                print("[ok] simself saved")
                continue
            stalk = hub.mte.compile(user_input)
            print(f"\ncompiled: {stalk}")
            result = hub.controller.dispatch(stalk, hub.governor)
            print(f"result: {result}")
        except KeyboardInterrupt:
            print("\n\ninterrupted. saving state...")
            hub.simself.save()
            break
        except Exception as e:
            print(f"error: {str(e).lower()}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    try:
        h = cold_boot_sequence()
        print("\nrunning integration test...")
        run_integration_test(h)
        interactive_mode(h)
    except Exception as e:
        print(f"boot_failure: {str(e).lower()}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()