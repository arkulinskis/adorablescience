from anvil import *

from ._anvil_designer import MyProfileTemplate
from ... import api, router, state
from ...lab_config import AVATARS, BIO_MAX


class MyProfile(MyProfileTemplate):
    """Edit my profile (#me): lab critter, display name, specialty, bio, website."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        me = state.me()
        p = api.load("get_writer", me["uid"])
        self.uid = p["uid"]
        for key in ("back_link", "cancel_link"):
            self.dom_nodes[key].setAttribute("href", "#writer/%s" % self.uid)
        self.avatar = p["avatar"]
        self.name_box.text, self.spec_box.text = p["name"], p["specialty"]
        self.bio_box.text, self.site_box.text = p["bio"], p["website"]
        for box, n in ((self.name_box, 40), (self.spec_box, 60), (self.bio_box, BIO_MAX), (self.site_box, 200)):
            state.maxlength(box, n)
        state.set_control_attr(self.name_box, "autocomplete", "nickname")
        state.set_control_attr(self.site_box, "autocomplete", "url")
        self.avatar_panel.add_event_handler("x-pick", self._pick)
        self._draw_avatars()

    def _draw_avatars(self):
        key = state.focus_key()
        self.avatar_panel.items = [{"value": a, "on": a == self.avatar, "label": "Avatar " + a} for a in AVATARS]
        state.refocus(self.avatar_panel, key)

    def _pick(self, value, **event_args):
        self.avatar = value
        self._draw_avatars()

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        name = (self.name_box.text or "").strip()
        if len(name) < 2:
            state.toast("Your display name needs at least 2 characters.", "error")
            self.name_box.focus()
            return
        self.save_button.enabled = False
        try:
            r = state.call("update_profile", name, self.avatar, self.spec_box.text or "", self.bio_box.text or "",
                           self.site_box.text or "")
        finally:
            self.save_button.enabled = True
        if r is None:
            return
        state.toast("Profile saved. Looking sharp in that lab coat! 🥼", "ok")
        state.set_me(state.call("get_me"))
        router.go("writer", self.uid)
