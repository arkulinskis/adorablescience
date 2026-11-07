"""Page addresses: #name/arg1/arg2 -> a page Form (open_form), with sign-in rules. The addresses are the same as in the
old JavaScript-string version, so every link people have shared keeps working:

    #                 front page               #topic/<field>     front page filtered by field
    #article/<no>     read an article          #writers           the writer roster
    #writer/<uid>     a writer's profile       #me                edit my profile
    #write            new article              #write/<no>        edit my article
    #lab              my articles              #join[/<return>]   sign in / create account, then back to <return>
    #review           Lab Director desk        #review/<no>       review one article

    PAGES[name] = (who may open it, browser-tab title, header tab to light up)   who: None = anyone, "user", "admin"
Links in templates are plain <a href="#writers">; code calls router.go("article", 12).
New page: add it to PAGES and _form(); the header tabs are in Layouts/Shell (nav_items).
"""
import anvil
import anvil.js
from anvil.js import window

from . import api, state
from .lab_config import APP_NAME

PAGES = {
    "": (None, APP_NAME, "home"),
    "topic": (None, APP_NAME, "home"),
    "article": (None, "Article", "home"),
    "writers": (None, "Writers", "writers"),
    "writer": (None, "Writer", "writers"),
    "me": ("user", "My profile", ""),
    "write": ("user", "Write a discovery", "write"),
    "lab": ("user", "My lab", "lab"),
    "join": (None, "Join the lab", ""),
    "review": ("admin", "Review desk", "review"),
}
_r: dict = {"listening": False, "page": ""}


def _form(name):
    """The page's Form class (imported when first needed, so start-up stays quick)."""
    if name in ("", "topic"):
        from .Pages.Front import Front
        return Front
    if name == "article":
        from .Pages.Article import Article
        return Article
    if name == "writers":
        from .Pages.Writers import Writers
        return Writers
    if name == "writer":
        from .Pages.Writer import Writer
        return Writer
    if name == "me":
        from .Pages.MyProfile import MyProfile
        return MyProfile
    if name == "write":
        from .Pages.Editor import Editor
        return Editor
    if name == "lab":
        from .Pages.Lab import Lab
        return Lab
    if name == "join":
        from .Pages.Join import Join
        return Join
    from .Pages.Review import Review
    return Review


def parse(hash_text):
    h = (hash_text or "").lstrip("#").lstrip("!").lstrip("/").split("?")[0]
    parts = [window.decodeURIComponent(p) for p in h.split("/") if p]
    return (parts[0] if parts else ""), parts[1:]


def href(name, *args):
    """'#name/arg1/arg2' with every part URL-encoded."""
    if not name:
        return "#"
    return "#" + "/".join([name] + [window.encodeURIComponent(str(a)) for a in args if a not in (None, "")])


def current():
    """The open page's name ('' = the front page)."""
    return _r["page"]


def _problem(title, message, mood="sad", cta=None):
    from .Pages.Problem import Problem
    return Problem(title=title, message=message, mood=mood, cta=cta)


def show():
    """Open the page for the current address."""
    name, args = parse(window.location.hash)
    if name not in PAGES:
        name, args = "", []
    who, title, nav = PAGES[name]
    if who in ("user", "admin") and not state.me():
        # members only: sign in first, then come back here (#join/<this address>)
        window.location.replace("#join/" + (window.location.hash or "").lstrip("#"))
        return
    window.UI_READY = False
    _r["page"] = name
    try:
        if who == "admin" and not state.is_admin():
            page = _problem("Lab Directors only 🥼", "The review desk is for Lab Directors. Your articles are reviewed there.",
                            cta=("Go to my lab", "#lab"))
        else:
            page = _form(name)(args=args)
    except api.LabError as e:
        page = _problem("Oops, something fizzled 💥", str(e))
    page_title = getattr(page, "page_title", None) or title
    window.document.title = APP_NAME if page_title == APP_NAME else "%s · %s" % (page_title, APP_NAME)
    anvil.open_form(page)
    shell = getattr(page, "layout", None)
    if shell is not None and hasattr(shell, "refresh"):
        shell.refresh(nav)  # Anvil reuses the layout between pages: tell it who is signed in and which tab is open
    window.scrollTo(0, 0)
    window.UI_READY = True  # tests and screenshots wait for this


def go(name, *args):
    """Go to a page. Same address again = reload the page."""
    target = href(name, *args)
    if (window.location.hash or "#") == target:
        show()
    else:
        window.location.hash = target


def go_to(address):
    """Go to an address given as text ('article/12', '' = the front page)."""
    name, args = parse(address or "")
    go(name, *args)


def replace(name, *args):
    """Change the address without opening anything (after saving a new draft, the editor becomes #write/<no>)."""
    window.history.replaceState(None, "", href(name, *args))


def refresh_shell():
    """Redraw the header (after signing in or out, or when the number waiting for review changes)."""
    form = anvil.get_open_form()
    shell = getattr(form, "layout", None)
    if shell is not None and hasattr(shell, "refresh"):
        shell.refresh(PAGES.get(_r["page"], (None, "", ""))[2])


def _on_hash(event):
    show()


def start():
    if not _r["listening"]:
        window.addEventListener("hashchange", anvil.js.report_exceptions(_on_hash))
        _r["listening"] = True
    show()
