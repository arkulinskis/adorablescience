from anvil import *

from ._anvil_designer import SourceRefTemplate
from ... import bits


class SourceRef(SourceRefTemplate):
    """One numbered source under an article. item = {n, title, url, publisher, kind_label, kind_emoji, domain}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        s, d = self.item, self.dom_nodes
        bits.text(d["n"], s["n"])
        bits.text(d["link"], s["title"])
        d["link"].setAttribute("href", s["url"])
        pub = " · %s" % s["publisher"] if s.get("publisher") else ""
        bits.text(d["meta"], "%s %s · %s%s" % (s["kind_emoji"], s["kind_label"], s["domain"], pub))
