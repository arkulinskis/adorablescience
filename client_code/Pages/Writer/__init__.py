from anvil import *

from ._anvil_designer import WriterTemplate
from ... import api, bits
from ...lab_config import domain_of


class Writer(WriterTemplate):
    """A writer's profile (#writer/<uid>): their lab badge, stats, badges and published articles."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        w = api.load("get_writer", args[0] if args else None)
        self.page_title = w["name"]
        d, st = self.dom_nodes, w["stats"]
        bits.show(d["edit_link"], bool(w["is_me"]))
        bits.avatar(d["av"], w, "xxl")
        bits.specimen(d["lab_id"], 0)
        bits.text(d["lab_id"], "LAB ID · %s" % (w["uid"] or "").upper())
        bits.show(d["director"], bool(w.get("is_admin")))
        bits.text(d["name"], w["name"])
        bits.text(d["spec"], "🔭 " + (w.get("specialty") or "Community science writer"))
        bits.text(d["bio"], w.get("bio") or ("Tell readers about yourself!" if w["is_me"]
                                            else "This scientist prefers to let their articles do the talking."))
        bits.text(d["since"], "🧫 Lab member since %s" % w["since"])
        if w.get("website"):
            bits.show(d["site"], True)
            d["site"].setAttribute("href", w["website"])
            bits.text(d["site"], "🔗 " + domain_of(w["website"]))
        self.badge_panel.items = w.get("badges") or []
        bits.text(d["st_published"], st["published"])
        bits.text(d["st_sources"], st["sources"])
        bits.text(d["st_avg"], st["avg_sources"])
        bits.text(d["st_boops"], st["boops"])
        self.articles_box.visible = bool(w["articles"])
        self.card_panel.items = w["articles"]
        self.empty_box.visible = not w["articles"]
        self.empty_actions.visible = bool(w["is_me"])
        if w["is_me"]:
            bits.text(d["empty_title"], "No published articles yet")
            bits.text(d["empty_text"], "Your published articles will appear here. Drafts and articles in review stay in your lab.")
