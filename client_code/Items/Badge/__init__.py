from anvil import *

from ._anvil_designer import BadgeTemplate
from ... import bits


class Badge(BadgeTemplate):
    """A writer badge (🧫 First Culture). item = {emoji, label, why, small}: small shows only the emoji (the name
    stays readable for screen readers; the reason is the tooltip)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        b, d = self.item, self.dom_nodes
        d["badge"].setAttribute("title", b["why"])
        bits.text(d["emoji"], b["emoji"])
        bits.text(d["label"], b["label"])
