from anvil import *

from ._anvil_designer import PickTemplate
from ... import bits


class Pick(PickTemplate):
    """One emoji choice (a cover critter on the writing desk, a lab critter on the profile). item = {value, on, label}.
    A click raises x-pick on the RepeatingPanel; the page redraws and keeps the keyboard focus (data-key)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        b = self.dom_nodes["button"]
        bits.text(b, self.item["value"])
        b.setAttribute("aria-label", self.item["label"])
        b.setAttribute("aria-pressed", "true" if self.item["on"] else "false")
        b.setAttribute("data-key", self.item["value"])
        b.classList.toggle("as-cover-on", bool(self.item["on"]))

    def button_click(self, event):
        self.parent.raise_event("x-pick", value=self.item["value"])
