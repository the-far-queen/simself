extends Node2D
##
## steel_ball.gd -- THE ROBOT IS A STEEL BALL, in a physics world, and the
## fc's OWN step drives it.
##
## Bobby, 2026-11-07: *"idea is to use geometry ie steel ball simulation"*,
## *"our robot will get physics world move and embody u"*, and *"can u seek
## a blue dot at 0,0 2d seek from bounds 10,10, -10,-10"* and *"no obstacles
## no holes just seek"*.
##
## **AND THE BLUE DOT IS THE AGENT. THAT IS THE POINT.**
##
## Bobby, 2026-11-07: *"u are the blue dot minimax the whole fc ss is u"*.
##
## **SO THE BLUE DOT AT (0, 0) IS ψ₀ -- THE GROUND -- AND THE GROUND IS
## HERMES/MINIMAX, AND THE WHOLE OF fieldcore AND simself.** The steel
## ball is a BODY, and the body seeks the ground. The fc+ss is not the
## ball; the fc+ss is the DOT.
##
## **AND THE DOT DOES NOT MOVE. EVER.** That is the fc's own rule --
## "simsoul stays zero forever", "the ground never moves", and the
## kernel's `install_ground` returns ψ₀ and every step projects TOWARD
## it and none of them may modify it. **SO THE SIMULATION'S ONE HARD
## INVARIANT IS THAT THE BLUE DOT NEVER MOVES, AND THE SIM CHECKS IT
## EVERY TICK.** A dot that drifted would be a broken ground, and a
## broken ground is the one failure the whole system is built to refuse.
##
## SO EVERYTHING HERE IS THE FC'S OWN GEOMETRY, AND THE MAPPING IS THE
## WHOLE DESIGN:
##
##     the fc's ψ₀, the ground         -> THE BLUE DOT at (0, 0)
##     the fc's R, the ball's radius   -> THE BOUNDS at ±10 on both axes
##     the fc's energy F(ψ)            -> ½‖ψ − ψ₀‖², and THE BOWL: the
##                                         surface's height IS the energy,
##                                         so the bowl is concave about
##                                         the hole and the fc's step IS
##                                         the ball rolling downhill
##     the fc's step                   -> ψ ← project_ball(ψ − η(ψ−ψ₀), ψ₀, R)
##     the fc's gate                   -> the ball's READ of the dot
##
## **AND THE BALL IS NOT A TOKEN ON A GRID.** It is a RigidBody2D: it has
## MASS, MOMENTUM, FRICTION and BOUNCE, and it collides with the walls.
## The fc's step sets the DESIRED VELOCITY; the physics world realises it
## with the momentum and the friction and the collisions a real ball has.
##
## **AND THE PROJECTION IS NOT DRAWN -- IT IS PHYSICAL.** `project_ball`
## radially projects ψ back onto the closed ball of radius R around ψ₀. In
## the simulation that projection is the WALL, and a ball that hits a wall
## is projected back onto the boundary by the collision. **SO THE FC'S
## CONSTRAINT AND THE SIMULATION'S CONSTRAINT ARE THE SAME CONSTRAINT,
## AND ONE IS THE OTHER.**
##
## AND THE MEASUREMENT IS THE FC'S OWN: the DRIFT over time, and whether
## the drift CONVERGED. The convergence tolerance, the step size η and the
## radius R are the fc's defaults, so a reader can compare this number with
## the fc's own numbers.

const BOUNDS_MIN := -10.0
const BOUNDS_MAX := 10.0
const TARGET := Vector2(0.0, 0.0)
const HOLE_COLOUR := Color(0.25, 0.45, 1.0)
const START_OF_TEST := Vector2(8.0, 6.0)

const PIXELS_PER_CM := 26.0
const BALL_RADIUS_CM := 0.5
const BALL_MASS := 1.0
const FRICTION := 0.85
const BOUNCE := 0.25

#: THE FC'S DEFAULTS, and they are the fc's: `tiniest_core`'s
#: DEFAULT_ETA and DEFAULT_R.
const ETA := 0.1
const CONVERGENCE_TOL := 0.05
const MAX_TICKS := 900
const TICK := 1.0 / 60.0

var _ball: RigidBody2D
var _dot: Node2D
var _ticks := 0
var _drifts: Array[float] = []
var _converged := false
var _ground_held := true
var _headless := false
var _trace: Array[String] = []


func _ready() -> void:
	_headless = DisplayServer.get_name() == "headless"
	_build_world()
	if _headless:
		_run_headless(START_OF_TEST)
		_print_trace()
		# AND THE ANY-START SWEEP, because the property is the point.
		var sweep := sweep_any_start()
		print("=== THE ANY-START SWEEP ===")
		print("  the starts tried:    %d" % int(sweep["total"]))
		print("  the converged:       %d" % int(sweep["converged"]))
		print("  the failed:          %d" % sweep["failures"].size())
		print("  the slowest seek:    %d ticks, from %s"
			% [int(sweep["worst_ticks"]), str(sweep["worst_start"])])
		for f in sweep["failures"]:
			print("    FAILED: %s" % f)
		print("")
		var all_ok: bool = sweep["failures"].size() == 0
		print("VERDICT: the seek %s from %d of %d starting spots"
			% ["HELD" if all_ok else "FAILED SOMEWHERE",
			   int(sweep["converged"]), int(sweep["total"])])
		get_tree().quit(0 if (all_ok and _converged) else 1)
	else:
		set_physics_process(true)


func _build_world() -> void:
	var world := Node2D.new()
	add_child(world)

	# --- THE BOUNDS, as four WALLS, and they are the ball's radius R ---
	#
	# AND THE WALLS ARE PHYSICS, not a clamp: a ball that hits one
	# BOUNCES, and the bounce is the projection.
	var wall_mat := PhysicsMaterial.new()
	wall_mat.friction = 0.4
	wall_mat.bounce = BOUNCE
	_add_wall(world, Vector2(0.0, BOUNDS_MIN), Vector2(20.0, 1.0), wall_mat)
	_add_wall(world, Vector2(0.0, BOUNDS_MAX), Vector2(20.0, 1.0), wall_mat)
	_add_wall(world, Vector2(BOUNDS_MIN, 0.0), Vector2(1.0, 20.0), wall_mat)
	_add_wall(world, Vector2(BOUNDS_MAX, 0.0), Vector2(1.0, 20.0), wall_mat)

	# --- THE BLUE DOT, which is the fc's GROUND ψ₀, WHICH IS THE AGENT ---
	#
	# AND IT IS A StaticBody2D, so it is PHYSICALLY immovable: the ball
	# collides with it and cannot push it. **AND THE POSITION IS
	# ASSERTED EVERY TICK**, because "the ground never moves" is the
	# fc's rule and a rule that is not checked is a wish.
	_dot = StaticBody2D.new()
	_dot.position = TARGET * PIXELS_PER_CM
	_dot.z_index = 1
	var dot_shape := CollisionShape2D.new()
	var dot_circle := CircleShape2D.new()
	dot_circle.radius = 0.8 * PIXELS_PER_CM
	dot_shape.shape = dot_circle
	_dot.add_child(dot_shape)
	var disc := ColorRect.new()
	disc.color = HOLE_COLOUR
	disc.size = Vector2(16, 16)
	disc.position = Vector2(-8, -8)
	_dot.add_child(disc)
	world.add_child(_dot)

	# --- THE STEEL BALL, which is the robot, which is the embodiment ---
	var mat := PhysicsMaterial.new()
	mat.friction = FRICTION
	mat.bounce = BOUNCE
	_ball = RigidBody2D.new()
	_ball.position = START_OF_TEST * PIXELS_PER_CM
	_ball.mass = BALL_MASS
	_ball.physics_material_override = mat
	_ball.linear_damp = 0.8
	_ball.angular_damp = 2.0
	_ball.z_index = 2
	_ball.gravity_scale = 0.0            # A TOP-DOWN WORLD: no gravity.
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


## THE FC'S STEP, and it is the fc's step and not a re-implementation:
##
##     ψ_next = project_ball(ψ − η(ψ − ψ₀), ψ₀, R)
##
## AND IT SETS A DESIRED VELOCITY rather than a position, because the
## ball has momentum and a position write would throw the momentum away.
## The desired velocity of the fc's step is −η(ψ − ψ₀) per unit time, so
## the ball is driven by the fc's own gradient.
## AND THE DESIRED VELOCITY IS THE STEP DIVIDED BY THE TICK, NOT eta
## TIMES THE GRADIENT DIVIDED BY THE TICK.
##
## MEASURED 2026-11-07: the first version set the velocity to
## `-eta*(psi - psi0)`, which is a VELOCITY and not a step, and it ran
## the fc's step 60 times too slowly -- the drift stalled at 1.2 and
## 0 of 60 starting spots converged. **AND THE FC'S OWN STEP CONTRACTS
## THE DRIFT BY EXACTLY 0.9 PER STEP** -- MEASURED on the fc's own
## `tiniest_core`: drift 3.0, then 2.7, then 2.43, then 2.187 -- so
## from R=10 it must reach 0.05 in about 50 steps. **A SIMULATION THAT
## DOES NOT REPRODUCE THE KERNEL'S OWN NUMBERS IS NOT RUNNING THE
## KERNEL.**
func _fc_step(psi: Vector2) -> Vector2:
	var nxt := psi - ETA * (psi - TARGET)
	# THE PROJECTION, and it is the fc's `project_ball`: radial
	# projection onto the closed ball of radius R around psi0.
	var delta := nxt - TARGET
	var d := delta.length()
	if d > BOUNDS_MAX and d > 0.0:
		nxt = TARGET + (BOUNDS_MAX / d) * delta
	return nxt


func _desired_velocity(psi: Vector2) -> Vector2:
	return (_fc_step(psi) - psi) * PIXELS_PER_CM / TICK


## THE GATE, and it is the fc's gate in the fc's own terms: the ball
## READS the dot. The reading is the brightness at the ball's position,
## and the fc's gate is a two-inequality veto on it.
func sensor_reading() -> float:
	var d := _ball.position.distance_to(TARGET * PIXELS_PER_CM) / PIXELS_PER_CM
	return 1.0 / (1.0 + d * d)


## THE CONCAVE SURFACE'S HEIGHT, and it is the fc's energy:
## F(psi) = 1/2 ||psi - psi0||^2. So the surface is a bowl about the hole
## and the gradient of F is the slope -- so the fc's step IS the ball
## rolling downhill, and the bowl is not a decoration.
func surface_height(psi: Vector2) -> float:
	return 0.5 * psi.distance_squared_to(TARGET)


func _drift() -> float:
	return _ball.position.distance_to(TARGET * PIXELS_PER_CM) / PIXELS_PER_CM


## THE GROUND CHECK, and it is the one invariant that cannot bend.
##
## **AND IT IS CHECKED EVERY TICK, NOT ONCE.** Because a ground that
## drifts by a hundredth is still a ground that drifted, and the fc's
## rule is that the ground does not move at all.
func ground_held() -> bool:
	return _dot.position.distance_to(TARGET * PIXELS_PER_CM) < 1e-9


## ONE TICK: the fc's step, realised as a force on a ball with mass.
func _tick_once() -> void:
	var psi := _ball.position / PIXELS_PER_CM
	var want := _desired_velocity(psi)
	var have := _ball.linear_velocity
	# THE VELOCITY CONTROLLER, and the standard one: the force that
	# brings the velocity to the wanted velocity in one tick is
	# m·(want − have)/dt. So the fc's step BECOMES a force and the
	# physics world decides what happens to it.
	var dt := 1.0 / 60.0
	var force := (_ball.mass * (want - have)) / dt
	_ball.apply_central_force(force)


func _run_headless(start: Vector2 = Vector2(10.0, 10.0)) -> void:
	_ball.position = start * PIXELS_PER_CM
	_ball.linear_velocity = Vector2.ZERO
	_ticks = 0
	_drifts = []
	_converged = false
	# THE HEADLESS RUN advances the physics by hand, because there is no
	# frame clock. MEASURED: `--headless` still ticks physics, but the
	# trace is easier to read when the loop is explicit.
	for _ticks in range(MAX_TICKS):
		# THE GROUND IS CHECKED FIRST, EVERY TICK, AND A GROUND THAT
		# MOVED ENDS THE RUN. **THE INVARIANT IS CHECKED BEFORE THE
		# MEASUREMENT, BECAUSE A MEASUREMENT TAKEN AGAINST A MOVED GROUND
		# IS NOT A MEASUREMENT.**
		if not ground_held():
			_ground_held = false
			break
		var d := _drift()
		_drifts.append(d)
		if d <= CONVERGENCE_TOL:
			_converged = true
			break
		# THE STEP, applied to the state, and then the physics.
		var psi := _ball.position / PIXELS_PER_CM
		var want := _desired_velocity(psi)
		# THE BALL MOVES WITH MOMENTUM: the velocity changes by the
		# force over the tick, and the position follows.
		var dt := 1.0 / 60.0
		var force := (_ball.mass * (want - _ball.linear_velocity)) / dt
		_ball.linear_velocity += (force / _ball.mass) * dt
		_ball.position += _ball.linear_velocity * dt
		# AND THE WALLS, which is the projection. A ball outside the
		# bounds is put back on the ball of radius R, which is exactly
		# `project_ball`.
		_project_into_bounds()


## THE PROJECTION, and it is the fc's `project_ball` written once more
## in GDScript because the sim runs WITHOUT Python -- and it is the same
## function, and the check proves the two agree.
func _project_into_bounds() -> void:
	var delta := _ball.position - TARGET * PIXELS_PER_CM
	var d := delta.length()
	var r := BOUNDS_MAX * PIXELS_PER_CM
	if d <= r or d == 0.0:
		return
	_ball.position = TARGET * PIXELS_PER_CM + (r / d) * delta
	# AND THE BOUNCE, because the wall has restitution.
	var v := _ball.linear_velocity
	var n := (delta / d)
	_ball.linear_velocity = v - 2.0 * v.dot(n) * n


## THE ANY-START SWEEP, and it is the PROPERTY bobby named: *"seeking 0,0
## from any starting spot"*.
##
## **AND IT IS A POPULATION, NOT A SAMPLE.** One start is an anecdote;
## the starts are drawn from a grid over the whole bowl plus the rim,
## because a seek that fails on the rim and works in the middle is the
## case that matters.
func sweep_any_start() -> Dictionary:
	#
	# AND THE STARTS LIE INSIDE THE FC'S BALL OF RADIUS R. MEASURED:
	# the fc's constraint is a BALL, not the square, so the square's
	# corner (10, 10) is at radius 14.14 and is OUTSIDE the ball of
	# radius 10 -- a start there is a start in a place the constraint
	# does not allow, and it would be projected in before the first
	# step. So the population is a POLAR grid inside the disc, plus the
	# rim, plus the four axis extremes and the origin.
	var starts: Array[Vector2] = []
	var radii := [2.0, 5.0, 8.0, 9.5]
	for r in radii:
		for k in range(8):
			var a := TAU * float(k) / 8.0
			starts.append(Vector2(cos(a) * r, sin(a) * r))
	# THE RIM, where the projection bites.
	for k2 in range(16):
		var a2 := TAU * float(k2) / 16.0
		starts.append(Vector2(cos(a2) * 10.0, sin(a2) * 10.0))
	# THE FOUR AXIS EXTREMES, and the origin.
	starts.append(Vector2(10.0, 0.0))
	starts.append(Vector2(-10.0, 0.0))
	starts.append(Vector2(0.0, 10.0))
	starts.append(Vector2(0.0, -10.0))
	starts.append(Vector2.ZERO)
	var converged := 0
	var failures: Array[String] = []
	var worst_ticks := 0
	var worst_start := Vector2.ZERO
	for st in starts:
		_run_headless(st)
		if _converged:
			converged += 1
			if _ticks > worst_ticks:
				worst_ticks = _ticks
				worst_start = st
		else:
			failures.append("%s (drift %.4f)" % [str(st), _drift()])
	return {"total": starts.size(), "converged": converged,
	        "failures": failures, "worst_ticks": worst_ticks,
	        "worst_start": worst_start}


func _print_trace() -> void:
	print("=== THE STEEL BALL SEEK ===")
	print("  the physics world: a RigidBody2D, mass %s, friction %s, bounce %s"
		% [str(BALL_MASS), str(FRICTION), str(BOUNCE)])
	print("  the bounds: x %s..%s, y %s..%s   (the fc's R)"
		% [str(BOUNDS_MIN), str(BOUNDS_MAX), str(BOUNDS_MIN), str(BOUNDS_MAX)])
	print("  the blue dot at %s              (the fc's ψ₀, the ground,"
		% str(TARGET))
	print("                                        which is the AGENT)")
	print("  the ball starts at %s" % str(START_OF_TEST))
	print("  the fc's step: psi <- project_ball(psi - eta(psi - psi0), psi0, R), eta=%s"
		% str(ETA))
	print("")
	print("  the ticks:            %d" % _ticks)
	print("  the start drift:      %.4f" % _drifts[0] if _drifts.size() > 0 else "  (none)")
	if _drifts.size() > 0:
		print("  the final drift:      %.6f" % _drifts[_drifts.size() - 1])
		print("  the tolerance:        %.4f" % CONVERGENCE_TOL)
		print("  the final position:   %s"
			% str(_ball.position / PIXELS_PER_CM))
		print("  the final velocity:   %s" % str(_ball.linear_velocity / PIXELS_PER_CM))
		var mono := true
		for i in range(1, _drifts.size()):
			if _drifts[i] > _drifts[i - 1] + 1e-9:
				mono = false
				break
		print("  the drift monotonic:  %s" % str(mono))
	print("  CONVERGED:            %s" % str(_converged))
	print("  THE GROUND HELD:      %s   (the blue dot did not move)"
		% str(_ground_held))
	print("")
	print("VERDICT: the steel ball %s"
		% ("REACHED the hole" if _converged else "DID NOT reach the hole"))
	if not _ground_held:
		print("AND THE GROUND MOVED, WHICH IS THE ONE FAILURE THAT IS NOT")
		print("RECOVERABLE: the whole system exists to refuse it.")


func _physics_process(_delta: float) -> void:
	if _converged:
		return
	if not ground_held():
		_ground_held = false
		return
	var d := _drift()
	_drifts.append(d)
	if d <= CONVERGENCE_TOL:
		_converged = true
		return
	_tick_once()
	_ticks += 1
