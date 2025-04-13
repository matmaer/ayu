from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button

from rich.text import Text
from textual_slidecontainer import SlideContainer


class TreeFilter(SlideContainer):
    filter: reactive[dict] = reactive(
        {
            "show_favourites": True,
            "show_failed": True,
            "show_skipped": True,
            "show_passed": True,
        },
        init=False,
    )

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
            yield FilterButton(
                label=Text.from_markup("Favourites: :star:"),
                id="button_filter_favourites",
            )
            yield FilterButton(
                label=Text.from_markup("Passed: :white_check_mark:"),
                id="button_filter_passed",
            )
            yield FilterButton(
                label=Text.from_markup("Failed: :x:"),
                id="button_filter_failed",
            )
            yield FilterButton(
                label=Text.from_markup("Skipped: [on yellow]:next_track_button: [/]"),
                id="button_filter_skipped",
            )


class FilterButton(Button):
    class Pressed(Button.Pressed): ...

    """Button for filtering the TestTree"""

    filter_is_active: reactive[bool] = reactive(True)

    def on_button_pressed(self):
        self.filter_is_active = not self.filter_is_active

    def watch_filter_is_active(self):
        self.variant = "success" if self.filter_is_active else "error"
