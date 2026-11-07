from anvil import *

from ._anvil_designer import LabGroupTemplate
from ... import bits


class LabGroup(LabGroupTemplate):
    """One status group on My lab. item = {status, emoji, label, help, rows}. Passes its rows' x-reload up."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i, d = self.item, self.dom_nodes
        bits.text(d["title"], "%s %s" % (i["emoji"], i["label"]))
        bits.text(d["n"], len(i["rows"]))
        bits.text(d["help"], i["help"])
        self.row_panel.items = i["rows"]
        self.row_panel.add_event_handler("x-reload", self._reload)

    def _reload(self, **event_args):
        if self.parent is not None:
            self.parent.raise_event("x-reload")
