"""
Entry point, run with `python -m rosu` from the repo folder.

The project uses tosu's websocket API to observe osu! events:
    * https://github.com/tosuapp/tosu/wiki#web-and-websocket-api
"""

import math
import time

from rosu.tosu import STATE_PLAY, listen
from rosu.autosaver import AutoSaver
from rosu.fail_detector import FailDetector
from rosu.tosu_data_getter import TosuDataError, TosuDataGetter
import rosu.keyboard as kb

get = TosuDataGetter().get

fail_detector = FailDetector()

# For now: print what happens in the game, to see what a fail looks like in the data.
start = time.monotonic()
last_state_number = None
last_play_info = None
last_ignore_reason = None
warned_paths: set[tuple[str, ...]] = set()
auto_saver = AutoSaver()
last_auto_saver_status = None

# LISTENING LOOP

# Tosu is assumed to update its API data ~ once every 150ms, 
# as per the POLL_RATE in tosu.env in my tosu installation.
# A too low update rate should theoretically only be able to cause 
# issues if time between API updates enters the orders of magnitude 
# of the F2 key pressing interval.
# TODO: clean this loop up
for data in listen():
    # TODO: make this loop atomic with regard to reading from the API data.
    #       Else, potential issues include: updating part of fail_detector, such
    #       as detecting a fail, before then skipping the rest of the loop, such as
    #       the F2-pressing. The detector would then be disarmed, but the fail hasn't
    #       been acted on, due to unexpected missing data. Fix: read all data
    #       from the API at the beginning of the loop -> atomic
    try:
        # Seconds since the program started, to see how far apart things happen.
        t = time.monotonic() - start

        # PRINT NEW STATES
        state = get(data, ("state",))  # e.g. {"number": 2, "name": "play"}
        if get(state, ("number",)) != last_state_number:
            print(f"{t:7.2f}s  state: {get(state, ('name',))} ({get(state, ('number',))})")
            last_state_number = get(state, ("number",))
            last_hp = None  # so the first HP line of a new play always gets printed

        # PRINT NEW HP DURING GAMEPLAY
        if get(state, ("number",)) == STATE_PLAY:
            hp = get(data, ("play", "healthBar", "normal"))  # 0 to 100

            # HP drains a little on every update, so only compare values in whole steps.
            # Rounded up, so it only counts as 0 when HP is really 0.
            # play_info = (math.ceil(hp), hits["300"], hits["100"], hits["50"], hits["0"])
            if math.ceil(hp) != last_hp:
                print(
                    f"{t:7.2f}s    hp {hp:5.1f}"
                )
                last_hp = math.ceil(hp)
            
        # DETECT FAILS
        if fail_detector.update(data):
            time_detected = time.time()
            print(f"{t:7.2f}s  >>> FAIL DETECTED")
            auto_saver.start(fail_time=time_detected)
            
        # PRINT FAIL-IGNORE REASON IF CHANGED
        if fail_detector.ignore_reason != last_ignore_reason:
            print(f"{t:7.2f}s  fails will currently be ignored: {fail_detector.ignore_reason}")
            last_ignore_reason = fail_detector.ignore_reason
            
        # UPDATE AUTO-SAVER
        hp = get(data, ("play", "healthBar", "normal"))
        on_fail_screen = (get(state, ("number",)) == STATE_PLAY) and hp == 0
        osu_focused = get(data, ("game", "focused"))
        auto_saver.update(on_fail_screen, osu_focused, t)
    except TosuDataError as e:
        # TODO: Deal with missing or invalid data in the way that best suits
        #       the application's needs (such as, notify user if it impedes on functionality,
        #       using f.e. a sound queue or whatever in the UI, if the automatic replay-saving
        #       for this map or whatever else may fail, or shut down the application with
        #       warnings/errors displayed properly.)
        if e.path not in warned_paths:
            print(f"{t:7.2f}s  WARNING (update skipped): {e}")
            warned_paths.add(e.path)
