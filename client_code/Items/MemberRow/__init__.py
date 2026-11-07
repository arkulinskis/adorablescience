from anvil import *

from ._anvil_designer import MemberRowTemplate
from ... import bits, router, state


class MemberRow(MemberRowTemplate):
    """A lab member on the review desk (Directors only: emails show here). item = list_members() entry.
    Make / remove Lab Director; removing your own role takes you to the front page."""

    def __init__(self, **properties):
        super().__init__(**properties)
        m, d = self.item, self.dom_nodes
        bits.avatar(d["av"], m, "lg")
        bits.text(d["name"], m["name"])
        if m.get("uid"):
            d["name"].setAttribute("href", "#writer/%s" % m["uid"])
        bits.show(d["you"], bool(m["is_me"]))
        bits.text(d["meta"], "%s · joined %s · %d published / %d written"
                  % (m["email"], m["since"], m["published"], m["total"]))
        d["role"].className = "as-chip tone-%s" % ("lav" if m["is_admin"] else "mint")
        bits.text(d["role"], "🥼 Lab Director" if m["is_admin"] else "✍️ Writer")
        self.role_button.text = "Remove Director" if m["is_admin"] else "Make Lab Director"
        self.role_button.role = ["btn", "btn-ghost" if m["is_admin"] else "btn-soft", "btn-sm"]

    @handle("role_button", "click")
    def role_button_click(self, **event_args):
        m = self.item
        on = not m["is_admin"]
        if state.call("set_admin", m["uid"], on) is None:
            return
        state.toast("Promoted to Lab Director 🥼" if on else "Director role removed", "ok")
        if not on and m["is_me"]:
            state.set_me(state.call("get_me"))
            router.go("")
            return
        if self.parent is not None:
            self.parent.raise_event("x-reload")
