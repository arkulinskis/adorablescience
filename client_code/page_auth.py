# page_auth — sign in, create an account, or reset a password (#join, or #join/<page to return to>).
import anvil.users

from . import as_ui as ui
from .as_ui import esc

MODES = {
    "login": ("Welcome back, scientist!", "Sign in to write, boop and manage your articles.", "🔓 Sign in"),
    "signup": ("Join the lab", "Create a free account to write science news for everyone.", "🥼 Create my account"),
    "reset": ("Forgot your password?", "We'll email you a link to set a new one.", "📮 Send reset link"),
}


class AuthPage(ui.Page):
    nav = ""
    title = "Join the lab"

    def __init__(self, app, arg=None):
        super().__init__(app, arg)
        self.mode = "login"
        self.message = ""
        self.email = ""

    def load(self):
        if self.me is not None:  # already signed in
            self.app.go(self.arg or "")

    def html(self):
        heading, sub, cta = MODES[self.mode]
        msg = '<div class="as-banner as-banner-pending">📮 <span>%s</span></div>' % esc(self.message) if self.message else ""
        password = ""
        if self.mode != "reset":
            hint = ' placeholder="At least 8 characters"' if self.mode == "signup" else ""
            password = f"""<label class="as-field"><span class="as-field-label">Password</span>
  <input type="password" name="password" required autocomplete="{'new-password' if self.mode == 'signup' else 'current-password'}"{hint}></label>"""
        switch = {
            "login": '<p>New here? <button type="button" class="as-linkbtn" data-action="mode" data-arg="signup">Create an account</button>'
                     ' · <button type="button" class="as-linkbtn" data-action="mode" data-arg="reset">Forgot password?</button></p>',
            "signup": '<p>Already have an account? <button type="button" class="as-linkbtn" data-action="mode" data-arg="login">Sign in</button></p>',
            "reset": '<p><button type="button" class="as-linkbtn" data-action="mode" data-arg="login">← Back to sign in</button></p>',
        }[self.mode]
        perks = ""
        if self.mode == "signup":
            perks = """<ul class="as-perks"><li>✍️ Write articles about discoveries you love</li>
<li>🔬 Lab Directors review every article before it's published</li><li>🪪 Get a writer profile with badges</li></ul>"""
        mascot = ui.mascot("as-mascot-md")
        return f"""<div class="as-auth">
  <div class="as-auth-art">{mascot}</div>
  <form class="as-panel as-auth-card" data-form="auth">
    <h1>{heading}</h1>
    <p class="as-sub">{sub}</p>
    {msg}
    {perks}
    <label class="as-field"><span class="as-field-label">Email</span>
      <input type="email" name="email" required autocomplete="email" value="{esc(self.email)}"></label>
    {password}
    <button type="submit" class="as-btn as-btn-primary as-btn-block">{cta}</button>
    <div class="as-auth-switch">{switch}</div>
  </form>
</div>"""

    def mounted(self):
        el = self.q('[name="email"]')
        if el is not None:
            el.focus()

    def on_action(self, action, arg, el, ev):
        if action == "mode":
            self.email = self.val("email")
            self.mode = arg
            self.message = ""
            self.render()

    def on_submit(self, name, form, ev):
        email = self.val("email").strip()
        password = self.val("password")
        self.email = email
        if not email:
            ui.toast("Please enter your email.", "bad")
            return
        try:
            if self.mode == "reset":
                try:
                    anvil.users.send_password_reset_email(email)
                except anvil.users.AuthenticationFailed:
                    pass  # same answer either way, so nobody can probe which emails have accounts
                self.mode = "login"
                self.message = "If that email has an account, a reset link is on its way."
                self.render()
                return
            if self.mode == "signup":
                if len(password) < 8:
                    ui.toast("Please use at least 8 characters for your password.", "bad")
                    return
                anvil.users.signup_with_email(email, password, remember=True)
                if anvil.users.get_user() is None:
                    self.mode = "login"
                    self.message = "Account created! Check your inbox for a confirmation link, then sign in here."
                    self.render()
                    return
            else:
                anvil.users.login_with_email(email, password, remember=True)
        except anvil.users.UserExists:
            ui.toast("An account with that email already exists. Try signing in.", "bad")
            return
        except anvil.users.EmailNotConfirmed:
            ui.toast("Please confirm your email first. Check your inbox for the link 📮", "bad")
            return
        except anvil.users.AccountIsNotEnabled:
            ui.toast("This account is disabled.", "bad")
            return
        except anvil.users.TooManyPasswordFailures:
            ui.toast("Too many wrong attempts. Wait a little, or reset your password.", "bad")
            return
        except anvil.users.PasswordNotAcceptable as e:
            ui.toast(str(e) or "Please choose a stronger password.", "bad")
            return
        except anvil.users.AuthenticationFailed:
            ui.toast("That email and password don't match.", "bad")
            return
        self.app.refresh_me()
        me = self.app.me or {}
        ui.toast("Welcome to the lab, %s %s!" % (me.get("name", "scientist"), me.get("avatar", "")))
        self.app.go(self.arg or "")
