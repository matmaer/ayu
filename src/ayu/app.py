from pathlib import Path
from textual import work
from textual.app import App
from textual.reactive import reactive
from textual.events import Key
from textual.widgets import Log, Header, Footer, Collapsible
from textual.containers import Horizontal, Vertical

from ayu.event_dispatcher import EventDispatcher
from ayu.utils import EventType, run_all_tests
from ayu.widgets.navigation import TestTree


class AyuApp(App):
    CSS_PATH = Path("assets/ayu.tcss")
    TOOLTIP_DELAY = 0.5

    data_test_tree: reactive[dict] = reactive({}, init=False)
    counter_total_tests: reactive[int] = reactive(0, init=False)

    def __init__(self, *args, **kwargs):
        self.dispatcher = None
        super().__init__(*args, **kwargs)

    def compose(self):
        yield Header()
        yield Footer()
        outcome_log = Log(highlight=True, id="log_outcome")
        outcome_log.border_title = "Outcome"
        report_log = Log(highlight=True, id="log_report")
        report_log.border_title = "Report"
        collection_log = Log(highlight=True, id="log_collection")
        collection_log.border_title = "Collection"
        with Horizontal():
            yield TestTree(label="Tests")
            with Vertical():
                with Collapsible(title="Outcome", collapsed=False):
                    yield outcome_log
                with Collapsible(title="Report", collapsed=False):
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
        self.app.dispatcher.register_handler(
            event_type=EventType.COLLECTION,
            handler=lambda data: self.update_app_data(data),
        )

    def update_app_data(self, data):
        self.data_test_tree = data["tree"]
        self.counter_total_tests = data["meta"]["test_count"]
        # self.mutate_reactive(self.data_test_tree)

    @work(exclusive=True)
    async def start_socket(self):
        self.dispatcher = EventDispatcher()
        self.notify("Websocket Started", timeout=1)
        await self.dispatcher.start()

    def on_key(self, event: Key):
        if event.key == "ctrl+j":
            self.run_test()
        if event.key == "w":
            self.notify(f"{self.workers}")
        if event.key == "c":
            self.query_one(TestTree).reset_test_results()
            for log in self.query(Log):
                log.clear()

    @work(thread=True)
    def run_test(self):
        run_all_tests(tests_to_run=self.query_one(TestTree).marked_tests)

    def update_outcome_log(self, msg):
        self.query_one("#log_outcome", Log).write_line(f"{msg}")

    def update_report_log(self, msg):
        self.query_one("#log_report", Log).write_line(f"{msg}")

    def watch_data_test_tree(self):
        self.query_one("#log_collection", Log).write_line(f"{self.data_test_tree}")


# https://watchfiles.helpmanual.io
