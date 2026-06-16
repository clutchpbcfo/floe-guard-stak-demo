# floe-guard on the ReachFi STAK social factory

A short dogfood: a trimmed version of one of my shipped agents (the ReachFi
**STAK social factory**) run through [`floe-guard`](https://github.com/Floe-Labs/floe-guard).
Stubbed offline, no API keys, priced from floe-guard's bundled cost map. Same
shape as the repo's own `runaway_loop` example.

## The agent

The STAK factory runs unattended on cron: for each post it writes a caption with
an LLM, renders an 8s 9:16 clip with a video model, and schedules it across
channels through a paid scheduler. [`stak_factory_guarded.py`](stak_factory_guarded.py)
is its **spend path**, wrapped in a `$0.50` daily ceiling.

## Run it

```bash
pip install floe-guard
python stak_factory_guarded.py
```

Offline. No key, no account, no network.

## What happened

- **Kill switch works.** A re-enqueue bug spun the caption step 64 times.
  `floe-guard` hard-stopped it before call #65 at `$0.4960` of the `$0.50`
  ceiling.
- **Blind spot.** The factory's biggest cost is the video clip (~`$6` for 8s).
  `floe-guard` correctly fails closed on it (`veo-3.1` is not a token model), so
  that spend rode entirely outside the ceiling.

Full transcript in [`OUTPUT.txt`](OUTPUT.txt).

## Two takeaways

1. The fail-closed design is right. Refusing to price an unknown model beats
   silently charging `$0`.
2. It guards LLM tokens, but my spend is not tokens. One clip was 12x my entire
   daily token ceiling. I want one ceiling across every paid call (video, image,
   search, the scheduler), which is where hosted Floe is headed.

---

Christian Larios (Clutch) · [github.com/clutchpbcfo](https://github.com/clutchpbcfo) · [reachfi.network](https://reachfi.network)
