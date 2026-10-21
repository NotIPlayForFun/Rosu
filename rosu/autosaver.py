"""Can be controlled to repeatedly press F2 after failing until the replay is saved or
other stopping-criteria are met."""

import time
from pathlib import Path
from typing import List, Literal, Optional, Any, Union, Callable
import rosu.keyboard as kb
import rosu.replays as replays

FIRST_PRESS_DELAY = 1.0 # wait before first F2 press 
                        # (fail animation plays before F2 presses can tell osu! to save the replay)
PRESS_INTERVAL = 0.3 # time between repeated F2 presses
PRESS_HOLD = 0.1 # time between key-down and key-up SendInput executions
TIMEOUT = 10.0 # give up after this many seconds
REPLAYS_DIR = Path(r"C:\Users\Kael\AppData\Local\osu!\Replays")

class AutoSaver:
    """
    Call start() upon detecting a fail to begin auto-saving process.
    
    Presses F2 repeatedly until it detects a new matching replay file or timeout is reached.
    
    Current implementation uses a set `next_press` time to determine whether it should press F2.
    This assumes AutoSaver.update() is called frequently enough, so that time between presses
    does not exceed PRESS_INTERVAL significantly.
    
    Minimum recommended update-frequency: 1 / (2 * PRESS_INTERVAL)
    """
    
    def __init__(self) -> None:
        self.status: Literal["idle", "waiting", "spamming", "saved", "gave_up_timeout"] = "idle"
        """Status of the AutoSaver."""
        self.fail_time: float = 0.0
        """Time when the last fail was detected for which the AutoSaver was started."""
        self.next_press: float = float("inf")
        """Time after which the next F2 press is scheduled."""
    
    def start(self, fail_time: float) -> None:
        """Starts the auto-saving process for a detected fail."""
        now_unix = time.time()
        self.fail_time = fail_time
        self.next_press = now_unix + FIRST_PRESS_DELAY
        self.status = "waiting"
    
    def update(self, on_fail_screen: bool, osu_focused: bool, t: float) -> None:
        """Updates the auto-saving process. 
        
        Presses F2 at necessary intervals (within margin of error given by the frequency
        with which AutoSaver.update is called).
        
        Terminates if a new saved matching replay file is detected, or timeout is reached."""
        now_unix = time.time()
        
        # DO NOTHING IF NOT ACTIVE
        if self.status not in ["waiting", "spamming"]:
            return
        
        # PRESS IF SCHEDULED TIME HAS BEEN REACHED
        if now_unix >= self.next_press:
            if not on_fail_screen or not osu_focused:
                # make a 2 bit number where each bit represents a reason for not pressing F2
                # bit 0: not on fail screen
                # bit 1: osu not focused
                print(f"{t:7.2f}s  not pressing F2 because: not on fail screen={not on_fail_screen}, osu! not focused={not osu_focused}")
                return
            print(f"{t:7.2f}s  pressing F2")
            kb.press_F2(hold_time_s=PRESS_HOLD)
            self.next_press = now_unix + PRESS_INTERVAL
            self.status = "spamming"
        
        # CHECK FOR NEW MATCHING REPLAY FILE
        new_replays: List[Path] = replays.find_new_replays(REPLAYS_DIR, self.fail_time)
        if new_replays:
            for replay in new_replays:
                print(f"New replays detected: {len(new_replays)}")
                # print their last modifed times
                for replay in new_replays[:5]:
                    print(f"{replay}: {replay.stat().st_mtime}")
                print(f"fail time: {self.fail_time}")
                # TODO: check against current map
                self.status = "saved"
                return
            
        # CHECK FOR TIMEOUT
        if now_unix - self.fail_time >= TIMEOUT:
            self.status = "gave_up_timeout"
            return
    
    