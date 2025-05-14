from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ayu.app import AyuApp

from textual import on
from textual.binding import Binding
from textual.reactive import reactive
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, DataTable, TextArea

from ayu.utils import EventType


class CoverageExplorer(Vertical):
    app: "AyuApp"

    coverage_dict: reactive[dict] = reactive({})
    selected_file: reactive[str] = reactive("")
    selected_line: reactive[list] = reactive([])

    def on_mount(self):
        self.display = False

        self.app.dispatcher.register_handler(
            event_type=EventType.COVERAGE,
            handler=lambda msg: self.update_coverage_dict(msg),
        )

    def compose(self):
        yield CoverageLabel("[bold]Test Coverage[/]")
        with Vertical():
            with Horizontal():
                yield CoverageTable(id="table_coverage").data_bind(
                    CoverageExplorer.coverage_dict
                )
                yield MissingLinesTable(id="table_lines").data_bind(
                    coverage_dict=CoverageExplorer.coverage_dict,
                    selected_file=CoverageExplorer.selected_file,
                )
            yield CoverageFilePreview("Preview").data_bind(
                selected_file=CoverageExplorer.selected_file,
                selected_line=CoverageExplorer.selected_line,
            )

    def update_coverage_dict(self, msg):
        self.coverage_dict = msg["coverage_dict"]

    @on(DataTable.RowHighlighted, "#table_coverage")
    def update_selected_file(self, event: DataTable.RowHighlighted):
        if event.row_key:
            file_name = self.query_one(CoverageTable).get_row(event.row_key)[0]
            self.selected_file = file_name

    @on(DataTable.RowHighlighted, "#table_lines")
    def update_selected_line(self, event: DataTable.RowHighlighted):
        if event.row_key:
            line = self.query_one(MissingLinesTable).get_row(event.row_key)[0]
            self.selected_line = line


class CoverageLabel(Label):
    "Label for Coverage Explorer"


class CoverageTable(DataTable):
    """General Table for Coverage Information"""

    BINDINGS = [
        Binding("j, down", "cursor_down", "down", key_display="j/↓"),
        Binding("k, up", "cursor_up", "up", key_display="k/↑"),
        Binding("l, right", "go_to_lines", "to lines"),
    ]

    coverage_dict: reactive[dict] = reactive({})

    def on_mount(self):
        self.cursor_type = "row"
        self.add_columns(
            "Name",
            "Statements",
            "Missing",
            "Covered",
        )

    def watch_coverage_dict(self):
        if not self.coverage_dict:
            return

        self.clear()
        for module_name, module_dict in self.coverage_dict.items():
            self.add_row(
                module_name,
                module_dict["n_statements"],
                module_dict["n_missed"],
                module_dict["percent_covered"],
                key=module_name,
            )

    def action_go_to_lines(self):
        self.app.action_focus_next()


class MissingLinesTable(DataTable):
    """Table for Missing Lines"""

    BINDINGS = [
        Binding("j, down", "cursor_down", "down", key_display="j/↓"),
        Binding("k, up", "cursor_up", "up", key_display="k/↑"),
        Binding("h, left", "back_to_coverage", "to cov table"),
    ]
    coverage_dict: reactive[dict] = reactive({})
    selected_file: reactive[str] = reactive("")

    def on_mount(self):
        self.cursor_type = "row"
        self.add_columns(
            "Missing Lines",
        )

    def watch_selected_file(self):
        if not self.selected_file:
            return

        self.clear()
        for missing_lines in self.coverage_dict[self.selected_file]["lines_missing"]:
            self.add_row(missing_lines)

    def action_back_to_coverage(self):
        self.app.action_focus_previous()


class CoverageFilePreview(TextArea):
    """Preview of Lines in source file"""

    selected_file: reactive[str] = reactive("")
    selected_line: reactive[int] = reactive(0)

    def on_mount(self):
        self.language = "python"
        self.show_line_numbers = True
        self.read_only = True
        # self.

    def watch_selected_file(self):
        if self.selected_file:
            with open(self.selected_file, "r") as file:
                self.text = file.read()

    def watch_selected_line(self):
        if self.selected_line:
            self.scroll_to(
                y=self.selected_line - 1,
                animate=True,
                duration=0.5,
            )
