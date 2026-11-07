from anvil import *

from ._anvil_designer import LabTileTemplate
from ... import bits


class LabTile(LabTileTemplate):
    """A count tile on My lab (🧪 2 Needs more data). item = {status, emoji, label, n}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i, d = self.item, self.dom_nodes
        d["tile"].classList.add("as-status-" + i["status"])
        bits.text(d["emoji"], i["emoji"])
        bits.text(d["n"], i["n"])
        bits.text(d["label"], i["label"])
