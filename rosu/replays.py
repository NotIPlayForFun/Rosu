"""find osu! replay files"""

from pathlib import Path
import time
from typing import Literal
import timeit

# TODO: Idea: Scan at startup and shutdown, and keep track of set(current_files).
# Then, set(current_files) - set(old_files) will isolate new replay files since last scan.
# -> O(Delta n)
def find_new_replays(replays_dir: Path, since: float) -> list[Path]:
    """
    Return a list of replay files in `replays_dir` that have been 
    modified since the given timestamp `since`.

    **Testing (62 files in C: \\Users\\Kael\\AppData\\Local\\osu!\\Replays, 
    last modified criteria: past 100 hours, manually re-tested a few times):**
    
        * Glob appeared to be superior; ~1/3 faster than scandir in this test (70% of the time)
        * Glob execution time: 0.0019404999911785126
        10 new replays found
        hash of produced list: 3dce1d5f7c961736b7dc704cd86b68f15af2eb4f2aafff5f38f16468851c2162
        * Scandir execution time: 0.0030201999470591545
        10 new replays found
        hash of produced list: 3dce1d5f7c961736b7dc704cd86b68f15af2eb4f2aafff5f38f16468851c2162
    
    """
    # DEBUG: Time the file gathering method
    _GLOB_TEST: Literal["glob"] = "glob"
    _SCANDIR_TEST: Literal["scandir"] = "scandir"
    _FILE_GATHERING_METHOD: Literal["glob", "scandir"] = _GLOB_TEST 
    # _FILE_GATHERING_METHOD: Literal["glob", "scandir"] = _SCANDIR_TEST
    
    if _FILE_GATHERING_METHOD == _SCANDIR_TEST:
#         stmt="""[
#     replay for replay in Path(replays_dir).iterdir()
#     if replay.is_file() and replay.suffix == ".osr" and replay.stat().st_mtime >= since
# ]"""
#         execution_time = timeit.timeit(stmt, number=1, globals=globals())
#         print(f"Scandir execution time: {execution_time}")
        return [
            replay for replay in Path(replays_dir).iterdir()
            if replay.is_file() and replay.suffix == ".osr" and replay.stat().st_mtime >= since
        ]
    elif _FILE_GATHERING_METHOD == _GLOB_TEST:
#         stmt="""[
#     replay for replay in replays_dir.glob("*.osr") 
#     if replay.stat().st_mtime >= since
# ]"""
#         execution_time = timeit.timeit(stmt, number=1, globals=globals())
#         print(f"Glob execution time: {execution_time}")
        return [
            replay for replay in replays_dir.glob("*.osr") 
            if replay.stat().st_mtime >= since
            ]

if __name__ == "__main__":
    # test it
    replays_dir = Path(r"C:\Users\Kael\AppData\Local\osu!\Replays")
    since = time.time() - 100 * 60 * 60  # last 100 hours
    new_replays = find_new_replays(replays_dir, since)
    print(len(new_replays))
    # print a unique hash of the list
    import hashlib
    replay_list_hash = hashlib.sha256("".join(str(p) for p in new_replays).encode()).hexdigest()
    print(replay_list_hash)