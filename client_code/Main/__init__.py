# Main — the startup Form. It owns the header, footer, dialogs and routing.
#
# Pages live in the page_* modules. Each one builds HTML (see as_ui.Page), and Main sends clicks on
# anything with data-action="..." back to the current page's on_action(). Navigation is plain links
# to URL hashes, so every page can be bookmarked and shared:
#   #               front page             #topic/<field>     front page filtered by field
#   #article/<no>   read an article        #writers           the writer roster
#   #writer/<uid>   a writer's profile     #me                edit my profile
#   #write          new article            #write/<no>        edit my article
#   #lab            my articles            #join              sign in / create account
#   #review         Lab Director desk      #review/<no>       review one article
import random

from ._anvil_designer import MainTemplate
from anvil import *
import anvil.js
import anvil.users
from anvil.js import window

from .. import api
from .. import legal
from .. import as_ui as ui
from .. import lab_config as C
from ..page_home import HomePage
from ..page_article import ArticlePage
from ..page_editor import EditorPage
from ..page_lab import LabPage
from ..page_writers import WritersPage, WriterPage, ProfileEditPage
from ..page_auth import AuthPage
from ..page_review import ReviewPage

ROUTES = {
    "": HomePage,
    "topic": HomePage,
    "article": ArticlePage,
    "writers": WritersPage,
    "writer": WriterPage,
    "me": ProfileEditPage,
    "write": EditorPage,
    "lab": LabPage,
    "join": AuthPage,
    "review": ReviewPage,
}


class Main(MainTemplate):
    def __init__(self, **properties):
        super().__init__(**properties)
        self.me = None
        self.page = None
        self.root = None
        self._seq = 0
        self.add_event_handler("show", self._on_show)

    # ---------- start-up ----------

    def _on_show(self, **event_args):
        if self.root is not None:
            return
        node = anvil.js.get_dom_node(self)
        self.root = node.querySelector('[data-as="app"]') or node
        self.header = self.root.querySelector('[data-as="header"]')
        self.view = self.root.querySelector('[data-as="view"]')
        self.footer = self.root.querySelector('[data-as="footer"]')
        self.root.addEventListener("click", self._on_click)
        self.root.addEventListener("input", self._on_input)
        self.root.addEventListener("change", self._on_input)
        self.root.addEventListener("submit", self._on_submit)
        window.addEventListener("hashchange", self._on_hash)
        window.addEventListener("keydown", self._on_key)
        self.paint_footer()
        self.refresh_me()
        self.route()

    def refresh_me(self):
        try:
            self.me = api.load("get_me")
        except Exception as e:
            print("get_me failed:", e)
            self.me = None
        self.paint_header()
        legal.refresh_soon()  # Privacy & Terms: records the sign-up tick, or reminds people to review

    # ---------- routing ----------

    def current_hash(self):
        h = window.location.hash or ""
        if h.startswith("#"):
            h = h[1:]
        try:
            h = window.decodeURIComponent(h)
        except Exception:
            pass
        return h.strip("/")

    def go(self, h):
        """Navigate to a hash route like 'article/12'."""
        h = (h or "").strip("/")
        if self.current_hash() == h:
            self.route()
        else:
            window.location.hash = "#" + h  # fires hashchange -> route()

    def replace_hash(self, h):
        """Change the address bar without reloading the page (e.g. after saving a new draft)."""
        window.history.replaceState(None, "", "#" + h)

    def _on_hash(self, *args):
        self.route()

    def route(self):
        h = self.current_hash()
        name, _, arg = h.partition("/")
        cls = ROUTES.get(name)
        if cls is None:
            name, arg, cls = "", "", HomePage
        page = cls(self, arg or None)
        if page.needs and self.me is None:
            self.go("join/" + h)
            return
        if page.needs == "admin" and not self.me.get("is_admin"):
            self.page = page
            self.paint_header()
            self.view.innerHTML = ui.empty("Lab Directors only 🥼",
                                           "The review desk is for Lab Directors. Your articles are reviewed there.",
                                           ui.btn("Go to my lab", href="#lab", kind="primary"), mood="sad")
            return
        self.show(page)

    def show(self, page):
        self._seq += 1
        seq = self._seq
        ui.close_modal()
        self.page = page
        self.paint_header()
        self.view.innerHTML = ui.loading(getattr(page, "loading_text", "Calibrating the microscopes…"))
        window.scrollTo(0, 0)
        try:
            page.load()
        except api.LabError as e:
            if seq == self._seq:
                self.view.innerHTML = ui.error_block(str(e))
            return
        except Exception as e:
            print("load failed:", repr(e))
            if seq == self._seq:
                self.view.innerHTML = ui.error_block("The lab equipment hiccuped. Please try again in a moment.")
            return
        if seq == self._seq:  # skip if the reader already clicked somewhere else
            self.paint(page)

    def paint(self, page):
        self.view.innerHTML = page.html()
        window.document.title = "%s · %s" % (page.title, C.APP_NAME) if page.title != C.APP_NAME else C.APP_NAME
        page.mounted()

    # ---------- header & footer ----------

    def paint_header(self):
        me = self.me
        active = self.page.nav if self.page else ""

        def tab(key, href, label, badge=0):
            b = '<span class="as-badge">%d</span>' % badge if badge else ""
            cls = "as-tab as-tab-on" if key == active else "as-tab"
            return '<a class="%s" href="%s">%s%s</a>' % (cls, href, label, b)

        tabs = [tab("home", "#", "📰 Front page"), tab("writers", "#writers", "🧑‍🔬 Writers")]
        if me:
            tabs += [tab("write", "#write", "✍️ Write"), tab("lab", "#lab", "🧫 My lab")]
            if me.get("is_admin"):
                tabs.append(tab("review", "#review", "🔬 Review desk", me.get("pending_reviews") or 0))
            right = ('<a class="as-me" href="#writer/%s" title="My profile">%s<span>%s</span></a>%s'
                     % (ui.esc(me["uid"]), ui.avatar(me, "sm"), ui.esc(me["name"]),
                        ui.btn("Sign out", "signout", kind="ghost sm")))
        else:
            right = ui.btn("Join the lab 🥼", href="#join", kind="primary sm")
        brand = ui.mascot("as-brand-mark")
        tabs = "".join(tabs)
        tagline = ui.esc(C.TAGLINE)
        self.header.innerHTML = f"""<div class="as-topbar">
  <a class="as-brand" href="#" aria-label="Adorable Science home">{brand}
    <span class="as-brand-text"><span class="as-brand-name">Adorable<b>Science</b></span>
    <span class="as-brand-tag">{tagline}</span></span></a>
  <div class="as-user">{right}</div>
</div>
<nav class="as-nav" aria-label="Main">{tabs}</nav>"""

    def paint_footer(self):
        fact = ui.esc(random.choice(C.LAB_FACTS))
        self.footer.innerHTML = f"""<div class="as-footer-in">
  <div class="as-fact"><span class="as-fact-tag">🔬 Lab fact</span><span>{fact}</span>
    <button type="button" class="as-linkbtn" data-action="new-fact">another!</button></div>
  <p>🥽 <b>Adorable Science</b> · Every article is reviewed by a Lab Director before it's published.
  Every claim should wear its citations.</p>
  <p><a class="as-linkbtn" href="https://prepsto.com/#f/7uhztrz" target="_blank" rel="noopener" data-prepsto-open>💡 Suggest an idea</a> · <button type="button" class="as-linkbtn" data-lk-open="overview">Privacy &amp; Terms</button></p>
</div>"""

    # ---------- events ----------

    def run(self, fn, el=None):
        busy = el is not None and el.tagName == "BUTTON"
        if busy:
            el.disabled = True
        try:
            fn()
        except api.LabError as e:
            ui.toast(str(e), "bad")
        except anvil.users.AuthenticationFailed as e:
            ui.toast(str(e) or "Sign-in failed.", "bad")
        except Exception as e:
            print("action failed:", repr(e))
            ui.toast("Something fizzled in the lab. Please try again.", "bad")
        finally:
            if busy:
                el.disabled = False

    def _on_click(self, ev):
        try:
            el = ev.target.closest("[data-action]")
        except Exception:
            el = None  # e.g. the click landed on something that isn't an element
        if el is None:
            return
        if el.tagName == "A":
            ev.preventDefault()
        action = el.getAttribute("data-action")
        arg = el.getAttribute("data-arg")
        self.run(lambda: self._dispatch(action, arg, el, ev), el)

    def _dispatch(self, action, arg, el, ev):
        if action == "modal-close":
            ui.close_modal()
        elif action == "signout":
            anvil.users.logout()
            self.me = None
            legal.signed_out()
            ui.toast("Signed out. Come back soon! 👋")
            self.paint_header()
            self.go("")
        elif action == "new-fact":
            self.paint_footer()
        elif self.page is not None:
            self.page.on_action(action, arg, el, ev)

    def _on_input(self, ev):
        if self.page is not None and ev.target is not None:
            try:
                self.page.on_input(ev.target, ev)
            except Exception as e:
                print("input handler failed:", repr(e))

    def _on_submit(self, ev):
        ev.preventDefault()
        form = ev.target
        name = form.getAttribute("data-form") if form is not None else None
        button = form.querySelector('button[type="submit"]') if form is not None else None
        if self.page is not None:
            self.run(lambda: self.page.on_submit(name, form, ev), button)

    def _on_key(self, ev):
        if ev.key == "Escape":
            ui.close_modal()
