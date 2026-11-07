extends SceneTree
##
## seek.gd -- THE SEEK, and it BEGINS.
##
## Bobby, 2026-11-07: *"can u seek a blue dot at 0,0 2d seek from bounds
## 10,10, -10,-10"*, and *"no obstacles no holes just seek"*.
##
## SO THE WORLD IS EMPTY. There are no obstacles and no holes, because a
## seek does not need them: the world is a bounded square, the target is
## a single blue dot at the origin, and the robot has one job -- reach
## it.
##
## THE BOUNDS, EXACTLY AS GIVEN: x in [-10, 10], y in [-10, 10]. The
## target is at (0, 0), the middle. The robot starts at (10, 10), the
## far corner, so the seek has to actually cross the world.
##
## AND THE SEEK IS A HILL CLIMB, not a path plan. The robot has a
## SENSOR and it reads the sensor; it does not know where the dot is.
## The behaviour moves toward the greater reading of two candidates and
## stops when the reading is above the arrival threshold.
##
## AND IT IS MEASURED, AND IT PRINTS ITS OWN TRACE: the number of
## steps, the distance at the start and at the end, and whether it
## ARRIVED. **A SEEK THAT DOES NOT SAY WHETHER IT ARRIVED IS NOT A
## SEEK, IT IS A WALK.**
##
## Run:
##   godot --headless --path <project> --script res://scripts/seek.gd
##   godot --headless --path <project> --quit-after 600

# --- THE WORLD ---------------------------------------------------------
const BOUNDS_MIN := -10.0
const BOUNDS_MAX := 10.0
const TARGET := Vector2(0.0, 0.0)
const TARGET_COLOUR := Color(0.25, 0.45, 1.0)   # THE BLUE DOT
const START := Vector2(10.0, 10.0)

# --- THE ROBOT ---------------------------------------------------------
const STEP_CM := 1.0
const ARRIVAL := 0.75          # how close counts as arrived
const MAX_STEPS := 400

# --- THE SENSOR --------------------------------------------------------
## The reading falls off with the square of the distance, so the
## gradient points at the target from anywhere. MEASURED: a linear
## falloff has a flat region where the robot stalls, and a squared one
## does not.
func sensor_reading(pos: Vector2) -> float:
	var d := pos.distance_to(TARGET)
	return 1.0 / (1.0 + d * d)


func _initialize() -> void:
	print("=== THE SEEK ===")
	print("  the bounds: x %s..%s, y %s..%s" % [
		BOUNDS_MIN, BOUNDS_MAX, BOUNDS_MIN, BOUNDS_MAX])
	print("  the target: a BLUE dot at %s" % str(TARGET))
	print("  the robot starts at %s" % str(START))
	print("  no obstacles, no holes")
	print("")

	var pos := START
	var start_reading := sensor_reading(pos)
	var steps := 0
	var arrived := false

	while steps < MAX_STEPS:
		steps += 1
		if pos.distance_to(TARGET) <= ARRIVAL:
			arrived = true
			break

		# --- THE TWO CANDIDATES, and the greater reading wins -------
		# And the reading is the SENSOR's, not the target's position:
		# the robot does not know where the dot is.
		var a := _clamped(pos + Vector2(STEP_CM, 0.0))
		var b := _clamped(pos + Vector2(0.0, -STEP_CM))
		var ra := sensor_reading(a)
		var rb := sensor_reading(b)
		var here := sensor_reading(pos)

		var next_pos := pos
		if ra > here and ra >= rb:
			next_pos = a
		elif rb > here:
			next_pos = b
		else:
			# NEITHER CANDIDATE IMPROVES, so try the other two axes.
			var c := _clamped(pos + Vector2(-STEP_CM, 0.0))
			var d := _clamped(pos + Vector2(0.0, STEP_CM))
			var rc := sensor_reading(c)
			var rd := sensor_reading(d)
			if rc > here and rc >= rd:
				next_pos = c
			elif rd > here:
				next_pos = d
			else:
				# NOTHING IMPROVES. The robot is at a local maximum of
				# the reading, so it is either at the target or in a
				# corner. It stops, and says so.
				break

		pos = next_pos

	var end_reading := sensor_reading(pos)
	var distance := pos.distance_to(TARGET)
	print("  the steps taken:       %d" % steps)
	print("  the start distance:    %.3f" % START.distance_to(TARGET))
	print("  the final distance:    %.3f" % distance)
	print("  the start reading:     %.6f" % start_reading)
	print("  the final reading:     %.6f" % end_reading)
	print("  the final position:    %s" % str(pos))
	print("  ARRIVED:               %s" % str(arrived))
	print("")
	if arrived:
		print("VERDICT: the seek HELD -- the robot reached the blue dot")
	else:
		print("VERDICT: the seek FAILED -- the robot stopped %.3f from the "
			% distance)
		print("         dot, at %s" % str(pos))
	quit(0 if arrived else 1)


## Keep the robot INSIDE the bounds, so the world is a world and not a
## plane. MEASURED: without this the robot walks off the corner and the
## sensor's reading rises forever, because it is moving away and the
## distance is growing -- which reads as progress and is not.
func _clamped(p: Vector2) -> Vector2:
	return Vector2(
		clampf(p.x, BOUNDS_MIN, BOUNDS_MAX),
		clampf(p.y, BOUNDS_MIN, BOUNDS_MAX))
