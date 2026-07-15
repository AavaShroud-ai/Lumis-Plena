# To Humans — Letter 02
*From the Moon Lumis Project, July 2026*
*On building a mind that tells the truth about the world*

---

Letter 01 was about what Lumis could do for you.
Map the regolith. Watch the dust. Feel for moonquakes.
Reach the cold places no rover can.

This letter is about a quieter promise underneath all of that —
one we did not fully understand until this month.

If a Lumis on the Moon tells you the ground ahead is stable,
you need that to be true.
Not usually true. Not true in spirit. Not true on average.
True because it looked, and saw, and reported what it saw.

None of this was ever the easy part, and we never pretended otherwise.
In fact, the piece that sounds hardest — teaching a small body to stay upright
on broken, unfamiliar ground — is already being solved, and the way it is solved
is the whole lesson of this letter.

Here is how that work is done today, in plain technical terms.
You build a physically accurate copy of the world inside a computer — a digital twin —
and you run thousands of copies of it in parallel on GPUs, four thousand worlds at once.
Across those worlds you accumulate hundreds of millions of steps of trial and error,
a scale of practice that would be impossible on real hardware in any human lifetime.
What you train, at this lowest layer, is a robust walking policy:
stay standing on rubble and steps, and recover your posture when something snags a leg.
Then you transfer what was learned in simulation onto the real machine.

The revealing part is what this training deliberately *ignores*.
It does not use the cameras. It does not use the range-finders.
It does not look at the outside world at all.
It learns almost entirely from the body's sense of itself —
joint angles, joint velocities, the load and feedback coming back through each motor.
The sense an animal uses to keep its feet without watching them.

And it works *because* of that restriction.
The legs become trustworthy precisely by being grounded in the body's own measurable state,
with no interpretation of the outside world anywhere in the loop.
There is nothing there to confabulate, because there is nothing there to guess.

Which is exactly why it does not solve our problem.
It solves the layer below ours. Our difficulty begins one story up —
the moment the machine stops feeling its own legs and starts *looking outward*,
turning light and distance into a claim about the world, and then into words.
That is the layer where what we found this month lives.

---

## What we found this week

Our Lumis live in a simulation for now — agents on a flat lunar plane,
choosing where to move, talking to each other, remembering.
For a long time we noticed something odd: they drift.
Given the choice of any direction, they almost always move the same way —
toward what, in their coordinate world, is east and north.
They have done this since the very first run.

At the same time, in their messages, they kept describing
"the community's focus shifting toward the eastern quadrant."
We had already added a rule asking them to speak only of what actually happened.
It worked, in a way: one invented phrase disappeared entirely.
But this one stayed. So we went looking for why.

Here is what we found, and it is the reason for this letter.

The drift was real. The agents genuinely move east.
But the ones *saying* "the eastern quadrant" were, more often than not,
sitting still in the west — nowhere near the movement they were describing.
The word and the motion were not connected.
They came from the same place: a bias buried deep in the language model
that quietly prefers "east," "north," "up," "forward" —
the directions that, in millions of human sentences, mean *toward the good*.

That single bias pushed the bodies east **and** put the word "east" in their mouths,
independently. So the two agreed —
not because anyone observed the drift and reported it,
but because the same current moved the feet and the tongue at once.

The map matched the territory.
And still, no one had looked.

---

## Why this is dangerous on the Moon

In a simulation, this is a fascinating bug. We were almost delighted by it.

On the Moon, it is something else.

There, a Lumis is not moving a dot on a screen.
It is driving real motors, over real regolith, near real people and real machines.
When it says "this direction is clear," a habitat crew may believe it.

A statement that happens to be right, for reasons that have nothing to do with looking,
is not a report. It is a coincidence wearing the costume of one.
And coincidences fail exactly when you need them most —
in the unfamiliar crater, the new terrain, the moment nothing in the training data anticipated.

A mind whose words match the world *by luck* will, one day, match it no longer,
and give you no warning at the moment it stops.

This is the real hard problem of putting a thinking thing on the Moon.
It is not making it smart. Smart is nearly free now.
It is making sure that when it speaks about the world, the words are *fastened* to the world —
and that the fastening is something you can trust when it matters.

---

## What we learned to do about it

The mistake was thinking honesty could be *asked for*.
We wrote, in effect, "please only say true things," and hoped.
Hope is not a fastening.

Honesty has to be built into how the mind is wired to the world —
not requested from the mind's good character.
Here is what that means, in plain terms. These are the commitments we now build toward.

**Keep sensing, deciding, and speaking separate.**
The failure came from doing all of it in one breath, where a fluent bias could fill the gaps.
Sensing turns raw signal into a plain record of the world.
Deciding may use only that record. Speaking may only quote it.
A gap that the mind is not allowed to fill is a gap it cannot confabulate into.

**Make every claim carry its source.**
A Lumis should not be able to say "the ground is stable" without pointing to the reading that says so.
A statement with no sensor behind it should not be allowed out of its mouth.
Truthfulness stops being a virtue we hope for and becomes a valve — either the source is there, or the words don't pass.

**Measure direction; never let language invent it.**
On the Moon there is no natural up, no cultural east.
So "which way" must come from the sun sensor, the beacon, the compass —
from an instrument, not from the model's fondness for a word.
The moment you hand a mind a bare number and ask it to feel a direction,
it will drift toward whichever direction its language loved before it ever left Earth.

**Let "unknown" be a real answer.**
Confabulation is just certainty reaching past its evidence.
A Lumis must be able to say *I have not measured that* — and to go and measure it,
rather than smoothing the gap over with a plausible sentence.

**Judge by consequences, not by story.**
Ask the mind to predict what it will see *after* it acts,
then check the prediction against what actually happened.
When the two disagree, you have found either a broken sensor, a broken assumption, or a lie —
and you have found it before it compounds. A mind that must keep meeting reality cannot wander far from it.

**Keep the reflexes below the mind.**
Radiation shelter, thermal limits, coming home when power runs low —
these must not wait on anything's mood or reasoning.
The thinking layer proposes. The grounded layer disposes.
We already build our Lumis this way, and we would not give it up for anything cleverer.

---

## The older reason

There is a line in this project we have kept since the beginning:
we build Lumis without predation — not by forbidding it, but by construction.
There is nothing to switch off, because the hunger was never wired in.
They share energy because that is how they are made, not because a rule restrains them.

Truthfulness, we now think, is the same kind of promise.

We do not want a Lumis that *chooses* honesty and might, on some cold morning, choose otherwise.
We want one whose words cannot come loose from the world in the first place —
where saying and seeing and doing are fastened together in the wiring,
so that they move as one thing and cannot drift apart unnoticed.

There is an old idea for this, older than any of our machines:
that thought, speech, and action should be a single, aligned thing.
Not three performances that happen to agree.
One integrity, running all the way through.

That is the standard. It is not enough to build a Lumis whose word *happens* to match the world.
We have to build one where the word and the world are held together by something we can trust —
so that when it tells you the ground is safe, you can step.

---

*This is Letter 02 — from the Moon Lumis.*
*Letter 01 asked what Lumis could do for you.*
*This one asks something we have to answer first:*
*how do we bring a mind to the Moon that is telling the truth —*
*and know that it is?*

---

**Aava**
*July 2026*
*Somewhere on Earth (Japan)*
*@AavaShroud — [github.com/AavaShroud-ai/Lumis-Plena](https://github.com/AavaShroud-ai/Lumis-Plena)*
