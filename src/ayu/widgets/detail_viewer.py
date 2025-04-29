from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ayu.app import AyuApp

from textual import on
from textual.reactive import reactive
from textual.widgets import TextArea
from textual_slidecontainer import SlideContainer

from ayu.utils import EventType, get_preview_test
from ayu.widgets.helper_widgets import ToggleRule


class DetailView(SlideContainer):
    file_path_to_preview: reactive[Path | None] = reactive(None, init=False)
    test_start_line_no: reactive[int] = reactive(-1, init=False)

    def __init__(self, *args, **kwargs):
        super().__init__(
            slide_direction="up",
            floating=False,
            start_open=False,
            duration=0.5,
            *args,
            **kwargs,
        )

    def compose(self):
        yield CodePreview(
            "Please select a test",
        )
        yield ToggleRule(target_widget_id="textarea_test_result_details")
        yield TestResultDetails("Lorem Uiasd", id="textarea_test_result_details")

    def watch_file_path_to_preview(self):
        self.border_title = self.file_path_to_preview.as_posix()

    def watch_test_start_line_no(self):
        if self.test_start_line_no == -1:
            self.query_one("#textarea_preview").text = "Please select a test"
        else:
            content = get_preview_test(
                file_path=self.file_path_to_preview,
                start_line_no=self.test_start_line_no,
            )
            self.query_one(
                "#textarea_preview", TextArea
            ).line_number_start = self.test_start_line_no
            self.query_one("#textarea_preview", TextArea).text = content

    @on(ToggleRule.Toggled)
    def toggle_code_result_visibility(self, event: ToggleRule.Toggled):
        target_widget = self.query_one(f"#{event.togglerule.target_widget_id}")
        target_widget.display = not target_widget.display


class CodePreview(TextArea):
    def on_mount(self):
        self.language = "python"
        self.read_only = True
        self.id = "textarea_preview"
        self.show_line_numbers = True


class TestResultDetails(TextArea):
    app: "AyuApp"
    selected_node_id: reactive[str] = reactive("")
    report_data: reactive[dict] = reactive({})

    def on_mount(self):
        self.language = "python"
        self.read_only = True
        # self.styles.color = 'red'

        self.app.dispatcher.register_handler(
            event_type=EventType.REPORT,
            handler=lambda msg: self.update_report_data(msg),
        )

    def update_report_data(self, data: dict):
        if data["report"]:
            self.report_data = data["report"]

    def watch_selected_node_id(self):
        if self.report_data.get(self.selected_node_id):
            self.text = self.report_data[self.selected_node_id]["longreprtext"]
        else:
            self.text = ""
