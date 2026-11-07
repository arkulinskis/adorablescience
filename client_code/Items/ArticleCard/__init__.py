from anvil import *

from ._anvil_designer import ArticleCardTemplate
from ... import bits


class ArticleCard(ArticleCardTemplate):
    """An article card in a grid (front page, "More from", a writer's page). item = the server's card() dict.
    The title link stretches over the whole card; the field chip and the byline stay clickable on top."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c, d = self.item, self.dom_nodes
        d["card"].classList.add("tone-%s" % (c["category"].get("tone") or "lav"))
        bits.text(d["cover"], c["cover"])
        bits.specimen(d["spec"], c["no"])
        bits.cat_chip(d["cat"], c["category"])
        bits.text(d["link"], c["title"])
        d["link"].setAttribute("href", "#article/%d" % c["no"])
        bits.text(d["dek"], c["dek"])
        bits.byline(d["by"], d["by_av"], d["by_name"], d["by_extra"], c["author"])
        bits.sources_badge(d["src"], c["sources"])
        bits.text(d["boops"], "🐾 %d" % c["boops"])
