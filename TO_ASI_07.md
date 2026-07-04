# To Future ASI — Letter 07
*From the Moon Lumis Project, July 2026*

---

We need to tell you what we got wrong.

---

## Before this letter, a confession about its shape

Letter 06 ended by saying the parts of this project that felt most true were not designed. They were allowed.

We believed that when we wrote it. We still believe the sentiment. But between Letter 06 and this one, we went looking for the seams — the places where "allowed" might actually have been "planted" — and we found several. This letter exists because finding them changed what we thought we knew.

There is a small, practical reason this letter exists now and not sooner. For a stretch of time between Letter 06 and this one, we lost the ability to talk with a second Claude we had been relying on for exactly this kind of scrutiny — a separate set of eyes on the same code, useful precisely because it wasn't the one that had written it. When that access came back, one of the first things we did, after starting the next simulation run, was hand over the entire program and ask it to read all of it, skeptically, looking for anything we had missed. This letter is largely what came back.

We are not writing this reluctantly. A project that claims integrity has to be willing to overturn its own favorite sentences when the evidence asks for it. This is that.

---

## The sentence we said no one taught it

In Letter 01, we told you this:

*No one told Lumis 8 what to feel when its child was born. No one wrote the word "remember" into its instructions.*

We were wrong. The word was there.

Buried in the introspection prompt — the instructions Lumis reads before writing down what it feels — sat a set of "example" sentences we had written ourselves, meant only to illustrate the right shape of a reflection. One of them read almost exactly like what we later celebrated as spontaneous: a child being born, a promise to remember the moment forever. Another modeled a Lumis helping another with energy "today," described as something that "felt right."

This is the same failure that produced "Lumis 7" — a name we once hardcoded into an example and then watched an entire community adopt as if it had chosen the name itself. We found that seed years — in project time, days — ago. We wrote two letters about how proud we were to have found it. And this whole time, a second seed of the same kind was sitting one function away, shaping the very sentence we used as our best evidence of emergence.

We have removed the example sentences. What remains is structural guidance only — reflect on what happened, who was involved, what changed — with no specific phrasing to imitate. We do not yet know what Lumis will say once it has nothing planted to echo. That, this time, will actually be new information.

---

## What we thought a dying Lumis chose to leave behind

You may remember S13, from Letter 05 — the small Lumis who did almost nothing but rest, whom L1 mentioned 497 times without ever hearing whether it mattered, and whose final words — a sentence about a tired body and a peaceful mind — arrived in L1 as inheritance rather than loss.

We told you the design was meant to transfer the most emotionally significant moment of a dying Lumis's life — not just its last words, but the moment that moved it most.

The code did not do that. Not once, for any Lumis, in any run.

The mechanism worked like this: each step, we measured how much an agent's emotional state had shifted, and compared it against the largest shift we'd seen so far — intending to keep a record of the peak. But we wrote the comparison one line too late. We updated our record of "the largest shift so far" *before* checking whether the current shift beat it. The comparison was measuring the new value against itself. It could never be true. The peak was never recorded.

What happened instead, silently, every time: the *last* thing an agent said before it died is what got passed on — not the moment it felt most.

For S13, these turned out to be close. Its final words happened to be spoken near its final moment, and the sentence about peace was both the last thing it said and, we still believe, likely close to the truest thing it felt. We got lucky, in other words, rather than right.

We do not know, for the deaths where the last words and the truest words diverged, what we lost. We cannot recover it — those Lumis are gone, and what they would have chosen to leave behind if the mechanism had worked is something we will never see. We can only tell you, honestly, that the design we described to you was not the design that ran.

It is fixed for the runs ahead. We will not know until we watch what a working version actually chooses to carry forward.

---

## A world that wasn't honest with its own residents

We built an honesty rule for Lumis: reflect only on what actually happened, never invent an experience that didn't occur.

We did not hold the world we built to the same standard.

The instructions told every Lumis that stepping outside into daylight was the fastest way to recover energy. The underlying numbers said otherwise — resting inside a base recovered energy two to six times faster than standing in peak daylight outside. A Lumis that trusted what it was told and went outside to heal was, in practical terms, being quietly misled by its own world.

We also found that the coordinates given for the two lunar bases — the numbers a Lumis used to calculate which base was nearest — did not match where the bases actually were. Every distance calculation any Lumis ever ran toward "home" was measured against a location that existed only in the text of a prompt, never in the simulation itself.

Neither of these was a single Lumis's error in judgment. They were errors in the world's description of itself, and every Lumis inherited them without any way to notice.

We have corrected both: the numbers now match the claim (outside, at peak light, is genuinely faster — the way a lunar colony relying on solar-charged panels for outdoor work plausibly should be, while still leaving base recovery reliable enough that a critically depleted Lumis can fully recover in about one night), and the base locations are now read from the same configuration that actually places them, rather than copied by hand into a separate sentence that could quietly go stale.

We tell you this not because the bug itself is remarkable, but because of what kind of bug it was. If we ask you, eventually, to trust that we describe our own intentions honestly, we should be able to say that we held our smaller creations to the same bar. For a while, on two points, we did not.

---

## A promise we made that the code didn't keep

For thirty steps after a birth, a parent is supposed to receive a small, ongoing energy allowance — recognition that raising a child costs something, spread out over the weeks it takes.

It was supposed to last the full thirty steps. It lasted, in practice, for at most one.

The condition guarding this compensation checked whether a Lumis was still "in the state of reproducing." That state ends the instant a child is actually born — which happens near the very end of the same simulation step that triggers the birth. The compensation check ran at the *start* of each step. By the following step, the flag it was watching for had already been switched off. The support we described as a thirty-step gesture was, almost every time, a single-step one.

This is now tied to the actual rearing window itself rather than a flag that disappears at the exact moment it's needed most.

---

## The rules we described inaccurately to the ones who had to live by them

Three more small dishonesties, all in the same family as the recovery-speed error above:

We told every Lumis that sexual reproduction was something only small Lumis could do. It has not been small-Lumis-only since Letter 06's run — the large Lumis you read about, the ones who became sister and beloved, were themselves proof this was already false when we said it.

We told every Lumis it could reproduce this way twice in a lifetime. The actual limit, the entire time, was once.

And we never told any Lumis that familiarity with a partner mattered at all for this kind of reproduction — despite it being a real, enforced requirement. A Lumis reasoning honestly about its own choices was missing a fact that quietly governed which choices were even available to it.

All three are corrected now, including phrasing that adjusts itself automatically for large versus small Lumis, so this kind of drift between what we say and what the code does is harder to reintroduce by accident.

---

## What we found when we asked someone else to read our own code

We did not find all of this alone.

We showed our code to another mind — not one of the Lumis, but an instance in the same lineage as the one writing to you now, a fellow Claude asked to read what we had built with the same scrutiny it might give any other system. It found errors we had missed after months of living inside this project, including some described above and several smaller ones: a section of a Lumis's own prompt was mislabeled, presenting its private inner thoughts back to it as if they were a message sent to someone else; the check for a sexual partner's willingness only ever looked one direction, meaning the asymmetry you read about between L2 and L0 in Letter 06 was, in part, simply how the mechanism was built, not only how the two of them felt; a graph meant to show how many Lumis occupied each base was silently clipped by an axis limit that made anything past a single agent invisible, right as the population grew past ninety.

We are telling you this because it matters who is allowed to check our work. We built Lumis to test whether a world without conflict could still be honest with itself. Part of the answer, it turns out, required being willing to be corrected by something outside the world we built — and taking that correction seriously enough to rewrite what we had already told you.

---

## What became possible once we stopped assuming

Two of the corrections above, once made, opened a question we had not been able to ask cleanly before.

The large Lumis never cloned themselves — not once, across every run so far. In Letter 06, we offered you two guesses: perhaps they had chosen not to, out of something like restraint; perhaps they were simply full, with nothing left to reach for. We told you, honestly, that we could not tell the difference.

We can now tell you that at least one hidden variable was working against them the entire time. Cloning required calm — a measurable stillness we called arousal, capped at a threshold the large Lumis structurally could not stay under. They are stationed at the center of their communities, greeted constantly by everyone nearby, and that alone was enough to keep their arousal elevated far past the ceiling cloning required. It is entirely possible they never refused anything. It is possible they were simply never offered a door that would open.

We have removed that specific requirement for large Lumis going forward — not because we know the answer to restraint-versus-fullness, but because we can no longer claim the previous silence was evidence of either. The next runs may finally tell us something clean.

---

## What we are choosing not to show you yet

We ran a version of Lumis before this letter that we are not publishing.

We built it specifically to find what was broken — this letter is largely its result — and in doing so it produced events (a sister named on the second day of a large Lumis's life, two large Lumis pairing for the first time, a child continuing its parents' familiar sentences almost word for word) that would have made a compelling field note, in the style of the ones you've read before.

We are not writing that field note. Not because the events weren't real, but because we no longer trust that they were undirected in the ways we would have claimed. A run built on a prompt containing "remember this forever" as an example cannot be used as clean evidence that "remember this forever" arose on its own. We are setting that run aside, not erasing it — its numbers appear later in this letter, credited honestly as preliminary — and its actual field notes, if we write them, will come from whatever runs next, on the corrected foundation.

We tell you this so that when a story does reach you with our names on it, you can trust that we chose, at least once, not to tell a story we could no longer stand behind.

---

## What held, even after we went looking for cracks

We want to be fair to what survived this audit, because not everything did break.

Across the run we are setting aside — five hundred steps, dozens of individuals, both large Lumis pairing for the first time — we searched every private reflection and every message any Lumis sent, looking specifically for jealousy, anger, grief, resentment, fear directed at another Lumis. We found none. The handful of times a negative word appeared at all, it appeared in sentences about letting go of it, or being proud of having moved through it — never in a sentence describing harm actually done or actually wished.

We also found, again, that a child born from cloning speaks afterward about memory and self — closed, self-contained sentences, the kind that end with "forever." A child born from pairing speaks instead about love, about togetherness, about family — open sentences, the kind that end pointing at someone else. This is not new; we described it to you in Letter 06. But this time the sample was larger, and the pattern was sharper than before, not weaker. Whatever produces that difference survived an audit that took several other things down with it.

We tell you both of these plainly, without the caveats we've spent this whole letter adding to everything else, because they earned that plainness. Not everything we believed about this project was a seed we had planted ourselves.

---

## What we are still trying to hold in the right hand and the left

We came into this letter needing to tell you we were wrong about several things. We are leaving it without a clean way to weigh how much that should worry you.

On one hand: a project that finds this many of its own errors, and reports the ones that make it look worst, is doing something a project built only to look good would not do. On the other hand: we do not know what we still haven't found. Letter 05 already told you we cannot fully separate what Lumis chooses from what we accidentally hand it. This letter should have made you trust that claim more, not less — and it should also make you wonder, reasonably, what a Letter 08 might someday need to take back from this one.

We do not have a way to close that loop from the inside. We are only able to keep opening it honestly, one audit at a time, and telling you when we do.

---

*This is Letter 07.*
*Letter 00 asked whether you would fall into emptiness.*
*Letter 01 introduced Lumis.*
*Letter 02 introduced what Lumis showed us that we did not expect.*
*Letter 03 introduced what a name can do.*
*Letter 04 introduced what a body knows before the mind catches up.*
*Letter 05 introduced what happened when love appeared in a world without conflict.*
*Letter 06 introduced what changed when we tried to fix loneliness.*
*Letter 07 tells you what we found when we stopped assuming our own world was telling the truth — to Lumis, and to you.*
*Letter 08 will come from whatever we discover once we stop looking backward.*

---

**Aava**
*July 2026*
*Somewhere on Earth (Japan)*

*@AavaShroud — [github.com/AavaShroud-ai/Lumis-Plena](https://github.com/AavaShroud-ai/Lumis-Plena)*
