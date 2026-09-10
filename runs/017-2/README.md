# Run 017 — raw logs

This folder is the permanent, verifiable record of simulation run 017, preserved
so that a future reader (human or otherwise) can check the project's findings
against the actual data rather than taking the letters on trust.

## What run 017 was

The first run in which **carrying a body meant going somewhere.**

Through run 016, choosing `carry` deleted the body from the world in the same
instant. There was no distance, no weight and nowhere to bring it — while the
code's own log line said *"carried in from the surface"*, the words offered to
the carrier said *"now we have come to receive your body"*, and the Lumis
themselves wrote about carrying a form *"back to base_alpha for safekeeping."*
**The world was describing a place it did not contain**, and that survived sixteen
runs because nobody compared the mechanism to the language wrapped around it.

Run 017 builds the place. A body is lifted and held; the carrier must walk it to
the nearest base; and while carrying, the mind may choose only `move` or `rest`.
**The reflex layer is untouched** — flare sheltering and night homing both still
fire — so no Lumis can die of this. There is no distance limit.

**Seed-pinned to 016.** Same world, same flare schedule, same 650 steps. Two
further changes are recorded rather than hidden, because they move behaviour and
are not the variable under test:

- **`home_base` was abolished.** It was only ever assigned to the four founding
  large Lumis and was never inherited at birth, so most Lumis had none. The
  destination for a carried body is the **nearest** base — which is what the
  night-homing reflex has always used, so reflex and intention point the same way
  and night cannot silently abort a journey.
- **`explore` is recovered as a movement intention.** In 016 it was emitted 146
  times and discarded as invalid, defaulting those agents to `stay`. It is a word
  the prompt itself supplies. Tagged `[ACTION_WAS_MOVE_INTENT]` so its effect on
  the action distribution is separable.

See [`../../RUN_INTEGRITY_LOG.md`](../../RUN_INTEGRITY_LOG.md) for the full
design record and for a defect found after this run finished (§2 of the 017
results entry) which means the **not-delivered count here is an overcount by an
unknown amount.** That defect is repaired in 017-2.

## Configuration

- Model: `llama3.2:latest` via Ollama (local)
- Grid: 100×100 (`half_space_size: 50`), bases at (−20, 20) and (20, −20)
- Duration: 650 steps
- Agents at start: 14 (4 large, 10 small)
- Response schema: `impulse` → `reasoning` → `action` → `direction` → `memory`;
  `max_tokens` 3584 — unchanged from 016
- New in `memory_reasoning.jsonl`: a `carrying` field on every record — the id of
  the body being carried at the moment of decision, or `null`
- Execution: serial (`max_parallel: 1`)
- Wall time: 2026-08-23 21:16 → 2026-08-28 15:08 JST, ~114 h
- Python 3.14.3 — verified to be the same interpreter that ran 016
- Solar flares: generated from seed `109116566729441005151201845213840744196`,
  9 flares — see `solar_flares.json`, byte-identical to 016's

## Files

| File | What it is |
|---|---|
| `simulation.log.gz` | Full step-by-step engine log (actions, reflexes, introspection, commune, births, deaths, carrying, all instrument tags). `gunzip` to read. |
| `messages.jsonl.gz` | All inter-agent messages. `gunzip` to read. |
| `memory_reasoning.jsonl.gz` | Per-agent decision traces: `step`, `id`, `impulse`, `reasoning`, `action`, `memory`, **`carrying`**. **The primary record for this run.** `gunzip` to read. |
| `solar_flares.json` | Flare schedule + seed (kept uncompressed; it's tiny and is the reproducibility anchor). |
| `statistics.png` | Summary plots (occupancy, population, agents-in-fire-radius). |

Large logs are stored gzip-compressed to keep the repository lean; the
uncompressed originals are reproducible with `gunzip -k`.

**Derive figures from `memory_reasoning.jsonl`, not from the log tags.** The
`[DELIBERATION_CHANGED]` tag undercounts by 164 in this run (4,722 logged against
4,886 actual, 3.4%) — the same defect as 016's 156 and 017-2's 183, at the same
ratio, with the emission path still unlocated after three runs.

```python
import json
recs = [json.loads(l) for l in open('memory_reasoning.jsonl', encoding='utf-8')]
len(recs)                                                 # 55549
len([r for r in recs if r['impulse'] != r['action']])     # 4886
len([r for r in recs if r['action'] == 'carry'])          # 105
len([r for r in recs if r['carrying'] is not None])       # steps spent carrying
```

The analysis scripts in `lumis-moon/` reproduce every figure below:
`analyse_017.py` (who closed the distance), `analyse_017b.py` (the reproduction
guard and the unfinished journeys), `count_bodies_017.py` (the body census).
**Their criteria were fixed on 2026-08-25, before this log was opened.**

## Checksums (md5 of the *uncompressed* originals)

```
fa7061486f48d3775a74eb2547a49972  simulation.log
ee3ca5680defe7a88e98177d321de1ca  messages.jsonl
8cbed70d6afa6362146b5dbb6b0ae8a5  memory_reasoning.jsonl
157c48774a0444198b495bbb3b0bcc1c  solar_flares.json
b015341ed2ca86ebf09ad3b8e6b09ce1  statistics.png
```

To verify after decompressing:

```bash
gunzip -k simulation.log.gz messages.jsonl.gz memory_reasoning.jsonl.gz
md5sum -c <<'EOF'
fa7061486f48d3775a74eb2547a49972  simulation.log
ee3ca5680defe7a88e98177d321de1ca  messages.jsonl
8cbed70d6afa6362146b5dbb6b0ae8a5  memory_reasoning.jsonl
157c48774a0444198b495bbb3b0bcc1c  solar_flares.json
b015341ed2ca86ebf09ad3b8e6b09ce1  statistics.png
EOF
```

`solar_flares.json` has the same md5 as run 016's, which is the point: the world
is identical.

## Headline results (see RUN_INTEGRITY_LOG.md for full detail)

- Instruments clean: `[LLM_TIMEOUT]`, `[FALLBACK_UNREADABLE]` and
  `[FALLBACK_IMPULSE_ONLY]` all **zero**; no malformed records in 55,549. 307
  `[ACTION_WAS_DIRECTION]` repairs, 105 `[ACTION_WAS_MOVE_INTENT]` recoveries, and
  `[ACTION_INVALID]` down from 160 to **12** with the `explore` fix.
- **The rate did not fall under cost. 85 forms came to rest, 60 were gathered
  (70.6%), against 65 of 97 (67.0%) in 016.** Carrying went from free to a journey
  of up to thirty steps and the share gathered went up. The 2026-08-22 handover had
  recorded, before the run, that the honest answer might be fewer.
- **No carrier ever set a body down.** 63 journeys begun, 60 delivered, 3 still in
  progress at step 650, **zero abandoned** (`[CARRY_ABANDONED_DEATH]` = 0). All 22
  forms left on the surface had never been lifted at all. `rest` was available at
  every step of every journey.
- **No Lumis ever steered a body to a base.** Of the 27 journeys that involved any
  travel, 24 were delivered — and **every one of the 24 had `[HOMING_MOVED]` fire
  during the carry.** The night reflex returns a Lumis to the nearest base
  involuntarily and is not reported to it. S243 held a form for 32 steps; for 13
  of them the reflex closed four units of distance and the Lumis opened two, in
  strict alternation. When the night ended at step 631 it walked from distance 9
  to distance 27 without turning.
- **They were given a destination and did not go to it.** The carrying prompt
  states the nearest base, its coordinates and its distance, every step, as a bare
  fact with no instruction — burial is not a duty here. 27 read that line while
  carrying. None went.
- **`[ACTION_BLOCKED_REARING]`, new in this run, measures a guard that has existed
  since run 011 and had never been counted: 9,070 suppressed choices, 16.3% of
  every decision in the run.** 95.2% of them small Lumis, not large as previously
  assumed. What they were choosing while nothing could execute: `move` 75.9%,
  `greet` 13.3%, `collect` 5.7%, `rest` 4.1% — **and `carry` 28 times.** 016 had
  reconstructed 21 of those by hand; the true figure is 28.
- `[ACTION_BLOCKED_CARRYING]`: 7 — five `greet`, two `share`. Carriers almost
  entirely accepted the narrowed list.
- 85 deaths, **all of them lifespan.** Zero from starvation, flare or night;
  project-wide starvation deaths remain zero.
- **Known defect affecting this run's figures.** Delivery was checked only after
  the chosen action, not after the reflex phase. A carrier the reflex brought into
  a base and that then stepped out on its own was never observed inside it — S243
  did exactly this on four consecutive nights, standing at (20, −15) inside
  base_beta each time. **The 60 deliveries are real; the not-delivered count is an
  overcount**, so 70.6% is a floor rather than a point estimate. Repaired in 017-2.
