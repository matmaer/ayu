from textual.containers import Horizontal
from textual.widgets import Button

from textual_slidecontainer import SlideContainer


class TreeFilter(SlideContainer):
    # file_path_to_preview: reactive[Path | None] = reactive(None, init=False)
    # test_start_line_no: reactive[int] = reactive(-1, init=False)

    def __init__(self, *args, **kwargs):
        super().__init__(
            slide_direction="down",
            floating=False,
            start_open=False,
            duration=0.5,
            *args,
            **kwargs,
        )

    def compose(self):
        with Horizontal():
            yield Button(variant="success")
            yield Button(variant="success")
            yield Button(variant="success")
