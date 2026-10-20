"""Enums derived from tosu's data formats, as per https://github.com/tosuapp/tosu."""

from enum import IntEnum, IntFlag

class Mods(IntFlag):
    """
    Extends `enum.IntFlag`. Essentially a bitwise enum.
    
    osu! mod number bit flags as per the osu! game client.
    
    Source:
        * https://osu.ppy.sh/wiki/en/Client/File_formats/osr_%28file_format%29 or
        * https://github.com/ppy/osu-api/wiki#mods
    
    
    """
    
    none           = 0
    NoFail         = 1
    Easy           = 2
    TouchDevice    = 4
    Hidden         = 8
    HardRock       = 16
    SuddenDeath    = 32
    DoubleTime     = 64
    Relax          = 128
    HalfTime       = 256
    Nightcore      = 512 # Only set along with DoubleTime. i.e: NC only gives 576
    Flashlight     = 1024
    Autoplay       = 2048
    SpunOut        = 4096
    Relax2         = 8192    # Autopilot
    Perfect        = 16384 # Only set along with SuddenDeath. i.e: PF only gives 16416  
    Key4           = 32768
    Key5           = 65536
    Key6           = 131072
    Key7           = 262144
    Key8           = 524288
    FadeIn         = 1048576
    Random         = 2097152
    Cinema         = 4194304
    Target         = 8388608
    Key9           = 16777216
    KeyCoop        = 33554432
    Key1           = 67108864
    Key3           = 134217728
    Key2           = 268435456
    ScoreV2        = 536870912
    Mirror         = 1073741824
    KeyMod = Key1 | Key2 | Key3 | Key4 | Key5 | Key6 | Key7 | Key8 | Key9 | KeyCoop
    FreeModAllowed = NoFail | Easy | Hidden | HardRock | SuddenDeath | Flashlight | FadeIn | Relax | Relax2 | SpunOut | KeyMod
    ScoreIncreaseMods = Hidden | HardRock | DoubleTime | Flashlight | FadeIn


class GameState(IntEnum):
    """
    game states and their corresponding integer value 
    reported by the tosu api's /websocket/v2
    
    Source:
        * https://github.com/tosuapp/tosu/blob/master/packages/common/enums/osu.ts
    """
    
    menu                   = 0
    edit                   = 1
    play                   = 2
    exit                   = 3
    selectEdit             = 4
    selectPlay             = 5
    selectDrawings         = 6
    resultScreen           = 7
    update                 = 8
    busy                   = 9
    unknown                = 10
    lobby                  = 11
    matchSetup             = 12
    selectMulti            = 13
    rankingVs              = 14
    onlineSelection        = 15
    optionsOffsetWizard    = 16
    rankingTagCoop         = 17
    rankingTeam            = 18
    beatmapImport          = 19
    packageUpdater         = 20
    benchmark              = 21
    tourney                = 22
    charts                 = 23
    # spectating,
    # watchingReplay