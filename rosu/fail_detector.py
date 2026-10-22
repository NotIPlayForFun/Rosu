"""Recognising a fail in tosu's game data."""

from rosu.tosu import STATE_PLAY

from rosu.tosu_enums import GameState, Mods
from rosu.tosu_data_getter import TosuDataGetter

get = TosuDataGetter().get

UNFAILABLE_MODS = Mods.NoFail | Mods.Relax | Mods.Autoplay | Mods.Relax2 | Mods.Cinema

# MULTIPLAYER STATES
# Gameplay entered from one of these states is a multiplayer match, which has
# no game over screen (you keep playing after failing).
# it should not be possible to enter a map from lobby or selectMulti,
# they were overkill for testing and can be removed 
MULTIPLAYER_STATES = {GameState.lobby, GameState.matchSetup, GameState.selectMulti}

class FailDetector:
    """Gets every tosu update; update() returns True once, at the moment the player fails."""

    # TODO: things that can look like a fail but aren't: NoFail (HP can sit at 0),
    #       someone else's replay or spectating, multiplayer, maybe quick retry or quitting.
    
    # TODO: watching your own replay looks just like playing (tosu can't tell). Check what
    #       happens there, and whether SD/PF fails bring HP to 0.

    def __init__(self) -> None:
        self.armed = False
        """
        Whether 
          * a map is in progress (STATE == STATE_PLAY)
          * HP > 0 since the last time a map was entered
        Only then => HP 0 could be a fail. 
        Second condition is in case tosu shows HP 0 while a map is still loading.
        """
        
        self.last_state: int | None = None
        """
        state number of previous update
        """
        
        self.entered_from: int | None = None
        """
        state number from which gameplay was entered. relevant if state is `STATE_PLAY`.
        """
        
        self.ignore_reason: str | None = None
        """
        The reason to ignore a fail in a current play, if any.
        """
        

    def update(self, data: dict) -> bool:
        """
        Should be called with every tosu poll update. 
        
        Returns True once per fail, in an update where the player fails a map.
        """
        state = get(data, ("state", "number"))
        
        # NOT IN GAMEPLAY
        if state != STATE_PLAY:
            # disarm fail detection
            self.armed = False
            # record state before returning
            self.last_state = state
            return False

        # ENTERING GAMEPLAY ON THIS UPDATE
        if state == STATE_PLAY and self.last_state != STATE_PLAY:
            self.entered_from = self.last_state

        # last_state won't be needed anymore in this loop
        self.last_state = state

        # IN GAMEPLAY, BUT HP GOING TO 0 DOESN'T WON'T CAUSE A FAIL
        ignore_reason = self.find_ignore_reason(data)
        self.ignore_reason = ignore_reason
        if ignore_reason is not None:
            return False

        hp = get(data, ("play", "healthBar", "normal"))

        # IN GAMEPLAY; HP ABOVE 0
        # A drop to 0 means fail => arm the fail detector
        if hp > 0:
            self.armed = True
            return False

        # IN GAMEPLAY; HP AT 0; ARMED
        # Report the fail once, then disarm the fail detector
        if self.armed:
            self.armed = False
            return True
        
        # IN GAMEPLAY; HP AT 0; NOT ARMED
        return False
    
    def find_ignore_reason(self, data: dict) -> str | None:
        """
        Returns a string explaining why a fail in the current play
        should be ignored, or None if it shouldn't be ignored.
        """
        # TODO: test all this
        
        # CHECK FOR UNFAILABLE MODS
        unfailable_mods_active = Mods(get(data, ("play", "mods", "number")) & UNFAILABLE_MODS)
        if unfailable_mods_active:
            return f'unfailable mods: {str(unfailable_mods_active.name)}' # or unfailable_mods_active.name
    
        # CHECK IF SOMEONE ELSE IS PLAYING
        # for example, someone else's replay or spectating
        player = get(data, ("play", "playerName"))
        profile = get(data, ("profile", "name"))
        
        # either may not have been loaded into data by tosu yet on first update in a map
        if player and profile:
            if player != profile:
                return f"someone else is playing: player={player}, profile={profile}"
        
        # ENTERED FROM A MULTIPLAYER LOBBY
        if self.entered_from in MULTIPLAYER_STATES:
            return "entered from multiplayer lobby"
        
        return None