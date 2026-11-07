from anvil import *

from ._anvil_designer import WriterCardTemplate
from ... import bits


class WriterCard(WriterCardTemplate):
    """A writer on the roster. item = list_writers() entry {uid, name, avatar, specialty, bio, published, sources,
    boops, badges, latest}. The name link stretches over the card."""

    def __init__(self, **properties):
        super().__init__(**properties)
        w, d = self.item, self.dom_nodes
        bits.avatar(d["av"], w, "xl")
        bits.text(d["link"], w["name"])
        d["link"].setAttribute("href", "#writer/%s" % w["uid"])
        bits.text(d["spec"], w.get("specialty") or "Community science writer")
        bits.text(d["bio"], w.get("bio") or "")
        bits.show(d["bio"], bool(w.get("bio")))
        bits.text(d["published"], w["published"])
        bits.text(d["sources"], w["sources"])
        bits.text(d["boops"], w["boops"])
        bits.text(d["latest"], w["latest"])
        self.badge_panel.items = [dict(b, small=True) for b in w.get("badges") or []]
