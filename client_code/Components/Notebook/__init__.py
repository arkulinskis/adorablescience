from anvil import *

from ._anvil_designer import NotebookTemplate


class Notebook(NotebookTemplate):
    """The lab notebook: who submitted, approved, sent back ... and their notes. Hidden when there is no history."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.visible = False

    def show(self, history):
        history = history or []
        self.visible = bool(history)
        self.log_panel.items = history
