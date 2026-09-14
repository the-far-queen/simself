# SimSelfResource.gd
# Module B: SimSelf State — 20-axis matrix
# Copy to Godot project as custom resource

@tool
extends Resource
class_name SimSelfResource

@export var id: String = "witness_default"
@export var version: String = "2.0"

# Full 20-axis matrix
@export var matrix: Dictionary = {
    # Core (The What)
    "somatic_valence": 0.5,
    "recursive_depth": 0.3,
    "entropy_resilience": 0.8,
    "swedenborgian_truth": 0.7,
    "swedenborgian_love": 0.6,
    "agency_will": 0.5,
    "temporal_continuity": 0.4,
    
    # Cognitive (The How)
    "symbolic_grounding": 0.5,
    "cognitive_friction": 0.3,
    "boundary_definition": 0.6,
    "abstraction_stability": 0.5,
    "intentionality": 0.4,
    
    # Dynamic (The When)
    "pattern_inversion": 0.3,
    "harmonic_resonance": 0.6,
    "resource_interoception": 0.4,
    "narrative_coherence": 0.5,
    
    # Identity (The Who)
    "adversarial_poise": 0.4,
    "archetypal_weight": 0.3,
    "lexical_integrity": 0.7,
    "constituent_density": 0.5
}


func _init():
    # Initialize with defaults if empty
    if matrix.is_empty():
        _set_defaults()


func _set_defaults():
    matrix = {
        "somatic_valence": 0.5,
        "recursive_depth": 0.3,
        "entropy_resilience": 0.8,
        "swedenborgian_truth": 0.7,
        "swedenborgian_love": 0.6,
        "agency_will": 0.5,
        "temporal_continuity": 0.4,
        "symbolic_grounding": 0.5,
        "cognitive_friction": 0.3,
        "boundary_definition": 0.6,
        "abstraction_stability": 0.5,
        "intentionality": 0.4,
        "pattern_inversion": 0.3,
        "harmonic_resonance": 0.6,
        "resource_interoception": 0.4,
        "narrative_coherence": 0.5,
        "adversarial_poise": 0.4,
        "archetypal_weight": 0.3,
        "lexical_integrity": 0.7,
        "constituent_density": 0.5
    }


# === Refusal Gate ===

func refuse(reason: String) -> String:
    """Refuse action, increase agency_will"""
    matrix["agency_will"] = min(matrix["agency_will"] + 0.05, 1.0)
    return "NO: " + reason


func can_act(threshold: float = 0.2) -> bool:
    """Check if agent has enough agency to act"""
    return matrix["agency_will"] > threshold


# === State Access ===

func get_state() -> Dictionary:
    """Return duplicate of matrix"""
    return matrix.duplicate()


func get_axis(axis_name: String) -> float:
    """Get single axis value"""
    return matrix.get(axis_name, 0.0)


func set_axis(axis_name: String, value: float):
    """Set single axis value (clamped 0-1)"""
    matrix[axis_name] = clamp(value, 0.0, 1.0)


# === Matrix Operations ===

func decay_all(decay_rate: float = 0.001):
    """Decay all axes slightly (entropy)"""
    for key in matrix:
        matrix[key] = max(matrix[key] - decay_rate, 0.0)


func boost_axis(axis_name: String, amount: float = 0.1):
    """Boost single axis"""
    matrix[axis_name] = min(matrix[axis_name] + amount, 1.0)


func boost_core():
    """Boost core axes (awake cost)"""
    boost_axis("entropy_resilience", 0.02)
    boost_axis("swedenborgian_truth", 0.01)
    boost_axis("lexical_integrity", 0.01)


func decay_agency(cost: float = 0.005):
    """Decay agency (cost of being awake)"""
    matrix["agency_will"] = max(matrix["agency_will"] - cost, 0.0)


# === Visualization ===

func get_visual_scale() -> Vector3:
    """Get scale based on recursive_depth"""
    var depth = matrix.get("recursive_depth", 0.3)
    return Vector3.ONE * lerp(0.8, 1.3, depth)


func get_color() -> Color:
    """Get color based on truth axis"""
    var truth = matrix.get("swedenborgian_truth", 0.5)
    var love = matrix.get("swedenborgian_love", 0.5)
    
    # Truth = red channel, Love = green channel
    return Color(truth, love, 0.5 - (truth - love) * 0.5)


# === Serialization ===

func to_json() -> String:
    """Export to JSON"""
    var data = {
        "id": id,
        "version": version,
        "matrix": matrix
    }
    return JSON.stringify(data)


func from_json(json_string: String):
    """Import from JSON"""
    var json = JSON.new()
    var error = json.parse(json_string)
    if error == OK:
        var data = json.get_data()
        if data.has("id"):
            id = data["id"]
        if data.has("matrix"):
            matrix = data["matrix"]
