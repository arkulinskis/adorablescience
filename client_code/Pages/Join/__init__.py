import re

from anvil import *
from anvil.js import window

from ._anvil_designer import JoinTemplate
from ... import auth, bits, legal, router, state

MODES = {
    "login": ("Welcome back, scientist!", "Sign in to write, boop and manage your articles.", "🔓 Sign in"),
    "signup": ("Join the lab", "Create a free account to write science news for everyone.", "🥼 Create my account"),
    "reset": ("Forgot your password?", "We'll email you a link to set a new one.", "📮 Send reset link"),
}
EMAIL = re.compile(r"^\S+@\S+\.\S+$")


class Join(JoinTemplate):
    """Sign in, create an account or reset the password (#join, or #join/<address to return to>, e.g. #join/write).
    Sign-up needs the Privacy & Terms tick (the legal kit draws it); Continue with Google signs in or makes the
    account. The first person ever to sign in becomes the first Lab Director (server get_me)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.back_to = "/".join(args)
        if state.me():  # already signed in
            window.location.replace("#" + self.back_to)
        self.mode = "login"
        self.dom_nodes["consent"].innerHTML = legal.consent_field()  # the kit's own tick box markup
        state.set_control_attr(self.email_box, "autocomplete", "email")
        img = state.control(self.google_button).querySelector("img")
        if img:
            img.setAttribute("alt", "")
        self._draw()

    def _draw(self, message=None, is_error=False):
        heading, sub, action = MODES[self.mode]
        d = self.dom_nodes
        bits.text(d["heading"], heading)
        bits.text(d["sub"], sub)
        self.submit_button.text = action
        bits.show(d["perks"], self.mode == "signup")
        self.password_field.visible = self.mode != "reset"
        self.consent_box.visible = self.mode == "signup"
        self.google_part.visible = self.mode != "reset"
        self.switch_login.visible = self.mode == "login"
        self.switch_signup.visible = self.mode == "signup"
        self.switch_reset.visible = self.mode == "reset"
        self.password_box.placeholder = "At least 8 characters" if self.mode == "signup" else ""
        state.set_control_attr(self.password_box, "autocomplete",
                               "new-password" if self.mode == "signup" else "current-password")
        self._say(message, is_error)

    def _say(self, message, is_error=True):
        self.message.visible = bool(message)
        self.message.text = message or ""
        self.message.role = "msg-error" if is_error else "msg-note"

    def mode_click(self, event):
        self.mode = event.currentTarget.getAttribute("data-mode")
        self._draw()
        self.email_box.focus()

    @handle("email_box", "pressed_enter")
    def email_box_pressed_enter(self, **event_args):
        self.submit_button_click()

    @handle("password_box", "pressed_enter")
    def password_box_pressed_enter(self, **event_args):
        self.submit_button_click()

    @handle("submit_button", "click")
    def submit_button_click(self, **event_args):
        mode = self.mode
        email, password = (self.email_box.text or "").strip(), self.password_box.text or ""
        problem = None
        if not EMAIL.match(email):
            problem = "Please enter your email."
        elif mode == "signup" and len(password) < 8:
            problem = "Please use at least 8 characters for your password."
        elif mode == "login" and not password:
            problem = "Please enter your password."
        if problem:
            self._say(problem)
            return
        if mode == "signup" and not legal.consent_ok(self.dom_nodes["consent"]):
            return  # the kit shows its own message next to the tick box
        self.submit_button.enabled = False
        try:
            if mode == "login":
                r = auth.sign_in(email, password)
            elif mode == "signup":
                r = auth.sign_up(email, password)
            else:
                r = auth.reset(email)
        finally:
            self.submit_button.enabled = True
        if not r["ok"]:
            self._say(r["error"])
        elif mode == "reset" or r.get("confirm"):
            self.mode = "login"
            self._draw("📮 " + r["message"], False)
        else:
            self._welcome()

    @handle("google_button", "click")
    def google_button_click(self, **event_args):
        if self.mode == "signup" and not legal.consent_ok(self.dom_nodes["consent"]):
            return
        r = auth.google()
        if not r["ok"]:
            self._say(r["error"])
            return
        self._welcome()

    def _welcome(self):
        me = state.me() or {}
        state.toast("Welcome to the lab, %s %s!" % (me.get("name", "scientist"), me.get("avatar", "")), "ok")
        router.go_to(self.back_to)

    @handle("", "show")
    def form_show(self, **event_args):
        self.email_box.focus()
