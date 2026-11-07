from anvil import *

from ._anvil_designer import MeterTemplate
from ... import bits
from ...lab_config import citation_meter


class Meter(MeterTemplate):
    """The citation meter: Pure hypothesis -> Single specimen -> Corroborated -> Peer-purr-viewed."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.show(0, 0)

    def show(self, n_sources, n_cited=0):
        m = citation_meter(n_sources, n_cited)
        d = self.dom_nodes
        d["box"].className = "as-meter tone-%s" % m["tone"]
        bits.text(d["face"], m["emoji"])
        bits.text(d["label"], m["label"])
        bits.text(d["count"], bits.plural(n_sources, "source") + (" · %d cited inline" % n_cited if n_sources else ""))
        bits.text(d["tip"], m["tip"])
        d["fill"].style.width = "%d%%" % m["pct"]
        d["track"].setAttribute("aria-valuenow", str(m["pct"]))
        d["track"].setAttribute("aria-valuetext", m["label"])
