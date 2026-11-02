# page_auth — sign in, create an account, or reset a password (#join, or #join/<page to return to>).
import anvil.users

from . import as_ui as ui
from . import legal
from .as_ui import esc

MODES = {
    "login": ("Welcome back, scientist!", "Sign in to write, boop and manage your articles.", "🔓 Sign in"),
    "signup": ("Join the lab", "Create a free account to write science news for everyone.", "🥼 Create my account"),
    "reset": ("Forgot your password?", "We'll email you a link to set a new one.", "📮 Send reset link"),
}
GOOGLE_G = '<svg viewBox="0 0 48 48" width="18" height="18" aria-hidden="true" style="flex:none"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>'


def _google_step_done():
    """After login_with_google() gave None: did the person finish the Google window (they just have no account yet)?"""
    try:
        import anvil.google.auth
        return bool(anvil.google.auth.get_user_email())
    except Exception:
        return True  # can't tell: go on to sign-up, which asks Google again if needed


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
        google = ""
        if self.mode != "reset":
            google = ('<p class="as-sub" style="text-align:center;margin:12px 0">or</p>'
                      '<button type="button" class="as-btn as-btn-block" data-action="google">%sContinue with Google</button>' % GOOGLE_G)
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
    {legal.consent_field() if self.mode == 'signup' else ''}
    <button type="submit" class="as-btn as-btn-primary as-btn-block">{cta}</button>
    {google}
    <div class="as-auth-switch">{switch}</div>
  </form>
</div>"""

    def mounted(self):
        el = self.q('[name="email"]')
        if el is not None:
            el.focus()

    def on_action(self, action, arg, el, ev):
        if action == "google":
            self._google()
            return
        if action == "mode":
            self.email = self.val("email")
            self.mode = arg
            self.message = ""
            self.render()

    def _google(self):
        """Continue with Google: sign in, or create the account on the first visit (sign-up asks for the tick here too)."""
        if self.mode == "signup" and not legal.consent_ok(self.q("form")):
            return
        try:
            if anvil.users.login_with_google(remember=True) is None:
                if not _google_step_done() or anvil.users.signup_with_google(remember=True) is None:
                    ui.toast("Google sign-in was cancelled.", "bad")
                    return
        except anvil.users.AccountIsNotEnabled:
            ui.toast("This account is disabled.", "bad")
            return
        except anvil.users.AuthenticationFailed as e:
            ui.toast(str(e) or "Google sign-in didn't work. Please try again.", "bad")
            return
        self._welcome()

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
                if not legal.consent_ok(form):
                    return
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
        self._welcome()

    def _welcome(self):
        self.app.refresh_me()
        me = self.app.me or {}
        ui.toast("Welcome to the lab, %s %s!" % (me.get("name", "scientist"), me.get("avatar", "")))
        self.app.go(self.arg or "")
