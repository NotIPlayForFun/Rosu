"""Getting game data from tosu."""

import json
from collections.abc import Iterator

from websockets.sync.client import connect, ClientConnection

# tosu's default address. The /websocket/v2 endpoint pushes the whole game state
# (current screen, map, HP, score, ...) as JSON, roughly 10 times per second.
TOSU_URL = "ws://127.0.0.1:24050/websocket/v2"

# tosu's state number for gameplay. The game over screen counts as gameplay too.
STATE_PLAY = 2


def listen(url: str = TOSU_URL) -> Iterator[dict]:
    """Connect to tosu and yield every update it sends, as a dict."""
    # TODO: crashes if tosu isn't running or closes the connection. Reconnecting comes later
    #       (websockets' reconnect(), since 17.1, can do this).
    # TODO: worry about what happens if the program can't keep up with the incoming messages.

    # ws: WebSocket ClientConnection
    with connect(url) as ws:
        for message in ws:
            yield json.loads(message)
