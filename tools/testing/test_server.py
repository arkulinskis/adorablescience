"""Server tests against the strict mock of Anvil (tools/testing/mock).

    python tools/testing/test_server.py          -> prints ALL OK, or the first failure

call(name, ...) runs a server function the way the browser does: by name, and the reply must be JSON (a datetime or
a row in a reply fails here, like it would break the page). The app's friendly problems come back as
{"__oops__": message} (server_code/Lab.py @api). Then tests/test_starters.py runs on an emptied database.
Add tests for every new server function: the happy path, bad input, and someone who isn't allowed.
"""
import datetime as dt
import importlib
import json
import os
import pathlib
import runpy
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
_tmp = pathlib.Path(tempfile.mkdtemp())
shutil.copytree(PROJECT / "server_code", _tmp / "app", ignore=shutil.ignore_patterns("__pycache__"))
shutil.copy(PROJECT / "client_code" / "lab_config.py", _tmp / "app" / "lab_config.py")  # shared with the server
(_tmp / "app" / "__init__.py").write_text("")
os.environ["ANVIL_APP_YAML"] = str(PROJECT / "anvil.yaml")  # the mock's tables follow the app's own schema
sys.path[:0] = [str(HERE / "mock"), str(_tmp)]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import anvil.server  # noqa: E402
import anvil.users  # noqa: E402
from anvil.tables import app_tables as T  # noqa: E402

M = {p.stem: importlib.import_module("app." + p.stem) for p in sorted((PROJECT / "server_code").glob("*.py"))}
now = dt.datetime.now(dt.timezone.utc)


def call(name, *args, **kwargs):
    r = anvil.server.call(name, *args, **kwargs)
    json.dumps(r)  # strict: must be JSON-able
    return r


def as_user(row):
    anvil.users.CURRENT[0] = row
    anvil.server.session.use(row.get_id() if row is not None else None)


def oops(r, words=""):
    assert isinstance(r, dict) and "__oops__" in r and words.lower() in r["__oops__"].lower(), (words, r)
    return r


def fine(r):
    assert not (isinstance(r, dict) and "__oops__" in r), r
    return r


def person(email, **kw):
    return T.users.add_row(email=email, enabled=True, signed_up=now, **kw)


SOURCES = [{"url": "https://doi.org/10.1000/xyz", "title": "A study", "publisher": "Nature", "kind": "journal"},
           {"url": "https://www.nasa.gov/a", "title": "", "publisher": "NASA", "kind": "agency"}]
BODY = "Tardigrades survived the vacuum of space [1], and the agency confirmed it [2]. " * 3

# ------------------------------------------------------------------------------ accounts: first sign-in = Director
first = person("first@example.com")
writer = person("writer@example.com")
other = person("other@example.com")
as_user(None)
assert call("get_me") is None
oops(call("my_articles"), "sign in")
as_user(first)
me = fine(call("get_me"))
assert me["is_admin"] is True and me["uid"] and me["name"] and me["avatar"], "the first person becomes a Lab Director"
as_user(writer)
me = fine(call("get_me"))
assert me["is_admin"] is False and me["pending_reviews"] == 0 and "email" in me
oops(call("update_profile", "X", "🐹", "", "", ""), "2 characters")
oops(call("update_profile", "Wendy Writer", "🐹", "", "", "not a link"), "https://")
p = fine(call("update_profile", "Wendy Writer", "🐹", "Space squishies", "I write.", "https://example.com"))
assert p["name"] == "Wendy Writer" and p["avatar"] == "🐹"
oops(call("review_queue"), "lab directors")

# ------------------------------------------------------------------------------ the writing desk
fields = {"title": "Tiny tardigrades", "dek": "They survive space.", "body": BODY, "category": "space",
          "evidence": "peer", "cover": "🔭"}
oops(call("save_article", None, dict(fields, title="no"), []), "title")
oops(call("save_article", None, fields, [{"url": "nope", "title": "x"}]), "web link")
r = fine(call("save_article", None, fields, SOURCES))
no = r["no"]
assert r["status"] == "draft"
d = fine(call("get_article_for_edit", no))
assert d["title"] == "Tiny tardigrades" and len(d["sources"]) == 2 and d["sources"][1]["title"] == "nasa.gov"
as_user(other)
oops(call("get_article_for_edit", no), "only the writer")
oops(call("get_article", no), "still in the lab")
as_user(writer)
assert call("save_article", no, fields, [], submit=True) == {"needs_ack": True}, "unsourced submit asks first"
oops(call("save_article", no, dict(fields, dek=""), SOURCES, submit=True), "summary")
r = fine(call("save_article", no, fields, SOURCES, submit=True))
assert r["status"] == "pending"
html = fine(call("preview_body", "**hi** [1] <script>x</script>", SOURCES))
assert "<strong>hi</strong>" in html and "<script>" not in html
mine = fine(call("my_articles"))
assert [c["status"] for c in mine] == ["pending"]
fine(call("withdraw_article", no))
fine(call("save_article", no, fields, SOURCES, submit=True))

# ------------------------------------------------------------------------------ the review desk
as_user(first)
assert fine(call("get_me"))["pending_reviews"] == 1
q = fine(call("review_queue"))
assert [c["no"] for c in q] == [no]
rv = fine(call("get_review", no))
assert len(rv["checks"]) == 7 and rv["sources"] == 2 and rv["history"]
oops(call("decide", no, "send_back", "no"), "what to fix")
fine(call("decide", no, "send_back", "Please link the original paper."))
as_user(writer)
a = fine(call("get_article", no))
assert a["status"] == "rejected" and a["review_note"].startswith("Please") and a["can_edit"]
fine(call("save_article", no, fields, SOURCES, submit=True))
as_user(first)
fine(call("decide", no, "approve", "Lovely", True))
oops(call("decide", no, "approve"), "isn't waiting")
front = fine(call("get_front_page"))
assert front["lead"]["no"] == no and front["lead"]["featured"] and front["stats"]["articles"] >= 1
assert fine(call("get_front_page", "space", "tardigrade"))["items"][0]["no"] == no
assert fine(call("get_front_page", None, "zzzz"))["items"] == []
pub = fine(call("published_list"))
assert any(c["no"] == no for c in pub)
fine(call("set_featured", no, False))
members = fine(call("list_members"))
assert any(m["email"] == "writer@example.com" for m in members)
oops(call("set_admin", fine(call("get_me"))["uid"], False), "at least one")
fine(call("set_admin", members[0]["uid"] if members[0]["email"] != "first@example.com" else members[1]["uid"], True))

# ------------------------------------------------------------------------------ readers: boops, writers
as_user(other)
art = fine(call("get_article", no))
assert art["history"] == [] and art["review_note"] == "", "readers don't see the lab notebook"
b = fine(call("toggle_boop", no))
assert b == {"booped": True, "boops": 1}
assert fine(call("toggle_boop", no)) == {"booped": False, "boops": 0}
as_user(None)
oops(call("toggle_boop", no), "sign in")
ws = fine(call("list_writers"))
assert ws[0]["name"] == "Wendy Writer" and "email" not in ws[0]
w = fine(call("get_writer", ws[0]["uid"]))
assert w["stats"]["published"] == 1 and "writer@example.com" not in json.dumps(w)
oops(call("get_writer", "nobody"), "couldn't find")

# ------------------------------------------------------------------------------ take down, delete
as_user(first)
oops(call("unpublish", no, ""), "note")
fine(call("unpublish", no, "A claim needs a source."))
as_user(writer)
assert fine(call("get_article", no))["status"] == "rejected"
fine(call("delete_article", no))
assert not len(T.articles.search(specimen_no=no))

# ------------------------------------------------------------------------------ the starter articles (own script)
for table in ("sources", "boops", "lab_log", "articles", "users"):
    for row in list(getattr(T, table).search()):
        row.delete()
anvil.users.CURRENT[0] = None
os.chdir(_tmp)
runpy.run_path(str(PROJECT / "tests" / "test_starters.py"), run_name="__main__")
