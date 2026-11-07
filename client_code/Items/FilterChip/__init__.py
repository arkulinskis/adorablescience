from anvil import *
import anvil.js

from ._anvil_designer import FilterChipTemplate
from ... import bits


class FilterChip(FilterChipTemplate):
    """A field filter on the front page. item = {href, label, count, tone, on}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        node = anvil.js.get_dom_node(self)
        node.setAttribute("href", i["href"])
        if i.get("tone"):
            node.classList.add("tone-%s" % i["tone"])
        if i["on"]:
            node.classList.add("as-filter-on")
        if i["on"]:
            node.setAttribute("aria-current", "page")
        bits.text(self.dom_nodes["label"], i["label"])
        bits.text(self.dom_nodes["count"], i["count"])
