extends Node2D
##
## robot_control.gd -- THE ROBOT'S BODY, AND EVERY ONE OF THE FIFTY
## COMMANDS IS A CALL ON THE BALL.
##
## Bobby, 2026-11-07: *"then simself and fc and godot to become a robot and
## mte to decqphier english"*, and *"nothing exists if not coded"*.
##
## **AND THIS FILE IS THAT BODY, AND IT DOES SEVEN THINGS:**
##
##   1. IT HOLDS A STEEL BALL -- a RigidBody2D, with mass and friction
##      and bounce, exactly as `steel_ball_seek.gd` does.
##   2. IT HOLDS THE SECOND BODY -- an ARM with a length and an angle,
##      a GRIPPER that can hold a named object, and a HEAD with a yaw
##      and a pitch. **THE MANIPULATION GROUP NEEDS A SECOND BODY, AND
##      THERE IS ONE.**
##   3. IT TAKES COMMANDS -- one JSON object per line, in the shape
##      `robot_bridge.to_godot()` produces: {"verb", "op", "args"}.
##      **AND THE OPERATION IS THE REGISTRY'S NAME** (`body.translate`,
##      `gripper.close`, `sensor.light`), so the model never names an
##      operation -- it names a verb, and the verb's registry entry
##      names the operation.
##   4. IT REFUSES WHAT IT DOES NOT KNOW, WITH A REASON -- and the
##      refusal is the PSB's own shape: a span without a primitive is
##      refused as OTHER, and a command without an operation is refused
##      as UNKNOWN.
##   5. IT PRINTS A RECEIPT PER COMMAND -- one JSON line, prefixed
##      `TRACE `, carrying the state before the command, the state
##      right after the command's OWN TICK (so the command's effect is
##      visible and the drive's is not), and the state after the drive.
##   6. IT PRINTS THE PATH THE DRIVE TOOK -- one line per command,
##      prefixed `PATH `, so the drive can be compared with the fc's
##      own kernel step for step, and not merely at its end.
##   7. IT PRINTS THE FC'S OWN STEP, over a few starts, prefixed
##      `KERNEL `, so the checker can compare the body's step with the
##      fc's OWN module -- step for step.
##
## **AND THE DRIVE IS THE FC'S OWN STEP, EXACTLY.** The drive's
## velocity controller has its gain at one, so one tick advances the
## body by EXACTLY one fc kernel step:
##
##     psi_next = project_ball(psi - eta*(psi - psi0), psi0, R)
##
## **AND A COMMAND IS THE INPUT AND THE STEP IS THE DRIVE.** A command
## is applied as ONE TICK of its own -- the body is displaced by
## exactly the impulse the command asked for -- and then the fc's step
## resumes and pulls the body home. **THE COMMAND IS THE INTENT AND THE
## SEEK IS THE BODY.**
##
## **AND THE STATE IS FLOAT64, AND NOT A Vector2.** MEASURED: Godot's
## `Vector2` is 32-bit (`Vector2(7.2, 5.4)` prints as `7.199999809265`),
## and the fc's kernel is 64-bit, so a Vector2 body cannot agree with
## the fc's own module to better than about 1e-7 -- which would make
## "the drive IS the fc's step" a claim no checker could measure. So
## the state is plain `float` scalars, and the Vector2 is used only to
## DRAW.
##
## **AND THE GROUND NEVER MOVES.** It is a StaticBody2D, and its
## position is checked EVERY TICK, before the measurement, because a
## measurement taken against a moved ground is not a measurement.
##
## **AND THE BOUNDS ARE HONOURED IN PHYSICS, NOT IN A CLAMP.** The fc's
## constraint is a BALL of radius R and not a square, so a command
## that would carry the body outside the ball is refused with a
## reason, because the walls are real and the fc's `project_ball` is
## the same constraint.
##
## **AND THE COMMANDS COME FROM A FILE, NOT FROM STDIN.** MEASURED:
## `OS.get_stdin()` does not exist in Godot 4 at all, and
## `OS.read_string_from_stdin(true)` returns ONE CHARACTER per call and
## swallows the newline -- so a line-oriented protocol over stdin
## cannot be read at all. So the commands are read from the file named
## by the `FC_COMMANDS` environment variable, or by the
## `--commands=<path>` user argument.
##
## Run:
##   FC_COMMANDS=cmds.jsonl godot --headless --path . \
##       res://scenes/RobotControl.tscn

const BOUNDS_MIN := -10.0
const BOUNDS_MAX := 10.0
const GROUND_X := 0.0
const GROUND_Y := 0.0
const PIXELS_PER_CM := 26.0
const BALL_RADIUS_CM := 0.5
const BALL_MASS := 1.0
const FRICTION := 0.85
const BOUNCE := 0.25

#: THE FC'S DEFAULTS, and they are the fc's: `tiniest_core`'s
#: DEFAULT_ETA, and the world's radius R.
const ETA := 0.1
const RADIUS := 10.0
const CONVERGENCE_TOL := 0.05
const MAX_TICKS := 900
const TICK := 1.0 / 60.0

#: THE START, and it is the same start `steel_ball_seek.gd` uses.
const START_X := 8.0
const START_Y := 6.0

#: THE DRIVE TICKS BETWEEN COMMANDS. **AND THEY ARE FEW ON PURPOSE:**
#: the drive must pull the body home, but a command must also be
#: OBSERVABLE, so the drive between commands is short enough that the
#: body is still where the command put it.
const DRIVE_TICKS := 12

#: THE ARRIVAL TOLERANCE, in cm, for a seek and for an approach.
const ARRIVAL_CM := 0.5

#: THE ARM, and it is the SECOND BODY.
const ARM_LEN_CM := 2.0
const ARM_MAX_CM := 5.0

#: THE HEAD, and it has a yaw and a pitch, because a 2D world has one
#: axis for "up" and one for "left", and four verbs that collapse into
#: two axes would be four names for two things.
const HEAD_YAW := 0.0
const HEAD_PITCH := 0.0

#: THE BATTERY, and it is a charge that drains as the body moves.
const BATTERY_FULL := 1.0
const BATTERY_PER_CM := 0.002

#: THE OBJECT, and it is the one thing the gripper can hold. **AND IT
#: SITS WITHIN THE ARM'S REACH OF THE HOLE, so a grasp can succeed.**
const CUBE_HOME_X := 1.5
const CUBE_HOME_Y := 0.0

#: THE EXPLORE, and it moves without a target, to COVER the world. So
#: its step is a WANDER whose direction turns with the command's
#: number, and the receipt says how far it covered.
const EXPLORE_CM := 2.0
const EXPLORE_TURN := 0.7

const MAX_COMMANDS := 200
const MAX_LINE_BYTES := 1 << 20
const KERNEL_STEPS := 60

var _ball: RigidBody2D
var _dot: StaticBody2D
var _arm: Node2D
var _head: Node2D
var _cube: Node2D
var _limb: ColorRect

#: THE STATE, in the fc's own units: centimetres, and +y is UP.
var _px := START_X
var _py := START_Y
var _vx := 0.0
var _vy := 0.0
var _rot := 0.0
var _arm_ang := 0.0
var _arm_len := ARM_LEN_CM
var _grip := "open"
var _held := ""
var _carried := false
var _yaw := HEAD_YAW
var _pitch := HEAD_PITCH
var _batt := BATTERY_FULL

#: THE PENDING IMPULSE, in centimetres, and it is applied over ONE
#: TICK -- the command's own tick -- and then the fc's step resumes.
var _pend_x := 0.0
var _pend_y := 0.0

#: THE IMPULSE THAT WAS APPLIED, and the receipt carries it.
var _imp_x := 0.0
var _imp_y := 0.0

#: THE HOLD, and `stop_moving` sets it: the body refuses to move
#: further, without ending the session.
var _hold := false

#: THE DESTINATION, and it is where the body was sent. The default is
#: the hole, and `body.approach` and `body.translate_to` name another.
var _dest_x := GROUND_X
var _dest_y := GROUND_Y

#: THE OBJECTS, and the cube is the one thing the gripper can hold.
#: Each is [x, y], in centimetres.
var _obj := {"cube": [CUBE_HOME_X, CUBE_HOME_Y]}

#: THE SESSION, and its states are named.
var _session := "new"
var _mode := "ghost"

#: THE LEDGER, and `cause` is a COMMIT into it.
var _causes: Array = []
var _promises: Array = []

#: THE LAST COMMAND, so the sim can be asked WHY it moved.
var _last_verb := ""
#: THE LAST OPERATION, and it is what the verification names.
var _last_op := ""

#: THE DRIVE MODE, and it is either a fixed number of ticks or "until
#: the body arrives".
var _drive_until_arrival := false
#: THE ARRIVAL RADIUS, and the seek commands carry their own.
var _arrival := ARRIVAL_CM

var _commands: Array = []
var _refused: Array = []
var _index := 0


func _ready() -> void:
	_build_world()
	_read_commands()
	_apply_all()
	_print_kernel()
	_print_ledger()
	_print_trace()
	get_tree().quit(0)


func _build_world() -> void:
	var world := Node2D.new()
	add_child(world)

	var wall_mat := PhysicsMaterial.new()
	wall_mat.friction = 0.4
	wall_mat.bounce = BOUNCE
	_add_wall(world, Vector2(0.0, BOUNDS_MIN), Vector2(20.0, 1.0), wall_mat)
	_add_wall(world, Vector2(0.0, BOUNDS_MAX), Vector2(20.0, 1.0), wall_mat)
	_add_wall(world, Vector2(BOUNDS_MIN, 0.0), Vector2(1.0, 20.0), wall_mat)
	_add_wall(world, Vector2(BOUNDS_MAX, 0.0), Vector2(1.0, 20.0), wall_mat)

	# --- THE GROUND, which is psi_0, and it NEVER MOVES ---------------
	_dot = StaticBody2D.new()
	_dot.position = Vector2(GROUND_X, -GROUND_Y) * PIXELS_PER_CM
	_dot.z_index = 1
	var dot_shape := CollisionShape2D.new()
	var dot_circle := CircleShape2D.new()
	dot_circle.radius = 0.8 * PIXELS_PER_CM
	dot_shape.shape = dot_circle
	_dot.add_child(dot_shape)
	var disc := ColorRect.new()
	disc.color = Color(0.25, 0.45, 1.0)
	disc.size = Vector2(14, 14)
	disc.position = Vector2(-7, -7)
	_dot.add_child(disc)
	world.add_child(_dot)

	# --- THE RED MARKER, and it is AT THE HOLE -----------------------
	# **AND IT IS RED BECAUSE `seek_red` FINDS THE HOLE AT (0, 0)**, so
	# the colour the sensor reads at the hole is red. The blue disc
	# above it is the fc's own ground, and the red marker is the
	# robot's TARGET, and the two are different things at one place.
	var marker := Node2D.new()
	marker.position = Vector2(GROUND_X, -GROUND_Y) * PIXELS_PER_CM
	var ring := ColorRect.new()
	ring.color = Color(0.85, 0.15, 0.15)
	ring.size = Vector2(24, 24)
	ring.position = Vector2(-12, -12)
	ring.z_index = 0
	marker.add_child(ring)
	world.add_child(marker)

	# --- THE STEEL BALL, which is the robot, which is the embodiment --
	var mat := PhysicsMaterial.new()
	mat.friction = FRICTION
	mat.bounce = BOUNCE
	_ball = RigidBody2D.new()
	_ball.position = _screen(_px, _py)
	_ball.mass = BALL_MASS
	_ball.physics_material_override = mat
	_ball.linear_damp = 0.8
	_ball.angular_damp = 2.0
	_ball.z_index = 2
	_ball.gravity_scale = 0.0
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

	# --- THE ARM, and it is the SECOND BODY ---------------------------
	_arm = Node2D.new()
	_arm.z_index = 3
	_limb = ColorRect.new()
	_limb.color = Color(0.55, 0.60, 0.68)
	_limb.size = Vector2(ARM_LEN_CM * PIXELS_PER_CM, 4)
	_limb.position = Vector2(0, -2)
	_arm.add_child(_limb)
	var hand := ColorRect.new()
	hand.color = Color(0.35, 0.75, 0.45)
	hand.size = Vector2(6, 6)
	hand.position = Vector2(ARM_LEN_CM * PIXELS_PER_CM - 3, -3)
	_arm.add_child(hand)
	world.add_child(_arm)

	# --- THE HEAD, and it is where the sensors look -------------------
	_head = Node2D.new()
	_head.z_index = 3
	var eye := ColorRect.new()
	eye.color = Color(0.95, 0.85, 0.30)
	eye.size = Vector2(5, 5)
	eye.position = Vector2(-2, -2)
	_head.add_child(eye)
	world.add_child(_head)

	# --- THE CUBE, and it is the thing the gripper can hold -----------
	_cube = Node2D.new()
	_cube.z_index = 2
	var cube_body := ColorRect.new()
	cube_body.color = Color(0.70, 0.40, 0.85)
	cube_body.size = Vector2(10, 10)
	cube_body.position = Vector2(-5, -5)
	_cube.add_child(cube_body)
	world.add_child(_cube)

	_render()


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


## THE SCREEN MAPPING, and it flips y. **THE FC'S PSI HAS +y UP, AND
## GODOT'S SCREEN HAS +y DOWN**, so a body that moved up in the fc's
## coordinates must be drawn up on the screen, and this is where that
## is decided.
func _screen(x: float, y: float) -> Vector2:
	return Vector2(x, -y) * PIXELS_PER_CM


# ---------------------------------------------------------------------------
# THE FC'S STEP, and it is the fc's step and not a re-implementation:
#
#     psi_next = project_ball(psi - eta*(psi - psi0), psi0, R)
#
# AND THIS IS `tiniest_core`'s step TO THE LAST BIT, and the checker
# compares the two step for step, over a population of starts.
func _fc_step(x: float, y: float) -> Array:
	return _project(x - ETA * (x - GROUND_X), y - ETA * (y - GROUND_Y))


## THE PROJECTION, and it is the fc's `project_ball` about the GROUND,
## because the ground is the centre of the world and the walls are the
## world's -- and the fc's constraint is a BALL and not a square.
func _project(x: float, y: float) -> Array:
	var dx := x - GROUND_X
	var dy := y - GROUND_Y
	var d := sqrt(dx * dx + dy * dy)
	if d <= RADIUS or d == 0.0:
		return [x, y]
	var s := RADIUS / d
	return [GROUND_X + s * dx, GROUND_Y + s * dy]


func _hole_distance() -> float:
	var dx := _px - GROUND_X
	var dy := _py - GROUND_Y
	return sqrt(dx * dx + dy * dy)


func _dest_distance() -> float:
	var dx := _px - _dest_x
	var dy := _py - _dest_y
	return sqrt(dx * dx + dy * dy)


# ---------------------------------------------------------------------------
# THE SENSORS, and they are the fc's own gate reading and the hole's colour.
func _light_reading() -> float:
	var d := _hole_distance()
	return 1.0 / (1.0 + d * d)


## THE COLOUR SENSOR, and it reads the colour of the MARKER -- and the
## only marker is the red one, which is AT THE HOLE. So the colour is
## red at the hole and there is nothing to read anywhere else.
func _colour_reading() -> String:
	if _hole_distance() <= ARRIVAL_CM:
		return "red"
	return ""


func _ground_held() -> bool:
	var d := _dot.position.distance_to(
		Vector2(GROUND_X, -GROUND_Y) * PIXELS_PER_CM)
	return d < 1e-9


# ---------------------------------------------------------------------------
# THE ARM, and it is the second body's own geometry.
func _arm_tip_x() -> float:
	return _px + cos(_arm_ang) * _arm_len


func _arm_tip_y() -> float:
	return _py + sin(_arm_ang) * _arm_len


func _set_arm_tip(x: float, y: float) -> void:
	var vx := x - _px
	var vy := y - _py
	var d := sqrt(vx * vx + vy * vy)
	if d < 1e-12:
		return
	_arm_ang = atan2(vy, vx)
	_arm_len = clampf(d, 0.0, ARM_MAX_CM)


# ---------------------------------------------------------------------------
# THE COMMANDS. **AND `OS.get_stdin()` DOES NOT EXIST IN GODOT 4** --
# MEASURED: the class database says `get_stdin` is absent and
# `read_string_from_stdin` is present -- and `read_string_from_stdin`
# returns ONE CHARACTER per call and swallows the newline, so a
# line-oriented protocol over stdin cannot be read at all. So the
# commands are read from the file named by the `FC_COMMANDS`
# environment variable, or by the `--commands=<path>` user argument.
func _commands_path() -> String:
	var env := OS.get_environment("FC_COMMANDS")
	if env != "":
		return env
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--commands="):
			return a.substr(11)
	return ""


func _read_commands() -> void:
	var path := _commands_path()
	if path == "":
		_refused.append({"verb": "", "op": "",
			"reason": "no commands: set FC_COMMANDS or pass "
				+ "--commands=<path>"})
		return
	if not FileAccess.file_exists(path):
		_refused.append({"verb": "", "op": "",
			"reason": "the commands file %s does not exist" % path})
		return
	var body := FileAccess.get_file_as_string(path)
	if body.length() > MAX_LINE_BYTES:
		body = body.substr(0, MAX_LINE_BYTES)
	for l in body.split("\n"):
		if _commands.size() >= MAX_COMMANDS:
			_refused.append({"verb": "", "op": "",
				"reason": "more than %d commands" % MAX_COMMANDS})
			break
		var t := l.strip_edges()
		if t == "":
			continue
		var j = JSON.parse_string(t)
		if j == null or typeof(j) != TYPE_DICTIONARY:
			_refused.append({"verb": "", "op": "",
				"reason": "the line is not a JSON object"})
			continue
		_commands.append(j)


# ---------------------------------------------------------------------------
# THE ACTING, and the operation is the REGISTRY'S.
func _apply_all() -> void:
	for c in _commands:
		var verb := str(c.get("verb", ""))
		var op := str(c.get("op", ""))
		var args: Dictionary = {}
		if typeof(c.get("args")) == TYPE_DICTIONARY:
			args = c.get("args")
		# --- THE QUERY, and it is how the sim is ASKED WHY it moved ---
		if str(c.get("query", "")) != "":
			_print_query(str(c.get("query", "")))
		# **AND THE QUERY COUNTS AS AN INDEX**, so the checker's index
		# is the index of the command in the file and nothing is skipped.
			_index += 1
			continue
		var pre := _state()
		var read: Variant = _read_value(op)
		var why := _apply_one(op, verb, args)
		if why != "":
			_refused.append({"i": _index, "verb": verb, "op": op,
				"reason": why})
			print("REFUSED ", JSON.stringify({"i": _index, "verb": verb,
				"op": op, "reason": why}))
			_index += 1
			continue
		# THE COMMAND'S OWN TICK, and it is the command's OWN tick, so
		# the receipt separates the command's effect from the drive's.
		var path: Array = []
		var first := _impulse_tick(path)
		var path_start_x := float(pre["pos"][0])
		var path_start_y := float(pre["pos"][1])
		# **AND `post` IS THE STATE AFTER THE COMMAND'S OWN TICK**, so
		# the receipt carries the command's effect and not the drive's.
		var post := _state()
		# AND THEN THE DRIVE, which is the fc's step.
		var ticks := first + _drive(path)
		_render()
		_last_verb = verb
		print("PATH ", _index, " ", _fmt_path(path))
		print("TRACE ", JSON.stringify({
			"i": _index,
			"verb": verb,
			"op": op,
			"ok": true,
			"reason": "",
			"pre": pre,
			"post": post,
			"drive": _state(),
			"ticks": ticks,
			"read": read,
			"verified": _verified(),
			"covered": _r(_covered(path, path_start_x, path_start_y)),
			"impulse": [_r(_imp_x), _r(_imp_y)],
		}))
		_index += 1


## THE COVERED DISTANCE, and it is the length of the path the drive
## took, so a command that moved the body says so.
func _covered(path: Array, start_x: float, start_y: float) -> float:
	var total := 0.0
	var prev_x := start_x
	var prev_y := start_y
	for p in path:
		var vx := float(p[0])
		var vy := float(p[1])
		var dx := vx - prev_x
		var dy := vy - prev_y
		total += sqrt(dx * dx + dy * dy)
		prev_x = vx
		prev_y = vy
	return total


## THE VERIFICATION, and it says WHICH SENSOR CONFIRMED THE SEEK, so
## the three seeks are three commands over the same sensors and not
## three names for one thing.
func _verified() -> String:
	if _last_op == "body.seek_colour":
		return "colour:" + _colour_reading()
	if _last_op == "body.seek_light":
		return "light:%.9f" % _light_reading()
	if _last_op == "body.seek":
		return "distance:%.9f" % _hole_distance()
	if _last_op == "body.approach":
		return "distance:%.9f" % _dest_distance()
	return ""


## THE READING, and it is taken BEFORE the command acts, because a sensor
## reads the world as the world was when the command arrived.
func _read_value(op: String) -> Variant:
	if op == "sensor.light":
		return _light_reading()
	if op == "sensor.distance":
		return _hole_distance()
	if op == "sensor.colour":
		return _colour_reading()
	if op == "body.position":
		return [_r(_px), _r(_py)]
	if op == "sensor.battery":
		return _r(_batt)
	if op == "sensor.sweep":
		var seen: Array = []
		for name in _obj.keys():
			var p: Array = _obj[name]
			var ox := float(p[0]) - _px
			var oy := float(p[1]) - _py
			seen.append({"name": name,
				"distance": _r(sqrt(ox * ox + oy * oy))})
		seen.append({"name": "hole", "distance": _r(_hole_distance())})
		return seen
	return ""


# ---------------------------------------------------------------------------
# AND THE REFUSAL, and the SESSION gate comes first: a session that has
# not started, has stopped, or has ended refuses everything, with a
# reason. **AND THE REASON NAMES THE STATE, because a refusal without a
# reason is not a refusal.**
func _apply_one(op: String, verb: String, args: Dictionary) -> String:
	_last_op = op
	if _session == "ended":
		return ("the session has ended, so %s cannot be acted on" % verb)
	if _session == "stopped" and op != "sim.end":
		return ("the session has stopped, so %s cannot be acted on" % verb)
	if _session == "new" and op != "sim.start":
		return ("the session has not started, so %s cannot be acted on"
			% verb)

	var cm := 0.0
	var deg := 0.0
	var x := 0.0
	var y := 0.0
	if args.has("cm"):
		cm = float(args.get("cm"))
	if args.has("deg"):
		deg = float(args.get("deg"))
	if args.has("x"):
		x = float(args.get("x"))
	if args.has("y"):
		y = float(args.get("y"))

	# -- THE LIFECYCLE ------------------------------------------------
	if op == "sim.start":
		if _session != "new":
			return ("the session is %s, and it cannot be started again"
				% _session)
		_mode = str(args.get("mode", "ghost"))
		_session = "running"
		return ""
	if op == "sim.pause":
		if _session != "running":
			return ("the session is %s, and only a running session can be "
				% _session + "paused")
		_session = "paused"
		return ""
	if op == "sim.resume":
		if _session != "paused":
			return ("the session is %s, and only a paused session can be "
				% _session + "resumed")
		_session = "running"
		return ""
	if op == "sim.reset":
		_px = START_X
		_py = START_Y
		_vx = 0.0
		_vy = 0.0
		_rot = 0.0
		_arm_ang = 0.0
		_arm_len = ARM_LEN_CM
		_grip = "open"
		_held = ""
		_carried = false
		_yaw = HEAD_YAW
		_pitch = HEAD_PITCH
		_batt = BATTERY_FULL
		_pend_x = 0.0
		_pend_y = 0.0
		_imp_x = 0.0
		_imp_y = 0.0
		_hold = false
		_dest_x = GROUND_X
		_dest_y = GROUND_Y
		_obj = {"cube": [CUBE_HOME_X, CUBE_HOME_Y]}
		return ""
	if op == "sim.stop":
		_session = "stopped"
		return ""
	if op == "sim.end":
		_session = "ended"
		_promises.append({"state": "closed",
			"at": [_r(_px), _r(_py)]})
		return ""

	# -- THE LOCOMOTION ------------------------------------------------
	if op == "body.translate":
		var dx := 0.0
		var dy := 0.0
		if verb == "move_up" or verb == "up":
			dy = cm
		elif verb == "move_down":
			dy = -cm
		elif verb == "move_left" or verb == "left":
			dx = -cm
		elif verb == "move_right":
			dx = cm
		elif verb == "strafe_left":
			dx = -sin(_rot) * cm
			dy = cos(_rot) * cm
		else:
			return ("the operation %s does not say which way, and the verb "
				% op + "%s does not say either" % verb)
		if not _in_ball(_px + dx, _py + dy):
			return ("the move would carry the body to (%.4f, %.4f), which is "
				% [_px + dx, _py + dy]
				+ "outside the fc's ball of radius %.4f" % RADIUS)
		_hold = false
		_pend_x += dx
		_pend_y += dy
		return ""
	if op == "body.translate_to":
		if not _in_ball(x, y):
			return ("the move would carry the body to (%.4f, %.4f), which is "
				% [x, y]
				+ "outside the fc's ball of radius %.4f" % RADIUS)
		_hold = false
		_dest_x = x
		_dest_y = y
		_pend_x += x - _px
		_pend_y += y - _py
		return ""
	if op == "body.rotate":
		var delta := 0.0
		if verb == "turn_left":
			delta = deg_to_rad(deg)
		elif verb == "turn_right":
			delta = -deg_to_rad(deg)
		else:
			return ("the operation %s does not say which way" % op)
		_rot += delta
		return ""
	if op == "body.velocity_zero":
		# THE HOLD, and it is `stop_moving`: the body refuses to move
		# further, WITHOUT ending the session.
		_hold = true
		_pend_x = 0.0
		_pend_y = 0.0
		_vx = 0.0
		_vy = 0.0
		return ""

	# -- THE SEEKING ----------------------------------------------------
	if op == "body.seek":
		var name := str(args.get("target", ""))
		if name != "hole":
			return ("the world holds one seekable thing, the hole, and %s "
				% name + "is not it")
		_hold = false
		_arrival = ARRIVAL_CM
		_drive_until_arrival = true
		return ""
	if op == "body.seek_colour":
		_hold = false
		_arrival = maxf(cm, 1e-9)
		_drive_until_arrival = true
		return ""
	if op == "body.seek_light":
		_hold = false
		_arrival = maxf(cm, 1e-9)
		_drive_until_arrival = true
		return ""
	if op == "body.approach":
		if not _in_ball(x, y):
			return ("the approach would carry the body to (%.4f, %.4f), which "
				% [x, y]
				+ "is outside the fc's ball of radius %.4f" % RADIUS)
		var tx := x - _px
		var ty := y - _py
		var dist := sqrt(tx * tx + ty * ty)
		if dist <= ARRIVAL_CM:
			return ("the body is already within %.4f cm of (%.4f, %.4f), so "
				% [ARRIVAL_CM, x, y] + "there is no distance to close")
		_hold = false
		_dest_x = x
		_dest_y = y
		var step := dist - ARRIVAL_CM
		_pend_x += tx / dist * step
		_pend_y += ty / dist * step
		return ""
	if op == "body.explore":
		# THE EXPLORE, and it moves without a target, to COVER the world.
		# So its step is a WANDER whose direction turns with the
		# command's number, and the receipt says how far it covered.
		_hold = false
		var ang := float(_index) * EXPLORE_TURN
		_pend_x += cos(ang) * EXPLORE_CM
		_pend_y += sin(ang) * EXPLORE_CM
		return ""

	# -- THE MANIPULATION, and it is the SECOND BODY -------------------
	if op == "arm.translate":
		var dx := 0.0
		var dy := 0.0
		var fx := cos(_rot)
		var fy := sin(_rot)
		if verb == "arm_up":
			dy = cm
		elif verb == "arm_down":
			dy = -cm
		elif verb == "arm_forward":
			dx = fx * cm
			dy = fy * cm
		elif verb == "arm_back":
			dx = -fx * cm
			dy = -fy * cm
		elif verb == "arm_left":
			dx = -fy * cm
			dy = fx * cm
		elif verb == "arm_right":
			dx = fy * cm
			dy = -fx * cm
		else:
			return ("the operation %s does not say which way" % op)
		_set_arm_tip(_arm_tip_x() + dx, _arm_tip_y() + dy)
		return ""
	if op == "arm.look_at":
		var vx := x - _px
		var vy := y - _py
		var d := sqrt(vx * vx + vy * vy)
		if d < 1e-9:
			return "the reach target is the arm's own base"
		if d > ARM_MAX_CM:
			return ("the reach target is %.4f cm away and the arm is %.4f cm "
				% [d, ARM_MAX_CM] + "long")
		_set_arm_tip(x, y)
		return ""
	if op == "arm.set_length":
		if cm < 0.0 or cm > ARM_MAX_CM:
			return ("the arm's extension must be between 0 and %.4f cm, and "
				% ARM_MAX_CM + "%.4f was asked for" % cm)
		if verb == "retract_arm":
			_arm_len = maxf(0.0, _arm_len - cm)
		else:
			_arm_len = cm
		return ""
	if op == "gripper.close":
		_grip = "closed"
		return ""
	if op == "gripper.open":
		_grip = "open"
		if verb == "drop":
			_held = ""
			_carried = false
		return ""
	if op == "gripper.close_at":
		var obj := str(args.get("object", ""))
		if not _obj.has(obj):
			return ("the world holds %s, and %s is not in it"
				% [", ".join(_obj.keys()), obj])
		var op_pos: Array = _obj[obj]
		var ox := float(op_pos[0]) - _arm_tip_x()
		var oy := float(op_pos[1]) - _arm_tip_y()
		var d := sqrt(ox * ox + oy * oy)
		if d > ARM_MAX_CM:
			return ("the object %s is %.4f cm from the gripper and the arm "
				% [obj, d] + "reaches %.4f cm" % ARM_MAX_CM)
		_grip = "closed"
		_held = obj
		_carried = false
		_obj[obj] = [_arm_tip_x(), _arm_tip_y()]
		return ""
	if op == "gripper.place_at":
		if _held == "":
			return "the gripper holds nothing to place"
		if not _in_ball(x, y):
			return ("the placement would put the object at (%.4f, %.4f), which "
				% [x, y]
				+ "is outside the fc's ball of radius %.4f" % RADIUS)
		_obj[_held] = [x, y]
		_held = ""
		_carried = false
		_grip = "open"
		return ""
	if op == "gripper.hold":
		if _held == "":
			return "the gripper holds nothing to carry"
		_carried = true
		return ""

	# -- THE SENSING ---------------------------------------------------
	if op == "sensor.light" or op == "sensor.distance" \
			or op == "sensor.colour" or op == "body.position" \
			or op == "sensor.battery" or op == "sensor.sweep":
		return ""
	if op == "head.rotate":
		var delta2 := 0.0
		if verb == "look_up":
			delta2 = deg_to_rad(deg)
		elif verb == "look_down":
			delta2 = -deg_to_rad(deg)
		elif verb == "look_left":
			delta2 = deg_to_rad(deg)
		elif verb == "look_right":
			delta2 = -deg_to_rad(deg)
		else:
			return ("the operation %s does not say which way" % op)
		if verb == "look_up" or verb == "look_down":
			_pitch += delta2
		else:
			_yaw += delta2
		return ""
	if op == "head.look_at":
		var vx2 := x - _px
		var vy2 := y - _py
		if sqrt(vx2 * vx2 + vy2 * vy2) < 1e-9:
			return "the look-at target is the body's own position"
		_yaw = atan2(vy2, vx2)
		_pitch = 0.0
		return ""

	# -- THE EPISTEMIC -------------------------------------------------
	if op == "sim.assert_cause":
		_causes.append({"effect": str(args.get("effect", "")),
			"cause": str(args.get("cause", "")),
			"at": [_r(_px), _r(_py)]})
		return ""
	if op == "sim.promise":
		_promises.append({"state": str(args.get("state", "")),
			"at": [_r(_px), _r(_py)]})
		return ""

	return ("the operation %s is not one the body knows" % op)


# ---------------------------------------------------------------------------
# THE COMMAND'S OWN TICK, and it is the impulse and NOTHING ELSE, so the
# receipt shows the command's effect and not the drive's.
func _impulse_tick(path: Array) -> int:
	_imp_x = 0.0
	_imp_y = 0.0
	if not _ground_held():
		return 0
	if _session == "paused":
		return 0
	if _hold:
		# THE HOLD, and the body refuses to move further.
		path.append([_px, _py])
		return 1
	if _pend_x == 0.0 and _pend_y == 0.0:
		path.append([_px, _py])
		return 1
	_imp_x = _pend_x
	_imp_y = _pend_y
	_pend_x = 0.0
	_pend_y = 0.0
	var pr := _project(_px + _imp_x, _py + _imp_y)
	_px = float(pr[0])
	_py = float(pr[1])
	_vx = _imp_x / TICK
	_vy = _imp_y / TICK
	_batt = maxf(0.0, _batt - BATTERY_PER_CM
		* sqrt(_imp_x * _imp_x + _imp_y * _imp_y))
	path.append([_px, _py])
	return 1


# ---------------------------------------------------------------------------
# THE DRIVE, and it is the fc's step, over and over. **AND WITH THE GAIN
# AT ONE, ONE TICK ADVANCES THE BODY BY EXACTLY ONE FC KERNEL STEP** --
# which is what makes "the drive IS the fc's step" a measurable claim
# and not a resemblance.
func _drive(path: Array) -> int:
	var ran := 0
	# **AND THE UNTIL-ARRIVAL DRIVE RUNS TO MAX_TICKS, NOT TO
	# DRIVE_TICKS** -- MEASURED: capped at 12, a seek from 10 cm away
	# stopped 0.79 cm short of the hole, outside the 0.5 cm arrival
	# tolerance. **A SEEK MUST ACTUALLY ARRIVE.**
	var limit := MAX_TICKS if _drive_until_arrival else DRIVE_TICKS
	for _i in range(limit):
		# AND THE ARRIVAL TEST IS AGAINST THE DESTINATION, because a
		# command that names a point must arrive at THAT point.
		if _drive_until_arrival and _dest_distance() <= _arrival:
			break
		if not _ground_held():
			break
		if _session == "paused":
			break
		if _hold:
			path.append([_px, _py])
			ran += 1
			continue
		var st := _fc_step(_px, _py)
		var nx := float(st[0])
		var ny := float(st[1])
		var mvx := nx - _px
		var mvy := ny - _py
		_px = nx
		_py = ny
		_vx = mvx / TICK
		_vy = mvy / TICK
		_batt = maxf(0.0, _batt - BATTERY_PER_CM
			* sqrt(mvx * mvx + mvy * mvy))
		if _held != "":
			if _carried:
				_obj[_held] = [_px, _py]
			else:
				_obj[_held] = [_arm_tip_x(), _arm_tip_y()]
		path.append([_px, _py])
		ran += 1
	_drive_until_arrival = false
	return ran


## THE BALL, and it is the fc's constraint: a BALL of radius R about
## the ground, and not a square.
func _in_ball(x: float, y: float) -> bool:
	var dx := x - GROUND_X
	var dy := y - GROUND_Y
	return sqrt(dx * dx + dy * dy) <= RADIUS


# ---------------------------------------------------------------------------
# THE RENDER, and it draws the second body where it is.
func _render() -> void:
	_ball.position = _screen(_px, _py)
	_ball.linear_velocity = Vector2(_vx, -_vy) * PIXELS_PER_CM
	_ball.rotation = -_rot
	_arm.position = _screen(_px, _py)
	_arm.rotation = -_arm_ang
	_limb.size = Vector2(_arm_len * PIXELS_PER_CM, 4)
	_head.position = _screen(_px, _py)
	_head.rotation = -_yaw
	if _obj.has("cube"):
		var p: Array = _obj["cube"]
		_cube.position = _screen(float(p[0]), float(p[1]))


# ---------------------------------------------------------------------------
# THE STATE, and it is what the receipt carries.
func _r(x: float) -> float:
	return roundf(x * 1e9) / 1e9


func _state() -> Dictionary:
	var objs := {}
	for name in _obj.keys():
		var p: Array = _obj[name]
		objs[name] = [_r(float(p[0])), _r(float(p[1]))]
	return {
		"pos": [_r(_px), _r(_py)],
		"vel": [_r(_vx), _r(_vy)],
		"rot": _r(_rot),
		"arm": {"angle": _r(_arm_ang), "length": _r(_arm_len),
			"tip": [_r(_arm_tip_x()), _r(_arm_tip_y())]},
		"gripper": _grip,
		"held": _held,
		"carried": _carried,
		"head": {"yaw": _r(_yaw), "pitch": _r(_pitch)},
		"battery": _r(_batt),
		"light": _r(_light_reading()),
		"distance": _r(_hole_distance()),
		"colour": _colour_reading(),
		"objects": objs,
		"session": _session,
		"hold": _hold,
		"dest_distance": _r(_dest_distance()),
		"causes": _causes.size(),
		"promises": _promises.size(),
	}


# ---------------------------------------------------------------------------
# THE KERNEL, and it is the fc's own step printed over a few starts, so
# the checker can compare it with the fc's OWN module -- step for step,
# and not merely at its end. **AND ONE START IS OUTSIDE THE BALL OF
# RADIUS R, so the projection is exercised and not merely present.**
func _print_kernel() -> void:
	var starts: Array = [[8.0, 6.0], [-5.0, 3.0], [9.0, 9.0]]
	for st in starts:
		var pair: Array = st
		var x := float(pair[0])
		var y := float(pair[1])
		var parts := PackedStringArray()
		parts.append("%.12f %.12f" % [x, y])
		for _i in range(KERNEL_STEPS):
			var nxt := _fc_step(x, y)
			x = float(nxt[0])
			y = float(nxt[1])
			parts.append("%.12f %.12f" % [x, y])
		print("KERNEL ", " ".join(parts))


# ---------------------------------------------------------------------------
# THE LEDGER, and the CAUSES and the PROMISES.
func _print_ledger() -> void:
	print("CAUSES ", JSON.stringify(_causes))
	print("PROMISES ", JSON.stringify(_promises))


func _print_query(which: String) -> void:
	if which == "causes":
		print("QUERY ", JSON.stringify({"causes": _causes,
			"last_command": _last_verb}))
	elif which == "promises":
		print("QUERY ", JSON.stringify({"promises": _promises}))
	else:
		print("QUERY ", JSON.stringify({"error":
			"the sim is asked about causes and promises, and %s is "
			% which + "neither"}))


# ---------------------------------------------------------------------------
# THE PATH, and it is printed at full precision so the drive can be
# compared with the fc's kernel step for step.
func _fmt_path(path: Array) -> String:
	var parts := PackedStringArray()
	for p in path:
		parts.append("%.12f %.12f" % [float(p[0]), float(p[1])])
	return " ".join(parts)


# ---------------------------------------------------------------------------
# THE TRACE, and it is JSON, one line per command, so a checker can read
# it without parsing prose.
func _print_trace() -> void:
	print("SIM ", JSON.stringify({"eta": ETA, "radius": RADIUS,
		"tick": TICK, "arrival": ARRIVAL_CM, "tol": CONVERGENCE_TOL,
		"drive_ticks": DRIVE_TICKS, "arm_max": ARM_MAX_CM,
		"arm_len": ARM_LEN_CM, "start": [START_X, START_Y],
		"cube_home": [CUBE_HOME_X, CUBE_HOME_Y],
		"explore_cm": EXPLORE_CM, "explore_turn": EXPLORE_TURN,
		"battery_per_cm": BATTERY_PER_CM, "kernel_steps": KERNEL_STEPS}))
	print("=== THE ROBOT'S BODY ===")
	print("  the commands read:    %d" % _commands.size())
	print("  the commands applied: %d" % _index)
	print("  the commands refused: %d" % _refused.size())
	for r in _refused:
		print("    REFUSED %s: %s" % [str(r.get("verb", "")),
			str(r.get("reason", ""))])
	print("  the final position:   (%.4f, %.4f)" % [_px, _py])
	print("  the distance to the hole: %.4f" % _hole_distance())
	print("  the ground held:      %s" % str(_ground_held()))
	print("  the session:          %s" % _session)
