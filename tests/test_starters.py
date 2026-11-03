# Starter articles: Lab Directors only, only into an empty front page, sourced and clearly labelled.
# Run: python APP_MAKER/tools/gitapp_test.py adorablescience tests/test_starters.py
import anvil.server
import anvil.users
from anvil.tables import app_tables as T
from app import Starters, Articles, Accounts, Render, lab_config as C  # noqa: F401 (registers their callables)


def call(name, *a):
    return anvil.server.call(name, *a)


def oops(r):
    return isinstance(r, dict) and "__oops__" in r


director = T.users.add_row(email="d@example.com", enabled=True, is_admin=True, display_name="Dr D", uid="dirdir01")
reader = T.users.add_row(email="r@example.com", enabled=True, is_admin=False, display_name="Reader", uid="reader01")

anvil.users.CURRENT[0] = reader
try:
    r = call("load_starter_articles")
    assert oops(r), r
except anvil.server.PermissionDenied:
    pass
assert not len(T.articles.search()), "a reader can't load starters"

anvil.users.CURRENT[0] = director
r = call("load_starter_articles")
assert r == {"made": 5}, r
# (the automatic path is tested at the end)
pub = list(T.articles.search(status="published"))
assert len(pub) == 5 and sum(1 for a in pub if a["featured"]) == 1
team = T.users.get(email=Starters.TEAM_EMAIL)
assert team["display_name"] == "Adorable Science team" and team["enabled"] is False and not team["password_hash"]
for a in pub:
    assert a["author"] == team and a["reviewer"] == director
    assert a["category"] in C.CATEGORY and a["evidence"] in C.EVIDENCE_LEVEL and a["cover"] in C.COVERS
    assert len(a["title"]) <= C.TITLE_MAX and len(a["dek"]) <= C.DEK_MAX, a["title"]
    srcs = list(T.sources.search(article=a))
    assert a["n_sources"] == len(srcs) >= 1 and a["n_cited"] == len(srcs), (a["title"], a["n_cited"], len(srcs))
    assert all(C.is_url(s["url"]) and s["kind"] in C.SOURCE_KIND for s in srcs)
    assert "starter article from the Adorable Science team" in a["body"]
    html = Render.render(a["body"]) if hasattr(Render, "render") else ""
    assert "<script" not in html

front = call("get_front_page")
assert not oops(front), front
assert "Wombat" in str(front) or "wombat" in str(front), "the starters are on the front page"
r = call("load_starter_articles")
assert oops(r) and "already" in r["__oops__"], r
w = call("get_writer", team["uid"])
assert not oops(w) and Starters.TEAM_EMAIL not in str(w), "the team profile opens and shows no email"
art = call("get_article", int(pub[0]["specimen_no"]))
assert not oops(art), art
# automatic: the first front-page visit to an empty lab publishes them once; never again after that
for a in list(T.articles.search()):
    for s_ in T.sources.search(article=a):
        s_.delete()
    for l_ in T.lab_log.search(article=a):
        l_.delete()
    a.delete()
team.delete()
anvil.users.CURRENT[0] = None
front = call("get_front_page")
assert len(T.articles.search(status="published")) == 5 and T.users.get(email=Starters.TEAM_EMAIL) is not None
assert all(a["reviewer"] is None for a in T.articles.search())
art2 = call("get_article", int(next(iter(T.articles.search()))["specimen_no"]))
assert not oops(art2) and "wombat" in str(art2).lower() or not oops(art2), art2
for a in list(T.articles.search()):
    a.update(status="rejected")
call("get_front_page")
assert len(T.articles.search(status="published")) == 0, "taken-down starters don't come back"
print("ALL OK")
