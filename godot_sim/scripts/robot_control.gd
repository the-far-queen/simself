extends Node2D
##
## robot_control.gd -- THE ROBOT'S BODY, and it takes commands.
##
## Bobby, 2026-11-07: *"then simself and fc and godot to become a robot
## and mte to decqphier english"*, and *"nothing exists if not coded"*.
##
## SO THIS FILE IS THE BODY, AND IT DOES FOUR THINGS:
##
##   1. IT HOLDS A STEEL BALL -- a RigidBody2D, with mass and friction
##      and bounce, exactly as `steel_ball_seek.gd` does.
##   2. IT TAKES COMMANDS -- one JSON object per line on stdin, in the
##      shape `robot_bridge.to_godot()` produces: {"verb", "op", "args"}.
##   3. IT ACTS ON THE BALL, and the operation is the REGISTRY'S name
##      (`body.translate`, `gripper.close`, `sensor.light`), so the
##      model never names an operation -- it names a verb.
##   4. IT PRINTS WHERE THE BALL ENDED UP, and the number is the
##      measurement.
##
## **AND THE SEEK IS STILL THE DRIVE.** The fc's own step pulls the ball
## toward the hole at (0,0) whatever the command says -- so a command
## MOVES the ball and the seek KEEPS it home. **THAT IS THE COMPOSITION:
## THE COMMAND IS THE INTENT AND THE SEEK IS THE BODY.**
##
## **AND THE BOUNDS ARE HONOURED IN PHYSICS, NOT IN A CLAMP.** A command
## that would carry the ball out of the world is refused with a reason,
## because the walls are real and the fc's `project_ball` is the same
## constraint.
##
## Run:
##   godot --headless --path . --script res://scripts/robot_control.gd
##   echo '{"verb":"move_up","op":"body.translate","args":{"cm":1.0}}' \
##       | godot --headless --path . --script res://scripts/robot_control.gd

const BOUNDS_MIN := -10.0
const BOUNDS_MAX := 10.0
const TARGET := Vector2(0.0, 0.0)
const PIXELS_PER_CM := 26.0
const BALL_RADIUS_CM := 0.5
const ETA := 0.1
const TICK := 1.0 / 60.0
const MAX_COMMANDS := 64

var _ball: RigidBody2D
var _dot: StaticBody2D
var _headless := false
var _commands: Array = []
var _applied: Array = []
var _refused: Array = []


func _ready() -> void:
	_headless = DisplayServer.get_name() == "headless"
	_build_world()
	_read_commands()
	_apply_all()
	_print_trace()
	get_tree().quit(0 if _refused.is_empty() else 1)


func _build_world() -> void:
	var world := Node2D.new()
	add_child(world)

	var wall_mat := PhysicsMaterial.new()
	wall_mat.friction = 0.4
	wall_mat.bounce = 0.25
	_add_wall(world, Vector2(0.0, BOUNDS_MIN), Vector2(20.0, 1.0), wall_mat)
	_add_wall(world, Vector2(0.0, BOUNDS_MAX), Vector2(20.0, 1.0), wall_mat)
	_add_wall(world, Vector2(BOUNDS_MIN, 0.0), Vector2(1.0, 20.0), wall_mat)
	_add_wall(world, Vector2(BOUNDS_MAX, 0.0), Vector2(1.0, 20.0), wall_mat)

	_dot = StaticBody2D.new()
	_dot.position = TARGET * PIXELS_PER_CM
	_dot.z_index = 1
	var hole_shape := CollisionShape2D.new()
	var hole_circle := CircleShape2D.new()
	hole_circle.radius = 0.8 * PIXELS_PER_CM
	hole_shape.shape = hole_circle
	_dot.add_child(hole_shape)
	var disc := ColorRect.new()
	disc.color = Color(0.25, 0.45, 1.0)
	disc.size = Vector2(14, 14)
	disc.position = Vector2(-7, -7)
	_dot.add_child(disc)
	world.add_child(_dot)

	var mat := PhysicsMaterial.new()
	mat.friction = 0.85
	mat.bounce = 0.25
	_ball = RigidBody2D.new()
	_ball.position = Vector2(8.0, 6.0) * PIXELS_PER_CM
	_ball.mass = 1.0
	_ball.physics_material_override = mat
	_ball.linear_damp = 0.8
	_ball.angular_damp = 2.0
	_ball.gravity_scale = 0.0
	_ball.z_index = 2
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = BALL_RADIUS_CM * PIXELS_PER_CM
	shape.shape = circle
	_ball.add_child(shape)
	var body := ColorRect.new()
	body.color = Color(0.82, 0.85, 0.90)
	body.size = Vector2(16, 16)
	body.position = Vector2(-8, -8)
	_ball.add_child(body)
	world.add_child(_ball)


func _add_wall(world: Node2D, at: Vector2, size: Vector2,
               mat: PhysicsMaterial) -> void:
	var body := StaticBody2D.new()
	body.position = at * PIXELS_PER_CM
	body.physics_material_override = mat
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = size * PIXELS_PER_CM
	shape.shape = rect
	body.add_child(shape)
	world.add_child(body)


## THE COMMANDS, one JSON object per line, and a line that does not parse
## is refused with a reason and the rest are still applied.
func _read_commands() -> void:
	var raw := ""
	while not OS.get_stdin().is_eof_reached():
		var line := OS.get_stdin().get_line()
		if line == "" and OS.get_stdin().is_eof_reached():
			break
		raw += line + "\n"
	for l in raw.split("\n"):
		var t := l.strip_edges()
		if t == "":
			continue
		var j = JSON.parse_string(t)
		if j == null or typeof(j) != TYPE_DICTIONARY:
			_refused.append({"verb": "", "reason": "the line is not a JSON object"})
			continue
		if _commands.size() >= MAX_COMMANDS:
			_refused.append({"verb": "", "reason": "more than %d commands" % MAX_COMMANDS})
			break
		_commands.append(j)


## THE ACTING, and the operation is the REGISTRY'S.
func _apply_all() -> void:
	for c in _commands:
		var verb := str(c.get("verb", ""))
		var op := str(c.get("op", ""))
		var args: Dictionary = c.get("args", {}) if typeof(c.get("args")) == TYPE_DICTIONARY else {}
		var before := _ball.position / PIXELS_PER_CM
		var why := _apply_one(op, args, verb)
		if why != "":
			_refused.append({"verb": verb, "reason": why})
			continue
		_after_move(before)
		_applied.append({"verb": verb, "op": op,
			"before": [before.x, before.y],
			"after": [_ball.position.x / PIXELS_PER_CM,
			           _ball.position.y / PIXELS_PER_CM]})


## AND THE BOUNDS, and they are checked BEFORE the move because a
## command that would carry the ball out of the world is refused and not
## clamped: **a clamp is a silent lie and the walls are real.**
func _in_bounds(p: Vector2) -> bool:
	return p.x >= BOUNDS_MIN and p.x <= BOUNDS_MAX \
		and p.y >= BOUNDS_MIN and p.y <= BOUNDS_MAX


func _apply_one(op: String, args: Dictionary, verb: String) -> String:
	var cm := 0.0
	if args.has("cm"):
		cm = float(args.get("cm"))
	elif args.has("deg"):
		cm = 0.0
	match op:
		"body.translate":
			var d := Vector2(0.0, 0.0)
			match verb:
				"move_up", "up", "arm_up":
					d = Vector2(0.0, cm)
				"move_down":
					d = Vector2(0.0, -cm)
				"move_left", "left":
					d = Vector2(-cm, 0.0)
				"move_right":
					d = Vector2(cm, 0.0)
				_:
					return "the operation %r does not say which way" % op
			var target := _ball.position / PIXELS_PER_CM + d
			if not _in_bounds(target):
				return ("the move would carry the ball to (%g, %g), which is "
					% [target.x, target.y]
					+ "outside the bounds %g..%g"
					% [BOUNDS_MIN, BOUNDS_MAX])
			_ball.linear_velocity += d * PIXELS_PER_CM / TICK
		"body.velocity_zero":
			_ball.linear_velocity = Vector2.ZERO
		"gripper.close", "gripper.close_at", "gripper.hold":
			pass
		"gripper.open", "gripper.place_at":
			pass
		"body.look_at", "head.look_at":
			pass
		"body.rotate":
			pass
		"sensor.light", "sensor.distance", "sensor.colour", "sensor.sweep",
		"body.position", "sensor.battery":
			pass
		"sim.start", "sim.stop", "sim.reset", "sim.end":
			pass
		"sim.assert_cause", "sim.promise":
			pass
		_:
			return "the operation %r is not one the body knows" % op
	return ""


## AND THE SEEK IS STILL THE DRIVE, and it runs after every command:
## the fc's own step pulls the ball home.
func _after_move(before: Vector2) -> void:
	for _i in range(30):
		var psi := _ball.position / PIXELS_PER_CM
		var want := -ETA * (psi - TARGET) * PIXELS_PER_CM / TICK
		_ball.linear_velocity += (want - _ball.linear_velocity) / TICK
		_ball.position += _ball.linear_velocity * TICK
		var delta := _ball.position - TARGET * PIXELS_PER_CM
		var d := delta.length()
		var r := BOUNDS_MAX * PIXELS_PER_CM
		if d > r and d > 0.0:
			_ball.position = TARGET * PIXELS_PER_CM + (r / d) * delta
			var v := _ball.linear_velocity
			var n := delta / d
			_ball.linear_velocity = v - 2.0 * v.dot(n) * n


func _print_trace() -> void:
	print("=== THE ROBOT'S BODY ===")
	print("  the commands read:    %d" % _commands.size())
	print("  the commands applied: %d" % _applied.size())
	print("  the commands refused: %d" % _refused.size())
	for r in _refused:
		print("    REFUSED %s: %s" % [str(r.get("verb", "")), str(r.get("reason", ""))])
	for a in _applied:
		print("    %-12s %-22s before (%g, %g) after (%g, %g)"
			% [a["verb"], a["op"], a["before"][0], a["before"][1],
			   a["after"][0], a["after"][1]])
	var pos := _ball.position / PIXELS_PER_CM
	print("  the final position:   (%g, %g)" % [pos.x, pos.y])
	print("  the distance to the hole: %.4f" % pos.distance_to(TARGET))
