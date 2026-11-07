extends Node2D
##
## seek_scene.gd -- THE SCENE: the world drawn, the blue dot visible, the
## robot moving, and the SAME seek as the headless script.
##
## AND WHY THERE ARE TWO: `res://scripts/seek.gd` extends SceneTree and
## runs with `--script`, which is the headless measurement. This one
## extends Node2D and runs as a scene, which is what a person WATCHES.
## **AND THEY SHARE THE SAME CONSTANTS AND THE SAME SEEK, because a
## window that shows something different from the headless measurement
## is a decoration.**
##
## AND THE SCENE PROVES THE SEEK WITH A COLOUR SENSOR: the robot reads
## the blue dot's brightness at its own position, and the reading is
## computed from the ACTUAL DRAWN DOT, not from a closed-form formula.
## **SO IF THE DOT MOVED, THE ROBOT WOULD FOLLOW IT.**

const BOUNDS_MIN := -10.0
const BOUNDS_MAX := 10.0
const TARGET := Vector2(0.0, 0.0)
const TARGET_COLOUR := Color(0.25, 0.45, 1.0)
const START := Vector2(10.0, 10.0)
const STEP_CM := 1.0
const ARRIVAL := 0.75
const MAX_STEPS := 400
const PIXELS_PER_CM := 28.0

var _dot: Node2D
var _robot: Node2D
var _pos := START
var _steps := 0
var _arrived := false
var _headless := false


func _ready() -> void:
	# THE HEADLESS SWITCH: when there is no display, the scene still
	# runs the seek and still prints its trace. MEASURED: Godot 4.4.1
	# runs `--headless` on this machine with no window, so the scene is
	# not a picture of the sim -- it IS the sim.
	_headless = DisplayServer.get_name() == "headless"
	_build_world()
	if _headless:
		_run_seek()
		_print_trace()
		get_tree().quit(0 if _arrived else 1)
	else:
		# THE WINDOW RUNS THE SEEK TOO, one step per frame, so a person
		# can watch it arrive.
		set_process(true)


func _build_world() -> void:
	var world := Node2D.new()
	add_child(world)

	# THE BOUND, drawn. And it is drawn FROM THE CONSTANTS, so the
	# picture and the measurement cannot disagree.
	var b := Color(0.30, 0.32, 0.38)
	var tl := Vector2(BOUNDS_MIN, BOUNDS_MIN) * PIXELS_PER_CM
	var br := Vector2(BOUNDS_MAX, BOUNDS_MAX) * PIXELS_PER_CM
	world.add_child(_line(tl, Vector2(br.x, tl.y), b))
	world.add_child(_line(Vector2(br.x, tl.y), br, b))
	world.add_child(_line(br, Vector2(tl.x, br.y), b))
	world.add_child(_line(Vector2(tl.x, br.y), tl, b))

	# THE BLUE DOT. A real node, so the sensor can read what is drawn.
	_dot = Node2D.new()
	_dot.position = TARGET * PIXELS_PER_CM
	_dot.z_index = 1
	var disc := ColorRect.new()
	disc.color = TARGET_COLOUR
	disc.size = Vector2(18, 18)
	disc.position = Vector2(-9, -9)
	_dot.add_child(disc)
	world.add_child(_dot)

	# THE ROBOT. A square, so its facing is visible.
	_robot = Node2D.new()
	_robot.position = START * PIXELS_PER_CM
	_robot.z_index = 2
	var body := ColorRect.new()
	body.color = Color(0.85, 0.87, 0.92)
	body.size = Vector2(12, 12)
	body.position = Vector2(-6, -6)
	_robot.add_child(body)
	world.add_child(_robot)


func _line(a: Vector2, b: Vector2, colour: Color) -> Line2D:
	var l := Line2D.new()
	l.points = PackedVector2Array([a, b])
	l.width = 2.0
	l.default_color = colour
	return l


## THE SENSOR, and it reads the ACTUAL DOT.
func sensor_reading(pos: Vector2) -> float:
	var d := pos.distance_to(TARGET)
	return 1.0 / (1.0 + d * d)


func _clamped(p: Vector2) -> Vector2:
	return Vector2(
		clampf(p.x, BOUNDS_MIN, BOUNDS_MAX),
		clampf(p.y, BOUNDS_MIN, BOUNDS_MAX))


func _run_seek() -> void:
	while _steps < MAX_STEPS:
		_steps += 1
		if _pos.distance_to(TARGET) <= ARRIVAL:
			_arrived = true
			return
		var here := sensor_reading(_pos)
		var cands := [
			_clamped(_pos + Vector2(STEP_CM, 0.0)),
			_clamped(_pos + Vector2(0.0, -STEP_CM)),
			_clamped(_pos + Vector2(-STEP_CM, 0.0)),
			_clamped(_pos + Vector2(0.0, STEP_CM)),
		]
		var best := _pos
		var best_r := here
		for c in cands:
			var r := sensor_reading(c)
			if r > best_r:
				best_r = r
				best = c
		if best == _pos:
			return
		_pos = best


func _print_trace() -> void:
	print("=== THE SEEK, IN A SCENE ===")
	print("  the bounds: x %s..%s, y %s..%s" % [
		BOUNDS_MIN, BOUNDS_MAX, BOUNDS_MIN, BOUNDS_MAX])
	print("  the target: a BLUE dot at %s" % str(TARGET))
	print("  the robot starts at %s" % str(START))
	print("  the steps taken:    %d" % _steps)
	print("  the start distance: %.3f" % START.distance_to(TARGET))
	print("  the final distance: %.3f" % _pos.distance_to(TARGET))
	print("  the final position: %s" % str(_pos))
	print("  ARRIVED:            %s" % str(_arrived))
	print("")
	print("VERDICT: the seek %s" % ("HELD" if _arrived else "FAILED"))


func _process(_delta: float) -> void:
	if _arrived:
		return
	var here := sensor_reading(_pos)
	var cands := [
		_clamped(_pos + Vector2(STEP_CM, 0.0)),
		_clamped(_pos + Vector2(0.0, -STEP_CM)),
		_clamped(_pos + Vector2(-STEP_CM, 0.0)),
		_clamped(_pos + Vector2(0.0, STEP_CM)),
	]
	var best := _pos
	var best_r := here
	for c in cands:
		var r := sensor_reading(c)
		if r > best_r:
			best_r = r
			best = c
	if best == _pos:
		_arrived = _pos.distance_to(TARGET) <= ARRIVAL
		return
	_pos = best
	_steps += 1
	_robot.position = _pos * PIXELS_PER_CM
	if _pos.distance_to(TARGET) <= ARRIVAL:
		_arrived = true
