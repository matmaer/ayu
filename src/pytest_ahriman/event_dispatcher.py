from typing import Callable, Any
from websockets.asyncio.server import serve
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosedOK
import asyncio

from pytest_ahriman.constants import WEB_SOCKET_HOST, WEB_SOCKET_PORT


class EventDispatcher:
    def __init__(self, host: str = WEB_SOCKET_HOST, port: int = WEB_SOCKET_PORT):
        self.host = host
        self.port = port
        self.running = False
        self.server = None
        self.event_handler: dict[Any, Any] = {}

        self.data = ""

    # Handler
    async def handler(self, websocket):
        while True:
            try:
                msg = await websocket.recv()
            except ConnectionClosedOK:
                break

            print(f"msg: {msg}")
            if self.event_handler:
                handler = self.event_handler["test"]
                handler(msg)

            self.data = msg

    def register_handler(self, handler: Callable):
        # with asyncio.Lock():
        self.event_handler["test"] = handler

    # Start Websocket Server
    async def start(self):
        asyncio.create_task(self.start_socket_server(), name="socket")

        # asyncio.run(
        #     asyncio.run(self.run())
        # )

    def stop(self):
        asyncio.get_running_loop().create_future()

    async def start_socket_server(self):
        self.server = await serve(self.handler, self.host, self.port)
        print("started")
        await self.server.wait_closed()

    def get_data(self):
        return self.data


# send events
async def send_event(
    msg: str, host: str = WEB_SOCKET_HOST, port: int = WEB_SOCKET_PORT
):
    uri = f"ws://{host}:{port}"

    async with connect(uri) as websocket:
        await websocket.send(f"{msg}")


async def check_connection(host: str = WEB_SOCKET_HOST, port: int = WEB_SOCKET_PORT):
    uri = f"ws://{host}:{port}"
    async with connect(uri) as websocket:
        await websocket.close()
