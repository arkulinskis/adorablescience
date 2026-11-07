from anvil import *

from ._anvil_designer import DeskRowTemplate
from ... import bits, state
from ...Dialogs.TakeDown import TakeDown


class DeskRow(DeskRowTemplate):
    """An article on the review desk. item = card() dict + mode: "queue" (Review button) or "published" (Feature,
    Take down). Actions call the server, then raise x-reload so the desk redraws."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c, d = self.item, self.dom_nodes
        queue = c["mode"] == "queue"
        bits.text(d["cover"], c["cover"])
        bits.specimen(d["spec"], c["no"])
        bits.cat_chip(d["cat"], c["category"], link=False)
        bits.sources_badge(d["src"], c["sources"])
        bits.text(d["title"], c["title"])
        if queue:
            d["title"].removeAttribute("href")
            bits.text(d["meta"], "by %s %s · submitted %s · %d min read"
                      % (c["author"]["avatar"], c["author"]["name"], c["submitted_ago"], c["minutes"]))
        else:
            d["title"].setAttribute("href", "#article/%d" % c["no"])
            bits.text(d["meta"], "by %s · published %s · 🐾 %d" % (c["author"]["name"], c["ago"], c["boops"]))
        bits.show(d["review_link"], queue)
        d["review_link"].setAttribute("href", "#review/%d" % c["no"])
        self.feature_button.visible = not queue
        self.down_button.visible = not queue
        self.feature_button.text = "⭐ Featured" if c["featured"] else "☆ Feature"
        self.feature_button.role = ["btn", "btn-soft" if c["featured"] else "btn-ghost", "btn-sm"]
        state.set_control_attr(self.feature_button, "aria-pressed", "true" if c["featured"] else "false")

    def _reload(self):
        if self.parent is not None:
            self.parent.raise_event("x-reload")

    @handle("feature_button", "click")
    def feature_button_click(self, **event_args):
        on = not self.item["featured"]
        if state.call("set_featured", self.item["no"], on) is not None:
            state.toast("Featured on the front page ⭐" if on else "No longer featured", "ok")
            self._reload()

    @handle("down_button", "click")
    def down_button_click(self, **event_args):
        note = alert(TakeDown(), buttons=[], role="app-dialog", dismissible=True)
        if note and state.call("unpublish", self.item["no"], note) is not None:
            state.toast("Taken down. The writer can see your note.", "ok")
            self._reload()
