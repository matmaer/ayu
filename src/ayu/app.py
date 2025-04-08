from pathlib import Path
from textual import work
from textual.app import App
from textual.events import Key
from textual.widgets import Log, Header, Collapsible

from ayu.event_dispatcher import EventDispatcher
from ayu.utils import EventType
from ayu.widgets.navigation import TestTree


class AyuApp(App):
    CSS_PATH = Path("assets/ayu.tcss")

    def __init__(self, *args, **kwargs):
        self.dispatcher = None
        super().__init__(*args, **kwargs)

    def compose(self):
        yield Header()
        yield TestTree(label="Tests")
        outcome_log = Log(highlight=True, id="log_outcome")
        outcome_log.border_title = "Outcome"
        report_log = Log(highlight=True, id="log_report")
        report_log.border_title = "Report"
        collection_log = Log(highlight=True, id="log_collection")
        collection_log.border_title = "Collection"
        with Collapsible(title="Outcome"):
            yield outcome_log
        with Collapsible(title="Report"):
            yield report_log
        with Collapsible(title="Collection", collapsed=False):
            yield collection_log

    async def on_load(self):
        self.start_socket()

    def on_mount(self):
        self.dispatcher.register_handler(
            event_type=EventType.OUTCOME,
            handler=lambda msg: self.update_outcome_log(msg),
        )
        self.dispatcher.register_handler(
            event_type=EventType.REPORT, handler=lambda msg: self.update_report_log(msg)
        )
        self.dispatcher.register_handler(
            event_type=EventType.COLLECTION,
            handler=lambda msg: self.update_collection_log(msg),
        )

    @work(exclusive=True)
    async def start_socket(self):
        self.dispatcher = EventDispatcher()
        self.notify("Websocket Connected", timeout=1)
        await self.dispatcher.start()

    def on_key(self, event: Key):
        if event.key == "space":
            self.run_test()
        if event.key == "c":
            for log in self.query(Log):
                log.clear()

    @work(thread=True)
    def run_test(self):
        import subprocess

        subprocess.run(
            # ["python", "-m", "pytest"],
            ["uv", "run", "--with", "../ayu", "pytest"],
            capture_output=True,
            # executable=Path(sys.executable),
            # cwd=Path.cwd(),
        )

    def update_outcome_log(self, msg):
        self.query_one("#log_outcome", Log).write_line(f"{msg}")

    def update_report_log(self, msg):
        self.query_one("#log_report", Log).write_line(f"{msg}")

    def update_collection_log(self, msg):
        self.query_one("#log_collection", Log).write_line(f"{msg}")


# https://watchfiles.helpmanual.io
