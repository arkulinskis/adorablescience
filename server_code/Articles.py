# Articles — the front page, reading, writing, submitting for review, and boops.
#
# Life of an article:
#   draft ("In the Petri dish") --submit--> pending ("Under the microscope")
#   pending --Lab Director approves--> published (front page)
#   pending --Lab Director sends back--> rejected ("Needs more data", with a note)
#   Editing a published article takes it off the front page until it is approved again.
import anvil.tables as tables
from anvil.tables import app_tables

from . import lab_config as C
from . import Render
from .Lab import (Oops, api, card, clean, full_article, get_article_row, is_admin, log, me,
                  next_specimen_no, now, same_user, sources_of)


@api
def get_front_page(category=None, query=None):
    rows = list(app_tables.articles.search(tables.order_by("published_at", ascending=False), status="published"))
    counts = {}
    for r in rows:
        counts[r["category"]] = counts.get(r["category"], 0) + 1
    stats = {
        "articles": len(rows),
        "writers": len(set(r["author"].get_id() for r in rows if r["author"] is not None)),
        "sources": sum(int(r["n_sources"] or 0) for r in rows),
    }
    if category:
        rows = [r for r in rows if r["category"] == category]
    q = clean(query, 80).lower()
    if q:
        def hit(r):
            hay = " ".join([r["title"] or "", r["dek"] or "",
                            (r["author"]["display_name"] or "") if r["author"] else ""]).lower()
            return all(word in hay for word in q.split())
        rows = [r for r in rows if hit(r)]
    lead = None
    if not q:
        lead = next((r for r in rows if r["featured"]), rows[0] if rows else None)
    rest = [card(r) for r in rows if lead is None or r.get_id() != lead.get_id()][:60]
    return {
        "lead": card(lead) if lead else None,
        "items": rest,
        "counts": counts,
        "stats": stats,
        "category": category or "",
        "query": q,
    }


@api
def get_article(no):
    a = get_article_row(no)
    viewer = me()
    if a["status"] != "published" and not (same_user(viewer, a["author"]) or is_admin(viewer)):
        raise Oops("Specimen #%s is still in the lab and hasn't been published yet. 🔬" % a["specimen_no"])
    d = full_article(a, viewer)
    if a["author"] is not None:
        more = app_tables.articles.search(tables.order_by("published_at", ascending=False),
                                          author=a["author"], status="published")
        d["more"] = [card(r) for r in more if r.get_id() != a.get_id()][:3]
    else:
        d["more"] = []
    return d


@api(user=True)
def get_article_for_edit(no):
    a = get_article_row(no)
    if not same_user(me(), a["author"]):
        raise Oops("Only the writer of an article can edit it.")
    return {
        "no": int(a["specimen_no"]),
        "status": a["status"],
        "title": a["title"] or "",
        "dek": a["dek"] or "",
        "body": a["body"] or "",
        "category": a["category"] or "",
        "evidence": a["evidence"] or "",
        "cover": a["cover"] or "",
        "review_note": a["review_note"] or "",
        "sources": [{"url": s["url"], "title": s["title"], "publisher": s["publisher"], "kind": s["kind"]}
                    for s in sources_of(a)],
    }


def _clean_sources(sources):
    out = []
    for i, s in enumerate(sources or []):
        url = clean(s.get("url"), 600)
        title = clean(s.get("title"), 200)
        publisher = clean(s.get("publisher"), 100)
        if not (url or title or publisher):
            continue  # an empty row the writer never filled in
        if not url:
            raise Oops("Source #%d needs a link. Paste the web address of the study or page." % (i + 1))
        if not C.is_url(url):
            raise Oops("Source #%d doesn't look like a web link. It should start with https://" % (i + 1))
        kind = s.get("kind") if s.get("kind") in C.SOURCE_KIND else "other"
        out.append({"url": url, "title": title or C.domain_of(url), "publisher": publisher, "kind": kind})
    if len(out) > C.SOURCES_MAX:
        raise Oops("That's a lot of sources! Please keep it to %d or fewer." % C.SOURCES_MAX)
    return out


@api(user=True)
def save_article(no, fields, sources, submit=False, acknowledge_unsourced=False):
    """Save a draft, or submit it for review. Returns {"no", "status"} or {"needs_ack": True}."""
    user = me()
    title = clean(fields.get("title"), C.TITLE_MAX)
    dek = clean(fields.get("dek"), C.DEK_MAX)
    body = (fields.get("body") or "")[:C.BODY_MAX]
    category = fields.get("category") if fields.get("category") in C.CATEGORY else ""
    evidence = fields.get("evidence") if fields.get("evidence") in C.EVIDENCE_LEVEL else ""
    cover = fields.get("cover") if fields.get("cover") in C.COVERS else ""
    srcs = _clean_sources(sources)

    if len(title) < 4:
        raise Oops("Give your article a title (at least 4 characters).")
    if submit:
        if not dek:
            raise Oops("Add a one-line summary. It's what readers see on the front page.")
        if len(body.strip()) < C.BODY_MIN_SUBMIT:
            raise Oops("The article body is a bit short. Write at least %d characters before submitting."
                       % C.BODY_MIN_SUBMIT)
        if not category:
            raise Oops("Pick a field (Space, Critters, Chemistry…) before submitting.")
        if not evidence:
            raise Oops("Choose an evidence level so readers know how solid the science is.")
        if not srcs and not acknowledge_unsourced:
            return {"needs_ack": True}

    if no:
        a = get_article_row(no)
        if not same_user(user, a["author"]):
            raise Oops("Only the writer of an article can edit it.")
        was = a["status"]
    else:
        a = None
        was = None

    cited = [n for n in C.cited_numbers(body) if 1 <= n <= len(srcs)]
    words = len(body.split())
    values = dict(
        title=title, dek=dek, body=body, category=category, evidence=evidence, cover=cover,
        n_sources=len(srcs), n_cited=len(cited), reading_min=max(1, int(round(words / 200.0))),
        updated=now(),
    )
    if submit:
        values.update(status="pending", submitted_at=now())
    else:
        values.update(status="draft")
    if was == "published":
        values["featured"] = False

    if a is None:
        a = _create(user, values)
    else:
        a.update(**values)

    for s in app_tables.sources.search(article=a):
        s.delete()
    for i, s in enumerate(srcs):
        app_tables.sources.add_row(article=a, position=i, **s)

    if submit:
        log(a, "submitted", "Resubmitted after revisions" if was in ("rejected", "published") else "")
    elif was in ("pending", "published"):
        log(a, "withdrawn", "Moved back to drafts by the writer")
    return {"no": int(a["specimen_no"]), "status": a["status"]}


@tables.in_transaction
def _create(user, values):
    return app_tables.articles.add_row(
        specimen_no=next_specimen_no(), author=user, created=now(), boops=0, featured=False,
        review_note="", **values)


@api(user=True)
def withdraw_article(no):
    a = get_article_row(no)
    if not same_user(me(), a["author"]):
        raise Oops("That's not your article.")
    if a["status"] != "pending":
        raise Oops("Only articles waiting for review can be withdrawn.")
    a.update(status="draft", updated=now())
    log(a, "withdrawn", "Withdrawn from review by the writer")
    return {"no": int(a["specimen_no"]), "status": "draft"}


@api(user=True)
def delete_article(no):
    a = get_article_row(no)
    user = me()
    if not (same_user(user, a["author"]) or is_admin(user)):
        raise Oops("That's not your article.")
    if a["status"] == "published" and not is_admin(user):
        raise Oops("Published articles can only be removed by a Lab Director. Edit it instead, or ask a Director.")
    for table in (app_tables.sources, app_tables.boops, app_tables.lab_log):
        for r in table.search(article=a):
            r.delete()
    a.delete()
    return {"deleted": True}


@api(user=True)
def my_articles():
    rows = app_tables.articles.search(tables.order_by("updated", ascending=False), author=me())
    return [card(r) for r in rows]


@api(user=True)
def toggle_boop(no):
    a = get_article_row(no)
    if a["status"] != "published":
        raise Oops("You can only boop published articles.")
    user = me()
    existing = app_tables.boops.get(article=a, user=user)
    if existing is None:
        app_tables.boops.add_row(article=a, user=user, at=now())
        booped = True
    else:
        existing.delete()
        booped = False
    n = len(app_tables.boops.search(article=a))
    a["boops"] = n
    return {"booped": booped, "boops": n}


@api(user=True)
def preview_body(body, sources):
    srcs = []
    for s in sources or []:
        url = clean(s.get("url"), 600)
        title = clean(s.get("title"), 200)
        if not (url or title or clean(s.get("publisher"))):
            continue  # same numbering rule as saving: blank rows don't count
        ok = C.is_url(url)
        srcs.append({"url": url if ok else "", "title": title or (C.domain_of(url) if ok else "")})
    return Render.markdown((body or "")[:C.BODY_MAX], srcs)
