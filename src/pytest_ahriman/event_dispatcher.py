# import websockets
# import asyncio
# import json

from pytest_ahriman.constants import WEB_SOCKET_HOST, WEB_SOCKET_PORT


class EventDispatcher:
    def __init__(self, host: str = WEB_SOCKET_HOST, port: int = WEB_SOCKET_PORT):
        self.host = host
        self.port = port
        self.client = None

    # Handler
    def handler(self): ...

    # Start Websocket Server
    def start(self): ...


# send events
def send_event(): ...
