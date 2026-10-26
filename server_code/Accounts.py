# Accounts — who you are, writer profiles, the writer roster, and Lab Director (admin) management.
import anvil.users
import anvil.tables as tables
from anvil.tables import app_tables

from . import lab_config as C
from .Lab import Oops, api, brief, card, clean, ensure_profile, is_admin, me, profile, same_user


@api
def get_me():
    """The signed-in user (or None). The very first person to sign in becomes the first Lab Director."""
    user = me()
    if user is None:
        return None
    ensure_profile(user)
    # (.get() would fail once there are several admins, so search and count instead)
    if not user["is_admin"] and len(app_tables.users.search(is_admin=True)) == 0:
        user["is_admin"] = True
    d = profile(user)
    d["email"] = user["email"]
    d["is_admin"] = bool(user["is_admin"])
    d["pending_reviews"] = len(app_tables.articles.search(status="pending")) if user["is_admin"] else 0
    return d


@api(user=True)
def update_profile(name, avatar, specialty, bio, website):
    user = me()
    name = clean(name, 40)
    if len(name) < 2:
        raise Oops("Your display name needs at least 2 characters.")
    website = clean(website, 200)
    if website and not C.is_url(website):
        raise Oops("Your website should be a full link starting with https://")
    user.update(
        display_name=name,
        avatar=avatar if avatar in C.AVATARS else (user["avatar"] or C.AVATARS[0]),
        specialty=clean(specialty, 60),
        bio=clean(bio, C.BIO_MAX),
        website=website,
    )
    return profile(user)


def _stats(articles):
    n_sources = sum(int(a["n_sources"] or 0) for a in articles)
    boops = sum(int(a["boops"] or 0) for a in articles)
    cats = set(a["category"] for a in articles if a["category"])
    n = len(articles)
    return {
        "published": n,
        "sources": n_sources,
        "boops": boops,
        "avg_sources": round(n_sources / n, 1) if n else 0,
        "categories": len(cats),
    }


def _badges(user, st):
    b = []
    if st["published"] >= 1:
        b.append(("🧫", "First Culture", "Published a first discovery"))
    if st["published"] >= 5:
        b.append(("🧪", "Prolific Pipette", "Published 5+ discoveries"))
    if st["published"] >= 1 and st["avg_sources"] >= 3:
        b.append(("📚", "Citation Champion", "Averages 3+ sources per article"))
    if st["boops"] >= 25:
        b.append(("🐾", "Boop Magnet", "Received 25+ boops"))
    if st["categories"] >= 3:
        b.append(("🔭", "Polymath", "Published in 3+ fields"))
    if user["is_admin"]:
        b.append(("🥼", "Lab Director", "Reviews and approves articles"))
    return [{"emoji": e, "label": l, "why": w} for e, l, w in b]


def _published_by(user):
    return list(app_tables.articles.search(tables.order_by("published_at", ascending=False),
                                           author=user, status="published"))


@api
def list_writers():
    by_author = {}
    for a in app_tables.articles.search(tables.order_by("published_at", ascending=False), status="published"):
        if a["author"] is None:
            continue
        key = a["author"].get_id()
        by_author.setdefault(key, (a["author"], []))[1].append(a)
    out = []
    for user, arts in by_author.values():
        st = _stats(arts)
        d = brief(user)
        d.update(st)
        d["bio"] = (user["bio"] or "")[:160]
        d["latest"] = arts[0]["title"]
        d["badges"] = _badges(user, st)
        out.append(d)
    out.sort(key=lambda d: (-d["published"], -d["boops"], d["name"].lower()))
    return out


@api
def get_writer(uid):
    user = app_tables.users.get(uid=clean(uid, 20)) if uid else None
    if user is None:
        raise Oops("We couldn't find that scientist. Maybe they're out on fieldwork?")
    arts = _published_by(user)
    st = _stats(arts)
    d = profile(user)
    d["stats"] = st
    d["badges"] = _badges(user, st)
    d["articles"] = [card(a) for a in arts]
    d["is_me"] = same_user(me(), user)
    return d


# ---------- Lab Directors only ----------

@api(admin=True)
def list_members():
    counts = {}
    for a in app_tables.articles.search():
        if a["author"] is not None:
            c = counts.setdefault(a["author"].get_id(), {"published": 0, "total": 0})
            c["total"] += 1
            if a["status"] == "published":
                c["published"] += 1
    out = []
    for u in app_tables.users.search(tables.order_by("signed_up", ascending=False)):
        ensure_profile(u)
        d = brief(u)
        d["email"] = u["email"]
        d["since"] = u["signed_up"].strftime("%b %d, %Y") if u["signed_up"] else ""
        d.update(counts.get(u.get_id(), {"published": 0, "total": 0}))
        d["is_me"] = same_user(me(), u)
        out.append(d)
    return out


@api(admin=True)
def set_admin(uid, flag):
    user = app_tables.users.get(uid=clean(uid, 20))
    if user is None:
        raise Oops("No such lab member.")
    if not flag and len(app_tables.users.search(is_admin=True)) <= 1 and user["is_admin"]:
        raise Oops("The lab needs at least one Lab Director. Promote someone else first.")
    user["is_admin"] = bool(flag)
    return {"uid": uid, "is_admin": bool(flag)}
