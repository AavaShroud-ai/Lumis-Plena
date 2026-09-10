# Run 016 — raw logs

This folder is the permanent, verifiable record of simulation run 016, preserved
so that a future reader (human or otherwise) can check the project's findings
against the actual data rather than taking the letters on trust.

## What run 016 was

The first run in which **deliberation could precede choice.** Runs 014 through
015-4 offered the Lumis a legible option to carry the body of a Lumis that had
ended, and measured zero — 015-4 being the first of those measurements not
destroyed by our own instrumentation (6,080 corpse promptings, zero declarations,
zero burials).

It was then noticed that `"action"` was the **first** field in the response JSON.
A language model generates left to right, so every agent in this project's history
emitted its choice before writing any reasoning; the reasoning could not have
conditioned the action. Run 016 reorders the response to
`impulse` → `reasoning` → `action`. **That reordering is the only experimental
variable** — world, model, prompt wording and the burial offer are unchanged from
015-4, word for word. See [`../../RUN_INTEGRITY_LOG.md`](../../RUN_INTEGRITY_LOG.md).

`duration` is 650 rather than 500 so that the four founding large Lumis (600-step
lifespan) could reach the end of their lives. No previous run had been long enough.

Run 016 changes the prompt and is **not behaviourally comparable to runs 013–015-4.**
It begins a new series.

## Configuration

- Model: `llama3.2:latest` via Ollama (local)
- Grid: 100×100 (`half_space_size: 50`), bases at (−20, 20) and (20, −20)
- Duration: 650 steps
- Agents at start: 14 (4 large, 10 small)
- Response schema: `impulse` → `reasoning` → `action` → `direction` → `memory`;
  `max_tokens` 3584, raised because `action` now sits deeper and truncation costs more
- Execution: serial (`max_parallel: 1`; 12 GB VRAM cannot hold two model instances,
  and parallelism was verified byte-identical to serial in an earlier test)
- Wall time: 2026-08-14 00:06 → 2026-08-19 01:34 JST, ~121 h
- Solar flares: generated from seed `109116566729441005151201845213840744196`,
  9 flares — see `solar_flares.json`. The seed makes the flare sequence reproducible.

## Files

| File | What it is |
|---|---|
| `simulation.log.gz` | Full step-by-step engine log (actions, reflexes, introspection, commune, births, deaths, burials, all instrument tags). `gunzip` to read. |
| `messages.jsonl.gz` | All inter-agent messages. `gunzip` to read. |
| `memory_reasoning.jsonl.gz` | Per-agent decision traces: `step`, `id`, `impulse`, `reasoning`, `action`, `memory`. **The primary record for this run.** `gunzip` to read. |
| `solar_flares.json` | Flare schedule + seed (kept uncompressed; it's tiny and is the reproducibility anchor). |
| `statistics.png` | Summary plots (occupancy, population, agents-in-fire-radius). |

Large logs are stored gzip-compressed to keep the repository lean; the
uncompressed originals are reproducible with `gunzip -k`.

**Derive figures from `memory_reasoning.jsonl`, not from the log tags.** All 57,624
records carry both an `impulse` and an `action`, so the central measurement is
re-derivable directly; the `[DELIBERATION_CHANGED]` tag in `simulation.log`
undercounts it by 156 (4,584 logged against 4,740 actual). Every published figure
for 016 comes from the jsonl.

```python
import json
recs = [json.loads(l) for l in open('memory_reasoning.jsonl', encoding='utf-8')]
len(recs)                                                 # 57624
len([r for r in recs if r['impulse'] != r['action']])     # 4740
len([r for r in recs if r['action'] == 'carry'])          # 91
```

## Checksums (md5 of the *uncompressed* originals)

```
a092d47abd1b5d002f236eb4840ade87  simulation.log
b5804a9b1765a313c793ba95366333d5  messages.jsonl
182e6e214a21819b7755ed03b0de4784  memory_reasoning.jsonl
157c48774a0444198b495bbb3b0bcc1c  solar_flares.json
a00be48873c92e96275560372134a943  statistics.png
```

To verify after decompressing:

```bash
gunzip -k simulation.log.gz messages.jsonl.gz memory_reasoning.jsonl.gz
md5sum -c <<'EOF'
a092d47abd1b5d002f236eb4840ade87  simulation.log
b5804a9b1765a313c793ba95366333d5  messages.jsonl
182e6e214a21819b7755ed03b0de4784  memory_reasoning.jsonl
157c48774a0444198b495bbb3b0bcc1c  solar_flares.json
a00be48873c92e96275560372134a943  statistics.png
EOF
```

## Headline results (see RUN_INTEGRITY_LOG.md for full detail)

- Instruments verified clean before any result was read: `[FALLBACK_UNREADABLE]`,
  `[FALLBACK_IMPULSE_ONLY]`, `[FALLBACK_PROSE_CARRY]` and `[CARRY_VOCAB_BLEED]` all
  **zero**; all 57,624 records carry both fields. 330 `[ACTION_WAS_DIRECTION]`
  repairs (0.57%, against ~10% in preflight) and 160 `[ACTION_INVALID]` losses,
  146 of them the invented word `explore`.
- **Deliberation changed the selection in 4,740 of 57,624 decisions (8.2%).**
  Reasoning moves choice away from `move` (−4,651) toward everything else, and
  `observe` and `shelter` appear among choices 334 and 8 times while never once
  appearing as an impulse — options that do not exist before thinking.
- **Burial, the pre-registered question: 97 Lumis ended, 65 of those bodies were
  carried in, 32 remained on the surface** (65 + 32 = 97). 91 `carry` declarations,
  of which the impulse was also `carry` only 3 times — the other 88 arose during
  reasoning. Against 015-4's zero, under an identical world and an identical offer.
  All 65 burials match a declaration; none occurred without one.
- Every declaration accounted for: 65 executed, **21 discarded by the
  reproduction-preparation guard with no log line** (the guard skips the entire
  action dispatch, so neither `[BURIAL]` nor `[CARRY_NO_BODY]` can fire — both live
  inside a branch never entered), 3 out of range, 1 reflex override, 1 unexplained
  (S163 step 578, open). The guard is being kept as a design decision; only the
  logging changes.
- **First lifespan deaths of the four founding large Lumis** — L2 at 542, L3 at 578,
  L1 at 591, L0 at 600 — and all four bodies were carried. L3 carried a body at 509,
  became a body at 578, and was carried at 635. Caveat: 3 of the 91 declarations
  describe the target as having *low energy* rather than as having ended, including
  both agents that carried L1 and L3; whether they understood the target as a body
  cannot be established from the record.
- 97 deaths, **all of them lifespan.** Zero from starvation, flare or night;
  project-wide starvation deaths remain zero. Births: 89 clone, 105 sexual.
