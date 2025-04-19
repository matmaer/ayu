from pathlib import Path
from textual import work, on
from textual.app import App
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.events import Key
from textual.widgets import Log, Header, Footer, Collapsible, Tree, Button
from textual.containers import Horizontal, Vertical

from ayu.event_dispatcher import EventDispatcher
from ayu.utils import EventType, NodeType, run_all_tests
from ayu.widgets.navigation import TestTree
from ayu.widgets.detail_viewer import DetailView, TestResultDetails
from ayu.widgets.filter import TreeFilter
from ayu.widgets.helper_widgets import ToggleRule


class AyuApp(App):
    CSS_PATH = Path("assets/ayu.tcss")
    TOOLTIP_DELAY = 0.5

    BINDINGS = [
        Binding("ctrl+j", "run_tests", "Run Tests", show=True),
        Binding("ctrl+j", "run_marked_tests", "Run ⭐ Tests", show=True),
        Binding("s", "show_details", "Details", show=True),
        Binding("c", "clear_test_results", "Clear Results", show=True),
    ]

    data_test_tree: reactive[dict] = reactive({}, init=False)
    counter_total_tests: reactive[int] = reactive(0, init=False)

    filter: reactive[dict] = reactive(
        {
            "show_favourites": True,
            "show_failed": True,
            "show_skipped": True,
            "show_passed": True,
        },
        init=False,
    )
    test_results_ready: reactive[bool] = reactive(False, init=False)

    def __init__(self, test_path: Path | None = None, *args, **kwargs):
        self.dispatcher = None
        self.test_path = test_path
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
            with Vertical(id="vertical_test_tree"):
                yield TestTree(label="Tests").data_bind(
                    filter=AyuApp.filter,
                    filtered_data_test_tree=AyuApp.data_test_tree,
                    filtered_counter_total_tests=AyuApp.counter_total_tests,
                )
                yield TreeFilter().data_bind(
                    test_results_ready=AyuApp.test_results_ready
                )
            with Vertical():
                yield DetailView()
                with Collapsible(title="Outcome", collapsed=True):
                    yield outcome_log
                with Collapsible(title="Report", collapsed=True):
                    yield report_log
                with Collapsible(title="Collection", collapsed=True):
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

    @work(exclusive=True)
    async def start_socket(self):
        self.dispatcher = EventDispatcher()
        self.notify("Websocket Started", timeout=1)
        await self.dispatcher.start()

    def on_key(self, event: Key):
        if event.key == "w":
            self.notify(f"{self.workers}")

    def action_show_details(self):
        self.query_one(DetailView).toggle()
        self.query_one(TreeFilter).toggle()

    @on(Button.Pressed, ".filter-button")
    def update_test_tree_filter(self, event: Button.Pressed):
        button_id_part = event.button.id.split("_")[-1]
        filter_state = event.button.filter_is_active
        self.filter[f"show_{button_id_part}"] = filter_state
        self.mutate_reactive(AyuApp.filter)

    def reset_filters(self):
        for btn in self.query(".filter-button"):
            btn.filter_is_active = True
        self.filter = {
            "show_favourites": True,
            "show_failed": True,
            "show_skipped": True,
            "show_passed": True,
        }
        self.mutate_reactive(AyuApp.filter)

    @on(Tree.NodeHighlighted)
    def update_test_preview(self, event: Tree.NodeHighlighted):
        detail_view = self.query_one(DetailView)
        detail_view.file_path_to_preview = Path(event.node.data["path"])
        if event.node.data["type"] in [
            NodeType.FUNCTION,
            NodeType.COROUTINE,
            NodeType.CLASS,
        ]:
            detail_view.test_start_line_no = event.node.data["lineno"]
        else:
            detail_view.test_start_line_no = -1

        self.query_one(ToggleRule).test_result = event.node.data["status"]
        self.query_one(TestResultDetails).selected_node_id = event.node.data["nodeid"]

    @work(thread=True)
    def action_run_tests(self):
        self.reset_filters()
        run_all_tests(tests_path=self.test_path)
        self.test_results_ready = True

    @work(thread=True)
    def action_run_marked_tests(self):
        self.reset_filters()
        run_all_tests(
            tests_path=self.test_path,
            tests_to_run=self.query_one(TestTree).marked_tests,
        )
        self.test_results_ready = True

    def action_clear_test_results(self):
        self.test_results_ready = False
        self.query_one(TestTree).reset_test_results()
        for log in self.query(Log):
            log.clear()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        # on app startup widget is not mounted yet so
        # try except is needed
        try:
            if action == "run_tests":
                if self.query_one(TestTree).marked_tests:
                    return False
            if action == "run_marked_tests":
                if not self.query_one(TestTree).marked_tests:
                    return False
        except NoMatches:
            return True
        return True

    def update_outcome_log(self, msg):
        self.query_one("#log_outcome", Log).write_line(f"{msg}")

    def update_report_log(self, msg):
        self.query_one("#log_report", Log).write_line(f"{msg}")

    def watch_data_test_tree(self):
        self.query_one("#log_collection", Log).write_line(f"{self.data_test_tree}")


# https://watchfiles.helpmanual.io
