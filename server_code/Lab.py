# Lab — shared server helpers: the @api decorator, permissions, profiles and article dicts.
# Every callable returns plain dicts (never rows), so emails and drafts never leak to the browser.
import functools
import random
import string
from datetime import datetime, timezone

import anvil.server
import anvil.users
import anvil.tables as tables
from anvil.tables import app_tables

from . import lab_config as C
from . import Render


class Oops(Exception):
    """A friendly error. The client shows the message to the user as a toast."""


def api(fn=None, *, user=False, admin=False):
    """Register a server callable. Oops errors come back as {"__oops__": message}."""
    def deco(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                if user or admin:
                    me = anvil.users.get_user()
                    if me is None:
                        raise Oops("Please sign in first. Lab coats required beyond this point 🥼")
                    if admin and not me["is_admin"]:
                        raise Oops("Only Lab Directors can do that.")
                return f(*args, **kwargs)
            except Oops as e:
                return {"__oops__": str(e)}
        anvil.server.callable(wrapper)
        return wrapper
    return deco(fn) if fn is not None else deco


def now():
    return datetime.now(timezone.utc)


def me():
    return anvil.users.get_user()


def is_admin(user):
    return bool(user is not None and user["is_admin"])


def same_user(a, b):
    return a is not None and b is not None and a.get_id() == b.get_id()


def clean(s, limit=None):
    s = (s or "").strip() if isinstance(s, str) else ""
    return s[:limit] if limit else s


def _rand_uid(n=8):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def ensure_profile(user):
    """Give a new account a lab ID, a cute default name and a critter avatar."""
    changes = {}
    if not user["uid"]:
        uid = _rand_uid()
        while app_tables.users.get(uid=uid) is not None:
            uid = _rand_uid()
        changes["uid"] = uid
    if not user["display_name"]:
        changes["display_name"] = "%s %s" % (random.choice(C.FUN_ADJECTIVES), random.choice(C.FUN_ANIMALS))
    if not user["avatar"]:
        changes["avatar"] = random.choice(C.AVATARS)
    if user["is_admin"] is None:
        changes["is_admin"] = False
    if changes:
        user.update(**changes)
    return user


# ---------- dates ----------

def fmt_date(d):
    if not d:
        return ""
    return "%s %d, %d" % (d.strftime("%b"), d.day, d.year)


def ago(d):
    if not d:
        return ""
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    s = (now() - d).total_seconds()
    if s < 90:
        return "just now"
    if s < 3600:
        return "%d min ago" % (s // 60)
    if s < 86400:
        h = int(s // 3600)
        return "%d hour%s ago" % (h, "" if h == 1 else "s")
    days = int(s // 86400)
    if days < 30:
        return "%d day%s ago" % (days, "" if days == 1 else "s")
    return fmt_date(d)


# ---------- people ----------

def brief(user):
    """The public face of a writer (never includes their email)."""
    if user is None:
        return {"uid": "", "name": "A mystery scientist", "avatar": "🥼", "specialty": ""}
    return {
        "uid": user["uid"] or "",
        "name": user["display_name"] or "A mystery scientist",
        "avatar": user["avatar"] or "🥼",
        "specialty": user["specialty"] or "",
        "is_admin": bool(user["is_admin"]),
    }


def profile(user):
    p = brief(user)
    p.update({
        "bio": user["bio"] or "",
        "website": user["website"] or "",
        "since": user["signed_up"].strftime("%B %Y") if user["signed_up"] else "",
    })
    return p


# ---------- articles ----------

def get_article_row(no):
    try:
        no = int(no)
    except (TypeError, ValueError):
        raise Oops("That specimen number looks wrong.")
    row = app_tables.articles.get(specimen_no=no)
    if row is None:
        raise Oops("Specimen #%s escaped the lab (we can't find it)." % no)
    return row


def next_specimen_no():
    top = app_tables.articles.search(tables.order_by("specimen_no", ascending=False))
    for r in top:
        return int(r["specimen_no"] or 0) + 1
    return 1


def sources_of(article):
    rows = sorted(app_tables.sources.search(article=article), key=lambda r: r["position"] or 0)
    out = []
    for i, r in enumerate(rows):
        kind = C.SOURCE_KIND.get(r["kind"] or "other", C.SOURCE_KIND["other"])
        out.append({
            "n": i + 1,
            "title": r["title"] or C.domain_of(r["url"]),
            "url": r["url"] or "",
            "publisher": r["publisher"] or "",
            "kind": kind["key"],
            "kind_label": kind["label"],
            "kind_emoji": kind["emoji"],
            "domain": C.domain_of(r["url"]),
        })
    return out


def card(a):
    """The summary of an article used on cards and lists."""
    cat = C.CATEGORY.get(a["category"] or "", {"key": "", "label": "Miscellany", "emoji": "✨", "tone": "lav"})
    ev = C.EVIDENCE_LEVEL.get(a["evidence"] or "", None)
    status = a["status"] or "draft"
    when = a["published_at"] if status == "published" else (a["updated"] or a["created"])
    return {
        "no": int(a["specimen_no"] or 0),
        "title": a["title"] or "Untitled specimen",
        "dek": a["dek"] or "",
        "category": cat,
        "evidence": ev,
        "cover": a["cover"] or cat["emoji"],
        "author": brief(a["author"]),
        "status": status,
        "status_label": C.STATUSES.get(status, ("", "", ""))[0],
        "status_emoji": C.STATUSES.get(status, ("", "", ""))[1],
        "date": fmt_date(when),
        "ago": ago(when),
        "submitted_ago": ago(a["submitted_at"]),
        "sources": int(a["n_sources"] or 0),
        "cited": int(a["n_cited"] or 0),
        "boops": int(a["boops"] or 0),
        "minutes": int(a["reading_min"] or 1),
        "featured": bool(a["featured"]),
        "review_note": a["review_note"] or "",
    }


def history_of(article):
    rows = sorted(app_tables.lab_log.search(article=article), key=lambda r: r["at"] or now(), reverse=True)
    return [{
        "action": r["action"],
        "note": r["note"] or "",
        "who": brief(r["actor"])["name"],
        "ago": ago(r["at"]),
        "date": fmt_date(r["at"]),
    } for r in rows[:20]]


def log(article, action, note=""):
    app_tables.lab_log.add_row(article=article, actor=me(), action=action, note=note or "", at=now())


def full_article(a, viewer):
    """Everything needed to read an article. Private bits only for its author and admins."""
    d = card(a)
    sources = sources_of(a)
    d["sources_list"] = sources
    d["body_html"] = Render.markdown(a["body"] or "", sources)
    owner = same_user(viewer, a["author"])
    d["is_author"] = owner
    d["can_edit"] = owner
    d["viewer_is_admin"] = is_admin(viewer)
    d["booped"] = bool(viewer is not None and app_tables.boops.get(article=a, user=viewer) is not None)
    if owner or is_admin(viewer):
        d["history"] = history_of(a)
    else:
        d["review_note"] = ""
        d["history"] = []
    return d
