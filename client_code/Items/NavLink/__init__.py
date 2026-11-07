from anvil import *
import anvil.js

from ._anvil_designer import NavLinkTemplate
from ... import bits


class NavLink(NavLinkTemplate):
    """A header tab. item = {key, href, label, badge, on} (Layouts/Shell.refresh). badge = articles waiting for
    review (Lab Directors)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        node = anvil.js.get_dom_node(self)
        node.setAttribute("href", i["href"])
        if i["on"]:
            node.classList.add("as-tab-on")
            node.setAttribute("aria-current", "page")
        bits.text(self.dom_nodes["label"], i["label"])
        bits.show(self.dom_nodes["badge"], bool(i["badge"]))
        bits.text(self.dom_nodes["badge"], i["badge"])
        if i["badge"]:
            self.dom_nodes["badge"].setAttribute("aria-label", "%d waiting" % i["badge"])
