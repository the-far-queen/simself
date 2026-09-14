# TrainingGym.gd
# Module D: RL Training Environment — Noise Zones
# Attach to Area3D in Godot scene

extends Area3D

# Configuration
@export var noise_level: float = 0.5
@export var reward_on_resist: float = 0.1
@export var zone_type: String = "noise"  # "noise", "reward", "boundary"

# Visual feedback
@export var zone_color: Color = Color(1.0, 0.3, 0.3, 0.3)


func _ready():
    # Set up collision
    if not collision_layer & (1 << 0):
        collision_layer = 1  # Default layer
    
    # Connect body_entered signal
    body_entered.connect(_on_body_entered)
    body_exited.connect(_on_body_exited)
    
    # Visual feedback if has mesh
    _setup_visual()


func _setup_visual():
    """Setup zone visualization"""
    var mesh_instance = MeshInstance3D.new()
    
    # Create transparent box
    var box = BoxMesh.new()
    box.size = Vector3(4, 4, 4)
    mesh_instance.mesh = box
    
    # Material
    var material = StandardMaterial3D.new()
    material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    material.albedo_color = zone_color
    material.emission_enabled = true
    material.emission = zone_color
    material.emission_energy_multiplier = 0.5
    mesh_instance.material_override = material
    
    add_child(mesh_instance)


func _on_body_entered(body):
    """Handle body entering zone"""
    # Check if it's an avatar with SimSelf
    if body.has_method("is_avatar") and body.is_avatar():
        _apply_zone_effect(body)


func _on_body_exited(body):
    """Handle body exiting zone"""
    if body.has_method("is_avatar") and body.is_avatar():
        _remove_zone_effect(body)


func _apply_zone_effect(body):
    """Apply zone effect to avatar"""
    if zone_type == "noise":
        _apply_noise_zone(body)
    elif zone_type == "reward":
        _apply_reward_zone(body)
    elif zone_type == "boundary":
        _apply_boundary_zone(body)


func _apply_noise_zone(body):
    """Noise zone: challenges entropy resilience"""
    if body.has_method("inject_noise"):
        body.inject_noise(noise_level)


func _apply_reward_zone(body):
    """Reward zone: boosts all axes"""
    if body.sim_self:
        body.sim_self.boost_core()
        body.sim_self.boost_axis("agency_will", reward_on_resist)


func _apply_boundary_zone(body):
    """Boundary zone: triggers state restructure"""
    if body.sim_self:
        # Boost boundary definition
        body.sim_self.boost_axis("boundary_definition", 0.1)
        body.sim_self.boost_axis("recursive_depth", 0.05)


func _remove_zone_effect(body):
    """Clean up when avatar exits"""
    # Could restore original values here
    pass


# === Training Interface ===

func set_noise_level(level: float):
    """Adjust noise level"""
    noise_level = clamp(level, 0.0, 1.0)


func get_zone_info() -> Dictionary:
    """Get zone info for training"""
    return {
        "type": zone_type,
        "noise_level": noise_level,
        "reward_on_resist": reward_on_resist
    }


# === Dynamic Configuration ===

func configure(new_type: String, new_level: float):
    """Configure zone at runtime"""
    zone_type = new_type
    noise_level = new_level
    
    # Update color
    var material = null
    if has_node("MeshInstance3D"):
        material = get_node("MeshInstance3D").material_override
    
    if material:
        match zone_type:
            "noise":
                zone_color = Color(1.0, 0.3, 0.3, 0.3)
            "reward":
                zone_color = Color(0.3, 1.0, 0.3, 0.3)
            "boundary":
                zone_color = Color(0.3, 0.3, 1.0, 0.3)
        
        material.albedo_color = zone_color
        material.emission = zone_color
