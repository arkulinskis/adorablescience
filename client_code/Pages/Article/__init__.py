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
        self.copy_button.text = "🔗 Copy link" if self._published() else "🔗 Copy preview link"
        self.share_button.visible = self._published() and bool(window.matchMedia("(pointer: coarse)").matches) \
            and bool(window.Reflect.has(window.navigator, "share"))

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

    def _published(self):
        return self.a["status"] == "published"

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        """Published: the story's real address (/a/N/slug, with its own link preview). Otherwise the private
        #article/N address, which only the writer and Lab Directors can open."""
        url = bits.public_link(self.a) if self._published() else window.location.href
        try:
            window.navigator.clipboard.writeText(url)
            state.toast("Link copied! Share the science 🔗" if self._published()
                        else "Preview link copied. Only you and Lab Directors can open it until it's published. 🔬", "ok")
        except Exception:
            state.toast("Couldn't copy. Here's the link: %s" % url)

    @handle("share_button", "click")
    def share_button_click(self, **event_args):
        done = bits.share(self.a["title"], self.a["dek"], bits.public_link(self.a))
        if done is False:
            state.toast("Link copied! Share the science 🔗", "ok")
        elif done is None:
            state.toast("Couldn't share. Use Copy link instead.")
