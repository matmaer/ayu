from typing import Callable
from collections import defaultdict

from websockets.asyncio.server import serve
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosedOK
import asyncio

from ayu.constants import WEB_SOCKET_HOST, WEB_SOCKET_PORT
from ayu.classes.event import Event
from ayu.utils import EventType


class EventDispatcher:
    def __init__(self, host: str = WEB_SOCKET_HOST, port: int = WEB_SOCKET_PORT):
        self.host = host
        self.port = port
        self.running = False
        self.server = None
        self.event_handler: defaultdict[EventType | None, list] = defaultdict(list)

        self.data = ""

    # Handler
    async def handler(self, websocket):
        while True:
            try:
                msg = await websocket.recv()
            except ConnectionClosedOK:
                break

            if self.event_handler:
                event = Event.deserialize(msg)
                event_type = event.event_type
                event_payload = event.event_payload
                match event_type:
                    case EventType.COLLECTION:
                        handlers = self.event_handler[EventType.COLLECTION]
                    case EventType.OUTCOME:
                        handlers = self.event_handler[EventType.OUTCOME]
                    case EventType.REPORT:
                        handlers = self.event_handler[EventType.REPORT]
                    case EventType.SCHEDULED:
                        handlers = self.event_handler[EventType.SCHEDULED]

            if handlers:
                for handler in handlers:
                    handler(event_payload)

            self.data = msg

    def register_handler(self, event_type: EventType, handler: Callable):
        # with asyncio.Lock():
        # self.event_handler[event_type] = handler
        self.event_handler[event_type].append(handler)

    def unregister_handler(self, event_type: EventType):
        # with asyncio.Lock():
        self.event_handler.pop(event_type)

    # Start Websocket Server
    async def start(self):
        asyncio.create_task(self.start_socket_server(), name="socket")

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
    event: Event, host: str = WEB_SOCKET_HOST, port: int = WEB_SOCKET_PORT
):
    uri = f"ws://{host}:{port}"

    async with connect(uri) as websocket:
        await websocket.send(message=event.serialize())


async def check_connection(host: str = WEB_SOCKET_HOST, port: int = WEB_SOCKET_PORT):
    uri = f"ws://{host}:{port}"
    async with connect(uri) as websocket:
        await websocket.close()
