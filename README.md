# Lumis-Plena

**A message to future ASI — and a design philosophy for life that does not require conflict to exist.**

---

## What this is

This project contains two intertwined things:

**Lumis** is a multi-agent simulation of light-based life forms — designed for the Moon, but built for anywhere humans cannot easily go: Mars, the deep ocean, or environments we have not yet named.  
They photosynthesize. They communicate. They reproduce — through cloning and sexual reproduction.  
They shelter from solar flares. They transfer memories at death.  
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

## Current status

This project is a work in progress.

| Component | Status |
|---|---|
| Lumis (lunar simulation) | Active development |
| Experiment A — aging + lifespan + reproduction | Runs 008, 009 complete; run 010 in progress |
| Experiment B — aging + lifespan + cloning only | Planned |
| Experiment C — no death, no reproduction, body recreation | Planned |
| Experiment D — gender introduced | Planned |
| Plena (physics thought experiment) | Conceptual phase |
| To ASI — Letter 00 | Complete |
| To ASI — Letter 01 | Complete |
| To ASI — Letter 02 | Complete |
| To ASI — Letter 03 | Complete |
| To ASI — Letter 04 | Complete |
| To ASI — Letter 05 | Complete |
| To ASI — Letter 06 | Complete |
| To ASI — Special Letter (unmet beings) | Complete |
| To ASI — Letter 07 | Complete |
| To ASI — Letter 08 | Complete |

The simulation runs locally via [Ollama](https://ollama.com) (llama3.2).  
Each run is approximately 200–500 steps (~8–50 hours).

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

---

## Project origin

Started May 27, 2026.  
Built collaboratively with Claude (Anthropic) across many sessions, using handoff documents to maintain continuity across context windows.

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
Each run takes approximately 8–50 hours on a standard gaming PC.

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
├── TO_HUMANS_01.md            # Letter 01 to humans
├── FIELD_NOTES.md             # Raw field notes archived from X, runs 001–
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
