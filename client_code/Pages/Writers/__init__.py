from anvil import *

from ._anvil_designer import WritersTemplate
from ... import api, bits, state


class Writers(WritersTemplate):
    """The writer roster (#writers): everyone with a published article, most published first."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        me = state.me()
        bits.show(self.dom_nodes["join_link"], not me)
        self.dom_nodes["first_link"].setAttribute("href", "#write" if me else "#join/write")
        writers = api.load("list_writers")
        self.empty_box.visible = not writers
        self.writer_panel.items = writers
