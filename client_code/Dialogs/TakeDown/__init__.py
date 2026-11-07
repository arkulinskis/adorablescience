from anvil import *

from ._anvil_designer import TakeDownTemplate


class TakeDown(TakeDownTemplate):
    """Taking a published article down needs a note for the writer. Closes with the note, or None."""

    def __init__(self, **properties):
        super().__init__(**properties)

    @handle("", "show")
    def form_show(self, **event_args):
        self.note_box.focus()

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("down_button", "click")
    def down_button_click(self, **event_args):
        note = (self.note_box.text or "").strip()
        if len(note) < 5:
            self.message.text, self.message.visible = "Leave the writer a note explaining why it was taken down.", True
            self.note_box.focus()
            return
        self.raise_event("x-close-alert", value=note)
