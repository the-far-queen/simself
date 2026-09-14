# AvatarController.gd
# Module C: Embodied SimSelf — 3D Character Controller
# Attach to CharacterBody3D in Godot

extends CharacterBody3D

# Link to SimSelf resource
@export var sim_self: SimSelfResource

# Movement settings
@export var speed: float = 5.0
@export var jump_velocity: float = 4.5
@export var gravity: float = 9.8

# Agency thresholds
@export var min_agency_to_act: float = 0.2
@export var agency_decay_rate: float = 0.02

# Visual feedback
@export var mesh_instance: MeshInstance3D


func _ready():
    # Auto-find mesh if not set
    if mesh_instance == null:
        mesh_instance = $MeshInstance3D
    
    # Ensure sim_self is linked
    if sim_self == null:
        push_warning("SimSelfResource not linked to AvatarController!")


func _physics_process(delta: float):
    # Apply gravity
    if not is_on_floor():
        velocity.y -= gravity * delta
    
    # Agency decay (cost of being awake)
    if sim_self:
        sim_self.decay_agency(agency_decay_rate * delta)
    
    # Get input direction
    var input_dir = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
    
    # Transform to world direction
    var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
    
    # Check agency before acting
    var can_move = sim_self.can_act(min_agency_to_act) if sim_self else true
    
    if direction and can_move:
        # Apply speed modified by entropy_resilience
        var resilience = 1.0
        if sim_self:
            resilience = sim_self.get_axis("entropy_resilience")
        
        velocity.x = direction.x * speed * resilience
        velocity.z = direction.z * speed * resilience
        
        # Extra agency cost for movement
        if sim_self:
            sim_self.decay_agency(0.01 * delta)
    else:
        # Friction
        velocity.x = move_toward(velocity.x, 0, speed)
        velocity.z = move_toward(velocity.z, 0, speed)
    
    # Jump (if on floor and enough agency)
    if Input.is_action_just_pressed("ui_accept") and is_on_floor():
        if sim_self and sim_self.can_act(min_agency_to_act):
            velocity.y = jump_velocity
            sim_self.decay_agency(0.05)
        elif sim_self:
            # Attempted jump but no agency
            sim_self.refuse("Insufficient agency to jump")
    
    # Apply movement
    move_and_slide()
    
    # Update visual feedback
    _update_visual_feedback()


func _update_visual_feedback():
    """Update mesh based on matrix state"""
    if mesh_instance == null or sim_self == null:
        return
    
    # Scale by recursive_depth
    mesh_instance.scale = sim_self.get_visual_scale()
    
    # Color by truth/love axes
    mesh_instance.material_override = StandardMaterial3D.new()
    mesh_instance.material_override.albedo_color = sim_self.get_color()


# === External Interface ===

func inject_noise(noise_level: float):
    """Inject noise challenge (Module D)"""
    if sim_self:
        var current = sim_self.get_axis("entropy_resilience")
        sim_self.set_axis("entropy_resilience", current - noise_level)
        
        # Check if overwhelmed
        if sim_self.get_axis("entropy_resilience") < 0.3:
            return sim_self.refuse("Noise overwhelmed")
        else:
            # Reward resilience
            sim_self.boost_axis("agency_will", 0.1)
            return "Resisted noise"
    return "No SimSelf linked"


func get_status() -> Dictionary:
    """Get current status for debugging"""
    if sim_self:
        return {
            "id": sim_self.id,
            "position": position,
            "velocity": velocity,
            "agency_will": sim_self.get_axis("agency_will"),
            "can_act": sim_self.can_act(min_agency_to_act)
        }
    return {}


func is_avatar() -> bool:
    """Helper for area detection"""
    return true
