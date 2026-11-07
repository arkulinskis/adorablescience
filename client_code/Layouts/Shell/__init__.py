import random

from anvil import *

from ._anvil_designer import ShellTemplate
from ... import auth, bits, router, state
from ...lab_config import LAB_FACTS

THEMES = ("auto", "light", "dark")


class Shell(ShellTemplate):
    """The frame around every page: header (Bea, the tabs, the signed-in writer or Join the lab), the footer (a lab
    fact, Submit feedback, Privacy & Terms, Contact developer, Parent company, light/dark). Pages use it with
    <anvil-form layout="Adorable_Science.Layouts.Shell">.

    Anvil keeps ONE Shell while pages come and go (open_form only swaps the "content" slot when the layout matches),
    so everything that depends on who is signed in or which page is open is drawn in refresh(nav), which
    router.show() calls after every page change. Never only in __init__."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self._fact()
        self.refresh("")

    def refresh(self, nav):
        me = state.me()
        self.member_actions.visible = bool(me)
        self.join_link.visible = not me
        tabs = [("home", "#", "📰 Front page", 0), ("writers", "#writers", "🧑‍🔬 Writers", 0)]
        if me:
            tabs += [("write", "#write", "✍️ Write", 0), ("lab", "#lab", "🧫 My lab", 0)]
            if me.get("is_admin"):
                tabs.append(("review", "#review", "🔬 Review desk", me.get("pending_reviews") or 0))
            d = self.dom_nodes
            d["me_link"].setAttribute("href", "#writer/%s" % me["uid"])
            bits.avatar(d["me_avatar"], me, "sm")
            bits.text(d["me_name"], me["name"])
        self.nav_panel.items = [{"key": k, "href": h, "label": l, "badge": b, "on": k == nav} for k, h, l, b in tabs]
        self._show_theme()

    def _fact(self):
        bits.text(self.dom_nodes["fact"], random.choice(LAB_FACTS))

    def fact_click(self, event):
        self._fact()

    def skip_click(self, event):
        event.preventDefault()  # (a #main-content address would open the front page)
        self.dom_nodes["main"].focus()

    def theme_click(self, event):
        state.set_theme(event.currentTarget.getAttribute("data-theme-set"))
        self._show_theme()

    def _show_theme(self):
        t = state.theme()
        for name in THEMES:
            self.dom_nodes["theme_" + name].classList.toggle("on", name == t)

    @handle("signout_button", "click")
    def signout_button_click(self, **event_args):
        auth.sign_out()
        state.toast("Signed out. Come back soon! 👋")
        router.go("")
