from textual.containers import Horizontal
from textual.widgets import Button

from rich.text import Text
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
            yield Button(
                label=Text.from_markup("Favourites: :star:"),
                id="button_filter_favourites",
                variant="success",
            )
            yield Button(
                label=Text.from_markup("Passed: :white_check_mark:"),
                id="button_filter_passed",
                variant="success",
            )
            yield Button(
                label=Text.from_markup("Failed: :x:"),
                id="button_filter_failed",
                variant="success",
            )
            yield Button(
                label=Text.from_markup("Skipped: [on yellow]:next_track_button: [/]"),
                id="button_filter_skipped",
                variant="success",
            )
