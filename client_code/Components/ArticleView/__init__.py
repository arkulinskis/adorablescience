from anvil import *

from ._anvil_designer import ArticleViewTemplate
from ... import bits
from ...lab_config import STATUSES


class ArticleView(ArticleViewTemplate):
    """One article as readers see it (also on the review desk). show(a) with the server's full_article dict.
    The body is HTML the server rendered from the writer's Markdown-style text (server_code/Render.py escapes
    everything first), so it is the only part set as HTML."""

    def __init__(self, **properties):
        super().__init__(**properties)

    def show(self, a, preview_note=""):
        d = self.dom_nodes
        status = a["status"]
        bits.show(d["banner"], status != "published")
        if status != "published":
            label, emoji, explain = STATUSES.get(status, ("", "", ""))
            d["banner"].className = "as-banner as-banner-%s" % status
            bits.text(d["banner_emoji"], emoji)
            bits.text(d["banner_title"], label)
            bits.text(d["banner_text"], ("%s %s" % (explain, preview_note)).strip())
        note = a.get("review_note") if status == "rejected" else ""
        bits.show(d["note"], bool(note))
        bits.text(d["note_text"], note or "")

        bits.tone(d["head"], a["category"].get("tone"))
        bits.text(d["cover"], a["cover"])
        bits.cat_chip(d["cat"], a["category"])
        bits.evidence(d["ev"], a["evidence"])
        bits.specimen(d["spec"], a["no"])
        bits.text(d["title"], a["title"])
        bits.text(d["dek"], a["dek"])
        when = "Published %s" % a["date"] if status == "published" else "Last edited %s" % a["ago"]
        bits.byline(d["by"], d["by_av"], d["by_name"], d["by_extra"], a["author"],
                    " · %s · %d min read" % (when, a["minutes"]))
        n = int(a["sources"] or 0)
        bits.show(d["src_btn"], n > 0)
        bits.show(d["src_none"], n == 0)
        if n:
            d["src_btn"].className = "as-srcbadge as-srcbadge-btn" + (" as-srcbadge-gold" if n >= 3 else "")
            bits.text(d["src_btn"], "📎 %s ↓" % bits.plural(n, "source"))
        else:
            bits.sources_badge(d["src_none"], 0)

        d["prose"].innerHTML = a.get("body_html") or ""  # safe: rendered and escaped by the server (Render.py)

        sources = a.get("sources_list") or []
        bits.show(d["refs"], bool(sources))
        bits.show(d["refs_none"], not sources)
        bits.text(d["refs_title"], "📚 Sources (%d)" % len(sources))
        bits.show(d["gold"], len(sources) >= 3)
        self.refs_panel.items = sources

    def src_click(self, event):
        target = self.dom_nodes["refs"] if not self.dom_nodes["refs"].hidden else self.dom_nodes["refs_none"]
        target.scrollIntoView({"behavior": "smooth", "block": "start"})
