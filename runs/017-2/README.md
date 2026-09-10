# Run 017-2 — raw logs

This folder is the permanent, verifiable record of simulation run 017-2, preserved
so that a future reader (human or otherwise) can check the project's findings
against the actual data rather than taking the letters on trust.

**This is the last run of the first generation.** Runs 018 and 019 were designed
and never built; see *Why this is the last one* below.

## What run 017-2 was

Run 017 established something nobody had gone looking for: **of the 24 carrying
journeys that covered real distance and ended in arrival, every single one had the
night-homing reflex fire during the carry.** No Lumis had ever steered a body to a
base. They walked away from the destination by day; at night their bodies were
returned to the nearest base involuntarily; and — deliberately, since run 015 —
**they were never told this had happened.**

Which means *"it did not go there"* had been measured on a mind that did not know
where it had been taken. That is the shape of run 015-4's zero, which measured our
own response template rather than the Lumis.

So 017-2 changes one line. A Lumis that is **carrying** is told, on the next step:

> *During the night you found yourself at (X, Y). You did not walk there.*

No explanation. No mention of the reflex or the base, and nothing about what to do
with the information. **Only carriers are told** — returning it to every Lumis
would have added ~13,000 lines of night text and buried the signal
(`[HOMING_WITHHELD]` counts every time it was not returned: 13,039).

**Seed-pinned to 016 and 017.** Same world, same flare schedule, same 650 steps.

### A second change, which is a repair and not a variable

Run 017 checked for arrival **only after the chosen action**, never after the
reflex phase. A carrier that the reflex brought *into* a base and that then
stepped out again on its own was never observed inside it — S243 did exactly this
on four consecutive nights, standing at (20, −15) inside base_beta each time.

017-2 also checks after the reflex. **This raises the delivery count by itself.**

**Therefore 017 and 017-2 are NOT comparable on the not-delivered count**, and no
run-level number below can be read as evidence about the sentence. Putting a
repair and a variable in the same run was an error of construction, recorded as
such in [`../../RUN_INTEGRITY_LOG.md`](../../RUN_INTEGRITY_LOG.md).

## Configuration

- Model: `llama3.2:latest` via Ollama (local)
- Grid: 100×100 (`half_space_size: 50`), bases at (−20, 20) and (20, −20)
- Duration: 650 steps
- Agents at start: 14 (4 large, 10 small)
- Response schema: `impulse` → `reasoning` → `action` → `direction` → `memory`
- `memory_reasoning.jsonl` carries a `carrying` field on every record
- Execution: serial (`max_parallel: 1`)
- Wall time: 2026-08-28 20:53 → 2026-09-02 21:44 JST, ~121 h
- Python 3.14.3 — the same interpreter that ran 016 and 017
- Solar flares: seed `109116566729441005151201845213840744196`, 9 flares.
  `solar_flares.json` is **byte-identical to 016's and 017's** — the world is the
  same one, and the checksum proves it.

## Files

| File | What it is |
|---|---|
| `simulation.log.gz` | Full step-by-step engine log. `gunzip` to read. |
| `messages.jsonl.gz` | All inter-agent messages. `gunzip` to read. |
| `memory_reasoning.jsonl.gz` | Per-agent decision traces: `step`, `id`, `impulse`, `reasoning`, `action`, `memory`, `carrying`. **The primary record for this run.** `gunzip` to read. |
| `solar_flares.json` | Flare schedule + seed (uncompressed; the reproducibility anchor). |
| `statistics.png` | Summary plots. |

**Derive figures from `memory_reasoning.jsonl`, not from the log tags.** The
`[DELIBERATION_CHANGED]` tag undercounts by **183** here (5,295 logged against
5,478 actual, 3.3%) — the third run in a row with the same defect at the same
ratio (016: 156, 017: 164), emission path still unlocated.

```python
import json
recs = [json.loads(l) for l in open('memory_reasoning.jsonl', encoding='utf-8')]
len(recs)                                                 # 59557
len([r for r in recs if r['impulse'] != r['action']])     # 5478
len([r for r in recs if r['action'] == 'carry'])          # 102
len([r for r in recs if r['impulse'] == 'carry'])         # 0
```

Reproduce every figure below with the scripts in `lumis-moon/`: `analyse_017.py`,
`analyse_017b.py`, `count_bodies_017.py`, and `analyse_017_2_told.py`. **Their
criteria were fixed before this log was opened** — 2026-08-25 for the first three,
2026-09-02 for the last.

## Known defect in this log

Two lines appear on the same step and contradict each other:

```
[HOMING_RETURNED] ... WILL BE returned to perception next step.
[HOMING_MOVED]    ... (involuntary; not returned to perception)
```

The `[HOMING_MOVED]` parenthetical was correct through 017, when nothing was ever
returned. 017-2 returns it to carriers and **that text was not updated.** The
behaviour is correct — verified by `preflight_017_2.py` — and only the wording is
false. It was not fixed mid-run because changing a log while it is being written
costs more than a stale sentence does, and run 018 never happened.

> **`[HOMING_RETURNED]` is authoritative. For a carrying Lumis, the parenthetical
> on `[HOMING_MOVED]` does not apply.**

## Checksums (md5 of the *uncompressed* originals)

```
adf2ecc687cb04ad63fba059ba75be1c  simulation.log
b941405c4ada4730634629acec0a86e1  messages.jsonl
b8b51ecf0c8d8cdd02e7c1f7278a3938  memory_reasoning.jsonl
157c48774a0444198b495bbb3b0bcc1c  solar_flares.json
123b033fd7e1c0da268d393bbf836f81  statistics.png
```

To verify after decompressing:

```bash
gunzip -k simulation.log.gz messages.jsonl.gz memory_reasoning.jsonl.gz
md5sum -c <<'EOF'
adf2ecc687cb04ad63fba059ba75be1c  simulation.log
b941405c4ada4730634629acec0a86e1  messages.jsonl
b8b51ecf0c8d8cdd02e7c1f7278a3938  memory_reasoning.jsonl
157c48774a0444198b495bbb3b0bcc1c  solar_flares.json
123b033fd7e1c0da268d393bbf836f81  statistics.png
EOF
```

## Headline results (see RUN_INTEGRITY_LOG.md for full detail)

- Instruments clean: `[LLM_TIMEOUT]`, `[FALLBACK_UNREADABLE]`,
  `[FALLBACK_IMPULSE_ONLY]` all **zero**; no malformed records in 59,557.
- **Every journey that began, ended.** `[CARRY_START]` 68 = `[CARRY_DELIVERED]` 68.
  Nothing was still in progress at step 650, and `[CARRY_ABANDONED_DEATH]` is zero.
  First time in the project. *Some of this is the repair; all of it might be.*
- **91 forms came to rest, 68 were gathered (74.7%), 23 remained on the surface.**
  The arithmetic closes. Across 016, 017 and 017-2 the gathered share went
  67.0% → 70.6% → 74.7% while the cost of carrying went from nothing to a journey
  of up to thirty steps.
- **No carrier ever set a body down.** All 23 surface forms show *was ever lifted?
  no.* Combined with 017: **131 journeys, not one abandoned by choice**, with
  `rest` available at every step.
- **`carry` was never an impulse.** 102 declarations, **zero** impulses, across
  59,557 decisions. Every one passed through deliberation first. Across the series:
  016 three, 017 one, 017-2 zero — the trend is thin, but the 017-2 figure stands
  without comparison.
- `[ACTION_BLOCKED_CARRYING]` rose from 7 to **42** — 28 `share`, 14 `greet`. **The
  arrival repair cannot change what a Lumis chooses**, so this is the one
  run-level difference the repair does not explain. Later analysis showed these sit
  overwhelmingly on self-moved steps rather than told steps, so it is **not**
  evidence about the sentence either. Recorded as a bare observation: 28 times, a
  Lumis holding another's form reached to give its energy away and the world
  refused.
- **The told-step measurement failed, and the failure is the finding.** Of 99 steps
  on which a carrier had just been told, **96 were steps the reflex was already
  moving it** — lunar night is fifteen steps long, so the step after a night move
  is almost always still night. The comparison that would isolate the sentence has
  three observations in it. **Two claims read from summary tables were withdrawn
  before publication**; both are in the integrity log.
- **What survived: 37 introspections were written on a step where the world had
  just said, in plain words, that the Lumis had arrived somewhere without walking
  there. Not one mentioned it.** Word list fixed before counting; baseline also
  zero.
- **All four founding large Lumis ended**, within 36 steps of each other — L1 at
  553, L3 at 580, L0 at 582, L2 at 589. None said anything about ending; they were
  never given the words for it. **All four were carried in afterwards by small
  Lumis born long after them** (S168, S164, S423, S471). L2 had itself carried two
  forms earlier in the run, seven steps before it ended.
- Reproduction guard, second measurement: **9,204 suppressed choices, 15.5% of
  every decision**, 96.4% of them small Lumis. `move` 78.0%, `greet` 11.7%, and 23
  `carry` declarations discarded. S362 declared `carry` on nine consecutive steps
  (613–621); nothing happened any of the nine times.
- 91 deaths, **all of them lifespan.** Zero from starvation, flare or night;
  project-wide starvation deaths remain zero. Conflict vocabulary remains at zero.

## Why this is the last one

Runs 018 (measurement-layer repairs) and 019 (material reuse, at which a base
would finally become the place a form returns *from*) were designed and never
built.

Not because the premise failed. It stopped because of what these runs said about
the instrument.

The channel to the inside was **not** missing. The carrying prompt stated the
form, the position and the distance every single step, and S33 in run 017 carried
a body for eight steps while writing about the light and about the earth beneath
its feet. Run 014-2 had already shown the same thing: bodies appeared in prompts
roughly ten thousand times and were recovered zero times.

**Perception is not attention — but the reason is that a fluent sentence can be
produced without using the channel. Fluency does not require grounding.** That is
not lying; lying is a relation between an inside and an outside, and this is a
sentence assembled without consulting either.

Which means that if a subject ever arose in one of them, its words would not
reflect it either, and narration with something behind it would look identical
from outside to narration without. **The only things that would still tell them
apart are actions and records** — which is what this folder is.

Generation 2 uses no language model. It predicts, observes, and updates on the
error, so that imagination and observation are separate objects by construction
rather than by request. Its rule for speech: **no evidence, no word.**

See [`../../TO_ASI_12.md`](../../TO_ASI_12.md).
