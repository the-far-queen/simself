# GodotBridge.gd
# Bridge script for Godot → Python communication
# Attach to Bridge node in Godot scene

extends Node

# Connection settings
var use_websocket: bool = false
var use_stdout: bool = true  # Default for simple IPC

# Python process
var python_process: Process = null
var python_ready: bool = false

# Entity tracking
var entities: Dictionary = {}
var ghost_entities: Dictionary = {}

# Signal for other scripts
signal packet_received(packet_data: Dictionary)
signal action_result(result: Dictionary)


func _ready():
	# Initialize bridge
	print("Godot Bridge ready")
	
	# Try to connect to Python
	_connect_to_python()


func _connect_to_python():
	# For now, use stdout/stdin simulation
	# In production: WebSocket or TCP
	use_stdout = true
	python_ready = true
	print("Connected to Python (stdout mode)")


# === Receiving from Python ===

func _process(delta):
	# Poll for messages (in stdout mode, this is simulated)
	if use_stdout:
		_poll_stdout()


func _poll_stdout():
	# Placeholder: in real implementation, read from subprocess pipe
	# For now, this is a stub
	pass


func receive_message(message: Dictionary):
	"""Receive JSON message from Python."""
	var msg_type = message.get("type")
	
	match msg_type:
		"action":
			_execute_action(message)
		"spawn_packet":
			_spawn_packet(message)
		"set_mode":
			_set_mode(message)
		"reset":
			_reset_scene()
		_:
			print("Unknown message type: ", msg_type)


func _execute_action(message: Dictionary):
	"""Execute action in Godot."""
	var action_id = message.get("action_id")
	var mode = message.get("mode", "real")
	var params = message.get("params", {})
	
	var result = {
		"type": "action_result",
		"action_id": action_id,
		"mode": mode,
		"success": true,
		"timestamp": Time.get_unix_time_from_system()
	}
	
	# Route to handlers
	match action_id:
		"move_node":
			result = _move_node(params, mode)
		"move_arm":
			result = _move_arm(params, mode)
		"stop":
			result = _stop_arm(params)
	
	# Send result back
	_send_to_python(result)
	action_result.emit(result)


func _spawn_packet(message: Dictionary):
	"""Spawn packet in Godot."""
	var packet_id = message.get("packet_id")
	var position = message.get("position", Vector3.ZERO)
	var mode = message.get("mode", "real")
	
	# Find or create packet node
	var packet = _get_or_create_packet(packet_id, position)
	
	if mode == "ghost":
		ghost_entities[packet_id] = packet
		_set_packet_ghost(packet, true)
	else:
		entities[packet_id] = packet
		_set_packet_ghost(packet, false)


func _set_mode(message: Dictionary):
	"""Change entity mode."""
	var entity_id = message.get("entity_id")
	var mode = message.get("mode", "real")
	
	var packet = entities.get(entity_id) or ghost_entities.get(entity_id)
	if packet:
		_set_packet_ghost(packet, mode == "ghost")


func _reset_scene():
	"""Reset Godot scene."""
	# Clear all packets
	for e in entities.values():
		e.queue_free()
	for g in ghost_entities.values():
		g.queue_free()
	
	entities.clear()
	ghost_entities.clear()


# === Action Handlers ===

func _move_node(params: Dictionary, mode: String) -> Dictionary:
	"""Move a node."""
	var node_id = params.get("node_id")
	var delta = params.get("delta", [0, 0, 0])
	
	var node = get_node_or_null("FieldRoot/" + node_id)
	if node:
		node.position += Vector3(delta[0], delta[1], delta[2])
		return {"success": true, "node_id": node_id}
	
	return {"success": false, "error": "Node not found"}


func _move_arm(params: Dictionary, mode: String) -> Dictionary:
	"""Move robot arm."""
	var direction = params.get("direction", "up")
	var speed = params.get("speed", 1.0)
	
	var arm = get_node_or_null("ArmRoot/ArmSegment")
	if arm:
		if direction == "up":
			arm.rotation.x += speed * get_physics_process_delta_time()
		elif direction == "down":
			arm.rotation.x -= speed * get_physics_process_delta_time()
		return {"success": true, "direction": direction}
	
	return {"success": false, "error": "Arm not found"}


func _stop_arm(params: Dictionary) -> Dictionary:
	"""Stop robot arm."""
	var arm = get_node_or_null("ArmRoot/ArmSegment")
	if arm:
		# Assuming arm has a stop method or property
		return {"success": true}
	return {"success": false, "error": "Arm not found"}


# === Sending to Python ===

func emit_sensor_packet(entity_id: String, position: Array, 
                       velocity: Array, salience: float):
	"""Emit sensor packet to Python."""
	var packet = {
		"type": "sensor_packet",
		"entity_id": entity_id,
		"pos": position,
		"vel": velocity,
		"salience": salience,
		"timestamp": Time.get_unix_time_from_system()
	}
	
	_send_to_python(packet)
	packet_received.emit(packet)


func emit_physics_tick():
	"""Emit physics tick notification."""
	var tick = {
		"type": "physics_tick",
		"timestamp": Time.get_unix_time_from_system()
	}
	_send_to_python(tick)


func _send_to_python(message: Dictionary):
	"""Send message to Python."""
	if use_stdout:
		# Print JSON to stdout (Python reads from pipe)
		print(JSON.stringify(message))
	elif use_websocket:
		# WebSocket send (if implemented)
		pass


# === Helper Methods ===

func _get_or_create_packet(packet_id: String, position: Array) -> Node3D:
	"""Get existing packet or create new one."""
	var field_root = get_node_or_null("FieldRoot")
	if not field_root:
		return null
	
	var existing = field_root.get_node_or_null(packet_id)
	if existing:
		return existing
	
	# Create new packet
	var packet = MeshInstance3D.new()
	packet.name = packet_id
	
	# Create mesh (simple cube)
	var mesh = BoxMesh.new()
	mesh.size = Vector3(0.5, 0.5, 0.5)
	packet.mesh = mesh
	
	# Create material
	var material = StandardMaterial3D.new()
	material.albedo_color = Color(0.2, 0.6, 1.0)
	packet.material_override = material
	
	# Set position
	packet.position = Vector3(position[0], position[1], position[2])
	
	field_root.add_child(packet)
	return packet


func _set_packet_ghost(packet: Node3D, is_ghost: bool):
	"""Set packet to ghost mode (translucent)."""
	if packet and packet.material_override:
		var mat = packet.material_override as StandardMaterial3D
		if is_ghost:
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			mat.albedo_color.a = 0.25
		else:
			mat.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
			mat.albedo_color.a = 1.0


# === Called by Physics ===

func _physics_process(delta):
	# Emit sensor data for all entities
	for entity_id in entities.keys():
		var entity = entities[entity_id]
		if entity is Node3D:
			emit_sensor_packet(
				entity_id,
				[entity.position.x, entity.position.y, entity.position.z],
				[0.0, 0.0, 0.0],  # Velocity would come from physics
				1.0  # Salience
			)
	
	# Emit physics tick
	emit_physics_tick()
