from textual import work
from textual.app import App
from textual.widgets import Log

from pytest_ahriman.event_dispatcher import EventDispatcher


class AhrimanApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self):
        yield Log(highlight=True)

    async def on_load(self):
        self.start_socket()

    @work(exclusive=True, thread=True)
    def start_socket(self):
        self.dispatcher = EventDispatcher()
        self.dispatcher.run()

    async def action_quit(self) -> None:
        self.dispatcher.stop()
        await super().action_quit()


# https://watchfiles.helpmanual.io
