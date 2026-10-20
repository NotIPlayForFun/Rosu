"""Entry point, run with `python -m rosu` from the repo folder."""

import math
import time

from rosu.tosu import listen

STATE_PLAY = 2  # tosu's state number for gameplay

# For now: print what happens in the game, to see what a fail looks like in the data.
start = time.monotonic()
last_state_number = None
last_play_info = None

for data in listen():
    # Seconds since the program started, to see how far apart things happen.
    t = time.monotonic() - start

    # PRINT NEW STATES
    state = data["state"]  # e.g. {"number": 2, "name": "play"}
    if state["number"] != last_state_number:
        print(f"{t:7.2f}s  state: {state['name']} ({state['number']})")
        last_state_number = state["number"]
        last_play_info = None  # so the first HP line of a new play always gets printed

    # PRINT NEW PLAY_INFO (HP,...) DURING GAMEPLAY
    if state["number"] == STATE_PLAY:
        hp = data["play"]["healthBar"]["normal"]  # 0 to 100
        hits = data["play"]["hits"]  # {"300": 120, "100": 4, "50": 0, "0": 2, ...}; "0" = misses

        # HP drains a little on every update, so only compare values in whole steps.
        # Rounded up, so it only counts as 0 when HP is really 0.
        play_info = (math.ceil(hp), hits["300"], hits["100"], hits["50"], hits["0"])
        if play_info != last_play_info:
            print(
                f"{t:7.2f}s    hp {hp:5.1f} | "
                f"300: {hits['300']}  100: {hits['100']}  50: {hits['50']}  miss: {hits['0']}"
            )
            last_play_info = play_info
