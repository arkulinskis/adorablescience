from anvil import *

from ._anvil_designer import CheckTemplate
from ... import bits


class Check(CheckTemplate):
    """One line of the reviewer checklist. item = {ok, label, detail} from server Review._checks."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c, d = self.item, self.dom_nodes
        d["row"].classList.add("as-ok" if c["ok"] else "as-warn")
        bits.text(d["mark"], "✅" if c["ok"] else "⚠️")
        bits.text(d["label"], c["label"])
        bits.text(d["detail"], c["detail"])
