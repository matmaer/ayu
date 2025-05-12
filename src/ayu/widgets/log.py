from textual.containers import Center
from textual.widgets import Log, Label


class LogViewer(Center):
    def on_mount(self):
        self.display = False

    def compose(self):
        yield LogLabel("[bold]Log Output[/]")
        yield OutputLog(highlight=True)


class LogLabel(Label):
    "Label for log"


class OutputLog(Log):
    can_focus = False
    """Log to display command outputs"""
