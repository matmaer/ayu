from pathlib import Path

from textual import on
from textual.reactive import reactive
from textual.widgets import TextArea
from textual_slidecontainer import SlideContainer

from ayu.utils import get_preview_test
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
        target_widget = event.togglerule.target_widget_id
        self.query_one(f"#{target_widget}").toggle_class("hidden")


class CodePreview(TextArea):
    def on_mount(self):
        self.language = "python"
        self.read_only = True
        self.id = "textarea_preview"
        self.show_line_numbers = True


class TestResultDetails(TextArea): ...
