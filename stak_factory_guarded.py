"""
stak_factory_guarded.py

A trimmed reproduction of the ReachFi "STAK social factory" agent's SPEND PATH,
wrapped in floe-guard. The real agent runs unattended on cron: for each post it
writes a caption with an LLM and renders a 9:16 clip with a video model, then
schedules it across channels. Here the model calls are stubbed (fixed token
usage, no network, no keys) and priced OFFLINE from floe-guard's bundled cost
map — exactly as the README's runaway_loop demo does.

Two things this shows:
  A) THE KILL SWITCH  — a stuck caption-retry loop (a real failure mode for an
     unattended agent) gets hard-stopped before it crosses the daily ceiling.
  B) THE BLIND SPOT   — the factory's biggest cost line is video generation,
     which floe-guard can't meter (it prices LLM tokens). The guard fails closed
     on it, so my largest spend rides outside the ceiling.

Run:  PYTHONPATH=floe-guard/src python3 stak_factory_guarded.py
"""
from __future__ import annotations

from floe_guard import BudgetGuard, BudgetExceeded, UnpriceableModelError

CAPTION_MODEL = "gpt-4o"     # priceable from the bundled LiteLLM cost map
VIDEO_MODEL = "veo-3.1"      # per-second video gen — not a token model

# --- stubbed agent calls (no network, no keys) ------------------------------
def write_caption(post: str) -> dict:
    """Stub LLM. Real agent calls Claude/gpt for the no-slop caption."""
    return {"model": CAPTION_MODEL, "prompt_tokens": 1500, "completion_tokens": 400}

def render_clip(post: str) -> dict:
    """Stub video gen. Real agent renders an 8s 9:16 clip (~$0.75/s)."""
    return {"model": VIDEO_MODEL, "seconds": 8}

# --- one unattended cron run, $0.50 ceiling ---------------------------------
guard = BudgetGuard(limit_usd=0.50)
print(f"STAK factory run — daily ceiling ${guard.limit_usd:.2f}\n")

queue = ["staky stacks", "staky v staky (duel)", "score to beat: 1248", "free to play"]
buggy = True   # a re-enqueue bug: the classic unattended runaway
i = 0
while i < len(queue):
    post = queue[i]
    try:
        guard.check()                       # <-- kill switch, before the call
    except BudgetExceeded:
        print(f"\n[A] KILL SWITCH: factory halted before caption #{i+1}. "
              f"Spent ${guard.spent_usd:.4f} of ${guard.limit_usd:.2f}.")
        break
    r = write_caption(post)
    cost = guard.record(r["model"], r["prompt_tokens"], r["completion_tokens"])
    print(f"  caption '{post}': +${cost:.4f}   running ${guard.spent_usd:.4f}")
    if buggy and post.startswith("staky v staky"):
        queue.insert(i + 1, post)           # bug re-queues the same post forever
    i += 1

# --- the blind spot: the cost the token-guard can't see ---------------------
print("\n[B] BLIND SPOT: trying to bill the actual biggest cost line (video)...")
clip = render_clip("staky stacks")
try:
    guard.record(clip["model"], clip["seconds"], 0)   # there is no token shape for this
    print("    recorded video spend.")
except UnpriceableModelError as e:
    approx = clip["seconds"] * 0.75
    print(f"    floe-guard can't price '{clip['model']}' (fails closed).")
    print(f"    that ~${approx:.2f} clip rode OUTSIDE the ceiling — and video is "
          f"most of my real spend, not tokens.")
