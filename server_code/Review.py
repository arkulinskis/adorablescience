# Review — the Lab Director's desk. Nothing reaches the front page without passing through here.
import anvil.tables as tables
from anvil.tables import app_tables

from . import lab_config as C
from .Lab import Oops, api, card, clean, full_article, get_article_row, log, me, now, opt


def _snapshot_checks(a):
    """Study snapshot lines: who or what was studied, and a caveat when the results are early-stage."""
    key = opt(a, "study_subject")
    subject = C.STUDY_SUBJECT.get(key)
    size = opt(a, "study_size")
    caveat = opt(a, "caveat")
    if subject:
        who = "%s %s" % (subject["emoji"], subject["phrase"]) + (" · %s" % size if size else "")
    else:
        who = "Missing: people, animals, cells, a model…? Ask the writer to fill in the study snapshot."
    needed = C.needs_caveat(key, a["evidence"])
    if not needed:
        why = "Not needed for %s" % (subject["label"].lower() if subject else "this evidence level")
    elif caveat:
        why = "🐴 " + caveat
    elif subject and subject["early"]:
        why = "Missing: results in %s need a \"Hold your horses\" line" % subject["label"].lower()
    else:
        why = "Missing: preprints and speculative stories need a \"Hold your horses\" line"
    return [
        {"ok": subject is not None, "label": "Says who or what was studied", "detail": who},
        {"ok": not needed or bool(caveat), "label": "Early-stage results have a caveat", "detail": why},
    ]


def _checks(a, sources):
    """Automatic checks shown to the reviewer next to the article."""
    body = a["body"] or ""
    n = len(sources)
    cited = [x for x in C.cited_numbers(body) if 1 <= x <= n]
    insecure = [s for s in sources if s["url"].lower().startswith("http://")]
    news_only = n > 0 and all(s["kind"] == "news" for s in sources)
    words = len(body.split())
    checks = [
        {"ok": n >= 1, "label": "Has at least one source",
         "detail": "%d source%s linked" % (n, "" if n == 1 else "s") if n else "No sources at all. Be extra skeptical."},
        {"ok": n >= 3, "label": "Well sourced (3+)", "detail": C.citation_meter(n, len(cited))["label"]},
        {"ok": n == 0 or len(cited) == n, "label": "Every source is cited in the text",
         "detail": "%d of %d cited inline" % (len(cited), n) if n else "Nothing to cite"},
        {"ok": not news_only, "label": "Links beyond news coverage",
         "detail": "Only news reports, so check for the original study" if news_only else "Includes primary or expert sources"},
        {"ok": not insecure, "label": "Secure links (https)",
         "detail": "%d link%s use plain http" % (len(insecure), "" if len(insecure) == 1 else "s") if insecure else "All good"},
        {"ok": words >= 150, "label": "Substantial body (150+ words)", "detail": "%d words" % words},
        {"ok": bool(a["evidence"]), "label": "Evidence level declared",
         "detail": C.EVIDENCE_LEVEL[a["evidence"]]["label"] if a["evidence"] in C.EVIDENCE_LEVEL else "Missing"},
    ]
    # (the "No retracted or flagged papers" line comes later from Sources.check_retractions: it needs Crossref)
    return checks + _snapshot_checks(a)


@api(admin=True)
def review_queue():
    rows = app_tables.articles.search(tables.order_by("submitted_at", ascending=True), status="pending")
    return [card(r) for r in rows]


@api(admin=True)
def get_review(no):
    a = get_article_row(no)
    d = full_article(a, me())
    d["checks"] = _checks(a, d["sources_list"])
    return d


@api(admin=True)
def decide(no, decision, note="", feature=False):
    a = get_article_row(no)
    note = clean(note, C.NOTE_MAX)
    if a["status"] != "pending":
        raise Oops("This article isn't waiting for review any more (it's %s)."
                   % C.STATUSES.get(a["status"], ("unknown",))[0].lower())
    if decision == "approve":
        a.update(status="published", published_at=now(), reviewer=me(), review_note=note,
                 featured=bool(feature), updated=now())
        log(a, "approved", note)
    elif decision == "send_back":
        if len(note) < 5:
            raise Oops("Tell the writer what to fix. A short note helps them get it published.")
        a.update(status="rejected", reviewer=me(), review_note=note, featured=False, updated=now())
        log(a, "sent_back", note)
    else:
        raise Oops("Unknown decision.")
    return {"no": int(a["specimen_no"]), "status": a["status"]}


@api(admin=True)
def published_list():
    rows = app_tables.articles.search(tables.order_by("published_at", ascending=False), status="published")
    return [card(r) for r in rows]


@api(admin=True)
def set_featured(no, flag):
    a = get_article_row(no)
    if a["status"] != "published":
        raise Oops("Only published articles can be featured.")
    a["featured"] = bool(flag)
    log(a, "featured" if flag else "unfeatured", "")
    return {"no": int(a["specimen_no"]), "featured": bool(flag)}


@api(admin=True)
def unpublish(no, note=""):
    a = get_article_row(no)
    note = clean(note, C.NOTE_MAX)
    if a["status"] != "published":
        raise Oops("That article isn't published.")
    if len(note) < 5:
        raise Oops("Leave the writer a note explaining why it was taken down.")
    a.update(status="rejected", review_note=note, featured=False, reviewer=me(), updated=now())
    log(a, "unpublished", note)
    return {"no": int(a["specimen_no"]), "status": "rejected"}
