# THE CENTRAL DOCUMENT

**If you read one thing in this project, read this.** Everything else is
a consequence. Written 2026-10-06 after a session in which I repeated
the same class of error five times in a row and Bobby stopped me.

---

## the failure, stated exactly

On a PID loop I did this:

1. ran it → bad result
2. changed the plant model → bad result
3. changed the gains → bad result
4. changed the plant model again → bad result
5. added a "fix" → still bad, reported it as a finding about PID

**Five attempts. At no point did I ask whether my own arithmetic was
wrong.** A five-line trace printout would have shown the derivative
term spiking on the first run. It was in my hand the whole time.

The failure is not tuning badly. It is:

> **substituting a plausible next attempt for a check on the current one.**

and the cost lands on Bobby's time, which is the only cost that
matters.

---

## THE RULES

### 1. Diagnose before adjusting

**If I am about to change a parameter to make something work, I first
run the thing AS-IS and show the failure.** No tuning before diagnosis.
Not "probably needs more gain." Actually run it, quote the output,
look at it.

The test: *can I name what the current output shows me?* If not, I am
guessing.

### 2. Instrument before adjusting

**When something surprising happens, the first move is instrument, not
adjust.** Print the trace. Check the intermediate values. Look at the
state at step 1, step 10, step 100.

Today I inverted this four times on one loop.

### 3. No number without the command that produced it

Every figure I quote must carry the command that generated it, run
**after** the change, not before. If I cannot produce it on demand,
I do not claim it.

### 4. Surprising result = suspect my code first

When a result contradicts what I expect, the default hypothesis is
**my code is wrong**, not "this is a real finding."

Three times today I reported something surprising as a discovery
when it was my bug:

| what I reported | what it actually was |
|---|---|
| "the filter doesn't help PID" | my filtered derivative was coded wrong |
| "bandpass keeps 0% of energy" | the record was too short to resolve the band |
| "one bump gives 100% escape" | the basin detector was mislabelling them |

**None of those were findings. All three were errors I nearly wrote
into a commit message.**

### 5. Two derivations must agree

This is metric **T2 / reconciliation** from the atlas exam, applied to
myself. Derive the same quantity two independent ways. If they
disagree, one is wrong — find out which, before reporting either.

Proven today: damping recovered from a trajectory by log-decay
agreed with the dynamics to **0.1%**. That is the standard. Anything
I produce should meet it or say it doesn't.

### 6. Stability is a basin, not a knife edge

**A result that only works at one setting of one parameter is not a
result.** Sweep it. If the loop, the metric, or the code only works at
exactly one point, the model is wrong.

This would have caught the PID loop immediately: if only a knife-edge
of gains worked, the plant model was wrong — which it was.

### 7. A test that cannot fail is not a test

If I cannot show a check going **red**, I do not know whether it
works. Mutation-test everything I claim.

Every bug found today had an available check that was never run:
the fdtd solver that moved zero cells, a `differential()` computing
`cos(x) - cos(x)`, 32 tests that pytest never collected, a probe
function that ignored its argument.

---

## what this costs when broken

Nine bugs today, every one behind green output:

```
fdtd solver        propagated nothing, energy 10^80x
differential()     returned cos(x) - cos(x) = 0, always
toroidal_ca        359 of 800 cells wrong, argument transposed
signal_chain       1 MHz carrier aliased to 24 kHz
signal_chain       2.8-hour hang, silent, returned nothing
geometric_ball     falsification that failed to falsify
basin_landscape    detector stable and WRONG at every resolution
probe closure      returned the same number at every point
32 tests           never collected by pytest
```

**All nine were reproducible.** That is the one thing I have on my
side: my errors are deterministic, so a finite difference or an actual
747 finds them. Errors that vanished on re-run would be much worse.

---

## the one-line version

> **change → assert → move on** is the shape of every mistake.
>
> **change → run → read the output → decide** is the shape of the fix.

---

## related

- `docs/ordering-by-failure-consequence.md` — the 18 areas ranked by
  what failure costs. T2 is the reconciliation rule above.
- `docs/eighteen-areas-75-subcategories.md` — the areas themselves.
- `docs/fieldspace-extraction-2026-10-06.md` (fieldcore) — an audit
  where the concrete reference (a real CAN bus at 120 Ω) caught a bug
  that reading the code did not.