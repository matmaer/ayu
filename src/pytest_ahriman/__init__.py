import asyncio
from pytest_ahriman.event_dispatcher import EventDispatcher
# from pytest_ahriman.app import AhrimanApp


def main():
    # app = AhrimanApp()
    # app.run()
    dispatcher = EventDispatcher()
    asyncio.run(dispatcher.run())


# Start the WebSocket server
if __name__ == "__main__":
    main()
