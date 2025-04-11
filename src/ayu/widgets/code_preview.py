from pathlib import Path

from textual.reactive import reactive
from textual.widgets import TextArea
from textual_slidecontainer import SlideContainer

from ayu.utils import get_preview_test


class CodePreview(SlideContainer):
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
        yield TextArea.code_editor(
            "Please select a test",
            id="textarea_preview",
            language="python",
            read_only=True,
        )

    def watch_file_path_to_preview(self):
        self.border_title = self.file_path_to_preview.as_posix()

    def watch_test_start_line_no(self):
        if self.test_start_line_no == -1:
            self.app.query_one("#textarea_preview").text = "Please select a test"
        else:
            content = get_preview_test(
                file_path=self.file_path_to_preview,
                start_line_no=self.test_start_line_no,
            )
            self.app.query_one(
                "#textarea_preview", TextArea
            ).line_number_start = self.test_start_line_no
            self.app.query_one("#textarea_preview", TextArea).text = content
