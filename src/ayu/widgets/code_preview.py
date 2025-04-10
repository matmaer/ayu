from pathlib import Path

from textual.reactive import reactive
from textual.widgets import TextArea
from textual_slidecontainer import SlideContainer


class CodePreview(SlideContainer):
    file_path_to_preview: reactive[Path | None] = reactive(None)

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
            "No File Selected", id="textarea_preview", language="python", read_only=True
        )

    def watch_file_path_to_preview(self):
        if not self.file_path_to_preview:
            self.border_title = "No File selected"
