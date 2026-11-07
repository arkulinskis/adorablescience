from anvil import *

from ._anvil_designer import NoSourcesTemplate
from ... import state


class NoSources(NoSourcesTemplate):
    """Shown when someone submits an article without sources. Closes with "add" (add a source row) or "submit"
    (submit anyway; the server then takes it with acknowledge_unsourced)."""

    def __init__(self, **properties):
        super().__init__(**properties)

    @handle("", "show")
    def form_show(self, **event_args):
        state.focus(self.add_button)

    @handle("submit_button", "click")
    def submit_button_click(self, **event_args):
        self.raise_event("x-close-alert", value="submit")

    @handle("add_button", "click")
    def add_button_click(self, **event_args):
        self.raise_event("x-close-alert", value="add")
