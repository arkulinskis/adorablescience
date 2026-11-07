from anvil import *
from anvil.js import window

from ._anvil_designer import ArticleTemplate
from ... import api, bits, router, state


class Article(ArticleTemplate):
    """Reading one article (#article/<no>): the article, boops, the writer, the lab notebook (writer and Directors
    only) and more by the same writer."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.a = api.load("get_article", args[0] if args else None)
        self.page_title = self.a["title"]
        self._draw()

    def _draw(self):
        a, d = self.a, self.dom_nodes
        self.view.show(a)
        bits.show(d["edit_link"], bool(a["can_edit"]))
        d["edit_link"].setAttribute("href", "#write/%d" % a["no"])
        bits.show(d["review_link"], bool(a["viewer_is_admin"]) and a["status"] == "pending")
        d["review_link"].setAttribute("href", "#review/%d" % a["no"])

        bits.show(d["boop_box"], a["status"] == "published")
        bits.show(d["boop_hint"], state.me() is None)
        self._show_boop()

        author = a["author"]
        if author.get("uid"):
            d["author_box"].setAttribute("href", "#writer/%s" % author["uid"])
        bits.avatar(d["author_av"], author, "lg")
        bits.text(d["author_name"], author["name"])
        bits.text(d["author_spec"], author.get("specialty") or "Community science writer")
        self.notebook.show(a.get("history"))

        more = a.get("more") or []
        self.more_box.visible = bool(more)
        bits.text(d["more_title"], "More from %s %s" % (author["avatar"], author["name"]))
        self.more_panel.items = more

    def _show_boop(self):
        d = self.dom_nodes
        d["boop"].classList.toggle("as-boop-on", bool(self.a["booped"]))
        d["boop"].setAttribute("aria-pressed", "true" if self.a["booped"] else "false")
        bits.text(d["boop_count"], self.a["boops"])

    def boop_click(self, event):
        button = self.dom_nodes["boop"]
        if state.me() is None:
            state.toast("Sign in to boop articles 🐾")
            router.go("join", "article", self.a["no"])
            return
        r = state.call("toggle_boop", self.a["no"])
        if r is None:
            return
        self.a["booped"], self.a["boops"] = r["booped"], r["boops"]
        self._show_boop()
        if r["booped"]:
            button.classList.remove("as-boop-pop")
            button.offsetWidth  # restart the animation
            button.classList.add("as-boop-pop")

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        try:
            window.navigator.clipboard.writeText(window.location.href)
            state.toast("Link copied! Share the science 🔗", "ok")
        except Exception:
            state.toast("Couldn't copy. You can copy the address from your browser bar.")
