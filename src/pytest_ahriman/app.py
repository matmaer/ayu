from pathlib import Path
from textual import work
from textual.app import App
from textual.events import Key
from textual.widgets import Log

from pytest_ahriman.event_dispatcher import EventDispatcher


class AhrimanApp(App):
    CSS_PATH = Path("assets/ahriman.tcss")

    def __init__(self, *args, **kwargs):
        self.dispatcher = None
        super().__init__(*args, **kwargs)

    def compose(self):
        yield Log(highlight=True)

    async def on_load(self):
        self.start_socket()

    def on_mount(self):
        self.query_one(Log).write_line("Hello")
        self.dispatcher.register_handler(handler=lambda msg: self.update_log(msg))

    @work(exclusive=True)
    async def start_socket(self):
        self.dispatcher = EventDispatcher()
        self.notify("Websocket Connected", timeout=1)
        await self.dispatcher.start()

    def on_key(self, event: Key):
        if event.key == "space":
            self.notify("pressed")
            self.notify(f"{self.workers}")
            self.run_test()

    @work(thread=True)
    def run_test(self):
        import subprocess

        subprocess.run("pytest", capture_output=True)

    def update_log(self, msg):
        self.query_one(Log).write_line(f"{msg}")


# https://watchfiles.helpmanual.io
