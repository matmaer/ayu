from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ayu.app import AyuApp

from textual import on
from textual.reactive import reactive
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, DataTable, TextArea

from ayu.utils import EventType


class CoverageExplorer(Vertical):
    app: "AyuApp"

    coverage_dict: reactive[dict] = reactive({})
    selected_file: reactive[str] = reactive("")
    selected_lines: reactive[list] = reactive([])

    def on_mount(self):
        self.display = False

        self.app.dispatcher.register_handler(
            event_type=EventType.COVERAGE,
            handler=lambda msg: self.update_coverage_dict(msg),
        )

    def compose(self):
        yield CoverageLabel("[bold]Test Coverage[/]")
        with Horizontal():
            with Vertical():
                yield CoverageTable(id="table_coverage").data_bind(
                    CoverageExplorer.coverage_dict
                )
                yield CoverageFilePreview("Preview").data_bind(
                    selected_file=CoverageExplorer.selected_file,
                    selected_lines=CoverageExplorer.selected_lines,
                )
            yield MissingLinesTable(id="table_lines").data_bind(
                coverage_dict=CoverageExplorer.coverage_dict,
                selected_file=CoverageExplorer.selected_file,
            )

    def update_coverage_dict(self, msg):
        self.coverage_dict = msg["coverage_dict"]

    @on(DataTable.RowHighlighted, "#table_coverage")
    def update_selected_file(self, event: DataTable.RowHighlighted):
        if event.row_key:
            file_name = self.query_one(CoverageTable).get_row(event.row_key)[0]
            self.selected_file = file_name

    @on(DataTable.RowHighlighted, "#table_lines")
    def update_selected_lines(self, event: DataTable.RowHighlighted):
        if event.row_key:
            lines = self.query_one(MissingLinesTable).get_row(event.row_key)[0]
            self.selected_lines = lines


class CoverageLabel(Label):
    "Label for Coverage Explorer"


class CoverageTable(DataTable):
    """General Table for Coverage Information"""

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


class MissingLinesTable(DataTable):
    """Table for Missing Lines"""

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
        for missing_line_pairs in self.coverage_dict[self.selected_file][
            "lines_missing"
        ]:
            self.add_row(missing_line_pairs)


class CoverageFilePreview(TextArea):
    """Preview of Lines in source file"""

    selected_file: reactive[str] = reactive("")
    selected_lines: reactive[list] = reactive([])

    def on_mount(self):
        self.language = "python"
        self.show_line_numbers = True
        self.read_only = True

    def watch_selected_file(self):
        if self.selected_file:
            with open(self.selected_file, "r") as file:
                self.text = file.read()

    def watch_selected_lines(self):
        if self.selected_lines:
            self.scroll_to(
                y=self.selected_lines[0] - 1,
                animate=True,
                duration=0.5,
            )
