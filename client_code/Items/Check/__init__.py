from anvil import *

from ._anvil_designer import CheckTemplate
from ... import bits


class Check(CheckTemplate):
    """One line of the reviewer checklist. item = {ok, label, detail} from server Review._checks (or
    Sources.check_retractions). ok None = couldn't be checked; wait True = still checking (Crossref)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c, d = self.item, self.dom_nodes
        if c.get("wait") or c["ok"] is None:
            d["row"].classList.add("as-unk")
            bits.text(d["mark"], "⏳" if c.get("wait") else "❔")
        else:
            d["row"].classList.add("as-ok" if c["ok"] else "as-warn")
            bits.text(d["mark"], "✅" if c["ok"] else "⚠️")
        bits.text(d["label"], c["label"])
        bits.text(d["detail"], c["detail"])
