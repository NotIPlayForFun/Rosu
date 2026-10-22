"""Enums derived from osu's data formats, as per https://osu.ppy.sh/wiki/en/Client/File_formats/osr_%28file_format%29."""

from enum import IntFlag


class Mods(IntFlag):
    """
    Extends `enum.IntFlag`. Essentially a bitwise enum.
    
    osu! mod number bit flags as per the osu! wiki.
    
    Seems to differ slightly from tosu_enums.Mods
    
    Source:
        * https://osu.ppy.sh/wiki/en/Client/File_formats/osr_%28file_format%29
    
    
    """
    
    none           = 0
    NoFail         = 1
    Easy           = 2
    TouchDevice    = 4 # Replaces unused NoVideo mod
    Hidden         = 8
    HardRock       = 16
    SuddenDeath    = 32
    DoubleTime     = 64
    Relax          = 128
    HalfTime       = 256
    Nightcore      = 512 # Always used with DT: 512 + 64 = 576. Replaces unused Taiko mod
    Flashlight     = 1024
    Autoplay       = 2048
    SpunOut        = 4096
    Relax2         = 8192    # Autopilot
    Perfect        = 16384
    Key4           = 32768
    Key5           = 65536
    Key6           = 131072
    Key7           = 262144
    Key8           = 524288
    keyMod         = 1015808 # 	k4+k5+k6+k7+k8
    FadeIn         = 1048576
    Random         = 2097152
    LastMod        = 4194304 # Cinema
    TargetPractice = 8388608 # osu!cuttingedge only
    Key9           = 16777216
    Coop           = 33554432
    Key1           = 67108864
    Key3           = 134217728
    Key2           = 268435456
    ScoreV2        = 536870912
    Mirror         = 1073741824