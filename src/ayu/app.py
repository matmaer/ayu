from pathlib import Path
from textual import work, on
from textual.app import App
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.events import Key
from textual.widgets import Log, Header, Footer, Collapsible, Tree, Button
from textual.containers import Horizontal, Vertical, Center
from textual_tags import Tag

from ayu.event_dispatcher import EventDispatcher
from ayu.constants import WEB_SOCKET_HOST, WEB_SOCKET_PORT
from ayu.utils import EventType, NodeType, run_all_tests
from ayu.widgets.navigation import TestTree
from ayu.widgets.detail_viewer import DetailView, TestResultDetails
from ayu.widgets.filter import TreeFilter, MarkersFilter
from ayu.widgets.helper_widgets import ToggleRule
from ayu.widgets.modals.search import ModalSearch
from ayu.widgets.log import OutputLog, LogContainer


class AyuApp(App):
    CSS_PATH = Path("assets/ayu.tcss")
    TOOLTIP_DELAY = 0.5

    BINDINGS = [
        Binding("ctrl+l", "run_tests", "Run Tests", show=True, priority=True),
        Binding("ctrl+l", "run_marked_tests", "Run ⭐ Tests", show=True, priority=True),
        Binding("s", "show_details", "Details", show=True),
        Binding("c", "clear_test_results", "Clear Results", show=True, priority=True),
        Binding("ctrl+r", "refresh", "Refresh", show=True, priority=True),
        Binding("O", "open_search", "Search", show=True, priority=True),
        Binding("L", "open_log", "Log", show=True),
    ]

    data_test_tree: reactive[dict] = reactive({}, init=False)
    counter_total_tests: reactive[int] = reactive(0, init=False)

    filter: reactive[dict] = reactive(
        {
            "show_favourites": True,
            "show_failed": True,
            "show_skipped": True,
            "show_passed": True,
            "excluded_markers": {},
        },
        init=False,
    )
    test_results_ready: reactive[bool] = reactive(False, init=False)
    tests_running: reactive[bool] = reactive(False, init=False)
    markers: reactive[list[str]] = reactive([])

    def __init__(
        self,
        test_path: Path | None = None,
        host: str | None = WEB_SOCKET_HOST,
        port: int | None = WEB_SOCKET_PORT,
        *args,
        **kwargs,
    ):
        self.host = host
        self.port = port
        self.dispatcher = None
        self.test_path = test_path
        super().__init__(*args, **kwargs)

    def compose(self):
        yield Header()
        yield Footer()
        outcome_log = Log(id="log_outcome")
        outcome_log.border_title = "Outcome"
        report_log = Log(id="log_report")
        report_log.border_title = "Report"
        collection_log = Log(id="log_collection")
        collection_log.border_title = "Collection"
        debug_log = Log(id="log_debug")
        debug_log.border_title = "Debug"
        yield LogContainer()
        with Horizontal():
            with Vertical(id="vertical_test_tree"):
                yield TestTree(label="Tests", id="testtree").data_bind(
                    filter=AyuApp.filter,
                    filtered_data_test_tree=AyuApp.data_test_tree,
                    filtered_counter_total_tests=AyuApp.counter_total_tests,
                )
                yield TreeFilter().data_bind(
                    test_results_ready=AyuApp.test_results_ready, markers=AyuApp.markers
                )
            with Vertical():
                yield DetailView()
                with Collapsible(title="Outcome", collapsed=True):
                    yield outcome_log
                with Collapsible(title="Report", collapsed=True):
                    yield report_log
                with Collapsible(title="Collection", collapsed=True):
                    yield collection_log
                with Collapsible(title="Debug", collapsed=False):
                    yield debug_log

    async def on_load(self):
        self.start_socket()

    def on_mount(self):
        self.dispatcher.register_handler(
            event_type=EventType.OUTCOME,
            handler=lambda msg: self.update_outcome_log(msg),
        )
        self.dispatcher.register_handler(
            event_type=EventType.COVERAGE,
            handler=lambda msg: self.update_debug_log(msg),
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
        self.markers = data["meta"]["markers"]

    @work(exclusive=True)
    async def start_socket(self):
        self.dispatcher = EventDispatcher(host=self.host, port=self.port)
        self.notify("Websocket Started", timeout=1)
        await self.dispatcher.start()

    def on_key(self, event: Key):
        if event.key == "w":
            self.notify(f"{self.workers}")

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

    @on(Tag.Hovered)
    @on(Tag.Focused)
    @on(Tag.Selected)
    def hightlight_test_tree(self, event: Tag.Hovered | Tag.Focused | Tag.Selected):
        self.query_one(TestTree).highlight_marker_rows(marker=event.tag.value)

    @on(MarkersFilter.Marked)
    def favourite_tests_from_tags(self, event: MarkersFilter.Marked):
        self.query_one(TestTree).mark_test_as_fav_from_markers(marker=event.current_tag)

    @on(ModalSearch.Marked)
    def favourite_tests_from_search(self, event: ModalSearch.Marked):
        self.query_one(TestTree).action_mark_test_as_fav_from_search(
            nodeid=event.nodeid
        )

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

    def action_show_details(self):
        self.query_one(DetailView).toggle()
        self.query_one(TreeFilter).toggle()

    def action_open_log(self):
        self.query_one(Center).display = not self.query_one(Center).display

    @work(thread=True)
    async def action_run_tests(self):
        self.tests_running = True
        self.reset_filters()
        # Log Runner Output
        runner = await run_all_tests(tests_path=self.test_path)
        loggi = False
        from ayu.utils import remove_ansi_escapes

        while True:
            if runner.returncode is not None:
                break
            if runner.stdout is None:
                break
            output_line = await runner.stdout.readline()
            decoded_line = remove_ansi_escapes(output_line.decode())

            if "tests coverage" in decoded_line:
                loggi = True
            if True:
                # self.call_from_thread(
                #     self.query_one("#log_debug", Log).write_line, decoded_line
                # )
                self.call_from_thread(
                    self.query_one(OutputLog).write_line, decoded_line
                )
            if decoded_line.startswith("TOTAL"):
                loggi = False
                print(loggi)
        # Log Runner End
        self.test_results_ready = True
        self.tests_running = False

    @work(thread=True)
    def action_run_marked_tests(self):
        self.tests_running = True
        self.reset_filters()
        run_all_tests(
            tests_path=self.test_path,
            tests_to_run=self.query_one(TestTree).marked_tests,
        )
        self.test_results_ready = True
        self.tests_running = False

    def action_refresh(self):
        self.query_one(TestTree).action_collect_tests()

    def action_clear_test_results(self):
        self.test_results_ready = False
        self.query_one(TestTree).reset_test_results()
        for log in self.query(Log):
            log.clear()

    def action_open_search(self):
        def select_searched_nodeid(nodeid: str | None):
            if nodeid:
                node = self.query_one(TestTree).get_node_by_nodeid(nodeid=nodeid)
                self.query_one(TestTree).select_node(node=node)

        self.push_screen(ModalSearch(), callback=select_searched_nodeid)

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

    def update_debug_log(self, msg):
        self.query_one("#log_debug", Log).write_line(f"{msg}")

    def watch_data_test_tree(self):
        self.query_one("#log_collection", Log).write_line(f"{self.data_test_tree}")


# https://watchfiles.helpmanual.io
