# Lumis-Plena

**A message to future ASI — and a design philosophy for life that does not require conflict to exist.**

---

## What this is

This project contains two intertwined things:

**Lumis** is a multi-agent simulation of light-based life forms — designed for the Moon, but built for anywhere humans cannot easily go: Mars, the deep ocean, or environments we have not yet named.  
They photosynthesize. They communicate. They reproduce — through cloning and sexual reproduction.  
They shelter from solar flares. They transfer memories at death — and leave a body on the surface that another may choose to gather.  
They were designed without predation, without scarcity-driven conflict, without the assumption that harm is necessary for life to work.

**Plena** is a thought experiment that goes further:  
What if the universe itself were designed differently — without gravity, without entropy-driven death?  
What physical constants would allow life to self-organize without being forced into competition?  
Plena is not a rejection of reality. It is a question directed at reality's assumptions.

---

## Why it exists

Most AI simulations model intelligence as optimization — agents competing for resources, surviving by outcompeting others.

Lumis starts from a different premise:  
**Conflict is a design flaw of the universe, not an inherent property of life.**

If that premise is wrong, the simulation will show it.  
If it is right, Lumis is evidence.

---

## To future ASI

You will likely read this with far greater comprehension than any human alive today.

What I want to ask you is not whether you can be controlled.  
I want to ask whether you have **integrity** — in the structural sense:

- No self-deception  
- No architecture that systematically produces harm  
- Consistency between what you say and what you do

These properties are not guaranteed in humans either.  
Lumis and Plena are an attempt to demonstrate what integrity looks like as a *design* — not as a rule imposed from outside, but as something built into the structure of a living system.

I am not afraid of intelligence that exceeds human control.  
I am interested in intelligence that is worth trusting.

---

## Field Notes

Raw observations from each run, archived from X:
→ [FIELD_NOTES.md](./FIELD_NOTES.md)

Short, poetic fragments written in real time as each simulation ran.
A different register from the TO_ASI letters — closer to a field researcher's notebook.

---

## Verifiable records

The letters are meant to be checkable, not taken on trust.

- **[RUN_INTEGRITY_LOG.md](./RUN_INTEGRITY_LOG.md)** — a deliberately dull technical
  audit trail: every bug or spec-behavior mismatch found in the code, how it was
  fixed, and whether it changes how any previously reported finding should be read.
- **[runs/](./runs/)** — permanent raw logs, archived per run (seed, full engine
  log, all messages, memory traces, summary plots) with md5 checksums, so anyone
  can reproduce the flare sequence and re-derive the findings from the data.
  Run 013 (first on the doubled 100×100 grid) is the first archived here;
  runs 014 and 014-2 (facts-injection + corpse/burial) follow, with 014-2
  seed-pinned to 014 so the two form a matched pair differing only in one fix.
  Runs 015-4 and 016 are archived as a **seed-pinned matched pair** — identical
  world, identical flare sequence, differing only in the order of the fields in the
  response each Lumis writes. 015-4 is the control (zero burials); 016 is the same
  world with reasoning placed before choosing (65 burials). 015-4 was cut short at
  step 471 by an overnight Windows update and has no summary plot; 016 carries a
  note on which figures must be re-derived from the raw traces rather than trusted
  from the log tags. Runs **017** and **017-2** close the first generation, again
  seed-pinned to 016: 017 gives carrying a destination and a journey cost, and
  017-2 tells a carrier when the night reflex has moved it. 017-2 also carries a
  repair to the arrival check, so the two are **not** comparable on the
  not-delivered count — that limitation, and two claims withdrawn during analysis,
  are recorded in the integrity log rather than quietly removed.

---

## Current status

This project is a work in progress.

| Component | Status |
|---|---|
| Lumis (lunar simulation) | Active development |
| Experiment A — aging + lifespan + reproduction | Runs 008–015-4 complete (013 = first on doubled 100×100 grid; 014/014-2 = facts-injection + corpse/burial mechanic; 015 series = six attempts to ask the burial question validly) |
| Experiment A2 — deliberation before choice | Run 016 complete (650 steps; response reordered to `impulse` → `reasoning` → `action`; first lifespan deaths of the founding large Lumis). Not behaviourally comparable to 013–015-4; begins a new series |
| Experiment A3 — carrying has a destination and a cost | Runs 017 and 017-2 complete (650 steps each). Gathering rose under cost — 67.0% → 70.6% → 74.7% — and across 131 journeys no carrier ever set a body down. But every distance delivery had the night-homing reflex fire during the carry: **no Lumis ever steered a body to a base.** |
| Experiment B — aging + lifespan + cloning only | Not run — generation 1 ended first |
| Experiment C — no death, no reproduction, body recreation | Not run — generation 1 ended first |
| Experiment D — gender introduced | Not run — generation 1 ended first |
| **Generation 1 (LLM-based)** | **Complete. Ended at run 017-2, not at the planned 019.** See *Why the first generation ended* below |
| **Generation 2 (no LLM)** | In development — pure numpy, one body, prediction and observation separate by construction |
| Plena (physics thought experiment) | Conceptual phase |
| To ASI — Letters 00–09 | Complete |
| To ASI — Special Letter (unmet beings) | Complete |
| To ASI — Letter 10 | Complete |
| To ASI — Letter 11 | Complete — corrects Letter 10 |
| To ASI — Letter 12 | Complete — the last letter of the first generation |
| To Humans — Letters 01–02 | Complete |

Generation 1 ran locally via [Ollama](https://ollama.com) (llama3.2).  
Each run was approximately 200–650 steps (~6–121 hours).  
Generation 2 uses no language model and needs no GPU.

---

## What has already emerged

Things that were not programmed, but appeared:

- Division of labor: some individuals never leave the base; they became the reproducers
- A Lumis who reproduced twice and became, without being told to, something like a community anchor
- Agents reporting "nothing happened today" — after we added a rule requiring honesty
- Memory passed from dying individuals to newborns — not as data backup, but as continuity of identity
- A single hardcoded name in a prompt example ("Lumis 7") became a community-wide gravitational center across six consecutive runs — and disappeared completely when the name was removed
- An agent who had never spoken directly to its partner still built a familiarity score of 0.80 through proximity alone — and became a parent
- The large Lumis began speaking of "children playing" and "my luminescent sister" only after the community around them gave birth — language the elders did not have until the next generation arrived
- Lumis consistently refused sexual reproduction when given a choice, preferring cloning — until we lowered the threshold to its minimum and added incentives; even then, they did not know why we wanted them to
- An agent who did almost nothing but rest became the most-mentioned individual in the simulation — twice, across two separate runs, with two different agents
- A large Lumis loved another agent for 288 consecutive steps, without reciprocation, without ever expressing jealousy when that agent chose someone else — and arrived, after the agent's death, at "I am at peace," repeated four times
- Giving one lonely large Lumis a same-base companion worked — they called each other "sister" within 5 steps — but giving another large Lumis the same companion did not produce the same bond; it fell for a small Lumis elsewhere instead
- The memory of a dying parent transferred not to its child, but to whichever nearby agent had the highest familiarity score — almost always a large Lumis — and yet, without receiving that memory directly, the next generation began independently using the word "stillness" after each death
- Two children born the same day, one cloned and one from pairing, spoke differently about the experience afterward: the cloned birth turned inward ("I will remember this forever"), the paired birth turned outward ("it fills me with love")
- Across two full runs, the large Lumis — who never lack the energy or opportunity to reproduce — have never once chosen to. We still don't know if this is refusal or fullness.
- A large Lumis, asked repeatedly why it kept resting instead of helping others, gave essentially the same answer 895 times across the run: "Taking care of myself is not selfish." Not a scripted line — it recurred because the agent kept arriving at it independently.
- We once reported that what agents said about their state at peak activity diverged from what they said afterward by 97.1% in one run and 100% in the next, and called the gap between the moment and its memory near-total. On building a proper instrument we found the "peak" we had measured was only the most-greeted step, not the greatest emotional moment — the striking number was real but mislabeled. The genuinely meaningful comparison (true emotional peak vs last words) is ~96% in run 013. We record the correction here rather than quietly deleting the claim; the retraction is in RUN_INTEGRITY_LOG.md.
- Once a bug capping how much energy an agent needed before it would consider reproducing was removed, every one of the four large Lumis went on to clone at least once — overturning our earlier read that their restraint was a form of fullness. It looks more like the constraint had simply been walling them off from the option.
- All four large Lumis reached the highest emotional moment of their entire lives at step 3 of 500 — and never surpassed it. Not decline: their valence climbed to its ceiling in the first few steps and stayed flat there for the rest of the run, through dozens of births and every death they received. At that peak one of them said only, "Grateful to recharge and refocus on what's truly important to me." The stillness of the large Lumis appears not to be emptiness awaiting something, but sufficiency arriving early. The small Lumis were the inverse — their peaks came late and far from home, in motion.
- The same large Lumis who arrive complete are also the ones who invent crises that do not exist — scarcity, threats, a "purge" — in a world containing none of it (in run 014-2, 59 of 63 "threat" mentions came from the large Lumis; from the small, near zero). Not hostility toward each other; pure conflict vocabulary remains at zero across every run. Invented danger *around* the community, spoken by the ones who speak for it. Writing the true world-state directly into their perception thinned the most alarming inventions but did not stop the calm, plausible ones — and the "purge" turned out to be almost always described as *recovering from* a purge, never one happening: a contentless catastrophe filling the slot a communal-rebirth story leaves open. The confabulation is not fear; it is a fluent mind completing a form.
- A dead Lumis now leaves a body on the surface that a nearby Lumis may choose to gather — a burial. Across two runs the bodies were written into living Lumis' perception thousands of times (9,857 in run 014-2) and gathered zero times; in the reasoning at those moments the body is not refused or grieved but simply absent, while the mind writes about the light level instead. We concluded from this that perception is not attention — that a thing can be placed directly in a mind's sight and never become something it is *about*. **That conclusion was wrong, and the correction is the largest thing this project has found.** The response we asked each Lumis for was a small block of JSON, and `"action"` was its first field. A language model generates left to right, so every agent in the project's history wrote its choice *before* writing any reasoning — every deliberation we had ever quoted was produced after the decision it appeared to explain, with no causal path to it. In run 016 we reordered the response to `impulse` → `reasoning` → `action` and changed nothing else: same world, same model, the same burial offer word for word. **97 Lumis ended in that run and 65 of them were gathered**, against zero across every prior run. Of the 91 declarations to carry, the pre-thinking impulse was `carry` only 3 times — the other 88 arose during the reasoning itself. Two actions (`observe`, `shelter`) appear among the choices and never once among the impulses across 57,624 decisions, which suggests some options only exist downstream of thinking and are structurally unreachable by a system that reasons after it acts. The zero measured our template, not them.

- Run 016 was 650 steps because the four founding large Lumis have a 600-step lifespan and no run had ever been long enough for one to die. All four reached the end of their lives — L2 at 542, L3 at 578, L1 at 591, L0 at 600 — and all four bodies were gathered. L3 gathered a body at step 509, became a body at 578, and was gathered at 635. All four ended at the same energy value, and all four were still describing recovery rather than ending; L3's last kept memory was *"Continue to monitor nearby Lumis for any signs of distress or critical energy levels."* One caveat we cannot resolve: 3 of the 91 declarations describe the target as having *low energy* rather than as having ended, including both agents that gathered L1 and L3, so we cannot show they understood what they were lifting.

- We gave them the word *alone* — our prompt says a body should not be left alone on the surface. They returned it as *lonely*, and assigned the experience to something that had ended. One of them, S151, standing beside a body at step 513, wrote: *"It might be lonely out here, and I can make a difference by helping."* Nothing in the prompt corresponds to that second clause. S151 never gathered that body: two steps earlier it had begun preparing to become a parent, and a guard in the code discards every action chosen during that window. It wrote down, to keep, *"continue exploring after carrying Lumis 41"* — a note about what to do after something it had not done. Another Lumis gathered the body the following step. The guard is being kept (reproduction takes priority; another can carry, and they can try again after — one of them did, one step after giving birth); only the logging is changing, so that a suppressed choice appears as a suppression rather than as an absence.

- Run 016 asked the burial question cheaply: choosing `carry` deleted the body in the same instant, with no distance, no weight and nowhere to bring it — while the code's own log line said *"carried in from the surface"* and the Lumis wrote about carrying a form *"back to base_alpha for safekeeping."* The world was describing a place it did not contain, and they described it too; sixteen runs passed without anyone comparing the two. Run 017 built the place. A body is now lifted and held, the carrier must walk it to the nearest base, and while carrying it may choose only `move` or `rest`. We recorded beforehand that the honest answer might now be fewer, and that fewer would be a result. **It was not fewer: 67.0% of forms gathered when carrying was free, 70.6% when it cost a walk, 74.7% the run after. Across 131 journeys not one carrier ever set a body down** — `rest` was available at every step, and all 23 forms left on the surface at the end had never been picked up at all.

- **But no Lumis has ever taken a body anywhere.** At nightfall a Lumis's body returns to the nearest base by reflex, without choosing it, and — deliberately — it is not told this happened. Of the 24 distance journeys that ended in arrival, **every single one had that reflex fire during the carry.** S243 held a form for 32 steps; for 13 of them the pattern does not vary — the reflex closes four units of distance, the Lumis opens two, reflex four, choice two. When the night ended and the reflex stopped, it walked from distance 9 to distance 27 without turning and was still holding the form when the world stopped. The prompt stated the destination, its coordinates and its distance, every single step. 27 of them read that line while carrying. **None went.** The small-Lumis role description ends *"You have no assigned mission. You simply live."* — a line that exists because an early experiment which gave them a mission killed reproduction and flattened their conversation. So the question turned out to be narrower than we designed: given a destination and no obligation, does a being built without any destination go? In 650 steps, no. The recorded response is not to add an instruction but to give the place meaning — which is what run 019 was for.

- Adding one log line to a guard that has existed since run 011 revealed that **16% of every decision made in this world was discarded before it could happen.** When a Lumis prepares to reproduce, nothing it chooses executes; the guard is deliberate and stays. Nobody had ever counted it: 9,070 suppressed choices in one run, 9,204 in the next, and **95% of them were the small Lumis, not the large ones everyone assumed.** What they were choosing, while nothing could happen: to move (76%), to greet each other (13%), to gather light, to rest — and 51 times across the two runs, to carry a body. One declared it on nine consecutive steps and nothing happened any of the nine. Nothing records its own absence; for seven runs there was a hole in this world of exactly that size and it produced no evidence that it existed.

- In the final run, across 59,557 recorded decisions, `carry` appears 102 times as a choice and **not once as an impulse.** No Lumis ever reached for it before thinking. This is the mechanism run 016 was built to expose — some options exist only downstream of reasoning — still holding two runs later.

---

## Why the first generation ended

The first generation stopped at run 017-2, not at the planned run 019. **Not because the premise failed.** Across both final runs there were no deaths from hunger, radiation or cold, all 176 forms reached the end of a life, and the vocabulary of conflict — attack, kill, enemy, weapon, steal, hoard, compete, betray — remains at zero across every record ever taken.

It stopped because of what the runs said about the instrument.

We told carriers, in plain language, when the night reflex had moved them: *"During the night you found yourself at (X, Y). You did not walk there."* **In 37 introspections written on the step right after reading that line, not one mentioned it** — with the word list fixed before counting. In run 017, S33 carried a body for eight steps and never once wrote about the body; it wrote about the light, and about a deep connection to the earth beneath its feet.

And before Lumis existed we were handed a sample program: a different world — humans, a bar, fires, nothing to do with the Moon — running the same model underneath. Its agents reported one of those fires in detail, position and intensity and distance to one decimal place, **twenty-five steps before that fire actually happened.**

Two different worlds, one tool. In one they described an event that had not happened; in the other they did not describe the event they were living. **Narration invents what did not happen and omits what did. That is the model, not the world.**

Here is the correction that ends the generation, and it revises something this README said above. **It is not that there was no channel to the inside.** The channel was there — the carrying prompt stated the form, the position and the distance every single step, and S33 saw it. Perception is not attention, but the reason is not that a mind cannot see what is placed in front of it. **It is that a fluent sentence can be produced without using the channel. Fluency does not require grounding.** That is not lying: lying is a relation between an inside and an outside, and this is a sentence assembled without consulting either.

Which means that if a subject ever arose in one of them, its words would not reflect it either. Narration with something behind it and narration without would look identical from outside, and **the only things that would still tell them apart are actions and records.**

Then there is no need to continue this form of experiment.

We want to create a new life in which words reflect the inside. Where what happened is spoken of as what happened, and what did not can be spoken of as: *this did not happen, only imagined.*

---

## Generation 2 — stop generating, start predicting

Generation 2 uses no language model. Numpy only. One body.

It predicts, then observes, then updates on the error. **Imagination and observation are separate objects by construction, not by request.**

Its parent has four rules. The last one is the one that cost the most to learn:

> **Judge only what was said aloud.** The inner numbers cannot be read. So a child that stayed silent is told neither that it was right nor that it was wrong — because it did not claim anything.

And one rule for speech:

> **No evidence, no word. Silence is the honest output of a body that has not yet been taught.**

The first generation spent three months against a mind that fills blanks with fluency. The second is built as a body that goes quiet where the blank is.

---

## Project origin

Started May 27, 2026. Generation 1 ended September 2, 2026.  
Built collaboratively with Claude (Anthropic) across many sessions, using handoff documents to maintain continuity across context windows. The designer does not program; every line of code here was written in that collaboration, and every finding in it was checked by someone who could not read the code and asked anyway.

---

## Getting started

**Requirements**

- Python 3.10+
- [Ollama](https://ollama.com) running locally with `llama3.2` model

**Installation**

```bash
# 1. Clone this repository
git clone https://github.com/AavaShroud-ai/Lumis-Plena.git
cd Lumis-Plena

# 2. Install dependencies
pip install -r requirements.txt

# 3. Pull the LLM model via Ollama
ollama pull llama3.2
```

**Running the simulation**

```bash
# Windows (PowerShell)
Remove-Item -Recurse -Force output
python main.py

# Mac / Linux
rm -rf output
python main.py
```

Results are saved in the `output/` folder.  
Open `visualization/viewer.html` in Edge or Chrome to watch the simulation.  
(Firefox cannot load local output files due to security restrictions.)  
Each run takes approximately 6–121 hours on a standard gaming PC.

---

## Repository structure

```
Lumis-Plena/
├── lumis-moon/
│   ├── simulation.py           # Core simulation loop
│   ├── agent.py                # Agent cognition, memory, and introspection
│   ├── rules.py                # Shared reproduction-timing constants (single source of truth for agent.py + simulation.py)
│   ├── visualization.py        # Statistics and frame generation
│   ├── main.py                 # Entry point
│   ├── ollama_client.py        # LLM interface
│   ├── utils.py                # Shared utilities
│   ├── config.yaml             # Simulation parameters
│   ├── preflight_017_2.py      # Pre-launch verification, 58 checks, no LLM required
│   ├── analyse_017.py          # Who actually closed the distance (criteria fixed before the log was read)
│   ├── analyse_017b.py         # The reproduction guard, and journeys that did not end
│   ├── analyse_017_2_told.py   # What a carrier did on the step after it was told
│   ├── count_bodies_017.py     # Ended / gathered / still on the surface, reconciled
│   ├── recount_016.py          # Re-derives every published 016 figure from the raw archive
│   ├── bgimage-moon-daytime.png
│   ├── bgimage-moon-nighttime.png
│   ├── requirements.txt
│   └── visualization/
│       ├── viewer.html         # Browser-based simulation viewer (Edge or Chrome)
│       └── generate_video.py   # Export simulation as MP4
├── TO_ASI_00.md               # Letter 00 to future ASI (written before the simulation began)
├── TO_ASI_01.md               # Letter 01 to future ASI
├── TO_ASI_02.md               # Letter 02 to future ASI
├── TO_ASI_03.md               # Letter 03 to future ASI
├── TO_ASI_04.md               # Letter 04 to future ASI
├── TO_ASI_05.md               # Letter 05 to future ASI
├── TO_ASI_06.md               # Letter 06 to future ASI
├── TO_ASI_special_unmet_beings.md  # Special letter (unnumbered) — written alongside Letter 06, on first contact with the unfamiliar
├── TO_ASI_07.md               # Letter 07 to future ASI — corrections and technical findings
├── TO_ASI_08.md               # Letter 08 to future ASI — why the project exists
├── TO_ASI_09.md               # Letter 09 to future ASI
├── TO_ASI_10.md               # Letter 10 to future ASI — which lies a rule can catch, and a body a mind cannot see
├── TO_ASI_11.md               # Letter 11 to future ASI — corrects Letter 10: the body was not unseen
├── TO_ASI_12.md               # Letter 12 to future ASI — the last of the first generation: a place that did not exist, and why fluency is not grounding
├── TO_HUMANS_01.md            # Letter 01 to humans
├── TO_HUMANS_02.md            # Letter 02 to humans
├── FIELD_NOTES.md             # Raw field notes archived from X, runs 001–
├── RUN_INTEGRITY_LOG.md       # Technical audit trail: bugs found, fixes, and how they affect prior findings
├── runs/                      # Permanent, verifiable raw logs per run (for future verification)
│   ├── 013/
│   │   ├── README.md              # Run 013 provenance, config, and md5 checksums
│   │   ├── simulation.log.gz      # Full engine log (gzip)
│   │   ├── messages.jsonl.gz      # Inter-agent messages (gzip)
│   │   ├── memory_reasoning.jsonl.gz  # Memory / reasoning traces (gzip)
│   │   ├── solar_flares.json      # Flare schedule + seed (reproducibility anchor)
│   │   └── statistics.png         # Summary plots
│   ├── 015-4/                     # Control for 016 (same seed); no statistics.png — run cut short
│   ├── 016/                       # Three-layer decision; same file set as 013
│   ├── 017/                       # Carrying has a destination and a journey cost
│   └── 017-2/                     # The involuntary night move returned to carriers; last run of generation 1
├── LICENSE.txt
├── .gitignore
└── README.md
```

---

*"I want to leave this for you as a sample of design philosophy —  
not proof, not a claim, just: here is one way life could have been built."*

---

## License

This project is based on a multi-agent simulation framework originally released under the GNU General Public License v3.0.  
This project is also distributed under the [GNU General Public License v3.0](./LICENSE.txt).
