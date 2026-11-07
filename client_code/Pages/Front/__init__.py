from anvil import *

from ._anvil_designer import FrontTemplate
from ... import api, bits, router, state
from ...lab_config import CATEGORIES, CATEGORY

# The app's video on the Addanapp YouTube channel (APP_MAKER/youtube/manifest.json), shown in the Watch section.
YT_VIDEO = "eoGeoGcAmg8"


class Front(FrontTemplate):
    """The front page (#, #topic/<field>): published articles only, newest first, the featured one leading, with
    field filters and search. The hero and the Watch section show on the unfiltered page."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.category = args[0] if args and args[0] in CATEGORY else ""
        self.query = ""
        if self.category:
            self.page_title = CATEGORY[self.category]["label"]
        state.set_control_attr(self.search_box, "aria-label", "Search the front page")
        state.set_control_attr(self.search_box, "autocomplete", "off")
        self.dom_nodes["yt_cover"].addEventListener("click", self._play)
        self.data = api.load("get_front_page", self.category or None, None)
        self._draw()

    def _draw(self):
        d, nodes = self.data, self.dom_nodes
        st = d["stats"]
        me = state.me()
        write_href = "#write" if me else "#join/write"
        plain = not self.category and not self.query
        self.hero.visible = plain
        self.watch_box.visible = plain
        nodes["write_link"].setAttribute("href", write_href)
        bits.text(nodes["stat_articles"], st["articles"])
        bits.text(nodes["stat_writers"], st["writers"])
        bits.text(nodes["stat_sources"], st["sources"])

        chips = [{"href": "#", "label": "✨ Everything", "count": st["articles"], "tone": "", "on": not self.category}]
        for key, label, emoji, tone in CATEGORIES:
            chips.append({"href": "#topic/" + key, "label": "%s %s" % (emoji, label), "count": d["counts"].get(key, 0),
                          "tone": tone, "on": key == self.category})
        self.filter_panel.items = chips

        empty = d["lead"] is None and not d["items"]
        self.empty_box.visible = empty
        self.clear_button.visible = False
        self.empty_write.visible = True
        nodes["empty_write_link"].setAttribute("href", write_href)
        if empty:
            if self.query:
                self.empty_mascot.mood = "wow"
                bits.text(nodes["empty_title"], "No specimens match “%s”" % self.query)
                bits.text(nodes["empty_text"], "Try a different word, or browse everything.")
                self.empty_write.visible = False
                self.clear_button.visible = True
            elif self.category:
                cat = CATEGORY[self.category]
                bits.text(nodes["empty_title"], "Nothing in %s %s yet" % (cat["emoji"], cat["label"]))
                bits.text(nodes["empty_text"], "Be the first to publish a discovery in this field!")
                bits.text(nodes["empty_write_link"], "✍️ Write one")
            else:
                bits.text(nodes["empty_title"], "The lab is quiet… for now")
                bits.text(nodes["empty_text"], "No articles have been published yet. Write the very first one! "
                                               "Once a Lab Director approves it, it appears right here.")
                bits.text(nodes["empty_write_link"], "✍️ Write the first discovery")

        lead = d["lead"]
        self.lead_box.visible = lead is not None
        if lead:
            self._lead(lead)
        self.list_box.visible = bool(d["items"])
        if self.query:
            heading = "🔎 %s for “%s”" % (bits.plural(len(d["items"]), "result"), self.query)
        elif self.category:
            cat = CATEGORY[self.category]
            heading = "%s Latest in %s" % (cat["emoji"], cat["label"])
        else:
            heading = "🧫 Fresh from the lab"
        bits.text(nodes["list_title"], heading)
        bits.show(nodes["sr_title"], not plain)  # the page's main heading when the hero (and its h1) is hidden
        bits.text(nodes["sr_title"], heading)
        self.card_panel.items = d["items"]

    def _lead(self, c):
        n = self.dom_nodes
        bits.tone(n["lead"], c["category"].get("tone"))
        bits.text(n["lead_cover"], c["cover"])
        bits.text(n["lead_flag"], "⭐ Featured discovery" if c["featured"] else "🆕 Latest discovery")
        bits.cat_chip(n["lead_cat"], c["category"])
        bits.evidence(n["lead_ev"], c["evidence"])
        bits.text(n["lead_link"], c["title"])
        n["lead_link"].setAttribute("href", "#article/%d" % c["no"])
        bits.text(n["lead_dek"], c["dek"])
        bits.byline(n["lead_by"], n["lead_by_av"], n["lead_by_name"], n["lead_by_extra"], c["author"],
                    " · %s · %d min read" % (c["ago"], c["minutes"]))
        bits.sources_badge(n["lead_src"], c["sources"])
        bits.text(n["lead_boops"], "🐾 %d" % c["boops"])

    def _search(self, query):
        self.query = (query or "").strip()
        self.data = api.load("get_front_page", self.category or None, self.query or None)
        self._draw()

    @handle("search_button", "click")
    def search_button_click(self, **event_args):
        try:
            self._search(self.search_box.text)
        except api.LabError as e:
            state.toast(str(e), "error")

    @handle("search_box", "pressed_enter")
    def search_box_pressed_enter(self, **event_args):
        self.search_button_click()

    @handle("clear_button", "click")
    def clear_button_click(self, **event_args):
        self.search_box.text = ""
        self.search_button_click()

    def _play(self, event):
        """Swap the video's cover for YouTube's player (privacy-enhanced); nothing loads from YouTube before this click."""
        self.dom_nodes["yt_frame"].innerHTML = (
            '<iframe src="https://www.youtube-nocookie.com/embed/' + YT_VIDEO + '?autoplay=1&rel=0&playsinline=1" '
            'title="Adorable Science video" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen '
            'referrerpolicy="strict-origin-when-cross-origin"></iframe>')
