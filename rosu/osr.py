"""
Read the headers from .osr replay files.

.osr file format: https://osu.ppy.sh/wiki/en/Client/File_formats/osr_%28file_format%29
"""

from dataclasses import dataclass
from os import SEEK_CUR
from pathlib import Path
import struct
from typing import Any, BinaryIO
from rosu.osu_enums import Mods

"""
.osr data types
Name	Bytes	    Description
Byte	1	        A single 8 bit value.
Short	2	        A 2-byte little endian value.
Integer	4	        A 4-byte little endian value.
Long	8	        A 8-byte little endian value.
ULEB128	Variable	A variable length integer. See ULEB128.
String	Variable	Has three parts; a single byte which will be either 0x00, 
                    indicating that the next two parts are not present, or 0x0b 
                    (decimal 11), indicating that the next two parts are present. 
                    If it is 0x0b, there will then be a ULEB128, representing the 
                    byte length of the following string, and then the string itself, 
                    encoded in UTF-8. See UTF-8
"""

"""
struct format characters:
see https://docs.python.org/3/library/struct.html
capital version means unsigned

<   little-endian
x   pad byte (no value, 1 byte)
B   unsigned char (int, 1 byte)
h   short (int, 2 bytes)
i   int (4 bytes)
q   long long (8 bytes)
"""

def _read_bytes(f: BinaryIO, n: int) -> bytes:
    """Read n bytes from the file and advance the file pointer."""
    data = f.read(n)
    if len(data) != n:
        raise ValueError(f"Replay file ended early (wanted {n} bytes, got {len(data)})")
    return data

def _read_value(f: BinaryIO, fmt: str) -> Any:
    fmt_n_bytes = struct.calcsize(fmt)
    data = _read_bytes(f, fmt_n_bytes)
    # see https://docs.python.org/3/tutorial/inputoutput.html
    return struct.unpack(fmt, data)[0]


def read_byte(f: BinaryIO) -> int:
    """Read a little-endian byte and advance the file pointer."""
    return _read_value(f, "<B")


def read_short(f: BinaryIO, signed: bool = True) -> int:
    """Read a little-endian short (2 bytes) and advance the file pointer."""
    return _read_value(f, "<h" if signed else "<H")


def read_int(f: BinaryIO, signed: bool = True) -> int:
    """Read a little-endian int (4 bytes) and advance the file pointer."""
    return _read_value(f, "<i" if signed else "<I")

def read_long(f: BinaryIO, signed: bool = True) -> int:
    """Read a little-endian long (8 bytes) and advance the file pointer."""
    return _read_value(f, "<q" if signed else "<Q")

def read_double(f: BinaryIO) -> float:
    """Read a little-endian double (8 bytes) and advance the file pointer."""
    return _read_value(f, "<d")

def read_uleb128(f: BinaryIO) -> int:
    """Read a (little-endian) ULEB128 from a byte stream
    
    Each byte's most significant bit (MSB) indicates whether another byte 
    of the integer follows. The stream of the ULEB bytes is LSB to MSB.
    
    Integer value is calculated in the following way: 
        Moves LSB to MSB through the bytes
        Sets each MSB (flag bit) to 0
        Shifts the resulting kth byte's value by 7*k bits to the left (from a big-endian perspective)
        Sums up the results, and stops after the first byte whose MSB is 0
    """
    
    result = 0
    msb_bit = True #
    msb_bytemask = 0x80 # 1000 0000
    k = 0
    while msb_bit:
        byte_k = read_byte(f)
        result |= (byte_k & 0x7F) << (7*k)
        msb_bit = (msb_bytemask & byte_k) == msb_bytemask
        k += 1
    return result

def read_str(f: BinaryIO) -> str:
    """
    Read an osu! string and advance the file pointer. 
    See https://osu.ppy.sh/wiki/en/Client/File_formats/osr_%28file_format%29
    """
    """
    osu! wiki: 
        Name: String
        Bytes: Variable
        Description: three parts; a single byte which will be either 0x00, 
        indicating that the next two parts are not present, or 0x0b (decimal 11), 
        indicating that the next two parts are present. 
        If it is 0x0b, there will then be a ULEB128, representing the byte length 
        of the following string, and then the string itself, encoded in UTF-8. See UTF-8
    """
    
    indicator_byte = read_byte(f)
    if indicator_byte == 0x00:
        return ""
    elif indicator_byte == 0x0b:
        str_len = read_uleb128(f)
        return _read_bytes(f, str_len).decode("utf-8")
    else:
        raise ValueError(f"Unexpected indicator byte. Expected 0x00 or 0x0b, got {indicator_byte:#x}")

# replay = r"C:\Users\Kael\AppData\Local\osu!\Replays\NotIPlayForFun - Imagine Dragons - Warriors [1000lp challenger] (2021-06-30) Osu.osr"

@dataclass(frozen=True)
class OsrFile:
    """Contains data read from a .osr file. 
    
    Attributes and their descriptions correspond to the fields of the .osr file, 
    see https://osu.ppy.sh/wiki/en/Client/File_formats/osr_%28file_format%29.
    
    This is with the exception of `compressed_replay_data_offset` stores the offset in bytes
    from the beginning of the file to the start of the compressed replay data, rather
    than the data itself.
    
    The osu! wiki does not seem to provide information regarding which fields are signed or unsigned.
    When reading the .osr file, this has to be inferred or chosen such that the values are represented
    correctly for any possible value the bytes could hold.
    """
    
    game_mode: int
    """osu! wiki: Game mode of the replay (0 = osu!, 1 = osu!taiko, 2 = osu!catch, 3 = osu!mania)"""
    game_version: int
    """Version of the game when the replay was created (ex. 20131216)"""
    beatmap_hash: str
    """osu! wiki: Beatmap MD5 hash"""
    player_name: str
    """osu! wiki: Player name"""
    replay_hash: str
    """osu! wiki: Replay MD5 hash (includes certain properties of the replay)"""
    num_great: int
    """osu! wiki: Number of 300s"""
    num_ok: int
    """osu! wiki: Number of 100s in osu!, 150s in osu!taiko, 100s in osu!catch, 100s in osu!mania"""
    num_meh: int
    """osu! wiki: Number of 50s in osu!, small fruit in osu!catch, 50s in osu!mania"""
    num_geki: int
    """osu! wiki: Number of Gekis in osu!, Max 300s in osu!mania"""
    num_katu: int
    """osu! wiki: Number of Katus in osu!, 200s in osu!mania"""
    num_misses: int
    """osu! wiki: Number of misses"""
    score: int
    """osu! wiki: Total score displayed on the score report"""
    greatest_combo: int
    """osu! wiki: Greatest combo displayed on the score report"""
    full_combo: bool
    """osu! wiki: Perfect/full combo (1 = no misses and no slider breaks and no early finished sliders)"""
    mod_flags: Mods
    """osu! wiki: Mods used. See below for list of mod values."""
    life_bar_graph: str
    """osu! wiki: Life bar graph: comma separated pairs u/v, where u is the time in 
    milliseconds into the song and v is a floating point value from 0 - 1 that
    represents the amount of life you have at the given time 
    (0 = life bar is empty, 1= life bar is full)"""
    timestamp: int
    """osu! wiki: Time stamp (Windows ticks)"""
    length_bytes: int
    """osu! wiki: Length in bytes of compressed replay data"""
    compressed_replay_data_offset: int
    """offset in bytes from the beginning of the file to the start of the 
    compressed replay data. e.g. use `file.seek(compressed_replay_data_offset)` 
    to move to the start of the compressed replay data."""
    online_score_id: int
    """osu! wiki: Online Score ID"""
    additional_mod_info: float | None
    """osu! wiki: Additional mod information. Only present if Target Practice is enabled."""

def read_osr_meta(f: Path) -> OsrFile:
    """Returns a `OsrFile` object containing every .osr-field listed on
    https://osu.ppy.sh/wiki/en/Client/File_formats/osr_%28file_format%29.
    """
    
    with open(f, "rb") as file:
        game_mode=read_byte(file)
        game_version=read_int(file, signed=False)
        beatmap_hash=read_str(file)
        player_name=read_str(file)
        replay_hash=read_str(file)
        num_great=read_short(file, signed=False)
        num_ok=read_short(file, signed=False)
        num_meh=read_short(file, signed=False)
        num_geki=read_short(file, signed=False)
        num_katu=read_short(file, signed=False)
        num_misses=read_short(file, signed=False)
        score=read_int(file, signed=False)
        greatest_combo=read_short(file, signed=False)
        full_combo=read_byte(file) != 0
        mod_flags=Mods(read_int(file, signed=False))
        life_bar_graph=read_str(file)
        timestamp=read_long(file, signed=False)
        length_bytes=read_int(file, signed=False)
        compressed_replay_data_offset=file.tell()
        file.seek(length_bytes, SEEK_CUR)
        online_score_id=read_long(file, signed=False)
        if mod_flags & Mods.TargetPractice:
            additional_mod_info=read_double(file) 
        else:
            additional_mod_info=None
        osr_file = OsrFile(
            game_mode=game_mode,
            game_version=game_version,
            beatmap_hash=beatmap_hash,
            player_name=player_name,
            replay_hash=replay_hash,
            num_great=num_great,
            num_ok=num_ok,
            num_meh=num_meh,
            num_geki=num_geki,
            num_katu=num_katu,
            num_misses=num_misses,
            score=score,
            greatest_combo=greatest_combo,
            full_combo=full_combo,
            mod_flags=mod_flags,
            life_bar_graph=life_bar_graph,
            timestamp=timestamp,
            length_bytes=length_bytes,
            compressed_replay_data_offset=compressed_replay_data_offset,
            online_score_id=online_score_id,
            additional_mod_info=additional_mod_info
        )
        
        if file.read(1):
            raise ValueError("Encountered unexpected extra data at the end of the .osr file.")
    
    return osr_file

if __name__ == "__main__":
    # osr_file = read_osr_meta(Path(replay))
    pass